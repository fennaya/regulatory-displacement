---
description: Propose specific, falsifiable observations for a claim — refuses vague criteria
argument-hint: <claim, or claim-id from falsification.md>
---

Given the claim in `$ARGUMENTS` (or ask what claim, if not given), do the
following. This command exists to produce criteria good enough to survive
someone trying to weasel out of them later — treat that as the actual
bar, not a formality.

1. State the claim back in one precise sentence. If the claim as given is
   too vague to falsify (e.g. "displacement is happening," "this
   substance matters"), stop and ask for a sharper version before
   proceeding — do not soften a vague claim into something falsifiable on
   the user's behalf without checking that's what they meant.
2. Propose the specific observation(s), with actual numbers/thresholds,
   not qualitative language, that would make you abandon the claim.
   Ground every threshold in something in this repo (an existing
   convention, a prior finding's magnitude, a power calculation) rather
   than an arbitrary round number picked for the occasion. Say where the
   number comes from.
3. Explicitly state what would NOT count as falsification, if there's an
   obvious near-miss someone might later claim counts (see the "Refuses"
   pattern already used in `falsification.md`).
4. Self-check before presenting: would a motivated person, arguing in
   good faith that the claim survived, be able to satisfy this criterion
   by finding a technicality? If yes, tighten it. A criterion that can
   always be explained away is not a falsification criterion.
5. If this is a new claim (not already in `falsification.md`): propose a
   claim-id (kebab-case) and offer to append an entry in the same format
   as the existing ones. If it's a refinement of an existing entry,
   propose the edit and show a diff rather than silently rewriting it —
   a falsification criterion that gets looser over time without anyone
   noticing is worse than not having one.
6. Do not write to `falsification.md` without the user confirming the
   wording. This command proposes; it doesn't unilaterally commit.

This command does not touch analysis code, the register, or results.
