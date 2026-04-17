# Gotchas — sfdx-hardis Integration

## Gotcha 1: Plugin version drift

**What happens:** CI and local produce different output.

**When it occurs:** No version pin.

**How to avoid:** Pin `sfdx-hardis@X.Y.Z` in CI.


---

## Gotcha 2: Long monitor run

**What happens:** Daily job exceeds 2h.

**When it occurs:** Large orgs.

**How to avoid:** Monitor in scoped chunks or move to weekly.


---

## Gotcha 3: False-positive drift

**What happens:** Noise alerts.

**When it occurs:** Managed package auto-updates.

**How to avoid:** Maintain an ignore list.

