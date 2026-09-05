# Configuration Workbook — `<Release_Name>`

> Canonical 10-section workbook template. Copy to
> `docs/workbooks/<release>/cwb.md` and fill. Empty sections stay in the file
> with a single row whose `target_value` is `not-in-scope-this-release`.
>
> Authoritative skill: `skills/admin/configuration-workbook-authoring`.
> Validate before sprint commit (exit code 1 on any finding, so it drops
> straight into a hook or a CI step; do not pass `--allow-empty-section` at
> commit time):
> `python3 skills/admin/configuration-workbook-authoring/scripts/check_workbook.py --workbook <path>`

---

## Header

| Field | Value |
|---|---|
| Release | `<release-id>` |
| Sprint commit date | `YYYY-MM-DD` |
| Author | `<name>` |
| Reviewers | `<name>, <name>` |
| RTM source | `<path or URL>` |
| Status | `draft` \| `committed` \| `executed` |

---

## RTM Linkage Block

Cross-reference table — every row in this workbook traces back to a fit-gap
row and a user story, and forward to a single downstream agent.

| row_id | source_req_id | source_story_id | recommended_agent | status |
|---|---|---|---|---|
| CWB-OBJ-001 | FG-014 | US-2031 | object-designer | proposed |

---

## Per-Row Schema

Every row in every section uses this schema:

| Field | Required | Notes |
|---|---|---|
| `row_id` | yes | Stable, unique within the workbook (e.g. `CWB-FIELDS-014`). |
| `section` | yes | Must match one of the 10 canonical section names below. |
| `target_value` | yes | The configurable value (API name, formula, picklist set, sharing rule criterion, etc.). |
| `owner` | yes | Named human accountable for this row. Not a team alias. |
| `source_req_id` | yes | The RTM `req_id` (`REQ-XXX`), immutable and never reused. |
| `source_story_id` | yes | User-story id (e.g. `US-2031`). |
| `recommended_agent` | yes | Exactly ONE runtime agent id, optionally followed by `--flag` arguments. Must resolve to `agents/<id>/AGENT.md` whose frontmatter `status` is not `deprecated`. |
| `recommended_skills[]` | yes (≥ 1) | Skill ids the executing agent must consult; every entry resolves on disk (`<domain>/<slug>`, `<domain>/<slug> -> references/<file>.md`, or a repo-relative `templates/…` / `standards/…` path). |
| `status` | yes | One of `proposed`, `committed`, `in-progress`, `executed`, `verified`, `change-requested`. |
| `notes` | optional | Risks, ADR links, decision-tree branches cited. |

---

## Section 1 — Objects + Fields

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-OBJ-001 |  |  |  |  | object-designer |  | proposed | The object's `sharingModel` (OWD) is a row here, not in Section 4. |

---

## Section 2 — Page Layouts + Lightning Pages

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-PG-001 |  |  |  |  | audit-router --domain=lightning_record_page |  | proposed | `path-designer` instead for Path + Guidance rows. |

---

## Section 3 — Profiles + Permission Sets + PSGs

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-PSG-001 |  |  |  |  | permission-set-architect |  | proposed |  |

---

## Section 4 — Sharing Settings

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-SHR-001 |  |  |  |  | audit-router --domain=sharing |  | proposed | Required: cite `sharing-selection.md` and the `Q<n>` branch that resolved it. OWD (`sharingModel`) belongs in Section 1, not here. |

---

## Section 5 — Validation Rules

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-VR-001 |  |  |  |  | audit-router --domain=validation_rule |  | proposed | Bypass infrastructure (Custom Permission + Custom Setting) is its own row. |

---

## Section 6 — Automation (Flow / Apex / Approvals)

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-AUT-001 |  |  |  |  | flow-builder |  | proposed | Required: cite `automation-selection.md` and the `Q<n>` branch that resolved it. `apex-builder` / `apex-refactorer` / `assignment-and-auto-response-rules-designer` per the branch. |

---

## Section 7 — List Views + Search

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-LV-001 |  |  |  |  | audit-router --domain=list_view_search_layout |  | proposed |  |

---

## Section 8 — Reports + Dashboards

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-RPT-001 |  |  |  |  | audit-router --domain=report_dashboard |  | proposed |  |

---

## Section 9 — Integrations

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-INT-001 |  |  |  |  | integration-catalog-builder |  | proposed | Reference Named Credentials by alias only. Never inline secrets. |

---

## Section 10 — Data + Migration

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-DAT-001 |  |  |  |  | data-loader-pre-flight |  | proposed | Cutover order for the whole release lives in this row's notes. |

---

## JSON Envelope Schema

The workbook's machine-readable companion (`cwb.json`) conforms to:

```json
{
  "release": "string (release id)",
  "sprint_commit_date": "YYYY-MM-DD",
  "author": "string",
  "reviewers": ["string"],
  "rtm_source": "string (path or URL)",
  "status": "draft | committed | executed",
  "rows": [
    {
      "row_id": "string (unique)",
      "section": "Objects+Fields | Page Layouts+Lightning Pages | Profiles+Permission Sets+PSGs | Sharing Settings | Validation Rules | Automation | List Views+Search | Reports+Dashboards | Integrations | Data+Migration",
      "target_value": "string",
      "owner": "string (named human)",
      "source_req_id": "string (RTM id)",
      "source_story_id": "string (story id)",
      "recommended_agent": "string (one of the runtime roster)",
      "recommended_skills": ["string (skill id)"],
      "status": "proposed | committed | in-progress | executed | verified | change-requested",
      "notes": "string (optional)"
    }
  ]
}
```

---

## CSV Schema

Flat one-row-per-row export at `cwb.csv`:

```
row_id,section,target_value,owner,source_req_id,source_story_id,recommended_agent,recommended_skills,status,notes
```

`recommended_skills` is pipe-delimited within the cell:
`admin/object-creation-and-design|admin/custom-field-creation`.

---

## Hand-off Block

After sprint commit, hand off rows to downstream agents:

| row_id | recommended_agent | invocation |
|---|---|---|
| CWB-OBJ-001 | object-designer | `Follow agents/object-designer/AGENT.md to execute row CWB-OBJ-001 from this workbook.` |
| CWB-PSG-001 | permission-set-architect | `Follow agents/permission-set-architect/AGENT.md in design mode to execute row CWB-PSG-001.` |
| CWB-AUT-001 | flow-builder | `Follow agents/flow-builder/AGENT.md to execute row CWB-AUT-001.` |
| CWB-SHR-001 | audit-router | `Follow agents/audit-router/AGENT.md --domain=sharing to verify row CWB-SHR-001.` |

---

## Descope / Defer Ledger

Requirements that deliberately produced no row. Keep it: a missing row is
invisible without it, and `agents/config-workbook-author/AGENT.md` Step 3
refuses (`REFUSAL_DESCOPE_BREACH`) if a descoped story reappears as a row.

| source_req_id | source_story_id | fit-gap decision | Recorded as | Rationale | Decided by | Date |
|---|---|---|---|---|---|---|
| `REQ-XXX` | `US-XXXX` | `descope` \| `defer` \| `escalate` | No workbook row / carried to `<release>` / ADR required | `<why>` | `<forum>` | `YYYY-MM-DD` |
