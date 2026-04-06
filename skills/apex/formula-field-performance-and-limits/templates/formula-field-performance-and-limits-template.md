# Formula Field Performance and Limits — Work Template

Use this template when diagnosing SOQL performance problems caused by formula fields, hitting formula compile-size limits, or deciding whether to replace a formula field with a stored indexed field.

---

## Scope

**Skill:** `formula-field-performance-and-limits`

**Request summary:** (fill in what the user or practitioner asked for)

---

## Context Gathered

- **Object name:** _______________
- **Formula field name(s):** _______________
- **Approximate record count on object:** _______________
- **Is this field used in a SOQL WHERE clause, ORDER BY, or report filter?** Yes / No
- **SOQL query or debug log excerpt:** (paste here)
- **Query Plan Tool result (TableScan: true/false):** _______________
- **Number of cross-object spanning relationships in formula:** _______________
- **Estimated compiled formula size:** _______________  (verified by save attempt: Yes / No)

---

## Problem Classification

Check all that apply:

- [ ] Formula field in SOQL WHERE / ORDER BY / GROUP BY causing full table scan
- [ ] Formula compile-size limit exceeded or approaching limit
- [ ] Cross-object spanning limit at or near 10 relationships
- [ ] Trigger or CDC subscription incorrectly targeting a formula field
- [ ] Stored mirror field introduced but backfill not completed

---

## Approach

Which pattern from SKILL.md applies?

- [ ] **Materialize to stored field + Flow sync** — formula field in SOQL filter on LDV object
- [ ] **Split with helper formula fields** — compile-size limit exceeded
- [ ] **Replace with Flow-managed stored field** — spanning limit or CDC/trigger requirement
- [ ] **No action needed** — low record volume, formula only used for display

Justification: _______________

---

## Design Decisions

**Stored field name and type:** _______________

**Flow entry condition (to avoid unnecessary evaluations):** _______________

**Backfill method:** [ ] Batch Apex  [ ] Data Loader  [ ] Other: _______________

**Custom index request needed?** Yes / No — justification: _______________

---

## Checklist

Copy from SKILL.md and tick as complete:

- [ ] No formula field used as a filter, sort, or grouping criterion in SOQL on an LDV object
- [ ] Formula compile size verified within 5,000 compiled characters
- [ ] Cross-object spanning relationships counted and within 10-relationship limit
- [ ] Stored-field replacement backfilled for all existing records
- [ ] Record-Triggered Flow confirmed active on both Create and Update paths
- [ ] Query Plan Tool confirms `TableScan: false` on updated SOQL
- [ ] CDC/trigger requirements addressed with stored field if applicable

---

## Notes

Record any deviations from the standard pattern and why:

_______________
