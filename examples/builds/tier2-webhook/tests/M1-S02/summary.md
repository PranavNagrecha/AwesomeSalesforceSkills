# Test summary — M1-S02 (re-test after S2-F-13 repair)

Repair under test: `metadata-builder` run 3 (envelope `envelopes/M1-S02/2026-09-12T17-20-00Z.json`)
added one `objectPermissions` row (`Tier2_Escalation__e`, `allowCreate`/`allowRead` true) to
`permissionsets/Tier2_Webhook_Admin.permissionset-meta.xml` per `artefacts/M1-S02/deploy-order.md`
§ 0b (finding S2-F-13, `reports/MOCK-DEPLOY-M1.md` run 8). No new component: `package.xml` and the
External/Named Credential files are unchanged.

| Test | Type | Result | First line of output |
|---|---|---|---|
| xml | always-on | PASS | 4/4 files parsed (`externalCredentials/OnCall_Tool_EC…`, `namedCredentials/OnCall_Tool…`, `package.xml`, `permissionsets/Tier2_Webhook_Admin…`) |
| manifest | always-on | PASS | `package.xml` names `OnCall_Tool_EC` (ExternalCredential), `OnCall_Tool` (NamedCredential), `Tier2_Webhook_Admin` (PermissionSet) — 3 members, 3 files, no mismatch. `Tier2_Escalation__e` is a permission grant inside the existing PermissionSet file, not a new manifest member, so no change was expected here. |
| `check_apex_named_credentials_patterns.py --manifest-dir artefacts/M1-S02` | checker (scope: step) | PASS | exit 0 — `OK: no Named Credential findings.` |
| `check_permission_set_architecture.py --manifest-dir artefacts` | checker (scope: build) | PASS | exit 0 — `WARN: … modifyAllRecords=true …` (pre-existing, deliberate per D12) + `INFO: PSA-DESC-02 … description is 224 characters` (declared without `--strict`, so only ERROR fails) |
| `check-outputs` | precondition | PASS | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| manual (access review) | manual | deferred | Carried to the M1 human gate verbatim, with a re-test note added pointing the reviewer at the new `Tier2_Escalation__e` row inside checklist item (d) |

**Result: `passed: true`, 4 ran, 0 failed, 1 manual deferred.**

Raw checker captures: `checker1_stdout.txt`/`checker1_stderr.txt`/`checker1_exit.txt`,
`checker2_stdout.txt`/`checker2_stderr.txt`/`checker2_exit.txt`, `check_outputs.json`/
`check_outputs_stderr.txt`/`check_outputs_exit.txt`, `xml_check.txt`.
