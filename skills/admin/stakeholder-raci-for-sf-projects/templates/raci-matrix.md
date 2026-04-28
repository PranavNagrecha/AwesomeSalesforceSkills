# RACI Matrix — Salesforce Project

> Canonical template. Copy into your project workspace, fill the placeholders, run `python3 scripts/check_raci.py --json <path-to-json-mirror>` to validate, and circulate for sponsor review.

## Header

| Field | Value |
|---|---|
| Project | _____________ |
| Phase | discovery / build / UAT / hypercare |
| Version | 1.0.0 |
| Author | _____________ |
| Sponsor sign-off date | YYYY-MM-DD |
| Next review date | YYYY-MM-DD |

## Stakeholder roster

Fill a named individual for each role. If a role is unfilled, surface it as a project risk before publishing.

| Code | Role | Named individual | Notes |
|---|---|---|---|
| BSP | Business sponsor | _____________ | Holds A on scope/budget/license |
| PO | Process owner | _____________ | Holds A on data model + business process |
| DS | Data steward | _____________ | C on every data-model row |
| SA | Security architect | _____________ | A on security model |
| IA | Integration architect | _____________ | A on integration boundary |
| AL | CRM admin lead | _____________ | A on day-to-day automation |
| RM | Release manager | _____________ | A on deployment |
| AX | AppExchange owner | _____________ | A on managed-package namespace decisions; one per package in scope |
| CO | Compliance officer | _____________ | A on regulatory-control rows |
| EU | End-user representative | _____________ | C on process and UAT |

## Decision matrix

Fill each cell with R, A, C, I, or `—` (not involved). Exactly one A per row.

| Decision category | BSP | PO | DS | SA | IA | AL | RM | AX | CO | EU |
|---|---|---|---|---|---|---|---|---|---|---|
| Data model change | I | A | C | C | C | R | I | C | I | C |
| Automation tier | I | C | I | I | C | A | C | I | I | C |
| Security model | I | C | C | A | C | R | I | I | C | I |
| Integration boundary | I | C | C | C | A | R | C | I | C | I |
| Deployment | I | I | I | I | I | C | A | I | I | I |
| License + edition | A | C | I | C | I | C | I | C | I | I |

(Add sub-rows where a category needs scoping — e.g. "Data model — PHI" vs. "Data model — non-PHI" on regulated-data projects.)

## Escalation rules

One row per A cell from the matrix above.

| Decision category | A (named) | Trigger | Target | Time-box |
|---|---|---|---|---|
| Data model change | _____________ | A and C disagree | BSP | 5 business days |
| Automation tier | _____________ | Decision tree picks Apex / Platform Events | IA | 3 business days |
| Security model | _____________ | Requested control would block a documented business process | BSP | 3 business days |
| Integration boundary | _____________ | Pattern requires license tier upgrade | BSP | 5 business days |
| Deployment | _____________ | Change request bypasses sandbox path | BSP | 1 business day |
| License + edition | _____________ | Tier change requested | Steerco | 10 business days |

## Refusal-code-to-stakeholder map

Used by runtime agents in this repo when they emit a refusal code. Maps the code to the named A on the matching row.

| Refusal code | Decision category | Named A | C in the loop |
|---|---|---|---|
| `REFUSAL_NEEDS_HUMAN_REVIEW` | (named in refusal `message`) | (look up matching row) | (the C on that row) |
| `REFUSAL_INPUT_AMBIGUOUS` | (whichever category the input concerns) | (look up matching row) | (the C on that row) |
| `REFUSAL_SECURITY_GUARD` | Security model | _____________ (SA) | _____________ (CO if regulated) |
| `REFUSAL_POLICY_MISMATCH` | (depends) | (look up matching row) | BSP (informed) |
| `REFUSAL_MANAGED_PACKAGE` | License + edition (managed package scope) | _____________ (AX) | _____________ (PO) |
| `REFUSAL_COMPETING_ARTIFACT` | (depends) | (look up matching row) | (the C on that row) |
| `REFUSAL_DATA_QUALITY_UNSAFE` | Data model | _____________ (DS) | _____________ (PO) |
| `REFUSAL_FEATURE_DISABLED` | License + edition | _____________ (BSP) | _____________ (AL) |
| `REFUSAL_FIELD_NOT_FOUND` / `REFUSAL_OBJECT_NOT_FOUND` | Data model | _____________ (PO) | _____________ (DS) |
| `REFUSAL_STANDARD_SYSTEM_FIELD` | Data model | _____________ (PO) | — |
| `REFUSAL_OUT_OF_SCOPE` | (none — agent recommends a different agent) | — | — |
| `REFUSAL_OVER_SCOPE_LIMIT` | (none — partial result) | — | — |

## JSON mirror

`check_raci.py` validates this JSON shape:

```json
{
  "project": "Project Name",
  "phase": "build",
  "version": "1.0.0",
  "stakeholders": [
    {"code": "BSP", "role": "Business sponsor", "named": "Person A"},
    {"code": "PO", "role": "Process owner", "named": "Person B"},
    {"code": "DS", "role": "Data steward", "named": "Person C"},
    {"code": "SA", "role": "Security architect", "named": "Person D"},
    {"code": "IA", "role": "Integration architect", "named": "Person E"},
    {"code": "AL", "role": "CRM admin lead", "named": "Person F"},
    {"code": "RM", "role": "Release manager", "named": "Person G"},
    {"code": "AX", "role": "AppExchange owner", "named": "Person H"},
    {"code": "CO", "role": "Compliance officer", "named": "Person I"},
    {"code": "EU", "role": "End-user representative", "named": "Person J"}
  ],
  "rows": [
    {
      "decision": "Data model change",
      "cells": {
        "BSP": "I", "PO": "A", "DS": "C", "SA": "C", "IA": "C",
        "AL": "R", "RM": "I", "AX": "C", "CO": "I", "EU": "C"
      },
      "escalation": {
        "trigger": "A and C disagree",
        "target": "BSP",
        "time_box_business_days": 5
      }
    },
    {
      "decision": "Automation tier",
      "cells": {
        "BSP": "I", "PO": "C", "DS": "I", "SA": "I", "IA": "C",
        "AL": "A", "RM": "C", "AX": "I", "CO": "I", "EU": "C"
      },
      "escalation": {
        "trigger": "Decision tree picks Apex / Platform Events",
        "target": "IA",
        "time_box_business_days": 3
      }
    },
    {
      "decision": "Security model",
      "cells": {
        "BSP": "I", "PO": "C", "DS": "C", "SA": "A", "IA": "C",
        "AL": "R", "RM": "I", "AX": "I", "CO": "C", "EU": "I"
      },
      "escalation": {
        "trigger": "Requested control would block a documented business process",
        "target": "BSP",
        "time_box_business_days": 3
      }
    },
    {
      "decision": "Integration boundary",
      "cells": {
        "BSP": "I", "PO": "C", "DS": "C", "SA": "C", "IA": "A",
        "AL": "R", "RM": "C", "AX": "I", "CO": "C", "EU": "I"
      },
      "escalation": {
        "trigger": "Pattern requires license tier upgrade",
        "target": "BSP",
        "time_box_business_days": 5
      }
    },
    {
      "decision": "Deployment",
      "cells": {
        "BSP": "I", "PO": "I", "DS": "I", "SA": "I", "IA": "I",
        "AL": "C", "RM": "A", "AX": "I", "CO": "I", "EU": "I"
      },
      "escalation": {
        "trigger": "Change request bypasses sandbox path",
        "target": "BSP",
        "time_box_business_days": 1
      }
    },
    {
      "decision": "License + edition",
      "cells": {
        "BSP": "A", "PO": "C", "DS": "I", "SA": "C", "IA": "I",
        "AL": "C", "RM": "I", "AX": "C", "CO": "I", "EU": "I"
      },
      "escalation": {
        "trigger": "Tier change requested",
        "target": "Steerco",
        "time_box_business_days": 10
      }
    }
  ],
  "refusal_code_map": {
    "REFUSAL_SECURITY_GUARD": {"row": "Security model", "ping": "SA", "loop": ["CO"]},
    "REFUSAL_MANAGED_PACKAGE": {"row": "License + edition", "ping": "AX", "loop": ["PO"]},
    "REFUSAL_DATA_QUALITY_UNSAFE": {"row": "Data model change", "ping": "DS", "loop": ["PO"]},
    "REFUSAL_FEATURE_DISABLED": {"row": "License + edition", "ping": "BSP", "loop": ["AL"]},
    "REFUSAL_FIELD_NOT_FOUND": {"row": "Data model change", "ping": "PO", "loop": ["DS"]},
    "REFUSAL_OBJECT_NOT_FOUND": {"row": "Data model change", "ping": "PO", "loop": ["DS"]},
    "REFUSAL_STANDARD_SYSTEM_FIELD": {"row": "Data model change", "ping": "PO", "loop": []},
    "REFUSAL_NEEDS_HUMAN_REVIEW": {"row": "(per refusal message)", "ping": "(matching A)", "loop": ["(matching C)"]},
    "REFUSAL_INPUT_AMBIGUOUS": {"row": "(per input)", "ping": "(matching A)", "loop": ["(matching C)"]},
    "REFUSAL_POLICY_MISMATCH": {"row": "(per policy)", "ping": "(matching A)", "loop": ["BSP"]},
    "REFUSAL_COMPETING_ARTIFACT": {"row": "(per artifact)", "ping": "(matching A)", "loop": ["(matching C)"]}
  },
  "review_log": [
    {"date": "YYYY-MM-DD", "phase": "build", "attendees": ["BSP", "PO", "SA", "IA", "AL", "RM", "CO"], "next_review": "YYYY-MM-DD"}
  ]
}
```

## Notes

- One A per row is enforced by `check_raci.py`. Multiple As are a hard error.
- A role cannot hold both A and C in the same row.
- Every row must have at least one R.
- All cell values must be from the enum: `R`, `A`, `C`, `I`, or `—`.
- Every A cell must have an escalation rule with trigger + target + time-box.
- The matrix is version-locked per phase. New phase = new version, not in-place edit.
