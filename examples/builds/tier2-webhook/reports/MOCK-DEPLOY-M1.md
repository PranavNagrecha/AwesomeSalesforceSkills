# Mock deploy — tier2-webhook M1 in progress (validation only, nothing deployed)

## Run 1 — 2026-09-12, source mode, M1-S01 + M1-S02 (API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 --step M1-S02`

**Failed — 23 components, 22 ok, 2 errors.** M1-S01's object, twelve fields, the Case field and the platform event all
validated on first contact; the Named Credential validated. The failures:

| Component | Error |
|---|---|
| `ExternalCredential OnCall_Tool_EC` | `The parameter type "AuthHeader" requires these fields: ParameterValue.` |
| `PermissionSet Tier2_Webhook_Admin` | `The OnCallToolNamedPrincipal parameter value doesn't exist or you may not have permission to access it.` |

**S2-F-02 (HIGH, build + skill + clarifier).** An `AuthHeader` external-credential parameter must carry `parameterValue`
(the header's formula, e.g. `{!$Credential.<EC>.<ParamName>}`). The builder omitted it deliberately because no answer
named the parameter the API key is stored under — the clarifier never asked it, and never asked the endpoint URL
either (driver's log 26). The cited skill's example carries a dangling `$Credential.Partner_Orders_EC.ApiToken` with
no declared parameter (27). Remedy: the requester supplies both facts (recorded on the step by amendment); the skill
gains two Questions-to-Ask rows, a corrected example and a checker rule (AuthHeader without `parameterValue` → ERROR
with the org's text); rebuild M1-S02.

**S2-F-03 (cascade).** The permission set's `externalCredentialPrincipalAccesses` grant names the principal of the
credential that failed in the same deploy; expected to clear once the External Credential validates (re-check in run 2).

## Run 2 — 2026-09-12, source mode, M1-S01 + M1-S02 after the S2-F-02 rebuild (API 67.0)

**Succeeded — 23 total, 24 ok, 0 error(s).**
S2-F-02 closed (the AuthHeader formula parses on deploy); S2-F-03 was a cascade and cleared with it. Runtime header behaviour is confirmed at UAT.

## Run 3 — 2026-09-12, source mode, M1-S01 … M1-S04 (the Apex steps compiled by the org; API 67.0)

**Failed — 39 total, 29 ok, 11 error(s).**

| Component | Error |
|---|---|
| ApexClass | CaseTriggerHandler | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | IntegrationFailureResendTest | FAIL — field 'Request_Payload__c' can not be filtered in a query call |
| ApexClass | IntegrationFailureResendTest | FAIL — field 'Request_Payload__c' can not be filtered in a query call |
| ApexClass | IntegrationFailureTriggerHandler | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | Tier2EscalationService | FAIL — Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2EscalationServiceTest | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | Tier2WebhookFinalizer | FAIL — Dependent class is invalid and needs recompilation:
| ApexClass | Tier2WebhookQueueable | FAIL — Method was removed after version 58.0: getSalesforceBaseUrl |
| ApexClass | Tier2WebhookQueueableTest | FAIL — Dependent class is invalid and needs recompilation:
| ApexTrigger | CaseTrigger | FAIL — Variable does not exist: CaseTriggerHandler |
| ApexTrigger | IntegrationFailureTrigger | FAIL — Variable does not exist: IntegrationFailureTriggerHandler |


Triage: eleven errors, two roots, the rest cascade (`Dependent class is invalid`, `Variable does not exist: <handler>`).
M1-S04's four classes compiled clean.

**S2-F-04 (HIGH, build + skill).** `URL.getSalesforceBaseUrl()` — `Method was removed after version 58.0` — used by
`Tier2EscalationService` and `Tier2WebhookQueueable` for the link back to the Case. At API 67.0 the replacement is
`URL.getOrgDomainUrl()`. The skill example that carries the old method is the source to fix.

**S2-F-05 (MEDIUM, build + skill).** `IntegrationFailureResendTest` filters a SOQL query on `Request_Payload__c`
(Long Text Area) — `field 'Request_Payload__c' can not be filtered in a query call`. Long/rich text areas cannot be
filtered, grouped or sorted; the test must select and assert instead. `apex/test-class-standards` and
`admin/object-creation-and-design` gain the rule.

## Run 4 — 2026-09-12, source mode, M1-S01 … M1-S04 after the S2-F-04/S2-F-05 rebuild (API 67.0)

**Succeeded — 38 total, 39 ok, 0 error(s).**
Every Apex class and trigger of M1-S03 and M1-S04 compiled; S2-F-04 and S2-F-05 closed by the org.

## Run 5 — 2026-09-12, MANIFEST mode, milestone M1 (M1-S01 … M1-S05; the merged package.xml is what deploys; API 67.0)

**Succeeded — 38 total, 39 ok, 0 error(s).**
The build-level manifest (33 members incl. 13 ApexClass + 2 ApexTrigger) validates as a unit: this is the shape a real deployment would use.

## Run 6 — 2026-09-12T13:08Z, MANIFEST mode, milestone M1, `--test-level RunSpecifiedTests` (first run with Apex executing; API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --mode manifest --milestone M1 --test-level RunSpecifiedTests`
→ `reports/mock-deploy/2026-09-12T13-08-43Z/`

- status: **Failed** (checkOnly true). Components 39/39 ok — the metadata and the Apex compile exactly as runs 1–5 said.
- tests: level RunSpecifiedTests · **passed 0 · failed 28** · coverage 34.9%. Every test method in `Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest`, `IntegrationFailureResendTest` and `Tier2ChannelHealthTest` fails with one of two errors: `System.QueryException: No such column 'Tier2_Notified_At__c' on entity 'Case'` (user-mode SOQL) or `System.DmlException: Operation failed due to fields being inaccessible on Sobject Case / Integration_Failure__c` (`AccessLevel.USER_MODE` DML, surfacing at the test's own `insert` line because the trigger runs in user mode).
- **S2-F-11 (HIGH).** The tests run as the deploying user with no `System.runAs` of a permissioned user. The fields ship in this deployment; `Tier2_Webhook_Admin` carries their field permissions but no test assigns it; the deploying user's profile is not in the package, so it holds no FLS on the new fields. The code's user-mode enforcement (M1-S03 inputs) is correct — the tests are the first user-mode caller and were written as if the running user were omnipotent. A production deploy would fail identically. `templates/apex/tests/TestUserFactory.cls` (builds a user and assigns permission sets) exists and was not used. Runs 1–5 could not see this: `runTestsEnabled: false` on every one of them (S2-F-06).
- Tool note: `requested_tests` lists `MockHttpResponseGenerator` and `TestDataFactory` (class-level `@IsTest` helpers with no test methods) — the documented over-inclusion; harmless here, but the scan should require a test method.
- Consequence: the milestone gate accepted at 12:57Z rested on compile-only evidence. Skill rule first (apex/test-class-standards + fls skill), then M1-S03 and M1-S04 re-run (documented → running) for their test classes, tester, doc-keeper, run 7 with tests, and the acceptance re-signed.

## Run 7 — 2026-09-12T16:50Z, SOURCE mode, M1-S01 … M1-S04 after the S2-F-11 test repairs, `--test-level RunSpecifiedTests` (API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --step M1-S01 --step M1-S02 --step M1-S03 --step M1-S04 --test-level RunSpecifiedTests`

- status: **Failed**. Components 40/40 ok (TestUserFactory compiles). tests: passed 0 · **failed 30** — every method, at each class's `@TestSetup` seed insert of Case, now *inside* `System.runAs(agent)`: `System.DmlException: Operation failed due to fields being inaccessible on Sobject Case`.
- Operator probe (scratch copy, `Tier2EscalationServiceTest.seed` wrapped to report `getDmlFieldNames`, describe results and the running user): `createable=true Subject=true Status=true Origin=true AccountId=false Tier2_Notified_At__c=true profile=Standard User psa=1 | fields=AccountId | code=CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY`. The permission set is assigned and grants the custom field; the insert fails on **`AccountId`**.
- **S2-F-12 (HIGH, library).** `TestDataFactory.createCases(count, accountId, overrides)` — a verbatim copy of `templates/apex/tests/TestDataFactory.cls` — sets `AccountId = accountId` unconditionally, so a null argument still marks the field populated. In API 67.0 Apex runs in user context by default (apexdev L11741–11743), so the test's plain `insert` checks FLS on every populated field, and the Standard User in this org has no create access on `Case.AccountId`. The S2-F-11 repair was correct and exposed the next layer: the seed data must be creatable by the permissioned user, and the shared factory must not populate lookups it was not given. Fix at the template (assign lookups only when non-null) → both Apex steps re-run (their factory copies are verbatim) → run 8.
- Also answered: the "setup objects in user mode" ambiguity from the M1-S04 repair was never reached — it stays open for run 8.

## Run 8 — 2026-09-12T17:07Z, MANIFEST mode, whole build after the S2-F-12 repairs and the M1-S05 rebuild (34 members), `--test-level RunSpecifiedTests` (API 67.0)

`python3 scripts/mock_deploy.py plan.json --org-alias sfskills-dev --mode manifest --test-level RunSpecifiedTests` → `reports/mock-deploy/2026-09-12T17-06-54Z/`

- status: **Failed**. Components 40/40 ok. tests: **run 29 · passed 28 · failed 1 · coverage 74.0%** — from 0/30 in runs 6 and 7. The "setup objects in user mode" ambiguity (D-M1S04-10) is answered: the roster and schedule methods pass as the Standard User.
- The one failure: `Tier2EscalationServiceTest.ownerChangeToTier2QueueEscalatesAndStamps` — "A successful escalation writes no failure row: Expected 0, Actual 2". The stamps assertion before it passed (the webhook path succeeded).
- Operator probe (scratch copy, the assertion replaced by a dump of the rows): both rows are `Severity Error — "Tier2_Escalation__e publish rejected: Access to entity 'Tier2_Escalation__e' denied"`, one per escalated Case.
- **S2-F-13 (HIGH, design).** `Tier2EscalationService` publishes the platform event as the running user; at the 67.0 user-context default `EventBus.publish` requires Create on the event object, and neither `Tier2_Webhook_Admin` nor any shipped permission set grants `Tier2_Escalation__e`. In production every Tier 1 agent who reassigns a case to the Tier 2 queue would trip this — the webhook still fires (the Queueable is enqueued regardless) but each escalation writes a spurious failure row and the event never reaches subscribers. Fix at M1-S02: a permission set granting Create (and Read) on `Tier2_Escalation__e` to the users who escalate — the plan's decisions name who that is; the library gets the rule (platform-event publishers need object Create, and the checker should look for a permission set that grants it).
- Also from this run: **coverage 74.0% is under the 75% production floor** — `Tier2WebhookFinalizer` 63 of 76 lines uncovered (its retry/abandon paths are not exercised by the mocks) — a test-coverage obligation for the milestone, not a defect in the shipped code. Tool item: the summary should flag coverage under 75% explicitly.

## Run 9 — 2026-09-12T17:17Z, MANIFEST mode, whole build after the S2-F-13 repair (Create/Read on `Tier2_Escalation__e` in `Tier2_Webhook_Admin`), `--test-level RunSpecifiedTests` (API 67.0)

- Components 40/40 ok. tests: **run 30 · passed 30 · failed 0** · coverage **70.8%**. S2-F-13 closed by the org.
- status: **Failed** with zero component errors and zero test failures — the validation fails on the **75% coverage floor** alone. `Tier2WebhookFinalizer` is the gap (63 of 76 lines uncovered in run 8): the transient-retry, abandon-after-last-attempt and permanent-failure paths are asserted through the Queueable but the finalizer's own branches are not exercised. **S2-F-14 (MEDIUM, test coverage):** M1-S03 needs finalizer-path tests (a finalizer can be unit-tested by invoking `execute(FinalizerContext)` with a stub context, or by driving the Queueable to each outcome under `Test.stopTest()`) — a test-only addition, no shipped-code change. Until it lands, a production deploy of this milestone is refused by the platform, which is exactly the condition the tool's summary should print in words: tool item — flag `coverage < 75%` explicitly as the reason a zero-error run reports Failed.

## Run 10 — 2026-09-12T17:44Z, SOURCE mode, whole build after the S2-F-14 coverage repair (new `Tier2WebhookFinalizerTest`), `--test-level RunSpecifiedTests` (API 67.0)

- Components 41/41 ok — the org accepted a test class that implements `System.FinalizerContext` as a stub (the technique the repair flagged UNVERIFIED: it compiles at 67.0). tests: **run 34 · passed 33 · failed 1 · coverage 86.8%** — the 75% floor is cleared.
- The one failure: `transientFailureBelowAttemptCeilingIsRecordedRetryingAndReEnqueuedOnce` — the finalizer's re-enqueue of `Tier2WebhookQueueable` executed inside the test and threw its own designed transient exception (`Transient failure on attempt 2 of 3 … will retry`, `Tier2WebhookQueueable.execute` line 340). **S2-F-15 (LOW, test design):** the re-enqueued job must not run to a designed failure inside the test — register a 2xx `MockHttpResponseGenerator` before the boundary so the retry succeeds, or assert the enqueue without forcing execution. Test-only; shipped code unchanged.

## Run 11 — 2026-09-12T17:56Z, SOURCE mode, whole build after the S2-F-15 fix, `--test-level RunSpecifiedTests` (API 67.0)

- Components 41/41 ok. tests: **run 35 · passed 35 · failed 0** · coverage 86.2%. Every test the build ships passes in the org.
- status still **Failed**, zero errors, zero failures. The raw result carries the reason the summary did not print: `codeCoverageWarnings: Tier2EscalationService — Test coverage of selected Apex Class is 53.659%, at least 75% test coverage is required`. With `RunSpecifiedTests` the platform requires **each** class in the deployment to reach 75% individually, not only the aggregate. **S2-F-16 (MEDIUM, test coverage):** `Tier2EscalationService` (41 lines, 19 uncovered in run 9) needs its branches exercised — test-only. Tool item: print `codeCoverageWarnings` in the summary; the aggregate line alone misled the reader twice today.

## Run 12 — 2026-09-12T18:06Z, SOURCE mode, whole build after the S2-F-16 coverage tests, `--test-level RunSpecifiedTests` (API 67.0)

- **Succeeded.** Components 41/41 ok. tests: **run 37 · passed 37 · failed 0 · coverage 89.9%**, no coverage warnings. The org accepts this milestone's Apex under the same rules a production deploy applies (validate-only; nothing saved). Six findings from tests executing (S2-F-11..16), all closed; three of them became library rules today. Remaining for the milestone: M1-S03 tester + doc-keeper, M1-S05 re-run (two new ApexClass members: `TestUserFactory` already added; `Tier2WebhookFinalizerTest` pending), a manifest-mode run 13 on the rebuilt manifest, and the gate re-signed on this evidence.

## Run 13 — 2026-09-12T18:21Z, MANIFEST mode, the rebuilt 35-member build manifest (`artefacts/M1-S05/package.xml`), `--test-level RunSpecifiedTests` (API 67.0)

- **Succeeded.** Components 41/41 ok, no drift, no missing members. tests: **run 37 · passed 37 · failed 0 · coverage 89.9%**, no coverage warnings. This is the package a release would validate, validated the way a production deploy validates. The milestone gate is re-signed on this run (`gate milestone:M1 reject` then `approve`, the CLI's only path to a re-sign) once M1-S05 is tested and documented.
