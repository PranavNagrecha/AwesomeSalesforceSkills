# Worked example — Northwind Enterprise sales process (project tier, status `done`)

The largest of the five scenarios: one requirement in plain English — give the Enterprise team its own way of selling without touching the SMB team's pipeline — taken through sixteen steps, four milestones and nine human gates, validated against a real org without deploying, from first clarification on 12 September 2026 to acceptance on 3 October 2026. It crosses every technology the library covers: configuration (record types, stages, layouts), access (permission sets, a profile overlay), guardrails (validation rules with a custom-permission bypass), an approval process with workflow actions, Apex, a Lightning web component, a record page, reporting, and the compiled deliverables a client signs.

## Read in this order

1. `requirement.md` — the ask, seven items long.
2. `reports/drivers-log.md` — what it felt like to drive: every sprint, every decision, every friction item (72 of them, each one a tooling or contract fix that landed or is queued).
3. `PLAN.md` — the plan the clarifications produced (65 questions, 43 assumptions, 16 steps).
4. `reports/MOCK-DEPLOY-M1.md` … `MOCK-DEPLOY-M4.md` — the org's verdicts, 17 recorded runs, and the fourteen facts it taught (`N3-F-01..08`, `N4-F-01..06`).
5. `reports/MILESTONE-M1-REPORT.md` … `M4` — the four verifications; M1 by the agent, M2–M4 by the operator (fourteen minutes each).
6. `artefacts/M4-S03/` — the compiled workbook, traceability matrix, acceptance criteria and 73-case UAT pack.
7. `artefacts/M4-S04/deploy-order.md` — the two-request cutover runbook with every owned pre- and post-deploy step.
8. `decisions.md` — the register of every design decision and open item, append-only.

## What the org taught (and the library now enforces)

| Fact | Org message | Now a rule in |
|---|---|---|
| No default stage on an Opportunity business process | "Cannot specify a default on: Opportunity" | `admin/opportunity-management` OM-BP-DEFAULT-01 |
| Probability required on every Opportunity layout; Name/StageName Required | "Layout must contain an item for required layout field: Probability" / "Field:Name must be Required" | `admin/record-types-and-page-layouts` RTL-REQ-01/02 |
| A profile's record-type block must name a default or hide all | "No default record type specified for recordTypeVisibility" | `admin/permission-sets-vs-profiles` PSVP-RT-DEFAULT-01 |
| A validation rule's description is capped at 255 | "Validation rule description cannot be longer than 255 characters long" | `admin/validation-rules` VR-DESC-01 |
| Jest test folders reach the org without a `.forceignore` | LWC1503 ×13 on `getRecord.emit` | `scripts/mock_deploy.py` writes the standard ignore file |
| A persona test must seed its own object grant | "sObject type 'Opportunity' is not supported" under `WITH USER_MODE` | `apex/test-class-standards` Gotcha 17 |
| Chart dashboard components need `sortBy` and `chartAxisRange` | one attribute refused per run | `admin/reports-and-dashboards` RPT-DASH-SORT-01 / AXIS-01 |
| A custom report type's record-type column is the lookup's relationship name | three forms tried | `admin/reports-and-dashboards` gotcha N4-F-05 |
| A report cannot validate in the same deployment as its new type | "invalid report type" | runbook two-request split; gotcha N4-F-06 |

## What the loop could not see, and says so

Runtime behaviour (manager routing when the owner has no Manager; the product gate after a line-item deletion), the Jest suite (no harness in a build directory), the report and dashboard until the type exists, and two deploy-time risks the runbook makes blocking: a partial Opportunity object file that may replace the object definition, and a stage mapping the answers said would not be needed. Every one is an owned step in `artefacts/M4-S04/deploy-order.md`.

## Cost and shape

Roughly nine hours of granted sprint time across three weeks. Builders on Opus (12–25 minutes a step), testers and repairs on Sonnet (2–8 minutes), documentation by `scripts/render_step_docs.py` in seconds from M3 onward (the agent form of that pass had cost 250k–450k tokens a step), verification by the operator from M2 onward. Three builders ran in parallel where the plan allowed (M2); M3 and M4 were strict chains.

## Gates

| Gate | Signed | Notes |
|---|---|---|
| clarifications | 2026-09-12 | 65 questions, 30 informational left open with recorded defaults |
| plan (v2) | 2026-09-15 | after a verifier round |
| milestone:M1 | 2026-09-18 | four dry runs, four layout facts |
| step:M2-S01 | 2026-09-15 | bypass permission |
| step:M2-S02 | 2026-09-19 | record-type access; FLS grants added at repair |
| milestone:M2 | 2026-09-19 | operator-verified; 18/18 in the org |
| milestone:M3 | 2026-10-02 | 38/38 compile, 6/6 Apex tests, 95.6% |
| step:M4-S02 | 2026-10-02 | report type, report, dashboard |
| milestone:M4 | 2026-10-03 | build done; two runbook decisions attached |

## Regenerate

The build lives under gitignored `.sfskills/builds/northwind-sales/`; this folder is `python3 scripts/build_plan.py export` of it. `PLAN.md`, `CLARIFICATIONS.md` and the gate brief are rendered from `plan.json` — never hand-edit them. To re-render: `python3 scripts/build_plan.py render examples/builds/northwind-sales/plan.json`; to read any gate as a human did: `python3 scripts/build_plan.py brief examples/builds/northwind-sales/plan.json M4`.
