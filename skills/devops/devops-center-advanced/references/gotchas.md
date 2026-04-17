# Gotchas — DevOps Center Advanced Workflows

## Gotcha 1: WI merge conflict

**What happens:** Two admins edit same flow.

**When it occurs:** Parallel WIs.

**How to avoid:** DOC surfaces; resolve in GitHub with admin+dev review.


---

## Gotcha 2: Branch ≠ WI state

**What happens:** Branch pushed manually while WI is in progress.

**When it occurs:** Dev bypasses DOC.

**How to avoid:** Respect WI boundaries or mark WI as manual.


---

## Gotcha 3: Bypass becomes normal

**What happens:** Every deploy is 'emergency'.

**When it occurs:** Undisciplined team.

**How to avoid:** Track bypass rate; audit monthly.

