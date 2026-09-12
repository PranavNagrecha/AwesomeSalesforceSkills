# Mock deploy — milestone M5 in progress (validation only, nothing deployed)

## Run 1 — 2026-09-12, source mode, every built step M1-S01 … M4-S05 + M5-S01 (API 67.0)

**Failed — 60 components, 59 ok, 2 errors.** All three list views and the `ReportFolder Support_Operations` validated
(the folder's declared filename `Support_Operations-meta.xml` is accepted by the org — the step's F-B is a checker
recognition gap only). F-28 unchanged. New:

| Component | Error |
|---|---|
| `Report Support_Operations/Escalated_Open_Cases` | `Value too long for field: Description maximum length is:255` |

**F-49 (HIGH, build + skill).** The builder put its UNVERIFIED note into the report's `<description>`; the limit is 255.
`admin/reports-and-dashboards` has no description-length rule (the DESC rule family covers PermissionSet/Profile/
CustomPermission/CustomObject; Report needs one). Rebuild: description ≤ 255, notes stay in deploy-order.md.

## Operator probes on a scratch copy (nothing in the build changed)

With the description shortened, the org moved on to the report body:

| Probe | Result |
|---|---|
| `<reportType>Cases</reportType>` (the skill's UNVERIFIED value) | `invalid report type` |
| `<reportType>CaseList</reportType>` | accepted — validation moved to the grouping |
| grouping `USERS.NAME` (from the skill's example) | `Grouping: Invalid value specified: USERS.NAME` |
| grouping `OWNER` | accepted — validation moved to `You can't include groupings in the selected columns list: PRIORITY` (PRIORITY is both a column and a grouping in the built file — structural, fix by dropping one) |
| grouping `OWNER_NAME` | invalid |
| escalated filter column `ESCALATED`, `IS_ESCALATED`, `CASES.ESCALATED`, `ISESCALATED`, `CASE_ESCALATED` | all `filters-criteriaItems-column: Invalid value specified` |

**F-50 (HIGH, build + skill).** The standard Case report type's API name is `CaseList`, not `Cases`; the owner grouping
column is `OWNER`, not `USERS.NAME`; a field cannot be both a `<columns>` entry and a grouping. All three came from the
skill's example (marked UNVERIFIED there) and are now proven live.

**F-51 (MEDIUM, unresolved).** The `Case.IsEscalated` report column code could not be found by probing (five candidates
rejected). Per the skill's own rule, column codes are harvested from an org retrieve of an existing report — the honest
path is a deploy runbook step: deploy the report without the criterion, add "Escalated = True" in the report builder
(or retrieve one saved Case report to harvest the code), then re-export. Recorded, not guessed.

## Run 2 — 2026-09-12, source mode, every built step M1-S01 … M5-S01 after the F-49/F-50 rebuild (API 67.0)

**60 components, 60 ok, 1 error — F-28 only.** `Report Support_Operations/Escalated_Open_Cases` (`CaseList`, grouping
`OWNER` then `PRIORITY`, 219-char description, Escalated criterion deferred to the runbook per F-51) and its folder
validate. F-49 and F-50 closed in the build; the skill-side rules follow. Output: `reports/mock-deploy/2026-09-12T09-54-56Z/`.

## Run 3 — 2026-09-12, MANIFEST mode, every built step M1-S01 … M5-S05 (the merged package.xml, incl. the build-level M5-S05 manifest; API 67.0)

**Failed — 60 total, 60 ok, 1 error(s).**

| Component | Error |
|---|---|
| AutoResponseRule | Case.Case_Acknowledgement | FAIL — support-noreply@acme.example is an invalid From email address.: Email Address |

This is the first validation in the build that reads a manifest carrying the Apex (M4-S05's trigger and classes) — F-43 closed.

Still to validate for M5: nothing after this run; M5-S02 stays blocked.

## Run 4 — 2026-09-12T16:47Z, MANIFEST mode, every built step, `--test-level RunSpecifiedTests --tests CaseMilestoneServiceTest` (first run with Apex executing; API 67.0)

- As shipped: 60/60 components ok, 1 error — F-28 (the auto-response sender is not a verified org-wide address here), which stops the deployment before tests run (`run 0`). Tool notes: with `--milestone M5` the test scan found no `@IsTest` class because the Apex lives in M4-S05 and reaches M5 only through the build manifest — the scan should look at the assembled tree, not the selected steps; and `--milestone M5` alone copies only M5's files, so the 56-member manifest deploys with 8 missing files — the build-level manifest must be run with the default (every built step) selection, as run 3 was. Both queued for the tool.
- Operator probe on a scratch copy with the auto-response rule removed (the one F-28 component): 59/59 ok, tests **run 1 · passed 0 · failed 3**, coverage 36.4%. All three methods of `CaseMilestoneServiceTest` fail at their Case insert with `System.DmlException: Operation failed due to fields being inaccessible on Sobject Case` (`caseInsideProcess` line 103; `staysAtOneQueryAndOneDmlFor200Cases` line 193).
- **F-59 (HIGH).** The same pair of defects scenario 2 found today (S2-F-11, S2-F-12): the tests never run as a user holding the build's permission sets, and the step's `TestDataFactory` copy predates commit 5edcb3281 (null `AccountId` populated; user-mode DML at the 67.0 default checks FLS on it). Every earlier dry run of this build compiled the Apex and executed nothing (`runTestsEnabled: false`) — G4 and G5 rested on compile-only evidence for M4-S05. Fix: M4-S05 test-only repair (TestUserFactory + runAs of a user holding the M2 permission sets; refresh the factory copy) → tester → doc-keeper → run 5 with tests → note on the G4/G5 records.

## Run 5 (probe) — 2026-09-12T17:25Z, SOURCE mode, whole build minus the F-28 rule, after the M4-S05 test repair, `--tests CaseMilestoneServiceTest`

- 60/60 components ok; tests **0 passed · 4 failed**, all at the Case seed inside `System.runAs(agent)` (a `TestUserFactory` user on the shipped `Acme Support Tier 1` profile holding `Case_Agent_Core` + `Case_Tier1`): `Operation failed due to fields being inaccessible on Sobject Case`. Probe (`getDmlFieldNames`): **`Subject, Origin, AccountId, Priority, EntitlementId`** — every one a standard Case field.
- **F-60 (HIGH, design — the most consequential finding of this build).** `Case_Agent_Core` grants Create on Case with field permissions on exactly one field (`Severity__c`); `Case_Tier1` adds none; the shipped profile carries no field or object permissions at all (32 lines — by design, "all access comes from the group"). So the Tier 1 persona as shipped can create a Case object but cannot write Subject, Origin, Priority, the Account or the Entitlement — it cannot work a case. Standard fields carry field-level security exactly as custom fields do, and a permission set that is the persona's *only* source of access must list them; a profile deployed from metadata grants nothing it does not list. Five milestone verifications, every checker and two org dry runs passed this, because nothing in the library asserts that an object grant is accompanied by field grants for the fields the persona's layouts and processes use, and no Apex test ran as the persona until today. Fix: M2-S02 access-model repair (field permissions on the standard Case fields the Tier 1 layout and intake process use — the M2 workbook rows and the compact/record layouts name them) → the M4-S05 fixture seeds in `AccessLevel.SYSTEM_MODE` (fixture-only fields such as `EntitlementId` are not the persona's to set) and acts under `runAs(agent)` → run 6. Library: access-model skill gotcha + checker rule ("object Create/Edit granted with no field permissions on that object's standard fields → WARN"); test-class-standards Gotcha 15 (seed in system mode, act as the persona).

## Run 6 (probe) — 2026-09-12T17:47Z, SOURCE mode, whole build minus the F-28 rule, after the M2-S02 access repair (F-60) and the M4-S05 system-mode seeding (Gotcha 15), `--tests CaseMilestoneServiceTest`

- 60/60 components ok. tests **run 4 · passed 2 · failed 2** — the persona can now create and update the Case (F-59 and F-60 closed by the org). The two failures are the milestone assertions: *"No open 'First Response' milestone was generated for the test Case."*
- Operator check: the org has Entitlement Management on and one active process of its own, `Standard Case` (`sf data query … FROM SlaProcess`). The test's `requireActiveProcess()` selects `WHERE IsActive = true LIMIT 1` under `SeeAllData`, so it takes the org's process — which carries no `First Response` milestone — instead of the deployed `First_Response_Standard` / `First_Response_Premier`.
- **F-61 (MEDIUM, test grounding).** A `SeeAllData` test that needs a specific entitlement process must select it by name, never "any active one": in a target org with its own processes the test silently proves nothing. Fix: query the deployed process by its name (`First_Response_Standard`), assert exactly one, and fail with the process name if absent. Test-only. Library: entitlement-apex-hooks gotcha (SeeAllData + named process) — queue.

## Run 7 (probe) — 2026-09-12T17:57Z, SOURCE mode, whole build minus the F-28 rule, after the F-61 named-process fix, `--tests CaseMilestoneServiceTest`

- 60/60 components ok; tests run 4 · passed 2 · failed 2 · coverage 86.4%. The deployed `First_Response_Standard` process is found and the Case enters it (F-61 closed by the org).
- The two remaining failures are **behaviour**, the first functional Apex finding of this build: `skipsAMilestoneThatIsAlreadyCompleted` — *"A completed milestone must not be re-stamped … attempted > 0 means the CompletionDate = NULL filter is missing"* (Expected 0, Actual 1); `triggerWritesCompletionDateOnAnOpenMilestone` — *"CompletionDate is still null: the trigger did not run or the update did not take."* **F-62 (HIGH, shipped code or its user-mode context).** Either the service's `CaseMilestone` query lacks the open-milestone filter and its update never lands, or — the shape every other finding today took — the service now runs in the Tier 1 persona's context (67.0 user mode) and `CaseMilestone` is not writable by that persona (CaseMilestone.CompletionDate requires Edit on CaseMilestone, which no Tier 1 set grants), so the update silently affects nothing while the count of *attempts* is still 1. The repair must decide which, from the code and the persona's grants, and say so.

## Run 8 (probe) — 2026-09-12T18:2xZ, SOURCE mode, whole build minus the F-28 rule, after the F-62 system-mode boundary and the no-swallowed-errors assertions, `--tests CaseMilestoneServiceTest`

- **Succeeded.** 60/60 components ok; tests **run 4 · passed 4 · failed 0 · coverage 84.4%**, no coverage warnings. F-59, F-60, F-61 and F-62 closed by the org. The only thing between this build and a clean validation as shipped is F-28 (the verified sender address), the named org prerequisite recorded at G3 and G5.
- What changed since G5 was signed on compile-only evidence: `Case_Agent_Core` grants seven standard Case fields (M2-S02); `CaseMilestoneServiceTest` runs as the Tier 1 persona with system-mode seeding and a named process (M4-S05); `CaseMilestoneService` stamps milestones in an explicit system-mode boundary (M4-S05, shipped-code deviation § 11); `TestUserFactory` ships from M4-S05 and must join the M5-S05 manifest. Remaining bookkeeping: M4-S05 tester + doc-keeper, M5-S05 re-run (+1 member), and the G4/G5 records amended to cite this run.

## Run 9 — 2026-09-12T18:32Z, MANIFEST mode, the rebuilt 57-member build manifest as shipped, `--test-level RunSpecifiedTests` (API 67.0)

- Components **61/61 ok, 1 error** — `AutoResponseRule Case.Case_Acknowledgement`: the sender address is not a verified org-wide address in this org (F-28, the named prerequisite). No drift; `TestUserFactory` present. The org stops at the component stage, so the tests did not execute in this run; the tests-executing evidence for the same files is run 8 (probe minus the F-28 rule: Succeeded, 4/4, 84.4%). Final state of scenario 1 in this org: the build is a verified sender address away from a clean validation with its tests passing as the persona.
