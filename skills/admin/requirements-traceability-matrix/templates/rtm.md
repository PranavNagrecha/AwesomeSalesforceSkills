# Requirements Traceability Matrix — Skeleton

This file is the canonical RTM skeleton for a Salesforce project. Copy it into the
project repo at `governance/rtm.md` (markdown rendering) alongside `governance/rtm.csv`
(authoritative data) and regenerate the markdown from the CSV — never hand-edit the
markdown.

---

## Markdown Table Skeleton

| req_id | source | description | priority | story_ids | test_case_ids | defect_ids | sprint | release | status |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | interview | (one-sentence requirement) | must | US-101 | TC-201 |  | Sprint-1 | R1.0 | Released |
| REQ-002 | sow | (one-sentence requirement) | must | US-102\|US-103 | TC-202\|TC-203 | DEF-401 | Sprint-1 | R1.0 | Released |
| REQ-003 | regulatory | (one-sentence requirement) | must | US-104 | TC-204 |  | Sprint-2 | R1.0 | Released |
| REQ-004 | change-request | (one-sentence requirement) | should | US-105 |  |  | Sprint-2 | R1.1 | In Build |
| REQ-005 | interview | (one-sentence requirement) | could |  |  |  |  |  | Deferred |

For regulated projects, append two columns: `compliance_control_id` and `evidence_link`.

---

## CSV Schema

```csv
req_id,source,description,priority,story_ids,test_case_ids,defect_ids,sprint,release,status
```

Optional regulated columns appended:

```csv
req_id,source,description,priority,story_ids,test_case_ids,defect_ids,sprint,release,status,compliance_control_id,evidence_link
```

### Column Rules

| Column | Type | Allowed Values |
|---|---|---|
| `req_id` | string, unique, immutable | Project-prefixed: `REQ-001` or `ACME-REQ-001` |
| `source` | enum | `interview` / `sow` / `regulatory` / `change-request` / `defect-driven` |
| `description` | string | One-sentence requirement statement |
| `priority` | enum | `must` / `should` / `could` / `wont` (MoSCoW) |
| `story_ids` | string, multi-valued | Pipe-delimited: `US-101\|US-102` |
| `test_case_ids` | string, multi-valued | Pipe-delimited: `TC-201\|TC-202` |
| `defect_ids` | string, multi-valued | Pipe-delimited: `DEF-401\|DEF-402` |
| `sprint` | string | `Sprint-1`, `Sprint-2`, ... or empty |
| `release` | string | `R1.0`, `R1.1`, ... or empty until deploy |
| `status` | enum | `Draft` / `In Build` / `In UAT` / `Released` / `Deferred` / `Dropped` |
| `compliance_control_id` | string | Regulated only — e.g., `HIPAA-164.312(a)(1)` |
| `evidence_link` | string | Regulated only — relative path or URL |

### Multi-Value Delimiter

The pipe `|` is the only allowed delimiter inside a cell. Commas and semicolons must
be escaped or avoided because they collide with CSV format.

---

## JSON Envelope

For tool-to-tool exchange (e.g., handoff to `agents/deployment-risk-scorer/AGENT.md` or
`agents/audit-router/AGENT.md`), serialize the RTM as:

```json
{
  "schema_version": "1.0",
  "project": "ACME-Sales-Cloud",
  "phase": "R1.0",
  "generated_at": "2026-04-28T00:00:00Z",
  "rows": [
    {
      "req_id": "REQ-001",
      "source": "interview",
      "description": "Sales reps see only their accounts on My Accounts list view",
      "priority": "must",
      "story_ids": ["US-101"],
      "test_case_ids": ["TC-201"],
      "defect_ids": [],
      "sprint": "Sprint-1",
      "release": "R1.0",
      "status": "Released",
      "compliance_control_id": null,
      "evidence_link": null
    },
    {
      "req_id": "REQ-002",
      "source": "regulatory",
      "description": "Encrypt PHI fields at rest using Shield Platform Encryption",
      "priority": "must",
      "story_ids": ["US-201"],
      "test_case_ids": ["TC-501"],
      "defect_ids": [],
      "sprint": "Sprint-1",
      "release": "R1.0",
      "status": "Released",
      "compliance_control_id": "HIPAA-164.312(a)(2)(iv)",
      "evidence_link": "evidence/r1-encryption-test.pdf"
    }
  ],
  "summary": {
    "total_rows": 2,
    "by_status": {"Released": 2, "In Build": 0, "In UAT": 0, "Draft": 0, "Deferred": 0, "Dropped": 0},
    "by_source": {"interview": 1, "sow": 0, "regulatory": 1, "change-request": 0, "defect-driven": 0},
    "coverage_gaps": []
  }
}
```

### Envelope Rules

- `rows[].story_ids`, `test_case_ids`, `defect_ids` are JSON arrays of strings (never piped strings).
- The CSV-to-JSON converter splits the `|`-delimited cells into arrays.
- `summary` is computed from `rows` — never hand-written.
- `coverage_gaps` is the list of `req_id` values that fail the audit pass (status `Released` with empty `story_ids` or `test_case_ids`).

---

## Generation

Generate the markdown rendering and the JSON envelope from the CSV; never hand-maintain
either. The `scripts/check_rtm.py` checker validates the CSV. The Steerco rollup is
derived from the JSON envelope's `summary` block.
