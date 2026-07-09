# SOSL Search Result Limits — Diagnosis Worksheet

Use this worksheet to trace a "SOSL is dropping a record" report to the specific stage limit
responsible, then apply the documented remedy. Fill each section in order.

## Scope

**Skill:** `sosl-search-result-limits`

**Reported symptom:** (e.g. "record X matches but never appears", "search returns exactly 250",
"dynamic search returns zero rows", "AND behaves like OR")

**The SOSL statement under review:**

```apex
// paste the static [FIND ...] or the dynamic Search.query() call here
```

## Context Gathered

- **Static or dynamic?** static `[FIND ...]` / dynamic `Search.query(...)`
- **Object count (n) in RETURNING:** ____
- **Per-object clauses — does each have a WHERE / ORDER BY / LIMIT?** (list per object)
- **Running user holds View All Data?** yes / no  →  reproduced as the *affected* user? yes / no
- **Dynamic SearchQuery length (chars):** ____  (thresholds: 4,000 / 10,000; statement limit 100,000)

## Stage-Limit Triage

Check the first row that matches the symptom; that is your likely cause.

| Observation | Likely stage limit | Remedy |
|---|---|---|
| Returns exactly 250, single object, no WHERE/ORDER BY | 250 single-object default | Add `WHERE` or `ORDER BY` inside the object's `RETURNING` parentheses (→ up to 2,000) |
| Per-object counts shrink as objects are added; n ≥ 9 | min(2000/n, 250) split | Reduce object count or scope to the single needed object |
| Admin sees the record, standard user does not | Per-user permission filtering | Fix sharing/FLS/CRUD for the user; do **not** grant View All Data as a workaround |
| Dynamic query returns zero rows | SearchQuery > 10,000 chars | Bound the string length before `Search.query` |
| `AND`/`NOT` matches too broadly (dynamic) | SearchQuery > 4,000 chars (operators removed) | Bound the string length well under 4,000 chars |
| Record beyond ~2,000 scanned never matches | 2,000-record term-matching scan (API 28.0+) | Narrow the `FIND` term / scope to one object so the target is inside the scan window |
| Need > 2,000 total ordered rows | 2,000-per-statement ceiling | Redesign around SOQL / reporting; SOSL tops out at 2,000 total |

## Chosen Remedy

(state which stage limit was confirmed and the exact change applied, with the revised SOSL)

## Verification

- [ ] Re-ran the search **as the affected user** (not as an admin)
- [ ] Ran `scripts/check_sosl_search_result_limits.py --manifest-dir <apex-dir>` and addressed findings
- [ ] Confirmed the target record now returns (or documented why SOSL is the wrong tool here)
- [ ] Verified the change did not push a multi-object search past 8 objects or the statement past its char limit

## Notes

(record any deviation — e.g. intentionally accepting the 250 cap, or moving to SOQL — and why)
