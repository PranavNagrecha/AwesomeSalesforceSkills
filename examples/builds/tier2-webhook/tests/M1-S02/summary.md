# M1-S02 — step-tester results (run 2, post S2-F-02 rebuild)

Run at 2026-09-12T10:32:00Z, against `envelopes/M1-S02/2026-09-12T10-28-30Z.json` (metadata-builder rebuild run 2). Supersedes the stale `2026-09-12T10-19-53Z` result, which tested the pre-rebuild credential that `mock-deploy` rejected (S2-F-02).

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `xml` | xml (always-on) | pass — 4/4 files parsed | — |
| `manifest` | manifest (always-on) | pass — consistent, no exclusions | — |
| `skills/apex/apex-named-credentials-patterns/scripts/check_apex_named_credentials_patterns.py` --manifest-dir artefacts/M1-S02 (scope: step) | checker | pass — exit 0, check-outputs ok | — |
| `skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py` --manifest-dir artefacts (scope: build) | checker | pass — exit 0 (one non-failing WARN), check-outputs ok | `WARN: ... modifyAllRecords=true, which bypasses sharing for that object` (deliberate, decision D12) |
| Access review at the M1 gate | manual | deferred to milestone gate — not ticked by this agent | — |

Raw captures: `checker1_stdout.txt` / `checker1_stderr.txt` / `checker1_exit.txt`, `checker2_stdout.txt` / `checker2_stderr.txt` / `checker2_exit.txt`, `xml_check.txt`, `check_outputs.json`.

## Manual test evidence (not ticked)

Clause (d) asks the reviewer to confirm `fieldPermissions` carries `Case.Tier2_Notified_At__c` plus every `Integration_Failure__c` field from M1-S01. Counted directly from `artefacts/M1-S02/permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml`: **12 `<fieldPermissions>` rows** — `Case.Tier2_Notified_At__c` plus 11 `Integration_Failure__c` fields (`Attempt_Count__c`, `Case_Number__c`, `Case__c`, `Endpoint__c`, `Error_Message__c`, `HTTP_Status__c`, `Last_Attempted_At__c`, `Request_Payload__c`, `Resend__c`, `Response_Body__c`, `Severity__c`). `Status__c` is correctly excluded (required field, F-S2-01). This is reported as evidence for the human reviewer at the M1 gate; it is not a pass/fail tick by this agent.

## Test-coverage observation

Both declared checkers exited 0 on **run 1's** credential (see `envelopes/M1-S02/2026-09-12T10-19-53Z.json`) — the same artefact set that `mock-deploy` run 1 then rejected with `The parameter type "AuthHeader" requires these fields: ParameterValue.` (S2-F-02, `reports/MOCK-DEPLOY-M1.md`). Neither `check_apex_named_credentials_patterns.py` nor `check_permission_set_architecture.py` asserts that an `AuthHeader` `externalCredentialParameters` entry carries a non-empty `parameterValue` — that is a real gap between "checker green" and "org would accept this," not a defect in either checker's stated scope. This run's artefacts carry `parameterValue` (`{!$Credential.OnCall_Tool_EC.ApiKey}`) after the rebuild, and both checkers still exit 0 — consistent with, not proof against, the same blind spot.
