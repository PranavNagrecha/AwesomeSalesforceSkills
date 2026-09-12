# Traceability — REQ → step → artefact → test

Written by the build doc keeper.

Format: the build-layer RTM defined by `skills/admin/requirements-traceability-matrix`
(SKILL.md § "The Build-Layer RTM: `traceability.md`", worked through in
`references/worked-examples.md` § 4). The ten canonical build columns come first;
`artefact_paths` and `test_result` follow them because `agents/build-doc-keeper/AGENT.md`
Step 7 requires those two cells and the canonical set has no column for either. Lint with:

```bash
python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py \
  --file traceability.md --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
```

**Correction (2026-09-12, second pass):** the first pass through this file keyed `req_id` on the
raw clarification id (`Q10`, `Q12`, …) and reported the resulting `check_rtm.py` format errors as
an accepted, documented gap. That was wrong — this build's own precedent
(`examples/builds/case-onboarding/traceability.md` § "Requirement id derivation") already
establishes that a build with no formal elicitation pass still mints `REQ-XXX` ids at the
documentation step; the checker's key format is the contract regardless of whether intake was
formal. The seven rows below are now keyed on minted `REQ-001`–`REQ-007`, with the settling
clarification id preserved in `source`. See "Requirement id derivation" below the matrix for the
anchor from each minted id back to `requirement.md` and the clarification that settled it.

---

## Matrix

| req_id | source | requirement | step_id | artefact | agent | decision_ref | test_id | test_type | status | artefact_paths | test_result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | Q10 | If the Case-escalation transaction rolls back, nothing reaches the on-call tool or the dashboard; enqueue the callout and publish `Tier2_Escalation__e` only on commit (publish-after-commit semantics). | M1-S01 | `CustomObject:Tier2_Escalation__e` | metadata-builder | D10 | check_platform_events_apex | checker | In UAT | `artefacts/M1-S01/objects/Tier2_Escalation__e/Tier2_Escalation__e.object-meta.xml`\|`artefacts/M1-S01/package.xml`\|`artefacts/M1-S03/triggers/CaseTrigger.trigger`\|`artefacts/M1-S03/classes/CaseTriggerHandler.cls`\|`artefacts/M1-S03/classes/Tier2EscalationService.cls` | pass — `check_platform_events_apex.py --manifest-dir artefacts/M1-S01` exit 0 asserts `publishBehavior` `PublishAfterCommit` (R6); `check_platform_events_apex.py --manifest-dir artefacts/M1-S03` exit 0, zero findings (R1/R2/R7, `tests/M1-S03/results.json`). **Updated at the `M1-S03` documentation pass:** the sequencing half is now built and structurally verified by direct inspection — `Tier2EscalationService.escalate()` calls `EventBus.publish` before `CaseTriggerHandler`'s enqueue of `Tier2WebhookQueueable` runs, in the same escalating transaction, per the step's manual acceptance-test clause (a) (`artefacts/M1-S03/deploy-order.md` § 11(a): "the `EventBus.publish` call is in the service, in the escalating transaction ... not discarded and not inside the Queueable"). **No Apex test executed** — this is a design-only build with no target org, so the rollback behaviour itself (does a rolled-back transaction really suppress both the publish and the enqueue) rests on the platform's own transactional guarantee for `PublishAfterCommit` plus the code shape, not on a run test. **Manual test outstanding:** the step's manual clause (a), deferred to the M1 gate per `tests/M1-S03/results.json` → `skipped_manual[0]`, not ticked by any agent. `status: In UAT`, not `Released`: nothing in this build ever deploys. |
| REQ-002 | Q12 | The ops dashboard dedupes duplicate `Tier2_Escalation__e` deliveries itself, on case number + escalation time; no Salesforce-side dedupe is built for the event. | M1-S01 | `CustomObject:Tier2_Escalation__e` | metadata-builder | D9 | check_platform_events_apex | checker | In UAT | `artefacts/M1-S01/objects/Tier2_Escalation__e/Tier2_Escalation__e.object-meta.xml`\|`artefacts/M1-S01/package.xml` | pass — same checker run as the Q10 row, exit 0. This requirement's only step is M1-S01: the event's five inline payload fields (including `Escalated_At__c`, the field the dashboard dedupes on) are fully declared here, and no later step in this plan touches the event definition again. No manual test names this row specifically; carried at `In UAT` pending the M1 milestone gate rather than `Released`, since nothing in this build ever deploys. |
| REQ-003 | Q14 | A re-save can re-fire the escalation from a second transaction; stamp `Case.Tier2_Notified_At__c` on webhook success and skip a Case already stamped within the last 10 minutes. | M1-S01 | `CustomField:Case.Tier2_Notified_At__c` | metadata-builder | D13 | xml | xml | In UAT | `artefacts/M1-S01/objects/Case/fields/Tier2_Notified_At__c.field-meta.xml`\|`artefacts/M1-S03/classes/CaseTriggerHandler.cls`\|`artefacts/M1-S03/classes/Tier2WebhookQueueable.cls` | pass — 16/16 `*.xml`/`*-meta.xml` files under M1-S01 parsed (`tests/M1-S01/results.json`), and the field is one of the 13 `CustomField` manifest members confirmed consistent both directions. `check_object_creation_and_design.py` does not judge this file (standard-object stem), so the field's own shape rests on structural coverage only, named rather than papered over. **Updated at the `M1-S03` documentation pass:** the ten-minute suppression window and the on-success stamp are now built — checked twice per `artefacts/M1-S03/deploy-order.md` § 6 ("`suppression` / **D13**"): once in `CaseTriggerHandler` at detection, again in `Tier2WebhookQueueable`'s job because the handler cannot see an escalation still in flight in another transaction; a resend bypasses the window on purpose. Verified by direct source inspection this pass (both call sites present), not by a runtime-executed test — `check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03` exit 0 covers the file structurally but asserts nothing about the suppression logic itself. `status: In UAT`. |
| REQ-004 | Q17 | The failure record's Status picklist is exactly New / Retrying / Resent / Resolved / Abandoned; Severity is exactly Error / Warning; the Apex in M1-S03 must write exactly those values and nothing else. | M1-S01 | `CustomField:Integration_Failure__c.Status__c` | metadata-builder | — | check_picklist_and_value_sets | checker | In UAT | `artefacts/M1-S01/objects/Integration_Failure__c/fields/Status__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Severity__c.field-meta.xml`\|`artefacts/M1-S03/classes/Tier2WebhookQueueable.cls`\|`artefacts/M1-S03/classes/IntegrationFailureTriggerHandler.cls` | pass — `check_picklist_and_value_sets.py --manifest-dir artefacts/M1-S01 --min-severity ERROR` exit 0, "No findings." Also `check_object_creation_and_design.py` exit 0. **Updated at the `M1-S03` documentation pass — the requirement's own second half is now built:** `artefacts/M1-S03/deploy-order.md` § 6 ("`picklist_values` / **Q17**") states the Apex writes named constants only — `New`, `Retrying`, `Resent`, `Resolved`, `Abandoned`, `Error` — with no other literal written to either restricted field; verified by direct source inspection this pass, not by an executed test (no Apex test runs in this design-only build). **Manual test outstanding, per `agents/build-doc-keeper/AGENT.md`'s `In UAT` rule** — `tests/M1-S01/results.json` → `skipped_manual[0]` still names the field-metadata half of this check, deferred to the M1 gate, not ticked by any agent. |
| REQ-005 | Q18 | The failure record carries: Case lookup, case number, endpoint, HTTP status, response body (first 32k chars), attempt count, last attempt time, error message, the JSON payload sent, Status, and a Resend checkbox. | M1-S01 | `CustomObject:Integration_Failure__c` | metadata-builder | — | check_object_creation_and_design | checker | In UAT | `artefacts/M1-S01/objects/Integration_Failure__c/Integration_Failure__c.object-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Case__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Case_Number__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Endpoint__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/HTTP_Status__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Response_Body__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Attempt_Count__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Last_Attempted_At__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Error_Message__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Request_Payload__c.field-meta.xml`\|`artefacts/M1-S01/objects/Integration_Failure__c/fields/Status__c.field-meta.xml`\|`artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml`\|`artefacts/M1-S02/package.xml`\|`artefacts/M1-S03/classes/Tier2WebhookQueueable.cls` | pass — `check_object_creation_and_design.py --manifest-dir artefacts/M1-S01` exit 0, "No issues found across 2 object file(s) and 13 field file(s)." All ten named fields exist and parse. **Updated at the `M1-S02` documentation pass:** the permission set that makes these fields usable is built and tested — `check_permission_set_architecture.py --manifest-dir artefacts` (build scope) exit 0 (`tests/M1-S02/results.json`), one non-failing WARN unrelated to this row (deliberate D12 sharing-bypass). 12 `fieldPermissions` rows carry `readable`/`editable` true: the 10 fields this requirement names plus `Case.Tier2_Notified_At__c` (REQ-003) and `Resend__c` (this requirement's own checkbox). `Status__c` is correctly absent from the grant (required field, decision D-M1S01-02). **Updated at the `M1-S03` documentation pass:** the fields this requirement names are now actually populated on failure — `Tier2WebhookQueueable.attemptOne(...)` writes `Endpoint__c`, `HTTP_Status__c`, `Response_Body__c`, `Attempt_Count__c`, `Last_Attempted_At__c`, `Error_Message__c`, `Request_Payload__c`, `Case_Number__c`, `Case__c` and `Status__c` on every failed attempt (`artefacts/M1-S03/deploy-order.md` §§ 1, 6), verified by direct source inspection this pass, not by an executed test. The resend-actionable *behaviour* proper (the Apex that reads `Resend__c` and re-enqueues) stays tracked at `REQ-006`, per that row's own note, so as not to double-count one behaviour under two requirements. **Manual test outstanding:** the M1 gate access review clause (d), deferred per `tests/M1-S02/results.json` → `skipped_manual[0]`. `status: In UAT`, not `Released`: nothing in this build ever deploys. **Updated at the `M1-S02` repair pass (S2-F-13):** `Tier2_Webhook_Admin`'s content changed again — a new `objectPermissions` row grants `allowCreate`/`allowRead` on `Tier2_Escalation__e` (`decisions.md` `D-M1S02-07`) — but the file's path is unchanged and none of the 12 `fieldPermissions` rows this requirement's grant depends on were touched; noted for the record only, no re-verification needed for this requirement. |
| REQ-006 | Q20 | Support Engineering resends a failed webhook by ticking Resend on the failure record; the same team reviews the backlog. | M1-S01 | `CustomField:Integration_Failure__c.Resend__c` | metadata-builder | D14 | check_object_creation_and_design | checker | In UAT | `artefacts/M1-S01/objects/Integration_Failure__c/fields/Resend__c.field-meta.xml`\|`artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml`\|`artefacts/M1-S02/package.xml`\|`artefacts/M1-S03/triggers/IntegrationFailureTrigger.trigger`\|`artefacts/M1-S03/classes/IntegrationFailureTriggerHandler.cls`\|`artefacts/M1-S03/classes/Tier2WebhookQueueable.cls`\|`artefacts/M1-S03/classes/IntegrationFailureResendTest.cls` | pass — covered by the same `check_object_creation_and_design.py` exit 0 run as the Q18 row, plus `xml`/`manifest`. The checkbox exists. **Updated at the `M1-S02` documentation pass:** who is *granted* the tick is built and tested — `Resend__c` is one of the 11 `Integration_Failure__c` fields carrying `readable`/`editable` true on `Tier2_Webhook_Admin.permissionset-meta.xml` (`tests/M1-S02/results.json`). Assignment (decision D14) is wider than this requirement's own "the same team" answer — every user who can escalate a Case plus the M1-S04 scheduling user (assumption A13) — and is a post-deploy human step, not shipped by any step. **Updated at the `M1-S03` documentation pass — what happens when the box is ticked is now built:** `IntegrationFailureTrigger` (`after update`) detects `Resend__c` turning true and `IntegrationFailureTriggerHandler` re-enqueues `Tier2WebhookQueueable` for that row, replaying the stored Idempotency-Key (`REQ-013`/D6) and setting `Status__c` to `Retrying`, then reuses the same Queueable and Finalizer rather than duplicating the callout (`artefacts/M1-S03/deploy-order.md` § 1 row 2, § 6 "`resend_path`"). `IntegrationFailureResendTest` (6 methods) asserts the resend transition to `Resent`, the stored-key replay, a resend overriding a recent suppression window, the no-payload fallback, an orphaned row, and the checkbox clearing — all three declared checkers exit 0 on this file (`tests/M1-S03/results.json`), but no Apex test is executed in this design-only build, so the assertions are read, not run. `status: In UAT`, not `Released`: nothing in this build ever deploys. **Updated at the `M1-S02` repair pass (S2-F-13):** `Tier2_Webhook_Admin`'s content changed again — a new `objectPermissions` row grants `allowCreate`/`allowRead` on `Tier2_Escalation__e` (`decisions.md` `D-M1S02-07`), unrelated to the `Resend__c` grant this requirement tracks; the file's path is unchanged, noted for the record only. |
| REQ-007 | Q30 | Superseded by Q2: the platform event's payload fields are case number, severity, subject and case link, per the requirement. | M1-S01 | `CustomObject:Tier2_Escalation__e` | metadata-builder | — | check_platform_events_apex | checker | In UAT | `artefacts/M1-S01/objects/Tier2_Escalation__e/Tier2_Escalation__e.object-meta.xml` | pass — same checker run as the Q10/Q12 rows, exit 0. All four named payload fields (`Case_Number__c`, `Severity__c`, `Subject__c`, `Case_Link__c`) plus `Escalated_At__c` are declared inline on the event, per `inputs.platform_event.fields` and `deploy-order.md` § 2 item 3. This requirement's only step is M1-S01 and nothing further touches the event's field list; carried at `In UAT` pending the M1 gate, not `Released`, since this build never deploys. |
| REQ-008 | Q4 | Salesforce must notify our on-call tool (PagerDuty-style, HTTPS REST endpoint, API-key authentication) within a minute, with the case number, severity, subject and a link back to the case. | M1-S02 | `ExternalCredential:OnCall_Tool_EC` | metadata-builder | D3 | check_apex_named_credentials_patterns | checker | In UAT | `artefacts/M1-S02/externalCredentials/OnCall_Tool_EC.externalCredential-meta.xml`\|`artefacts/M1-S02/namedCredentials/OnCall_Tool.namedCredential-meta.xml`\|`artefacts/M1-S03/classes/Tier2WebhookQueueable.cls` | pass — `check_apex_named_credentials_patterns.py --manifest-dir artefacts/M1-S02` (step scope) exit 0 on the rebuilt credential pair (`tests/M1-S02/results.json`). Named Principal (Q4, D3), `SecuredEndpoint` (D3), a custom `X-API-Key` `AuthHeader` (Q6), a reused API name with a per-org `Url` parameter (Q25) all written and structurally verified. **Checker-coverage gap, named rather than papered over:** no checker in the library asserts an `AuthHeader` parameter carries a non-empty `parameterValue` — run 1 of this credential passed every declared checker and was then rejected by the org (`reports/MOCK-DEPLOY-M1.md` run 1, S2-F-02). **Updated at the `M1-S03` documentation pass:** the actual HTTPS POST is now built — `Tier2WebhookQueueable.attemptOne(...)` composes the endpoint as `'callout:' + 'OnCall_Tool'` with no path appended (M1-S02's `Url` parameter is already the full path) and `check_callouts_and_http_integrations.py --manifest-dir artefacts/M1-S03 --fail-on HIGH` exits 0, zero findings (`tests/M1-S03/results.json`). **The "within a minute" delivery latency is not measured by anything in this build** — the Queueable enqueues synchronously from the trigger transaction with no artificial delay, which is consistent with the requirement but is a design property, not a timed test; no offline compile check exists either (`agents/_shared/AGENT_CONTRACT.md` § Gate C), so the callout has never actually executed against the org. `status: In UAT`, not `Released`: nothing in this build ever deploys. |
| REQ-009 | Q5 | The on-call tool's API key must never be stored in code or in a custom setting. | M1-S02 | `ExternalCredential:OnCall_Tool_EC` | metadata-builder | — | manual_access_review_clause_b | manual | In UAT | `artefacts/M1-S02/externalCredentials/OnCall_Tool_EC.externalCredential-meta.xml`\|`artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml`\|`artefacts/M1-S03/classes/Tier2WebhookQueueable.cls` | no checker in the library asserts the absence of a literal secret value — direct inspection of the M1-S02 artefacts found no literal API-key value; the `AuthHeader` `parameterValue` is a merge-field formula naming *where* the platform reads the secret, not the secret itself. The key is entered directly in Setup after deploy and does not survive a sandbox refresh. **Updated at the `M1-S03` documentation pass — independently confirmed on the consuming Apex side too:** the step's own manual clause (b) and this pass's mechanical grep (`grep -n "setHeader\|Authorization\|X-API-Key" artefacts/M1-S03/classes/*.cls`, run this pass) both confirm no class in `M1-S03` sets an `X-API-Key` or `Authorization` header, reads a credential value, or names a literal hostname — the platform injects the header from the External Credential's own `AuthHeader` parameter, and the only endpoint expression in the step is `'callout:' + 'OnCall_Tool'`. Formally deferred to the M1 gate's manual clause (b), `tests/M1-S02/results.json` → `skipped_manual[0]` and `tests/M1-S03/results.json` → `skipped_manual[0]`, not ticked by any agent. `status: In UAT`. **Updated at the `M1-S02` repair pass (S2-F-13):** `Tier2_Webhook_Admin`'s content changed — a new `objectPermissions` row grants `allowCreate`/`allowRead` on `Tier2_Escalation__e` (`decisions.md` `D-M1S02-07`) — the file's path is unchanged and the new row carries no credential value, so this requirement's own finding (no literal secret in any M1-S02 file) is unaffected; noted for the record only. |
| REQ-010 | Q24 | Alert a named owner when the notification channel itself goes dark — not only when one delivery fails: an hourly check emails Support Engineering when more than three `Integration_Failure__c` rows land in an hour, or no success is stamped in 24 hours while escalations exist. | M1-S04 | `ApexClass:Tier2ChannelHealthSchedulable` | apex-builder | D11 | check_apex_scheduled_jobs | checker | In UAT | `artefacts/M1-S04/classes/Tier2ChannelHealthSchedulable.cls`\|`artefacts/M1-S04/classes/Tier2ChannelHealthQueueable.cls`\|`artefacts/M1-S04/classes/Tier2ChannelHealthTest.cls`\|`artefacts/M1-S04/classes/TestDataFactory.cls`\|`artefacts/M1-S03/classes/TestUserFactory.cls` | pass — built once against `include_logger:true`, `failed` its own P0 (`Application_Log__c`/`Logger_Setting__mdt` shipped by no step, decision `D-M1S04-01`), reset and rebuilt against the 2026-09-12 amendment (`include_logger:false`, roster = active `Tier2_Webhook_Admin` assignees). All three declared checkers — `check_apex_scheduled_jobs.py`, `check_apex_queueable_patterns.py`, `check_error_handling_framework.py` — exit 0 on the rebuilt 4-class package (`tests/M1-S04/results.json`); `xml` 4/4 `*-meta.xml` parse at apiVersion 67.0; `manifest` skipped-not-applicable, naming build-level step `M1-S05` (which must expect **four** `ApexClass` members here, not the three its own stale acceptance-test text still says — `D-M1S04-07`). No Apex test ran and no offline compile check exists in this design-only build; coverage on `Tier2ChannelHealthQueueable` is `deploy-order.md`'s own estimate (~80–95%), not a measured number. **Not fully proven:** the scheduling user's read access to `PermissionSetAssignment` (the alert roster) and to `Case` records (the dead-channel count) are both granted by nothing this build ships — two M1-gate confirmation items, `D-M1S04-03`. The recipient-gap self-alert loop and the absence of duplicate-alert suppression are accepted as designed, `D-M1S04-04`. `WITH USER_MODE` on the three aggregate `COUNT()` queries stays UNVERIFIED by plan instruction, `D-M1S04-05`. **Updated at the `M1-S04` repair/retest pass (run 3):** the manual test's three prerequisite checks are unchanged, but the executed test fixture is not — `reports/MOCK-DEPLOY-M1.md` run 6 (`S2-F-11`) found all 11 `Tier2ChannelHealthTest` methods failing at execution because none ran as a permissioned user, while `Tier2ChannelHealthQueueable`'s three `COUNT()` queries correctly enforce the running user's FLS under API 67.0 default user mode. The repair (`D-M1S04-08`) wraps every method in `System.runAs` against a `TestUserFactory`-provisioned user holding `Tier2_Webhook_Admin` — this step does not ship `TestUserFactory` itself, it depends on the copy `M1-S03`'s own S2-F-11 repair already shipped, a cross-step dependency `plan.json`'s `depends_on` cannot yet record (`D-M1S04-09`). Two of the eleven methods (`rosterResolutionReturnsTheDistinctActiveAssigneeEmails`, `scheduleCreatesAWaitingCronTriggerAndDispatchesTheQueueable`) now depend on that permissioned agent's ability to read `PermissionSetAssignment`/`CronTrigger`/`AsyncApexJob`, which `Tier2_Webhook_Admin` grants nothing on — an UNVERIFIED question whose org answer is still pending (`D-M1S04-10`). All three declared checkers re-ran unchanged at exit 0 and `check-outputs` is ok on all six declared paths (`tests/M1-S04/results.json`, `step-tester` run `2026-09-12T16-45-00Z`). **Manual test outstanding:** `tests/M1-S04/results.json` → `skipped_manual[0]` — a reviewer confirms the CRON literal is hourly and `execute()` only enqueues, the two Q24 thresholds match the code, and the org-wide sender is verified in the target org (assumption A4) — deferred to the M1 gate, not ticked by any agent. `status: In UAT`, not `Released`: this build never deploys. |
| REQ-011 | Q11 | `EventBus.publish`'s `SaveResult` for `Tier2_Escalation__e` is inspected in the escalating transaction; a rejected publish writes a distinct `Integration_Failure__c` row (Severity Error, blank `Endpoint__c`) rather than being silently discarded. | M1-S03 | `ApexClass:Tier2EscalationService` | apex-builder | D10 | check_platform_events_apex | checker | In UAT | `artefacts/M1-S03/classes/Tier2EscalationService.cls` | pass — `check_platform_events_apex.py --manifest-dir artefacts/M1-S03` exit 0, zero findings; rule R1 (a discarded `EventBus.publish` result) does not fire, which is the checker's own way of confirming the `List<Database.SaveResult>` is assigned and walked rather than dropped (`tests/M1-S03/results.json`). `artefacts/M1-S03/deploy-order.md` § 6 (`publish_result` / **Q11**) narrates the same shape: `publishResults` is walked index-parallel with the Case list, and a rejection writes a row with a **blank `Endpoint__c`**, which is how an admin tells a publish failure from a webhook failure. This is exactly the step's manual acceptance-test clause (a). No Apex test executed (design-only build). **Manual test outstanding:** clause (a), `tests/M1-S03/results.json` → `skipped_manual[0]`, not ticked by any agent. `status: In UAT`. |
| REQ-012 | Q13 | Exactly one Queueable is enqueued per transaction carrying every escalated Case in it, never one per Case. | M1-S03 | `ApexClass:Tier2EscalationService` | apex-builder | — | check_apex_queueable_patterns | checker | In UAT | `artefacts/M1-S03/classes/Tier2EscalationService.cls`\|`artefacts/M1-S03/classes/Tier2EscalationServiceTest.cls`\|`artefacts/M1-S03/classes/TestUserFactory.cls` | pass — `check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03` exit 0, zero findings; rule QP001 (`System.enqueueJob` inside a loop) does not fire, consistent with `Tier2EscalationService.escalate()` enqueuing once for the whole transaction. `artefacts/M1-S03/deploy-order.md` § 6 states three tests assert `Limits.getQueueableJobs() == 1`, one of them at 200 Cases — read from the test source this pass, not executed (no Apex test runs in this design-only build, so the assertion is verified by inspection of `Tier2EscalationServiceTest.cls`, not by a measured limit). The enqueue ceiling this protects against — 50 per synchronous transaction, 1 per asynchronous one — is why a per-Case enqueue would pass a single-record test and fail in production. **Updated at the `M1-S03` repair/retest pass (run 4):** the three `Limits.getQueueableJobs() == 1` assertions in `Tier2EscalationServiceTest` are unchanged in body; they now execute inside `System.runAs(agent())` against a `Tier2_Webhook_Admin` user provisioned by the new `classes/TestUserFactory.cls` (verbatim copy of `templates/apex/tests/TestUserFactory.cls`), the repair that closed `S2-F-11` (`reports/MOCK-DEPLOY-M1.md` run 6: 0/28 tests passed as the deploying user). `step-tester`'s retest (`envelopes/M1-S03/2026-09-12T16-30-00Z.json`) re-ran the same declared checker at exit 0 against the 13-file package. `status: In UAT`. |
| REQ-013 | Q7 | A webhook failure classified transient (429, 502, 503, 504, or a connection timeout) is retried up to three times via a Finalizer re-enqueue with a backoff; one classified permanent (400, 401, 403, 404, 422) is not retried. | M1-S03 | `ApexClass:Tier2WebhookFinalizer` | apex-builder | — | check_apex_queueable_patterns | checker | In UAT | `artefacts/M1-S03/classes/Tier2WebhookQueueable.cls`\|`artefacts/M1-S03/classes/Tier2WebhookFinalizer.cls`\|`artefacts/M1-S03/classes/Tier2WebhookQueueableTest.cls`\|`artefacts/M1-S03/classes/Tier2WebhookFinalizerTest.cls`\|`artefacts/M1-S03/classes/MockHttpResponseGenerator.cls`\|`artefacts/M1-S03/classes/TestUserFactory.cls` | pass — `check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03` exit 0, zero findings, including QP004 (a callout after DML in the same `AllowsCallouts` `execute()` body), which the retry/DML ordering must not trip. `Q15`'s finalizer contract settles the retry mechanism itself: `System.attachFinalizer(...)` is the first statement of `execute()`; on `UNHANDLED_EXCEPTION` `Tier2WebhookFinalizer` re-enqueues with `AsyncOptions.MinimumQueueableDelayInMinutes` while `attempt < 3`; on `SUCCESS` it records completion, using `getAsyncApexJobId()`, `getRequestId()`, `getResult()` and `getException()` — not `getJobId()`, which `FinalizerContext` does not have (`artefacts/M1-S03/deploy-order.md` § 6). `Tier2WebhookQueueableTest` asserts the transient/permanent classification directly and the exhausted-budget end (503 at the last attempt lands `Abandoned`) through a real job. **Deliberately uncovered by any executed test:** the throw → Finalizer → re-enqueue path itself — an unhandled exception in a job run by `Test.stopTest()` fails the test method, so this branch cannot be driven from inside a test (`artefacts/M1-S03/deploy-order.md` § 5 item 3; finding `S3-F-05`, INFO); this specific chain (a live `System.enqueueJob` throwing and the platform itself invoking the Finalizer) remains undriveable by any test for the reason just stated. **Updated at the `M1-S03` repair/retest pass (run 4):** `Tier2WebhookQueueableTest`'s transient/permanent classification and exhausted-budget assertions are unchanged in body; they now execute inside `System.runAs(agent())` against a `Tier2_Webhook_Admin` user provisioned by the new `classes/TestUserFactory.cls`, the repair that closed `S2-F-11` (`reports/MOCK-DEPLOY-M1.md` run 6: 0/28 tests passed as the deploying user). **Updated at the `M1-S03` § 4 repair pass (runs 6–8), closing the coverage gap named above by a different route:** `Tier2WebhookFinalizer`'s own decision logic — the transient-retry re-enqueue, the abandon-at-ceiling stop, the existing-row update, the `SUCCESS` no-op and the `ctx == null` guard — is now directly unit-tested by the new `classes/Tier2WebhookFinalizerTest.cls` (5 methods), which calls `Tier2WebhookFinalizer.execute(FinalizerContext)` against a hand-built `System.FinalizerContext` stub rather than driving the live throw chain the paragraph above still correctly calls undriveable. The technique itself was UNVERIFIED against this repo's corpus at introduction (run 6, `S6-F-02`) and confirmed compilable and passing by the org at run 10 (`S7-F-02`) — see `D-M1S03-13` for the full arc, including the one-line `Test.setMock` fix run 7 needed for a method the re-enqueued job executed regardless of `Test.startTest()`/`Test.stopTest()` wrapping. `reports/MOCK-DEPLOY-M1.md` run 12 (SOURCE mode, `--test-level RunSpecifiedTests`) shows 37/37 tests passing at 89.9% aggregate coverage with no coverage warnings, closing `S2-F-14`'s coverage-floor finding against this class. `status: In UAT`, still not `Released`: nothing in this build ever deploys. |
| REQ-014 | Q8 | A resend replays the identical `Idempotency-Key` (Case Id + the escalation timestamp captured at enqueue time) rather than minting a new one, so the on-call tool can dedupe a retried or resent delivery. | M1-S03 | `ApexClass:Tier2WebhookQueueable` | apex-builder | D6 | check_apex_queueable_patterns | checker | In UAT | `artefacts/M1-S03/classes/Tier2WebhookQueueable.cls`\|`artefacts/M1-S03/classes/IntegrationFailureTriggerHandler.cls`\|`artefacts/M1-S03/classes/IntegrationFailureResendTest.cls`\|`artefacts/M1-S03/classes/TestUserFactory.cls` | pass — `check_apex_queueable_patterns.py --manifest-dir artefacts/M1-S03` exit 0. `artefacts/M1-S03/deploy-order.md` § 6 (`idempotency` / **D6**) states `idempotencyKey(caseId, escalatedAt)` = Case Id + `':'` + epoch millis, with the escalation timestamp captured once in `Tier2EscalationService` and carried per Case, so a Finalizer retry and an admin resend rebuild the identical key; `IntegrationFailureResendTest` asserts stored-key replay, and `Tier2WebhookQueueableTest` asserts key stability — both read this pass, neither executed (design-only build, no Apex test runs). **Updated at the `M1-S03` repair/retest pass (run 4):** `IntegrationFailureResendTest`'s stored-key-replay assertion is unchanged in body; it now executes inside `System.runAs(agent())` against a `Tier2_Webhook_Admin` user provisioned by the new `classes/TestUserFactory.cls`, the repair that closed `S2-F-11` (`reports/MOCK-DEPLOY-M1.md` run 6: 0/28 tests passed as the deploying user, including this class's 6 methods). `status: In UAT`. |
| REQ-015 | Q22 | The design tolerates the stated production volume — 15 escalations a day, peaking at 2 an hour, worst single burst 50 in five minutes — without breaching the per-transaction callout, DML or CPU ceilings. | M1-S03 | `ApexClass:Tier2WebhookQueueable` | apex-builder | — | check_callouts_and_http_integrations | checker | In UAT | `artefacts/M1-S03/classes/Tier2WebhookQueueable.cls`\|`artefacts/M1-S03/classes/Tier2EscalationServiceTest.cls`\|`artefacts/M1-S03/classes/Tier2WebhookQueueableTest.cls`\|`artefacts/M1-S03/classes/TestUserFactory.cls` | pass — `check_callouts_and_http_integrations.py --manifest-dir artefacts/M1-S03 --fail-on HIGH` exit 0, zero findings; rule 4 (a callout inside a loop) does not fire on `Tier2WebhookQueueable.execute()`'s per-Case callout loop, because `MAX_CASES_PER_JOB = 50` bounds it against the 100-callouts-per-transaction ceiling with an explicit `setTimeout(20000)` against the 120s cumulative budget (`artefacts/M1-S03/deploy-order.md` § 6 "A note on why the callout loop is legal"), and the `new Http().send(req)` call lives in `attemptOne`, not in the loop body. `Tier2EscalationServiceTest` and `Tier2WebhookQueueableTest` each carry a 200-Case bulk test proving the *shape* is bulk-safe, run to prove headroom rather than because the stated volume demands it — no test is executed and no coverage number is measured in this design-only build (`artefacts/M1-S03/deploy-order.md` § 8). **Updated at the `M1-S03` repair/retest pass (run 4):** both 200-Case bulk tests are unchanged in body; they now execute inside `System.runAs(agent())` against a `Tier2_Webhook_Admin` user provisioned by the new `classes/TestUserFactory.cls`, the repair that closed `S2-F-11` (`reports/MOCK-DEPLOY-M1.md` run 6: 0/28 tests passed as the deploying user). `status: In UAT`. |
| REQ-016 | Q23 | Apex classes touching this feature run `with sharing` in API 67.0 default user mode; SOQL uses `WITH USER_MODE`; `WITH SECURITY_ENFORCED` is never emitted. | M1-S03 | `ApexClass:CaseTriggerHandler` | apex-builder | — | check_apex_queueable_patterns | checker | In UAT | `artefacts/M1-S03/classes/CaseTriggerHandler.cls`\|`artefacts/M1-S03/classes/Tier2WebhookFinalizer.cls`\|`artefacts/M1-S03/classes/IntegrationFailureTriggerHandler.cls` | pass — mechanically verified this pass, not narrated from `deploy-order.md` alone: `grep -n "with sharing\|without sharing" artefacts/M1-S03/classes/*.cls` (excluding test classes) returns exactly five `public with sharing class` declarations (`CaseTriggerHandler`, `IntegrationFailureTriggerHandler`, `Tier2EscalationService`, `Tier2WebhookQueueable`, `Tier2WebhookFinalizer`) and no `without sharing` anywhere; `grep -n "WITH USER_MODE"` returns exactly three hits, one per SOQL `SELECT` in the package (`CaseTriggerHandler.cls:69`, `Tier2WebhookQueueable.cls:311`, `Tier2WebhookFinalizer.cls:143`); `grep -rn "WITH SECURITY_ENFORCED" artefacts/M1-S03/` returns zero hits in any `.cls` file. **Note, and it is a small correction to the artefact's own prose:** `artefacts/M1-S03/deploy-order.md` § 6 states "All six production classes are `with sharing`" and "both SOQL statements carry `WITH USER_MODE`" — this pass's count is **five** classes and **three** SOQL statements, not six and two; the underlying compliance claim is still true (100% of both), only the artefact's own arithmetic is off by one in each count. No checker in the library specifically asserts `with sharing` / `WITH USER_MODE` / the absence of `WITH SECURITY_ENFORCED` as a named rule — `agents/_shared/AGENT_CONTRACT.md` § *Apex security idiom by API version* is the governing standard, applied by inspection here. `status: In UAT`. |

---

## Requirement id derivation

This build minted no `REQ-XXX` ids during intake: `plan.json` carries `clarifications[]` but no
requirement register, and `requirement.md` is eleven lines of prose. Per this loop's own
precedent (`examples/builds/case-onboarding/traceability.md` § "Requirement id derivation"), the
ids below are **assigned here and anchored**, not inherited — each one names the `requirement.md`
line the need traces to (or states that none exists) and the clarification that settled it. Ids
are stable and are never reused.

| req_id | Anchored to `requirement.md` | Settled by |
|---|---|---|
| REQ-001 | — (no requirement line; rollback/commit semantics for the notification are a platform-behaviour risk the requirement text never names) | Q10 (answered) |
| REQ-002 | — (no requirement line; at-least-once event delivery and dashboard-side dedupe are a platform behaviour, not stated in the requirement) | Q12 (answered) |
| REQ-003 | L3–L4 — "Salesforce must notify our on-call tool … within a minute" (one notification per escalation, not one per re-save) | Q14 (answered) |
| REQ-004 | L6 — "a visible failure record are required" (the picklists that make the record's state legible) | Q17 (answered) |
| REQ-005 | L6–L7 — "an admin must be able to see it and re-send" (the field set that makes a failure diagnosable and replayable) | Q18 (answered) |
| REQ-006 | L7 — "an admin must be able to see it and re-send" (who the admin is, and whether it is the backlog-reviewing team) | Q20 (answered) |
| REQ-007 | L3–L4 — "with the case number, severity, subject and a link back to the case" (the event payload field list) | Q30 (answered) |
| REQ-008 | L3–L4 — "Salesforce must notify our on-call tool (PagerDuty-style, HTTPS REST endpoint, API-key authentication) within a minute" (the authentication *mechanism* itself — a single named service credential usable from Queueable Apex, distinct from the notification-sequencing behaviour REQ-001/REQ-002 already cover) | Q4 (answered) |
| REQ-009 | L7–L8 — "The on-call tool's API key must never be stored in code or in a custom setting." | Q5 (answered) |
| REQ-010 | — (no requirement line; a dead-channel alert distinct from a single failed delivery is a resilience need the requirement text never names) | Q24 (answered) |
| REQ-011 | — (no requirement line; inspecting the publish `SaveResult` rather than trusting `EventBus.publish` silently is a platform-behaviour risk the requirement text never names) | Q11 (answered) |
| REQ-012 | — (no requirement line; the one-Queueable-per-transaction enqueue discipline is a governor-limit safety property, not a stated business requirement) | Q13 (answered) |
| REQ-013 | L3–L4 — "Salesforce must notify our on-call tool ... within a minute" (read as: a transient delivery failure does not become a permanent loss) | Q7 (answered; Q15 settles the Finalizer half of the same requirement) |
| REQ-014 | L7 — "an admin must be able to see it and re-send" (read as: a resend must be safely replayable, not a second, differently-keyed delivery) | Q8 (answered) |
| REQ-015 | — (no requirement line; the stated production volume in Q22's answer is an operational constraint the requirement text never names as a number) | Q22 (answered) |
| REQ-016 | — (no requirement line; the sharing/security-mode compliance is the platform's own default-user-mode standard applied to this feature, not a business requirement) | Q23 (answered) |

---

## Coverage notes (build-wide, updated after the `M1-S03` § 4 repair pass, runs 6–8 — supersedes the `M1-S04` repair/retest pass note below)

- **Still 16 requirements; no new row minted, one row updated in place.** This pass documents
  `M1-S03` runs 6–8 — three consecutive § 4 test-only repairs (`documented` → `running` → `built`,
  three times, `tested` once at the end) closing `reports/MOCK-DEPLOY-M1.md` findings `S2-F-14`
  (`Tier2WebhookFinalizer` under the 75% coverage floor), `S2-F-15` (one test method's re-enqueued job
  ran with no registered mock) and `S2-F-16` (`Tier2EscalationService` under the 75% floor
  individually, even though the aggregate had cleared it). Run 6 added
  `classes/Tier2WebhookFinalizerTest.cls` (+ `-meta.xml`), 5 methods unit-testing
  `Tier2WebhookFinalizer.execute(FinalizerContext)` directly against a hand-built
  `System.FinalizerContext` stub — a technique UNVERIFIED against this repo's corpus at introduction
  and confirmed compilable and passing by the org at run 10 (`D-M1S03-13`). Run 7 added one line — a
  registered 2xx mock — to close the one method run 10 still failed (`D-M1S03-13`). Run 8 added two
  methods to the existing `Tier2EscalationServiceTest.cls`, closing the two branches
  `Tier2EscalationService` needed for its own individual coverage floor (`D-M1S03-14`). **`REQ-013`**
  is the one row whose `artefact_paths` names the new test class directly (`Tier2WebhookFinalizer.cls`
  is this row's own artefact); it gains `artefacts/M1-S03/classes/Tier2WebhookFinalizerTest.cls` in
  its `artefact_paths` and a note in its `test_result` correcting the "deliberately uncovered" framing
  a prior pass wrote, now that the Finalizer's own decision branches are directly unit-tested (though
  the live throw → Finalizer chain itself remains undriveable by any test, for the reason that row
  already states). No row names `Tier2EscalationService`'s two new branch-test methods specifically —
  `REQ-011` (the publish-rejection requirement one of those methods exercises) and `REQ-012` (the
  enqueue-once requirement the other brushes past via its early-return guard) already cite
  `Tier2EscalationServiceTest.cls`/`Tier2EscalationService.cls` in their `artefact_paths` from an
  earlier pass, so no new file reference was needed there; this pass's own scope, per the task that
  produced it, is limited to rows whose artefacts gained **the new test class**
  (`Tier2WebhookFinalizerTest.cls`), which is `REQ-013` alone. `REQ-001`–`REQ-010`, `REQ-014`–`REQ-016`
  are unaffected.
- **Six non-test classes and both triggers are unchanged by this pass** — all three repairs are
  test-only, per `artefacts/M1-S03/deploy-order.md` §§ 0d–0f and `decisions.md` `D-M1S03-13`/
  `D-M1S03-14`. No row naming only a production class needed an update.
- **Three new decisions this pass:** `D-M1S03-13` records the Finalizer-stub technique and its
  UNVERIFIED-then-confirmed status across runs 6–7; `D-M1S03-14` records the per-class 75% floor
  finding and the two branch tests that close it; `D-M1S03-15` records `Tier2WebhookFinalizerTest` as
  a new `ApexClass` member `M1-S05`'s manifest must add — an obligation being resolved in a parallel
  `M1-S05` re-run this pass does not touch.
- **`M1-S05` currency remains an open question, not newly created by this pass.** `M1-S05` (already
  `documented`) still lists the pre-run-6 thirteen `ApexClass` members for this step, not the fourteen
  it now ships; `Tier2WebhookFinalizerTest` is named as a shared obligation in `D-M1S03-15`, and its
  resolution is a parallel `M1-S05` re-run this pass explicitly leaves alone.
- **0 orphans confirmed, not assumed, after this pass's edit.** `check_rtm.py` run this pass reports
  16 rows, 0 coverage gaps, 0 orphans — see "RTM checker output, this pass" below.
- **Workbook:** still not written. `scale: feature` makes the ten-section workbook optional
  (`standards/build-orchestration.md` § 3.1: "workbook optional, traceability required"); this build
  has never populated one at any pass, and a single-cell update to one existing row does not change
  that build-wide choice.
- **No row is `Released`.** `build_mode: design-only`; nothing in this build has ever been deployed.
- Every fact in this note was read from `plan.json` (`steps[M1-S03].runs`), the four envelopes under
  `envelopes/M1-S03/2026-09-12T17-40-00Z.json`, `.../17-50-00Z.json`, `.../18-05-00Z.json` and
  `.../18-08-27Z.json`, `tests/M1-S03/results.json`, `artefacts/M1-S03/deploy-order.md` §§ 0d–0f, and
  `reports/MOCK-DEPLOY-M1.md` runs 9–12 — none narrated past what those sources state.

### M1-S04 repair/retest pass note (superseded by the `M1-S03` § 4 repair pass note above, kept for the record)

- **Still 16 requirements; no new row minted, one row updated in place.** This pass documents
  `M1-S04` run 3 — a § 4 test-only repair (`documented` → `running` → `built` → `tested`) that closed
  `reports/MOCK-DEPLOY-M1.md` run 6's `S2-F-11` finding for this step's own test class: all 11 methods
  in `Tier2ChannelHealthTest` had failed at execution because none ran as a permissioned user, while
  `Tier2ChannelHealthQueueable` correctly enforces default user mode on its three aggregate `COUNT()`
  queries. The repair added `PERM_SET`/`PROFILE` constants and a new setup-object `runAs` fence around
  `TestUserFactory.createUser(...)`, then wrapped every pre-existing `@IsTest` method body in
  `System.runAs(agent())` — no assertion, statement or message changed. **`REQ-010`** is the one row
  whose `artefact_paths` names the test class this repair touched (`Tier2ChannelHealthTest`); it gains
  `artefacts/M1-S03/classes/TestUserFactory.cls` in its `artefact_paths` (the class the repair
  references but this step does not ship) and a note in its `test_result` that the same assertions now
  run under a permissioned user. `REQ-001`–`REQ-009` and `REQ-011`–`REQ-016` belong to other steps and
  are unaffected.
- **Two non-test classes are unchanged by this pass** — `Tier2ChannelHealthSchedulable.cls` and
  `Tier2ChannelHealthQueueable.cls` are untouched, per `artefacts/M1-S04/deploy-order.md` § 0c and
  `decisions.md` `D-M1S04-08`. No row naming only a production class needed an update.
- **Three new decisions this pass:** `D-M1S04-08` records the deviation itself (tests now run as a
  permissioned agent); `D-M1S04-09` records the cross-step dependency on `M1-S03`'s `TestUserFactory`
  copy that `amend-step` could not add to `depends_on`; `D-M1S04-10` records the still-open ambiguity
  of two methods reading `PermissionSetAssignment`/`CronTrigger`/`AsyncApexJob` in user mode as a
  `Standard User` profile, with the org's own answer pending a dry run that actually executes them.
- **`M1-S05` currency remains an open question, not newly created by this pass.** `M1-S05` (already
  `documented`) still lists the pre-repair `ApexClass` membership for this step; `TestUserFactory` is
  already named as a shared, once-only member `M1-S05` must carry per `M1-S03`'s own `D-M1S03-11` and
  this step's own `deploy-order.md` § 0c/§ 2 — this pass adds no new manifest obligation beyond what
  `D-M1S03-11` already names.
- **0 orphans confirmed, not assumed, after this pass's edit.** `check_rtm.py` run this pass reports
  16 rows, 0 coverage gaps, 0 orphans — see "RTM checker output, this pass" below.
- **Workbook:** still not written. `scale: feature` makes the ten-section workbook optional
  (`standards/build-orchestration.md` § 3.1: "workbook optional, traceability required"); this build
  has never populated one at any pass, and a single-cell update to one existing row does not change
  that build-wide choice.
- **No row is `Released`.** `build_mode: design-only`; nothing in this build has ever been deployed.
- Every fact in this note was read from `plan.json` (`steps[M1-S04].runs`), the two envelopes under
  `envelopes/M1-S04/2026-09-12T16-30-00Z.json` and `.../2026-09-12T16-45-00Z.json`,
  `tests/M1-S04/results.json`, and `artefacts/M1-S04/deploy-order.md` §§ 0c, 2, 4, 8 — none narrated
  past what those sources state.

### M1-S03 repair/retest pass note (superseded by the `M1-S04` repair/retest pass note above, kept for the record)

- **Still 16 requirements; no new row minted, four rows updated in place.** This pass documents
  `M1-S03` run 4 — a § 4 test-only repair (`documented` → `running` → `built` → `tested`) that closed
  `reports/MOCK-DEPLOY-M1.md` run 6's `S2-F-11` finding: all 28 test methods across the step's three
  test classes had failed at execution because none ran as a permissioned user, while
  `Tier2WebhookQueueable` and `CaseTriggerHandler` correctly enforce `WITH USER_MODE`. The repair added
  `classes/TestUserFactory.cls` (+ `-meta.xml`) and wrapped every pre-existing `@IsTest` method body in
  `System.runAs(agent())` — no assertion, statement or message changed. **`REQ-012`, `REQ-013`,
  `REQ-014` and `REQ-015`** are the four rows whose `artefact_paths` name a test class this repair
  touched (`Tier2EscalationServiceTest`, `Tier2WebhookQueueableTest`, `IntegrationFailureResendTest`);
  each gains `artefacts/M1-S03/classes/TestUserFactory.cls` in its `artefact_paths` and a note in its
  `test_result` that the same assertions now run under a permissioned user. `REQ-011` and `REQ-016`
  name only production classes untouched by this repair and are left unchanged; `REQ-001`–`REQ-010`
  belong to other steps and are unaffected.
- **Six non-test classes and both triggers are unchanged by this pass** — the repair's own scope, per
  `artefacts/M1-S03/deploy-order.md` § 0b and `decisions.md` `D-M1S03-09`. No row naming only a
  production class needed an update.
- **Two new decisions this pass, beyond `D-M1S03-09`:** `D-M1S03-10` records `PROFILE = 'Standard
  User'` as an unconfirmed library default (finding `S4-F-03`); `D-M1S03-11` records that
  `TestUserFactory` is a new `ApexClass` member `M1-S05`'s build-level manifest must still add
  (finding `S4-F-02`) — an `M1-S05` obligation, not this pass's to close.
- **`M1-S05` currency is now a confirmed open question, not a hypothetical one.** `M1-S05` (already
  `documented`) was built before this repair existed; its `package.xml` and
  `reports/MILESTONE-M1-package.xml` still list the pre-run-4 twelve `ApexClass` members, not the
  thirteen this step now ships. This traceability pass does not add
  `artefacts/M1-S05/package.xml`/`deploy-order.md` to any row for the same reason the `M1-S05` pass
  note below already gives (`check_rtm.py`'s `setdefault` indexing and the `.md`-suffix carve-out) —
  re-running `M1-S05` is what would change that, and it is out of scope for an `M1-S03`-only pass.
- **0 orphans confirmed, not assumed, after this pass's edits.** `check_rtm.py` run this pass reports
  16 rows, 0 coverage gaps, 0 orphans — see "RTM checker output, this pass" below.
- **Workbook:** still not written. `scale: feature` makes the ten-section workbook optional
  (`standards/build-orchestration.md` § 3.1: "workbook optional, traceability required"); this build
  has never populated one at any pass, and a single-artefact row (`TestUserFactory.cls`) would make the
  workbook a partial, misleading record rather than an honest absence — this pass keeps the build-wide
  choice rather than starting a one-row workbook.
- **No row is `Released`.** `build_mode: design-only`; nothing in this build has ever been deployed.
- Every fact in this note was read from `plan.json` (`steps[M1-S03].runs`), the two envelopes under
  `envelopes/M1-S03/2026-09-12T16-13-43Z.json` and `.../2026-09-12T16-30-00Z.json`,
  `tests/M1-S03/results.json`, and `artefacts/M1-S03/deploy-order.md` § 0b — none narrated past what
  those sources state.

## RTM checker output, this pass

```text
$ python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py --file traceability.md --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"
traceability.md: 16 row(s), build schema, 0 coverage gap(s), 0 orphan(s), 0 error(s), 0 warning(s)
```

### M1-S05 pass note (superseded by the `M1-S03` repair/retest note above, kept for the record)

- **Still 16 requirements, no new row and no row edited.** `M1-S05` is the build-level manifest
  aggregation step (`package.xml` + `deploy-order.md`); it ships no `CustomObject`, `CustomField`,
  `ApexClass`, `ApexTrigger`, `PermissionSet`, `ExternalCredential` or `NamedCredential` file of its
  own — every component it manifests is backed by a file `M1-S01`–`M1-S04` already contributed and
  already carries in some row's `artefact_paths` above. Per `agents/build-doc-keeper/AGENT.md` Step 7,
  this step "mints no requirement of its own"; this coverage note, not a row edit or a new
  `artefact_paths` entry, is what it produces for the matrix.
- **Why no row gained `artefacts/M1-S05/package.xml` or `artefacts/M1-S05/deploy-order.md`.**
  `check_rtm.py`'s `index_manifest` does parse every `package.xml` it walks, including this step's
  build-level one, and calls `add(mtype, member, where)` for each of its 33 members
  (`skills/admin/requirements-traceability-matrix/scripts/check_rtm.py` lines 473–475). But `add`
  keys the index with `index.setdefault(key, where)` (line 463): the **first** file `os.walk` visits
  that mints a given `Type:Name` key wins the recorded path, and `os.walk` reaches `M1-S01/`…`M1-S04/`
  before the alphabetically-later `M1-S05/`. Every one of the 33 keys `M1-S05/package.xml` declares
  was already minted by an `M1-S01`–`M1-S04` file (or that step's own `package.xml` fragment) before
  the walk reaches `M1-S05`, so `setdefault` is a no-op for all 33 and `M1-S05/package.xml` adds zero
  new keys to `manifest_index` — orphan detection (line 762, `for key, where in
  sorted(manifest_index.items())`) never sees a key whose only source is `M1-S05`. Adding
  `artefacts/M1-S05/package.xml` to a row's `artefact_paths` would resolve to a real file but cover a
  key some earlier row already covers. `deploy-order.md` is a `.md` note, one of the suffixes
  `check_rtm.py` treats as documentation rather than a deployable component when resolving an
  `artefact_paths` cell (`NON_METADATA_ARTEFACT_PATH_SUFFIXES`, Gotcha 19's own carve-out). Neither
  file is an "addressable artefact" in the sense Step 4/Step 7 use the word for this step; both are
  the compiled record of artefacts other rows already name.
- **0 orphans confirmed, not assumed.** `python3 skills/admin/requirements-traceability-matrix/scripts/check_rtm.py
  --file traceability.md --manifest-dir artefacts --repo-root "/Users/pranavnagrecha/VS Code/Personal/SfSkills"`
  run this pass reports 16 rows and 0 orphan artefacts under `artefacts/M1-S01` through
  `artefacts/M1-S04` — the 11 orphans the `M1-S03` pass resolved stay resolved, and `M1-S05` itself
  contributes no new derived component for the checker to find uncovered. See "RTM checker output,
  this pass" below the matrix for the run transcript.
- **What `M1-S05` proves about the 16 rows above, read here rather than re-derived from
  `artefacts/M1-S05/deploy-order.md`:** the build-level manifest — 7 `<types>` blocks, 33 members,
  `<version>67.0</version>`, no wildcards — was built by aggregating exactly the files these 16 rows'
  `artefact_paths` already name (plus `TestDataFactory`'s one deduplicated member,
  `D-M1S05-01`/`D-M1S03-06`/`D-M1S04-06`), and `reports/MOCK-DEPLOY-M1.md` run 5 (manifest mode)
  deployed that manifest end to end at 38/38, matching run 4's per-file count exactly
  (`D-M1S05-05`). No row's `status` moves because of this: `build_mode: design-only`, nothing in this
  build has ever actually deployed, so every row stays at `In UAT` regardless of how thoroughly its
  manifest membership is now proven.
- **Two plan-text defects this step's own inputs carried, both recorded in `decisions.md` rather than
  silently corrected here:** `inputs.members.ApexClass` names 11 classes where the artefacts (and
  this step's own manifest) carry 13 (`D-M1S05-01`), and `inputs.deploy_order` sequences
  `PermissionSet` ahead of the fields it grants (`D-M1S05-02`). Neither changes any row above — both
  are about how `M1-S05` itself was built, not about which requirement any row traces.
- **The `PV-007` AuthHeader prose lag (`D-M1S02-06`), narrowed not closed:** `REQ-009`'s row above
  (`M1-S02`, `ExternalCredential:OnCall_Tool_EC`) still carries its `M1-S02`/`M1-S03`-pass test_result
  text unchanged at this pass — that text already states the parameter/formula are supplied and the
  org has confirmed the element is required. `D-M1S05-04` records the further narrowing
  `artefacts/M1-S05/deploy-order.md` § 3 Step 1 makes (the grammar-parses-on-deploy half is now also
  closed, by run 5) and why `M1-S05`'s own plan text could not be amended to match. `REQ-009`'s row is
  not re-worded here because the narrowing is `M1-S05`'s own manual test's text, not this
  requirement's `test_result` cell.
- **Workbook:** still not written. `scale: feature` makes the ten-section workbook optional
  (`standards/build-orchestration.md` § 3.1: "workbook optional, traceability required"), and this is
  the build-wide choice `M1-S05`'s own step notes name — this pass keeps it, as every prior pass has.
- **No row is `Released`.** `build_mode: design-only`; nothing in this build has ever been deployed.
- Every fact in this note was read from `plan.json` (`steps[M1-S05]`), the three envelopes under
  `envelopes/M1-S05/`, `tests/M1-S05/results.json` and `manifest-check.txt`,
  `artefacts/M1-S05/package.xml` and `deploy-order.md`, and `reports/MOCK-DEPLOY-M1.md` runs 4–5 —
  none narrated past what those sources state. This is the last `M1` step to document; `M1` is now
  ready for `milestone-verifier`.

### M1-S03 pass note (superseded by the M1-S05 note above, kept for the record)

- **16 requirements now have a row.** `REQ-001`–`REQ-010` unchanged in *count* from the `M1-S04` pass;
  seven of them (`REQ-001`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-008`, `REQ-009`) are
  updated **in place** at this pass — same `step_id`, `artefact_paths` gains the `M1-S03` files,
  `test_result` narrates the Apex half landing — per the model this file's own `M1-S02` pass note
  established (`req_id` is unique across the whole matrix; a requirement whose delivery spans steps
  stays on its originating row, never a second row for the same `req_id`). Six new rows, `REQ-011`
  through `REQ-016`, are minted at this pass for `M1-S03` inputs that named a distinct, testable
  requirement no earlier row already covered — see "Requirement id derivation" above for each anchor.
- **Out-of-chronological-step-order note.** `M1-S04` was documented (previous pass) before `M1-S03`
  finished its third build — the two Apex steps in this plan are independent in the DAG
  (`M1-S03.depends_on = [M1-S01, M1-S02]`; `M1-S04` depends on neither), so `M1-S03`'s documentation
  pass legitimately runs after `M1-S04`'s. `decisions.md` is append-only and its `D-M1S03-*` entries
  therefore sit after `D-M1S04-*`, in pass order rather than step-number order — recorded here so a
  reader does not mistake the ordering for a mistake.
- **Why seven rows were updated in place rather than left alone.** `REQ-001` (Q10, rollback/publish
  sequencing), `REQ-003` (Q14, suppression stamp), `REQ-004` (Q17, picklist enforcement in Apex —
  literally named "the Apex in M1-S03" in the requirement's own text), `REQ-005` (Q18, field
  population on failure), `REQ-006` (Q20, the resend behaviour itself), `REQ-008` (Q4, the actual
  HTTPS POST) and `REQ-009` (Q5, no-secret-in-code, now independently confirmed on the Apex side) were
  all explicitly named in prior passes' own `test_result` prose as "pending M1-S03" or "not yet
  built." Leaving them unchanged after `M1-S03` is tested would mean the matrix still says something
  the build has already falsified.
- **The six new rows (`REQ-011`–`REQ-016`) cover `M1-S03` inputs that were never anchored to an
  earlier row:** `Q11` (publish-result inspection), `Q13` (enqueue-once-per-transaction), `Q7`/`Q15`
  (retry classification and the Finalizer contract), `Q8` (idempotency-key replay), `Q22` (volume /
  governor-limit headroom), and `Q23` (sharing and security-mode compliance). Each is a genuinely
  separate, independently-testable behaviour rather than a restatement of an existing row — none of
  `REQ-001`–`REQ-010` names any of these six facts.
- **No coverage gap and 11 fewer orphans.** Before this pass, `check_rtm.py --file traceability.md
  --manifest-dir artefacts --repo-root <repo>` reported 11 orphan artefacts, all under `M1-S03`: the
  ten `ApexClass`/`ApexTrigger` members no row named yet plus `MockHttpResponseGenerator` (the eleventh
  was `TestDataFactory`, already evidenced via `REQ-010`'s `M1-S04` reference before this pass). This
  pass's `artefact_paths` additions resolve all eleven; re-run the checker after this pass to confirm
  0 orphans.
- **Workbook:** still not written. `scale: feature` makes the ten-section workbook optional
  (`standards/build-orchestration.md` § 3.1: "workbook optional, traceability required"), and no pass
  of this build has written one — `M1-S05`'s own step notes name the same choice build-wide. This pass
  follows that precedent rather than starting a workbook unilaterally at the third documented step.
- **No row is `Released`.** `build_mode: design-only`; nothing in this build has ever been deployed, so
  every row above tops out at `In UAT` regardless of how thoroughly its Apex is built and checked.
- Every artefact, decision and clarification id touched or added at this pass was read from
  `plan.json` (`steps[M1-S03]`, `.amendments[]`), the eight envelopes under `envelopes/M1-S03/`,
  `tests/M1-S03/results.json`, `artefacts/M1-S03/deploy-order.md`, and `reports/MOCK-DEPLOY-M1.md`
  (runs 3–4, the org's own compile record) — none narrated past what those sources state. Three facts
  in `REQ-009`'s and `REQ-016`'s rows were verified by a `grep` this pass rather than merely quoted
  from `deploy-order.md`'s prose, and one small arithmetic slip in `deploy-order.md` § 6 ("six
  production classes," "both SOQL statements") was caught by that same `grep` and is noted, not
  silently corrected, in `REQ-016`'s row — the artefact itself is not this agent's to edit.

### M1-S04 pass note (superseded by the M1-S03 note above, kept for the record)

- **10 requirements now have a row.** `REQ-001`–`REQ-009` unchanged from the `M1-S02` pass; `REQ-010`
  minted at this `M1-S04` pass, settled by `Q24` — see "Requirement id derivation" above for the
  anchor.
- **`REQ-010` is the fit-gap row PLAN.md's own coverage table names "Alert a named owner when the
  notification channel itself goes dark, not only when one delivery fails,"** tiered `partial` and
  routed to decision `D11` (Schedulable Apex, not a schedule-triggered Flow, per
  `standards/decision-trees/async-selection.md`). Its only step is `M1-S04`; nothing else in this plan
  touches the channel-health check.
- **Workbook:** not written this pass. `scale: feature` makes the ten-section workbook optional
  (`standards/build-orchestration.md` § 3.1: "workbook optional, traceability required"), and this
  build has not written one at any prior pass either — `M1-S05`'s own step notes name the same choice
  build-wide ("at the feature tier the workbook is optional and traceability is produced from the plan
  record rather than built as a step"). This pass follows that precedent rather than starting a
  workbook unilaterally at the fourth step.
- **`REQ-001`–`REQ-009` are untouched at this pass** — `M1-S04` is the channel-health monitor and does
  not touch platform-event sequencing, dedupe, the suppression stamp, the picklist value sets, the
  event payload, the credential, or the API-key-storage requirement.
- **No row is `Released`.** `build_mode: design-only`; nothing in this build has ever been deployed.
- Every artefact, decision and clarification id touched or added at this pass was read from
  `plan.json` (`steps[M1-S04]`, `.amendments[0]`), the five envelopes under `envelopes/M1-S04/`,
  `tests/M1-S04/results.json`, and `artefacts/M1-S04/deploy-order.md` — none narrated. `REQ-010` is
  minted by this documentation pass, per the "Requirement id derivation" table above; its anchor is a
  direct statement that no `requirement.md` line names it, matching `REQ-001`/`REQ-002`'s own anchors.

### M1-S02 pass note (superseded by the M1-S04 note above, kept for the record)

- **9 requirements now have a row.** `REQ-001`–`REQ-007` (settled by `Q10`, `Q12`, `Q14`, `Q17`,
  `Q18`, `Q20`, `Q30`) from the `M1-S01` pass, plus `REQ-008` and `REQ-009` minted at this `M1-S02`
  pass, settled by `Q4` and `Q5` respectively — see "Requirement id derivation" above for both new
  anchors.
- **Correction to the M1-S01 pass's own prediction, caught by `check_rtm.py` at this pass:** the
  first pass wrote that `REQ-005`/`REQ-006` "will gain additional rows once M1-S02 … are
  documented." That is not what this schema supports — `check_rtm.py` enforces `req_id` unique
  **across the whole matrix** (item 2 of its own docstring; confirmed by running it with a second
  `REQ-005` row present: `ERROR: row 9: duplicate req_id 'REQ-005'`), and the real precedent this
  file already cites, `examples/builds/case-onboarding/traceability.md`, never carries two rows for
  one `req_id` either — a requirement whose delivery spans steps stays on its originating step's row
  (`step_id` unchanged), with the later step's contribution folded into `artefact_paths` and narrated
  in `test_result` (see that file's `REQ-018`/`REQ-019`/`REQ-020`, each staying on its own step while
  the prose tracks a dependency still `pending`). `REQ-005` and `REQ-006` are updated **in place**
  this pass on that model: `step_id` stays `M1-S01`, `artefact_paths` gains the two `M1-S02` files,
  and `test_result` narrates the permission-grant half landing. `REQ-001`–`REQ-004` and `REQ-007`
  are untouched at this pass — M1-S02 is the access layer and does not touch platform-event
  sequencing, dedupe, the suppression stamp, the picklist value sets, or the event payload.
- **Neither new requirement (`REQ-008`, `REQ-009`) is fully closed.** `REQ-008`'s "within a minute"
  delivery is M1-S03's Apex, not yet built (`status: In Build`); `REQ-009`'s no-secret-in-metadata
  claim rests on direct inspection and a manual test still outstanding at the M1 gate
  (`status: In UAT`). Both are named explicitly rather than rounded up to a status the evidence does
  not support yet.
- **No row is `Released`.** `build_mode: design-only`; nothing in this build has ever been deployed,
  so `Released` would misstate the build's own state regardless of test outcome.
- Every artefact, decision and clarification id touched or added at this pass was read from
  `plan.json` (`steps[M1-S02]`), `envelopes/M1-S02/2026-09-12T10-28-30Z.json` and
  `.../2026-09-12T10-32-00Z.json`, `tests/M1-S02/results.json` and `summary.md`, and
  `artefacts/M1-S02/deploy-order.md` — none narrated. `REQ-008` and `REQ-009` are minted by this
  documentation pass, per the "Requirement id derivation" table above; their anchors are direct
  quotes from `requirement.md`, not inferred paraphrase.

### M1-S01 pass note (its row-per-step-per-requirement prediction corrected above, kept for the record)

The first documentation pass wrote: "7 requirements now have a row for M1-S01 … the same seven ids
will gain additional rows once M1-S02/M1-S03/M1-S04 are documented." The *requirements themselves*
gaining further coverage from later steps was right; "additional rows" was not — `check_rtm.py`'s
`req_id`-uniqueness rule (see the correction above) means that coverage lands as an in-place update
to the requirement's one row, not a second row. `REQ-001`–`REQ-004` and `REQ-007` still await their
own updates from `M1-S03`/`M1-S04`.
