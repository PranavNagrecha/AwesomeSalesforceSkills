# RACI Matrix — Salesforce Project

> **What this template is for:** the *deliverable*. Copy it into your project workspace, fill the
> placeholders, mirror it into the YAML block at the bottom, lint with
> `python3 scripts/check_raci.py --file <path>/raci.yaml --repo-root <repo> --strict`, and circulate
> for sponsor review.
>
> The sibling template, `stakeholder-raci-for-sf-projects-template.md`, is the *intake sheet* — the
> context you gather before any cell here can be filled. Use both: intake first, then this.
>
> A filled version of everything below, for a two-region Service Cloud programme, is in
> `references/worked-examples.md`.

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

| Code | Role | Named individual | Org unit | Salesforce persona | User licence | Decision rights |
|---|---|---|---|---|---|---|
| BSP | Business sponsor | _____________ | _____ | Dashboard consumer | _____ | Scope, budget, go-live gate, licence tier |
| PO | Process owner | _____________ | _____ | _____ | _____ | Business process, UAT sign-off |
| DS | Data steward | _____________ | _____ | Data Loader user | _____ | Field semantics, dedupe, retention, load approval |
| SA | Security architect | _____________ | _____ | Setup-only admin | _____ | OWD, role hierarchy, sharing, restriction rules, FLS |
| IA | Integration architect | _____________ | _____ | Integration user owner | _____ | Integration pattern, contract, integration-user permissions |
| AL | CRM admin lead | _____________ | _____ | System Administrator | _____ | Declarative build, permission set composition |
| AD | Delegated administrator | _____________ | _____ | Delegated admin (group: _____) | _____ | User creation + assignment inside the delegate group only |
| RM | Release manager | _____________ | _____ | Deployment user | _____ | Promotion path, sandbox estate, hotfix, release updates |
| AX | AppExchange owner | _____________ | _____ | _____ | _____ | Decisions touching the package namespace; one row per package |
| CO | Compliance officer | _____________ | _____ | Audit reader | _____ | Retention, audit trail, regulated-data processing |
| EU | End-user representative | _____________ | _____ | _____ | _____ | UAT execution, adoption feedback |

Record the user licence as the `UserLicense.LicenseDefinitionKey` where you know it (`SFDC` for the
Full CRM user license, `AUL` for Salesforce Platform) so the register is checkable against the org.

## Decision matrix

Fill each cell with R, A, C, I, or `-` (not involved). Exactly one A per row, at least one R per row.
All ten activity rows are required — `check_raci.py` errors when a slug has no row.

| # | Activity (slug) | BSP | PO | DS | SA | IA | AL | RM | AX | CO | EU |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ACT-01 | Data model change (`data-model-change`) | I | C | A | C | C | R | I | C | C | I |
| ACT-02 | Sharing model change (`sharing-model-change`) | I | C | C | A | C | R | I | I | C | I |
| ACT-03 | Permission set change (`permission-set-change`) | I | C | I | C | I | A | I | I | I | I |
| ACT-04 | Integration change (`integration-change`) | I | I | C | C | A | R | C | I | C | I |
| ACT-05 | Release go / no-go (`release-go-no-go`) | A | C | C | C | C | R | R | I | C | C |
| ACT-06 | Sandbox refresh approval (`sandbox-refresh-approval`) | I | C | A | C | C | C | R | I | C | I |
| ACT-07 | Production hotfix (`production-hotfix`) | I | C | I | C | I | R | A | I | I | I |
| ACT-08 | Data load approval (`data-load-approval`) | I | C | A | I | C | R | C | I | C | I |
| ACT-09 | Release Update activation (`release-update-activation`) | I | I | C | C | C | R | A | C | I | I |
| ACT-10 | Seasonal release preview (`seasonal-release-preview`) | I | C | I | C | C | R | A | C | I | C |

Optional extra rows, added when they are live decisions on your programme: automation tier
(see `standards/decision-trees/automation-selection.md`) and license + edition.

(Add sub-rows where an activity needs scoping — e.g. two `data-model-change` rows, "regulated" and
"everything else", on a HIPAA or GDPR programme.)

## Escalation rules

One row per A cell from the matrix above.

| Activity | A (named) | Trigger | Target | Time-box |
|---|---|---|---|---|
| ACT-01 Data model change | _____________ | A and C disagree, or the change alters a field an integration writes | BSP | 5 business days |
| ACT-02 Sharing model change | _____________ | Requested visibility would cross a data-residency or regulatory boundary | CO | 3 business days |
| ACT-03 Permission set change | _____________ | Request carries Modify All Data, View All Data, or Manage Users | SA | 2 business days |
| ACT-04 Integration change | _____________ | Pattern change alters an external contract or needs a licence entitlement | BSP | 5 business days |
| ACT-05 Release go / no-go | _____________ | Any C votes no-go, or open P1 defects remain at the gate | Steerco | 1 business day |
| ACT-06 Sandbox refresh approval | _____________ | Unmerged work or unfinished UAT evidence exists in the sandbox | RM | 3 business days |
| ACT-07 Production hotfix | _____________ | Hotfix touches sharing, an integration user, or an integrated field | SA | 1 business day |
| ACT-08 Data load approval | _____________ | Load is a hard delete, or overruns the rehearsed row count materially | BSP | 2 business days |
| ACT-09 Release Update activation | _____________ | Sandbox testing shows a regression, or enforcement is two releases away | BSP | 10 business days |
| ACT-10 Seasonal release preview | _____________ | Preview finds a break in a business-critical flow, integration, or report | BSP | 5 business days |

The target must be someone other than that row's A. An escalation that points back at the person who
is already stuck is a loop, and no linter can tell it from a real rule.

## Programme escalation path

Per-row time-boxes promote an item to level 1. Level time-boxes promote it onward.

| Level | Forum | Chair | Time-box | Resolves |
|---|---|---|---|---|
| 1 | Design authority | _____________ | 3 business days | A and C disagree on one activity row |
| 2 | Steering committee | _____________ | 10 business days | Cross-team conflict, licence spend, scope change |
| 3 | Executive arbitration | _____________ | 20 business days | Steering deadlock, or a contested compliance veto |

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

## YAML artefact (the file that gets linted)

`check_raci.py` reads this shape from YAML or from JSON with the same keys. Fill it and run
`python3 scripts/check_raci.py --file raci.yaml --repo-root <repo> --strict`.
The full worked version — eleven stakeholders, ten activities, escalation path, refusal map,
decision log — is in `references/worked-examples.md` §3; copy from there rather than retyping.

```yaml
project: "<project name>"
phase: build                 # discovery | build | UAT | hypercare
version: "1.0.0"
sponsor_signoff: "YYYY-MM-DD"
next_review: "YYYY-MM-DD"

stakeholders:
  - code: BSP
    role: Business sponsor
    named: "<person>"
    org_unit: "<org unit>"
    sf_persona: "Dashboard consumer"
    license: "Salesforce (SFDC)"
    decision_rights: "Scope, budget, go-live gate, licence tier"
  # ... one entry per roster row above (PO, DS, SA, IA, AL, AD, RM, AX, CO, EU)

activities:
  - id: ACT-01
    activity: data-model-change
    label: "Add or change objects, fields, relationships, record types"
    cells:
      BSP: I
      PO: C
      DS: A
      SA: C
      IA: C
      AL: R
      RM: I
      CO: C
      EU: I
    escalation:
      trigger: "DS and the process owner disagree, or an integrated field changes"
      target: BSP
      time_box_business_days: 5
    executed_by:
      - agents/object-designer/AGENT.md
      - agents/field-impact-analyzer/AGENT.md
  # ... repeat for ACT-02 sharing-model-change, ACT-03 permission-set-change,
  #     ACT-04 integration-change, ACT-05 release-go-no-go,
  #     ACT-06 sandbox-refresh-approval, ACT-07 production-hotfix,
  #     ACT-08 data-load-approval, ACT-09 release-update-activation,
  #     ACT-10 seasonal-release-preview

escalation_path:
  - level: 1
    forum: "Design authority"
    chair: AL
    time_box_business_days: 3
    resolves: "A and C disagree on one activity row"
  - level: 2
    forum: "Steering committee"
    chair: BSP
    time_box_business_days: 10
    resolves: "Cross-team conflict, licence spend, scope change"

refusal_code_map:
  REFUSAL_SECURITY_GUARD:
    row: ACT-02
    ping: SA
    loop: [CO]
  REFUSAL_DATA_QUALITY_UNSAFE:
    row: ACT-08
    ping: DS
    loop: [PO]
  REFUSAL_NEEDS_HUMAN_REVIEW:
    row: "(named in the refusal message)"
    ping: "(the A on the matching row)"
    loop: ["(the C on that row)"]

decision_log:
  - id: DEC-001
    date: "YYYY-MM-DD"
    activity: ACT-01
    decision: "<what was decided>"
    decided_by: DS
    consulted: [PO, SA]
    alternatives_rejected: "<what was not chosen, and why>"
    reversal_cost: "Low | Medium | High"
    evidence: "<agent output, decision-tree step, or document path>"
```

Write block style only — the reader in `check_raci.py` is stdlib and deliberately restricted, so
inline flow mappings are rejected with a message telling you to expand them.


## Notes

| Rule | Enforced by `check_raci.py` |
|---|---|
| Exactly one A per activity | ERROR on zero or more than one |
| At least one R per activity | ERROR |
| A role is not both A and C on a row | ERROR |
| A role that is both A and R on a row | WARN — legal, but a matrix full of them delegates nothing |
| All ten required activity slugs have a row | ERROR on a missing slug |
| Every A has trigger + target + time-box, time-box > 0 | ERROR |
| Programme `escalation_path` with level + forum + time-box | ERROR |
| Cell values from `R` / `A` / `C` / `I` / `-` / empty | ERROR |
| Stakeholder codes unique, each with a role | ERROR |
| Every stakeholder has a named individual | WARN — an unnamed role is a project risk |
| `executed_by` repo paths resolve | WARN — usually an agent that was renamed |
| `refusal_code_map` present and its `ping` values are in the roster | WARN |

Two things the linter cannot check, which is why a human still reviews: whether the A is the *right*
person, and whether the escalation target is anyone other than the A. The matrix is version-locked per
phase — a new phase gets a new version, not an in-place edit.
