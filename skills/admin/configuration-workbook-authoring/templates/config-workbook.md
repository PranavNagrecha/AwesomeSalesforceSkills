# Configuration Workbook — `<Release_Name>`

> Canonical 10-section workbook template. Copy to
> `docs/workbooks/<release>/cwb.md` and fill. Empty sections stay in the file
> with a single row whose `target_value` is `not-in-scope-this-release`.
>
> Authoritative skill: `skills/admin/configuration-workbook-authoring`.
> Validate before sprint commit:
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
| `source_req_id` | yes | Fit-gap id from the RTM. |
| `source_story_id` | yes | User-story id (e.g. `US-2031`). |
| `recommended_agent` | yes | Single downstream runtime agent. Must resolve to a real `agents/<name>/AGENT.md`. |
| `recommended_skills[]` | yes (≥ 1) | Skill ids the executing agent should consult. |
| `status` | yes | One of `proposed`, `committed`, `in-progress`, `executed`, `verified`, `change-requested`. |
| `notes` | optional | Risks, ADR links, decision-tree branches cited. |

---

## Section 1 — Objects + Fields

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-OBJ-001 |  |  |  |  | object-designer |  | proposed |  |

---

## Section 2 — Page Layouts + Lightning Pages

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-PG-001 |  |  |  |  | lightning-record-page-auditor |  | proposed |  |

---

## Section 3 — Profiles + Permission Sets + PSGs

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-PSG-001 |  |  |  |  | permission-set-architect |  | proposed |  |

---

## Section 4 — Sharing Settings

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-SHR-001 |  |  |  |  | sharing-audit-agent |  | proposed | Cite `standards/decision-trees/sharing-selection.md`. |

---

## Section 5 — Validation Rules

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-VR-001 |  |  |  |  | validation-rule-auditor |  | proposed |  |

---

## Section 6 — Automation (Flow / Apex / Approvals)

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-AUT-001 |  |  |  |  | flow-builder |  | proposed | Cite `standards/decision-trees/automation-selection.md`. |

---

## Section 7 — List Views + Search

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-LV-001 |  |  |  |  | list-view-and-search-layout-auditor |  | proposed |  |

---

## Section 8 — Reports + Dashboards

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-RPT-001 |  |  |  |  | report-and-dashboard-auditor |  | proposed |  |

---

## Section 9 — Integrations

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-INT-001 |  |  |  |  | integration-catalog-builder |  | proposed | Reference Named Credentials by alias only. Never inline secrets. |

---

## Section 10 — Data + Migration

| row_id | target_value | owner | source_req_id | source_story_id | recommended_agent | recommended_skills | status | notes |
|---|---|---|---|---|---|---|---|---|
| CWB-DAT-001 |  |  |  |  | data-loader-pre-flight |  | proposed |  |

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
