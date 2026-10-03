# Worked examples of the build loop

Each folder here records one client-style requirement. Four of them went through the requirement-to-build loop
described in [`standards/build-orchestration.md`](../../standards/build-orchestration.md) and were copied out of the
gitignored `.sfskills/builds/<id>/` with `python3 scripts/build_plan.py export`. They were produced by running the
loop, not written by hand, so they keep the false starts, the rebuilds and the rejected plans (§ 9 of the contract
states this for `case-onboarding`; the others were made the same way, and every `plan.json` here passes
`build_plan.py validate`). The other two, `cold-start-lead-source` and `cold-start-case-escalation-email`, are
experiments: a fresh session was given the repository and one client sentence, and graded on whether it found the
loop at all. The second one did, so its folder is an exported build as well. Nothing in any folder was deployed.
Every build is `design-only`, the only contact with a Salesforce org was validate-only (`scripts/mock_deploy.py`,
which runs `sf project deploy start --dry-run`), and every gate was signed by someone standing in for the requester
(the dry-run operator, or in the cold start the session itself), which each gate record says.

To read a build, start from `plan.json`. It is the single source of truth, `scripts/build_plan.py` is its only
writer, and `PLAN.md`, `CLARIFICATIONS.md`, `RUN.md` (ask tier only) and the gate brief
(`python3 scripts/build_plan.py brief <plan.json> <milestone>`) are views rendered from it and never edited by hand.
`artefacts/<step>/` is what each step built, `tests/<step>/` is every checker run verbatim with its exit code, and
`envelopes/` holds the record of every agent run. Four files are written rather than rendered, and they carry the
judgement. `reports/drivers-log.md` is the human experience: what the person driving was asked, what they read,
how long it took and what hurt (the cold starts keep theirs at the folder root, written by the session itself).
`reports/MOCK-DEPLOY-<milestone>.md` is the org's verdict, run by run, with each run's raw output under
`reports/mock-deploy/<timestamp>/`. `reports/MILESTONE-<milestone>-REPORT.md` is the milestone verifier's
acceptance report, the evidence each milestone gate rests on. `decisions.md` is the append-only decision log.

## The five scenarios

The loop's definition of done is five end-to-end scenarios that differ in size, domain and method. Scenario 5 was
run twice, before and after the fix it prompted.

| # | Folder | Tier | Questions | Steps | Milestones | Gate records | Org dry runs | What it taught | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [`case-onboarding`](case-onboarding/) | project (no `scale` recorded; the default) | 97 | 22 (2 blocked by design) | 5 | 13 | 32 | The org is the last reviewer | `done` |
| 2 | [`tier2-webhook`](tier2-webhook/) | feature | 45 | 5 | 1 | 4 | 13 | Compile-only Apex evidence is not enough | `done` |
| 3 | [`northwind-sales`](northwind-sales/) | project | 65 | 16 | 4 | 9 | 16 | Step docs can be rendered | `done` |
| 4 | [`opp-amount-lock`](opp-amount-lock/) | ask | 13 | 1 | 1 | 3 (two decisions: `go`, `accept`) | 0 (one operator probe) | A skill's GOOD example failed | `done` |
| 5, run 1 | [`cold-start-lead-source`](cold-start-lead-source/) | none (loop not found) | none recorded | none | none | 0 | 0 | Library worked; loop was invisible | no build record |
| 5, run 2 | [`cold-start-case-escalation-email`](cold-start-case-escalation-email/) | feature | 19 | 1 | 1 | 3 | 0 | One CLAUDE.md paragraph fixed discoverability | `done` |

How each column was counted:

- **Tier, Questions, Steps, Milestones, Gate records, Status** come from each `plan.json`: `scale`,
  `clarifications[]`, `steps[]`, `milestones[]`, `human_gates[]` and `status`. Most of them print with
  `python3 scripts/build_plan.py status <plan.json>`. Run 1 of scenario 5 never created a `plan.json`; its folder
  holds a design document and a `deliverable/` (one field, one Flow).
- **Org dry runs** are the numbered runs in each build's `reports/MOCK-DEPLOY-*.md`, one validate-only request each.
  A set of lettered probes inside one numbered run counts once; an unnumbered probe table does not count. The run
  folders on disk do not match one for one:

| Folder | Numbered runs in `MOCK-DEPLOY-*.md` | Folders in `reports/mock-deploy/` | Why they differ |
|---|---|---|---|
| `case-onboarding` | 32 (M1 10, M2 3, M3 6, M4 4, M5 9) | 16 | No folder for runs before M3 run 2 (the first M1 runs called `sf` directly, before `mock_deploy.py` existed) or for probe runs on scratch copies; M5 run 4 left four folders, two without a `summary.md` |
| `tier2-webhook` | 13 | 13 | none |
| `northwind-sales` | 16 (M1 4, M2 3, M3 5, M4 4) | 17 | Two folders are `--plan-only` and never reached the org; the M2 probe run wrote no folder |
| `opp-amount-lock` | 0 | 0 | One operator probe on a scratch copy, recorded in `plan.json` (`steps[0].amendments`) and `artefacts/M1-S01/deploy-order.md` |

## Read this first: opp-amount-lock

[`opp-amount-lock`](opp-amount-lock/) is the loop at its smallest: a one-line ask, one step, and a human who reads
a handful of files and makes two decisions. The ask tier replaces the workbook and traceability matrix with one
rendered page, [`RUN.md`](opp-amount-lock/RUN.md), which the human reads at both gates. Read it beside this
walkthrough:

1. [`requirement.md`](opp-amount-lock/requirement.md) is one sentence from Sales Ops, with no requirements document
   and no org to read. The requester answered the blocking questions in `CLARIFICATIONS.md` and ran
   `ingest-answers` once.
2. `RUN.md` lines 1–5: the banner says the page is generated, then one paragraph of scope rendered from `plan.json`.
3. Lines 7–20, the step: `M1-S01`, owned by `metadata-builder`, citing `admin/validation-rules` and
   `admin/custom-permissions`, with four declared outputs each marked `exists`. The bypass permission set rides
   inside this one step, so the single up-front gate is where a human sees that access is being granted.
4. Lines 22–36, the tests: two skill checkers plus the always-on `xml` and `manifest` checks, each with the exit code
   recorded in `tests/M1-S01/results.json`.
5. Lines 38–62, the questions: the requester's answers in their own words, the one default they accepted, and the
   informational rows still open, each with its proposed default.
6. Lines 64–66, manual acceptance: the one test only a deployed org can show (blocked without the permission,
   allowed with it). The verifier's warning W2 says so.
7. Lines 70–71, gate 1 (`go`): one command writes the `clarifications` and `plan` records together, at one
   timestamp. The notes in `plan.json` `human_gates[]` list what was accepted knowingly: the bypass grant (W1),
   historical violations left in place (W6), the per-rule bypass name (W5).
8. Between the gates the step was reset and rebuilt once. The plan's blank guard `NOT(ISBLANK(StageName))`, copied
   from the skill's own GOOD example, did not compile in the operator's probe; `NOT(ISBLANK(TEXT(StageName)))` did.
   The amendment is in `plan.json`, the story in `artefacts/M1-S01/deploy-order.md`, and the skill now carries
   checker rule `VR-PICK-01`.
9. Line 72, gate 2 (`accept`): signed after `RUN.md` and
   [`reports/MILESTONE-M1-REPORT.md`](opp-amount-lock/reports/MILESTONE-M1-REPORT.md) (`ready-with-findings`,
   F-01..F-11). The notes turn each P1 finding into a decision, for example that assigning the permission set is a
   post-deploy Setup action.
10. Lines 74–80, next: the one `scripts/mock_deploy.py` command a human runs against their own org. It is printed,
    never run.

What the run cost, and the product defects it surfaced along the way, are in
[`reports/drivers-log.md`](opp-amount-lock/reports/drivers-log.md).

## The org as teacher

The loop's checkers and verifiers read files. Some platform rules were in no checker and no skill example, and a
few are not marked as required in the official guides either; the only way to learn them was to send the build to
an org in validate-only mode and read the refusal. Every such
refusal across the builds is below, with where it lives now. Finding ids are per build: `F-` in case-onboarding,
`S2-F-` in tier2-webhook, `N3-F-` and `N4-F-` in northwind-sales. Rows marked *tooling* were defects in
`scripts/mock_deploy.py` itself that an org run exposed. Where the answer is "not yet", the row says so.

| Finding | Build | What the org refused or required | Where it lives now |
|---|---|---|---|
| F-09, F-10 | case-onboarding | Case layouts must carry `ContactId`, `Description`, `SuppliedEmail`; `Status` must be Required | `admin/record-types-and-page-layouts` RL-REQ-01/02 |
| F-11 | case-onboarding | A BusinessProcess file stem must equal its `fullName` | `admin/case-management-setup` CMS-STEM-01/02 |
| F-13 | case-onboarding | CompactLayout manifest members are object-qualified (`Case.Case_Intake`) | `admin/list-views-and-compact-layouts` CL-MEM-01/02 |
| F-15 | case-onboarding | PermissionSet and Profile descriptions are capped at 255 characters | `admin/permission-set-architecture`, `admin/permission-sets-vs-profiles` DESC-01/02 |
| F-24 | case-onboarding | *Tooling:* only `.xml` files were assembled, so email template bodies were missing | `scripts/mock_deploy.py` copies every artefact file |
| F-25 | case-onboarding | `useSystemUserAsDefaultCaseUser` true needs `systemUserEmail` | `admin/case-management-setup` CMS-SYSUSER-01 |
| F-26 | case-onboarding | `newEntityRecordType` needs API 64.0 or later and the object-qualified form | `admin/email-to-case-configuration` E2C-RT-01/02 |
| F-27 | case-onboarding | Every Email-to-Case routing address needs `casePriority` | `admin/email-to-case-configuration` E2C-PRI-01 |
| F-28 | case-onboarding | An auto-response sender must already be a verified org-wide address | `admin/assignment-rules` Gotcha 7 and AR-SENDER-01; still the build's one open org prerequisite |
| F-36 | case-onboarding | An escalation action that notifies needs `notifyToTemplate` | `admin/escalation-rules` E10 |
| F-37 | case-onboarding | A test that uses a template class must ship that class | `apex/entitlement-apex-hooks` EAH009; `agents/apex-builder/AGENT.md` |
| F-38 | case-onboarding | A Create-triggered FlowTest takes `InputTriggeringRecordInitial` only | `flow/record-triggered-flow-patterns` checker rule 9 |
| F-49 | case-onboarding | A report description is capped at 255 characters | `admin/reports-and-dashboards` RPT-DESC-01/02 |
| F-50 | case-onboarding | The standard Case report type is `CaseList`; the owner grouping is `OWNER`; a column cannot also be a grouping | `admin/reports-and-dashboards` RPT-TYPE-01, RPT-GRP-01 |
| F-51 | case-onboarding | The `IsEscalated` report column code could not be found by probing | `admin/reports-and-dashboards` RPT-COL-01; unresolved, a deploy runbook step |
| F-59 | case-onboarding | Tests never ran as a permissioned user; the factory populated a null lookup | the S2-F-11 and S2-F-12 rules below |
| F-60 | case-onboarding | A persona with Create on Case but one field grant cannot work a case | `admin/permission-sets-vs-profiles` PSVP-FLS-01 |
| F-61 | case-onboarding | A `SeeAllData` test must select its entitlement process by name | `apex/entitlement-apex-hooks` EAH010 |
| F-62 | case-onboarding | The milestone stamp was refused in the persona's context and the error swallowed | `apex/entitlement-apex-hooks` Gotcha 14 |
| S2-F-02 | tier2-webhook | An `AuthHeader` external-credential parameter needs `parameterValue` | `apex/apex-named-credentials-patterns` NC-AUTH-01 |
| S2-F-04 | tier2-webhook | `URL.getSalesforceBaseUrl()` was removed after API 58.0 | Not yet: filed as driver's-log friction 38 and 39; `apex/pdf-generation-patterns` still shows the old method |
| S2-F-05 | tier2-webhook | A Long Text Area field cannot be filtered in SOQL | Not yet a rule in the skills the report names (friction 38) |
| S2-F-06 | tier2-webhook | *Tooling:* runs 1–5 executed no Apex tests (`runTestsEnabled: false`) | `scripts/mock_deploy.py --test-level` |
| S2-F-11 | tier2-webhook | Tests of user-mode Apex must `runAs` a permissioned user | `apex/test-class-standards` checker rule `user-mode-test-without-runas` |
| S2-F-12 | tier2-webhook | The shared factory set a null lookup, and user-mode DML checks FLS on it | `templates/apex/tests/TestDataFactory.cls`; `apex/test-class-standards` gotcha |
| S2-F-13 | tier2-webhook | Publishing a platform event needs Create on the event object | `apex/platform-events-apex`, `admin/permission-set-architecture` gotchas |
| S2-F-14 | tier2-webhook | Uncovered finalizer paths left a zero-error run under the 75% floor | Test-only repair; `scripts/mock_deploy.py` now prints the coverage refusal |
| S2-F-15 | tier2-webhook | A re-enqueued job ran to its designed failure inside a test | Test-only repair, recorded in the build |
| S2-F-16 | tier2-webhook | `RunSpecifiedTests` needs 75% coverage per class, not in aggregate | `scripts/mock_deploy.py` lists per-class coverage and flags classes under 75% |
| N3-F-01 | northwind-sales | An Opportunity business process cannot carry a default stage | `admin/opportunity-management` OM-BP-DEFAULT-01 |
| N3-F-02..04 | northwind-sales | Opportunity layouts need `Probability`; `Name`, `StageName`, `CloseDate` Required | `admin/record-types-and-page-layouts` RTL-REQ-01/02 |
| N3-F-05 | northwind-sales | A profile's record-type block must name a default or hide every type | `admin/permission-sets-vs-profiles` PSVP-RT-DEFAULT-01 |
| N3-F-06 | northwind-sales | A validation rule description is capped at 255 characters | `admin/validation-rules` VR-DESC-01 |
| N3-F-07 | northwind-sales | *Tooling:* Jest test folders reached the org with no `.forceignore` | `scripts/mock_deploy.py` writes the standard ignore file |
| N3-F-08 | northwind-sales | A persona test must seed its own object grant | `apex/test-class-standards` Gotcha 17 |
| N4-F-01, N4-F-05 | northwind-sales | A custom report type's record-type column is the lookup's relationship name alone | `admin/reports-and-dashboards` gotcha N4-F-05 |
| N4-F-03, N4-F-04 | northwind-sales | Chart dashboard components need `sortBy` and `chartAxisRange` | `admin/reports-and-dashboards` RPT-DASH-SORT-01, RPT-DASH-AXIS-01 |
| N4-F-06 | northwind-sales | A report cannot validate in the same deployment as its new report type | `admin/reports-and-dashboards` gotcha N4-F-06; the two-request runbook |
| (amendment) | opp-amount-lock | `ISBLANK` on a raw picklist does not compile; wrap it in `TEXT()` | `admin/validation-rules` VR-PICK-01 |

Not listed: cascades of a listed finding (S2-F-03 of S2-F-02, N4-F-02 of N4-F-01), a prediction that did not fire
(F-02), and verifier findings that an org run merely closed (F-43). The cold starts never reached an org.

## What the loop could not see

Validate-only means the org compiles and checks the build and runs the Apex tests asked for, but saves nothing
and does nothing a user would do. Each build says what that leaves unproven; collected here:

| Blind spot | Where it showed | How the build carries it |
|---|---|---|
| Runtime behaviour | northwind-sales: approval routing when the owner has no Manager, and the product gate after a line-item deletion (`reports/MOCK-DEPLOY-M2.md`, `MOCK-DEPLOY-M3.md`); tier2-webhook: the auth header at runtime (`reports/MOCK-DEPLOY-M1.md` run 2) | Owned steps in `northwind-sales/artefacts/M4-S04/deploy-order.md`; manual acceptance tests at UAT |
| Jest | northwind-sales ships `artefacts/M3-S04/lwc/discountApprovalPanel/__tests__/`, which never ran: a build directory has no Jest harness | Accepted at the M3 gate as reviewed, not run (`reports/drivers-log.md`) |
| A report and its new report type in one deployment | northwind-sales N4-F-06 (`reports/MOCK-DEPLOY-M4.md` runs 3–4); case-onboarding F-51, a filter column no probe could name | The two-request cutover in `northwind-sales/artefacts/M4-S04/deploy-order.md`; a runbook step for F-51 |
| Data, including permission-set assignment | northwind-sales `reports/MOCK-DEPLOY-M2.md` run 3; opp-amount-lock F-02 in `reports/MILESTONE-M1-REPORT.md` | Post-deploy Setup actions and UAT preconditions (opp-amount-lock gate notes; phase P of the northwind-sales runbook) |
| Org prerequisites with no metadata type | case-onboarding F-28: the auto-response sender must be a verified org-wide address | A named prerequisite at G3 and G5; the final manifest run is one error away from clean (`case-onboarding/reports/MOCK-DEPLOY-M5.md` run 9) |
| Risks only a real deploy settles | northwind-sales: a partial Opportunity object file may replace the object definition; reassigned deals need a stage mapping | Blocking steps in `northwind-sales/artefacts/M4-S04/deploy-order.md` |
| Apex tests, until the tool could run them | case-onboarding and tier2-webhook were first accepted on compile-only evidence, then reopened and re-signed | `scripts/mock_deploy.py --test-level RunSpecifiedTests` |
| Checkers the plan did not declare | cold-start-case-escalation-email: the flow naming checker found errors after `done` | Filed for the planner playbook (that folder's `README.md`) |

## Run one yourself

1. Read [`standards/build-orchestration.md`](../../standards/build-orchestration.md) § 3.1. You do not pick the
   tier by feel: the clarifier counts metadata types, skills with question tables, objects and integration, and
   prints a sizing line, which `init --scale <tier>` can override.
2. `python3 scripts/build_plan.py init --help` shows how a build directory is created
   (`.sfskills/builds/<id>/`, gitignored).
3. In Claude Code, `/build-from-requirements` walks the whole loop and `/run-build <build-dir> <milestone>` walks
   one milestone. [`commands/build-from-requirements.md`](../../commands/build-from-requirements.md) is the map,
   with the exact command sequence. Each stage stops at a human gate and prints the next command; no agent signs a gate.
4. To check your own build against an org you control: `python3 scripts/mock_deploy.py <plan.json> --org-alias
   <alias> --milestone M1`. It has no deploy option.
5. To keep a finished build as an example: `python3 scripts/build_plan.py export <plan.json> <dest-dir>`, which
   refuses until `validate` passes (§ 2 of the contract).
