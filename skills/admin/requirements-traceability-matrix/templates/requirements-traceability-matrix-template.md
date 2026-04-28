# Requirements Traceability Matrix — Work Template

Use this template when a Salesforce project needs an RTM authored, refreshed, or
audited. The canonical RTM artifact (markdown + CSV + JSON shapes) is in
`templates/rtm.md` next to this file.

## Scope

**Skill:** `requirements-traceability-matrix`

**Request summary:** (fill in what the user asked for — new RTM, refresh existing
RTM, run audit pass, prepare Steerco rollup, etc.)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Are requirement IDs already assigned?** (yes / no — if no, stop and assign in source-of-truth tool)
- **Agile tool of record:** (Jira / Azure DevOps / DevOps Center / GUS / other)
- **Test management tool:** (qTest / Zephyr / Xray / spreadsheet / etc.)
- **Defect tracker:** (Jira / Azure DevOps / GUS / other)
- **Regulatory posture:** (none / HIPAA / SOX / GxP / FedRAMP / other — affects column set)
- **RTM owner:** (named BA / delivery lead — single owner only)
- **Update cadence:** (per-sprint / per-release-gate)

## Approach

Which pattern from SKILL.md applies?

- [ ] CSV-in-Git as single source of truth (`templates/rtm.md` schema)
- [ ] Two-phase population (planning forward traces, build/UAT test traces)
- [ ] Regulated-project schema with `compliance_control_id` + `evidence_link`

Note any deviations from canonical patterns and why.

## Checklist

Copy the Review Checklist from SKILL.md and tick items as you complete them.

- [ ] Every row has a unique `req_id`; no duplicates
- [ ] Every requirement with status `Released` has at least one `story_ids` and one `test_case_ids` value
- [ ] Every requirement with status `In UAT` has at least one `test_case_ids` value
- [ ] Every requirement with status `Deferred` or `Dropped` has a documented decision (owner + date + rationale)
- [ ] Every status value is in the enum: `Draft / In Build / In UAT / Released / Deferred / Dropped`
- [ ] Every `source` value is in the enum: `interview / sow / regulatory / change-request / defect-driven`
- [ ] No requirement IDs reused across the project lifetime
- [ ] A 10% sample of test cases trace back to a requirement (backward traceability sample)
- [ ] Multi-valued cells use the pipe `|` delimiter
- [ ] Markdown rendering is generated, not hand-edited
- [ ] Regulated rows (if applicable) have populated `compliance_control_id` and `evidence_link`

## Notes

Record any deviations from the standard pattern and why. Capture decisions about
column-set extensions, ID prefixing schemes, or non-standard delimiters here so
the next BA inherits the conventions.
