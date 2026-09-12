# step-tester — M2-S02 (rebuild #2 retest)

Retest after REBUILD #2 (PermissionSet descriptions trimmed to <= 200 chars for
mock-deploy finding F-15). See `envelopes/M2-S02/2026-09-12T01-25-00Z.md` and
`artefacts/M2-S02/deploy-order.md` section Rebuild #2.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `xml` | always-on | PASS | 8/8 files under `artefacts/M2-S02/` parsed with ElementTree |
| `manifest` | always-on | PASS | every PermissionSet/PermissionSetGroup member has a matching file and vice versa |
| `check_permission_set_architecture.py --manifest-dir artefacts` | checker (scope: build) | PASS (exit 0) | `WARN: PSA-DESC-02 artefacts/M2-S01/permissionsets/Case_Intake_Integration.permissionset-meta.xml: PermissionSet description is 244 characters, approaching the 255-character limit.` -- pre-existing M2-S01 WARN, expected and non-failing per task instructions; nothing about M2-S02 flagged |
| `check_permission_set_group_composition.py --manifest-dir artefacts/M2-S02` | checker (scope: step) | PASS (exit 0) | `GOOD: reuse: permission set 'Case_Agent_Core' is referenced by 3 PSGs (...) -- composition reuse working as intended.` Summary: 1 good, 0 error, 0 warn, 0 info, scanned 3 PSG file(s). |
| `check_access_model.py --manifest-dir artefacts/M2-S02` | checker (scope: step) | PASS (exit 0) | `{"score": 100, "findings": [], "summary": "Scanned 7 access-model metadata file(s); 0 finding(s) detected."}` |
| `check-outputs` | precondition for every checker | PASS (exit 0) | `{"ok": true, "step": "M2-S02", "missing": [], "empty": [], "malformed": []}` |

No `command` or `manual` acceptance tests declared on this step.

## File-checkable facts (all 7 metadata files under `artefacts/M2-S02/`)

| File | `<description>` length | `viewAllRecords: true`? | `modifyAllRecords: true`? |
|---|---|---|---|
| `permissionsets/Case_Agent_Core.permissionset-meta.xml` | 192 | no | no |
| `permissionsets/Case_Billing.permissionset-meta.xml` | 183 | no | no |
| `permissionsets/Case_Tier1.permissionset-meta.xml` | 193 | no | no |
| `permissionsets/Case_Tier2.permissionset-meta.xml` | 199 | no | no |
| `permissionsetgroups/PSG_Billing_Prod.permissionsetgroup-meta.xml` | 187 | no | no |
| `permissionsetgroups/PSG_Tier1_Prod.permissionsetgroup-meta.xml` | 194 | no | no |
| `permissionsetgroups/PSG_Tier2_Prod.permissionsetgroup-meta.xml` | 132 | no | no |

All 7 descriptions are <= 255 (all <= 200, confirming the rebuild's stated 192/183/193/199 for
the 4 PermissionSets and no change needed on the 3 PSGs). No `viewAllRecords` or
`modifyAllRecords` set `true` anywhere in the step's artefacts.

Raw checker captures: `check_permission_set_architecture.{stdout,stderr,exit}.txt`,
`check_permission_set_group_composition.{stdout,stderr,exit}.txt`,
`check_access_model.{stdout,stderr,exit}.txt`, `check_outputs.{stdout,stderr,exit}.txt`,
`xml_parse.json`, `manifest_check.json`.

**passed: true** (0 failed, 0 manual deferred).
