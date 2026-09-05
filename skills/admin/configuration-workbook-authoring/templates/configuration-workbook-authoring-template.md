# Configuration Workbook Authoring — Work Template

Use this template to plan a workbook authoring or revision task before
starting. The actual workbook artifact is authored from
`templates/config-workbook.md` (the canonical 10-section skeleton).

## Scope

**Skill:** `configuration-workbook-authoring`

**Request summary:** (fill in what was requested — new workbook for release X,
mid-sprint change request adding rows for feature Y, etc.)

## Context Gathered

- RTM source: <path or URL>
- Approved user stories: <ids>
- Approved fit-gap rows: <ids>
- Descope / defer / escalate decisions: <req_ids and the decision for each>
- Target org alias: <alias>
- Org probe date (for `target_value` reality checks): <YYYY-MM-DD>
- Sprint / release id: <release-id>
- Existing committed workbook (if revising): <path>

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — Source-grounded row authoring
- [ ] Pattern 2 — Version-locking at sprint commit
- [ ] Pattern 3 — One row, one agent, one section

Format rules applied end to end, with a real checker run:
`references/worked-examples.md`. A full ten-section workbook for a real
solution: `skills/admin/case-management-setup/references/worked-example-case-intake.md`.

## Authoring Checklist

- [ ] Copied `templates/config-workbook.md` to `docs/workbooks/<release>/cwb.md`
- [ ] All 10 canonical sections present
- [ ] Every row has `row_id`, `source_req_id`, `source_story_id`
- [ ] Every row has exactly one `recommended_agent`, resolving to a
      non-deprecated `agents/<id>/AGENT.md` (validated against
      `agents/_shared/SKILL_MAP.md` and `agents/_shared/AGENT_DISAMBIGUATION.md`)
- [ ] Every row has at least one entry in `recommended_skills[]`, and every
      entry resolves to a file that exists on disk
- [ ] No row has placeholder status (`TBD`, `WIP`, `?`, a bare to-do marker, empty)
- [ ] No `target_value` is a Setup navigation path
- [ ] Every Section 4 row cites `sharing-selection.md` + its `Q<n>` branch
- [ ] Every Section 6 row cites `automation-selection.md` + its `Q<n>` branch
- [ ] No Section 3 row grants access through a Profile (residue only)
- [ ] No row has inline credentials in `target_value`
- [ ] The descope / defer / escalate ledger is written and no descoped
      `req_id` has a row
- [ ] `python3 scripts/check_workbook.py --workbook <path>` exits 0
- [ ] Version-locked: statuses set to `committed` **and** the file snapshotted
      at `docs/workbooks/<release>/cwb.md` and tagged
- [ ] Reviewers tagged

## Notes

(Record decisions, deviations, and links to ADRs.)
