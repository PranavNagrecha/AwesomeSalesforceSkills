# Probe Validation Report — 2026-04-17

**Status:** Wave 9 live-org validation
**Org alias:** `sfskills-dev`
**Org Id:** `00DdL00000rG7qDUAS`
**API version:** `66.0`
**Total queries tested:** 21
**Passed:** 21 (100% if total else 0)
**Failed:** 0

Validated by `scripts/validate_probes_against_org.py`. Re-run on any probe edit.

---

## Probe: `apex-references-to-field`

**Queries:** 2 — **Passed:** 2 — **Failed:** 0

| # | Status | Explanation |
|---|---|---|
| 1 | ⚠️ empty | Query succeeded via Tooling API, 0 rows |
| 2 | ⚠️ empty | Query succeeded via Tooling API, 0 rows |

---

## Probe: `flow-references-to-field`

**Queries:** 2 — **Passed:** 2 — **Failed:** 0

| # | Status | Explanation |
|---|---|---|
| 1 | ✅ success | Query succeeded, 65 row(s) |
| 2 | ⚠️ empty | Query succeeded via Tooling API, 0 rows |

---

## Probe: `matching-and-duplicate-rules`

**Queries:** 3 — **Passed:** 3 — **Failed:** 0

| # | Status | Explanation |
|---|---|---|
| 1 | ✅ success | Query succeeded, 1 row(s) |
| 2 | ✅ success | Query succeeded, 1 row(s) |
| 3 | ⚠️ empty | Query succeeded, 0 rows |

---

## Probe: `permission-set-assignment-shape`

**Queries:** 4 — **Passed:** 4 — **Failed:** 0

| # | Status | Explanation |
|---|---|---|
| 1 | ⚠️ empty | Query succeeded, 0 rows |
| 2 | ⚠️ empty | Query succeeded, 0 rows |
| 3 | ✅ success | Query succeeded, 4 row(s) |
| 4 | ✅ success | Query succeeded, 1 row(s) |

---

## Probe: `user-access-comparison`

**Queries:** 10 — **Passed:** 10 — **Failed:** 0

| # | Status | Explanation |
|---|---|---|
| 1 | ✅ success | Query succeeded, 1 row(s) |
| 2 | ✅ success | Query succeeded, 4 row(s) |
| 3 | ⚠️ empty | Query succeeded, 0 rows |
| 4 | ⚠️ empty | Query succeeded, 0 rows |
| 5 | ⚠️ empty | Query succeeded, 0 rows |
| 6 | ⚠️ empty | Query succeeded, 0 rows |
| 7 | ⚠️ empty | Query succeeded, 0 rows |
| 8 | ⚠️ empty | Query succeeded, 0 rows |
| 9 | ⏭️ feature-gated | Object is gated by 'Enterprise Territory Management' which is not enabled in this org (correct behavior, not a probe bug) |
| 10 | ⏭️ feature-gated | Object is gated by 'Enterprise Territory Management' which is not enabled in this org (correct behavior, not a probe bug) |

---

## Takeaways

All probe queries validated successfully. No Mode 1 hallucinations detected.

### What passing means

- ✅ **SUCCESS** — query executed, returned rows.
- ⚠️ **EMPTY-RESULT** — query executed, returned zero rows (structurally valid; org may simply not have matching data).
- ✅ **SUCCESS-VIA-TOOLING** — query failed on Data API, succeeded on Tooling API (the probe recipe should document this).
- ❌ **FAILED** — classified error (see mode). Requires probe fix or explicit documentation that this org lacks the feature.
