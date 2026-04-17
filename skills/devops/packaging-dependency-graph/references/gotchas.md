# Gotchas — Packaging Dependency Graph

## Gotcha 1: LATEST rot

**What happens:** Dev bumped base package; dependent silently breaks in prod.

**When it occurs:** Using @LATEST.

**How to avoid:** Pin versions.


---

## Gotcha 2: Circular dep

**What happens:** `sf package version create` fails with SSA_CYCLIC_DEP.

**When it occurs:** Two packages evolved into bidirectional refs.

**How to avoid:** Extract shared code to a third package.


---

## Gotcha 3: Promotion skip

**What happens:** Promoted service-core before sales-core; installer fails.

**When it occurs:** Alphabetical promotion.

**How to avoid:** Promote per the dependency graph.

