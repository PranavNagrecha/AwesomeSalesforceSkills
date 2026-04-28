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
- Target org alias: <alias>
- Sprint / release id: <release-id>
- Existing committed workbook (if revising): <path>

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — Source-grounded row authoring
- [ ] Pattern 2 — Version-locking at sprint commit
- [ ] Pattern 3 — One row, one agent, one section

## Authoring Checklist

- [ ] Copied `templates/config-workbook.md` to `docs/workbooks/<release>/cwb.md`
- [ ] All 10 canonical sections present
- [ ] Every row has `row_id`, `source_req_id`, `source_story_id`
- [ ] Every row has exactly one `recommended_agent` (validated against
      `agents/_shared/SKILL_MAP.md`)
- [ ] Every row has at least one entry in `recommended_skills[]`
- [ ] No row has placeholder status (`TBD`, `TODO`, `?`, empty)
- [ ] No row has inline credentials in `target_value`
- [ ] `python3 scripts/check_workbook.py --workbook <path>` exits 0
- [ ] Reviewers tagged

## Notes

(Record decisions, deviations, and links to ADRs.)
