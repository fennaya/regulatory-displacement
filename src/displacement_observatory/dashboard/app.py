"""STEP 7 dashboard: FastAPI + Jinja2 + HTMX + Plotly. No React.

Five views per the project brief:
  /findings          ranked displacement events by effect size, caveats on the card
  /events/{id}        one event: flows, event-time plot, competing explanations, evidence
  /watchlist          forthcoming restrictions, predicted destinations, forecast date
  /scorecard          forecasts vs what happened -- the credibility of the whole project
  /register           every restriction with its source clause
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from displacement_observatory.analysis.report import headline_eligible
from displacement_observatory.db import connect
from displacement_observatory.pipeline import PipelineBundle, run_pipeline

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_state: dict[str, PipelineBundle] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    con = connect(read_only=True)
    try:
        _state["bundle"] = run_pipeline(con)
    finally:
        con.close()
    yield
    _state.clear()


app = FastAPI(title="Displacement Observatory", lifespan=lifespan)


def get_bundle() -> PipelineBundle:
    return _state["bundle"]


def _headline(study):
    if study is None:
        return None, None, None
    post_ks = sorted(k for k in study.relative_years if k >= 0)
    if not post_ks:
        return None, None, None
    k = max(post_ks)
    return k, study.coef[k], (study.ci_low[k], study.ci_high[k])


@app.get("/")
def root():
    return RedirectResponse(url="/findings")


@app.get("/findings")
def findings(request: Request):
    bundle = get_bundle()
    cards = []
    for r in bundle.did_results:
        k, coef, ci = _headline(r.study) if r.status == "ok" else (None, None, None)
        eligible, eligible_reason = headline_eligible(r)
        cards.append({
            "event": r.event,
            "result": r,
            "k": k,
            "coef": coef,
            "ci": ci,
            "significant": (ci is not None and (ci[0] > 0 or ci[1] < 0)),
            "eligible": eligible,
            "eligible_reason": eligible_reason,
            "competing": bundle.competing.get(r.event.event_id),
        })
    cards.sort(key=lambda c: (c["coef"] if c["coef"] is not None else float("-inf")), reverse=True)
    return templates.TemplateResponse(
        request, "findings.html", {"cards": cards, "bundle": bundle, "active": "findings"}
    )


@app.get("/events/{event_id}")
def event_detail(request: Request, event_id: str):
    bundle = get_bundle()
    result = bundle.did_by_id().get(event_id)
    if result is None:
        raise HTTPException(status_code=404, detail="event not found")
    competing = bundle.competing.get(event_id)
    k, coef, ci = _headline(result.study) if result.status == "ok" else (None, None, None)
    eligible, eligible_reason = headline_eligible(result)

    chart_data = None
    if result.study is not None:
        ks = sorted(result.study.relative_years)
        chart_data = {
            "x": ks,
            "y": [result.study.coef[kk] for kk in ks],
            "ci_low": [result.study.ci_low[kk] for kk in ks],
            "ci_high": [result.study.ci_high[kk] for kk in ks],
        }

    return templates.TemplateResponse(
        request,
        "event_detail.html",
        {
            "event": result.event, "result": result, "competing": competing,
            "k": k, "coef": coef, "ci": ci, "eligible": eligible, "eligible_reason": eligible_reason,
            "chart_data": chart_data, "active": "findings",
        },
    )


@app.get("/watchlist")
def watchlist(request: Request):
    bundle = get_bundle()
    rows = list(zip(bundle.forecasts, bundle.forecast_scores))
    return templates.TemplateResponse(request, "watchlist.html", {"rows": rows, "active": "watchlist"})


@app.get("/scorecard")
def scorecard(request: Request):
    bundle = get_bundle()
    rows = list(zip(bundle.forecasts, bundle.forecast_scores))
    n_scored = sum(1 for _, s in rows if s.status == "scored")
    n_pending = sum(1 for _, s in rows if s.status == "pending")
    return templates.TemplateResponse(
        request,
        "scorecard.html",
        {
            "rows": rows, "n_scored": n_scored, "n_pending": n_pending,
            "rediscovery": bundle.rediscovery, "active": "scorecard",
        },
    )


@app.get("/register")
def register(request: Request):
    bundle = get_bundle()
    mapping_by_substance = {m.substance: m for m in bundle.mappings.mappings}
    return templates.TemplateResponse(
        request,
        "register.html",
        {
            "events": bundle.register.events, "dropped": bundle.register.dropped,
            "mapping_by_substance": mapping_by_substance, "mappings": bundle.mappings, "active": "register",
        },
    )
