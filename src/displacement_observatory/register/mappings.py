"""Substance -> HS6 mapping store.

Per project rules: an agent PROPOSES mappings with confidence and reasoning;
a human confirms each one once; confirmed mappings are frozen into this
versioned YAML file. HS6 is coarser than a single substance, so the
imprecision of each mapping is recorded explicitly rather than hidden.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

MAPPINGS_DIR = Path(__file__).resolve().parents[3] / "data" / "register" / "mappings"


class SubstanceMapping(BaseModel):
    substance: str
    hs6: str = Field(pattern=r"^\d{6}$")
    hs6_description: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    imprecision: str
    confirmed: bool
    confirmed_by: str
    confirmed_note: str


class MappingFile(BaseModel):
    version: int
    frozen_at: date
    mappings: list[SubstanceMapping]


def load_mappings(version: int) -> MappingFile:
    path = MAPPINGS_DIR / f"chemical_hs6_mappings_v{version}.yaml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return MappingFile.model_validate(raw)


def latest_version() -> int:
    versions = [
        int(p.stem.rsplit("_v", 1)[1])
        for p in MAPPINGS_DIR.glob("chemical_hs6_mappings_v*.yaml")
    ]
    if not versions:
        raise FileNotFoundError(f"No mapping files found in {MAPPINGS_DIR}")
    return max(versions)


def load_latest_mappings() -> MappingFile:
    return load_mappings(latest_version())


def mapping_by_substance(mapping_file: MappingFile) -> dict[str, SubstanceMapping]:
    return {m.substance: m for m in mapping_file.mappings}
