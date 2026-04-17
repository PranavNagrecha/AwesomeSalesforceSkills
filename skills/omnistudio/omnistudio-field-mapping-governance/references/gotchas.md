# Gotchas — OmniStudio Field Mapping Governance

## Gotcha 1: Renamed field

**What happens:** DR returns empty silently.

**When it occurs:** Pre-deploy test missed it.

**How to avoid:** CI field check + automated test.


---

## Gotcha 2: DR version sprawl

**What happens:** Many active versions; unclear which runs.

**When it occurs:** Dev edits without promotion.

**How to avoid:** Version discipline + archive old.


---

## Gotcha 3: Custom metadata refs to DR name

**What happens:** Break on rename.

**When it occurs:** Rename.

**How to avoid:** Rename via alias; update refs atomically.

