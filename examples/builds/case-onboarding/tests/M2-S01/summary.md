# M2-S01 — test summary

Step: `M2-S01` — Intake bypass Custom Permission and the integration permission set that carries it
Type: `access` · Agent: `metadata-builder` · Status in: `built` · Status out: `tested`
Runner: `agents/step-tester/AGENT.md` · run_id `2026-09-06T07-30-00Z`

All checker commands were run **verbatim as declared**, from the build directory, after the
`standards/build-orchestration.md` § 5 deny-list cleared each one. No flag was added, removed or
re-ordered; no path was substituted.

| # | Test | Type | Runner invoked | Exit | Result |
|---|---|---|---|---|---|
| 1 | `check_custom_permissions.py` | `checker` | `python3 skills/admin/custom-permissions/scripts/check_custom_permissions.py --manifest-dir artefacts/M2-S01` | 0 | PASS — 0 error, 0 warning, 0 info; grant resolves to a defined permission |
| 2 | `check_access_model.py` | `checker` | `python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir artefacts/M2-S01` | 0 | PASS — score 100, 0 findings, 1 file scanned |
| 3 | `xml` (always-on + declared) | `xml` | `xml.etree.ElementTree` over `artefacts/M2-S01/**` | 0 | PASS — 3/3 files parsed |
| 4 | `manifest` (always-on + declared) | `manifest` | two-way derivation vs `artefacts/M2-S01/package.xml` | 0 | PASS — consistent in both directions, no wildcards |
| 5 | `check-outputs` (precondition on 1 and 2) | — | `python3 scripts/build_plan.py check-outputs .sfskills/builds/case-onboarding/plan.json M2-S01` | 0 | PASS — `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| 6 | B01 permission-set scope | `manual` | not runnable — deferred to the M2 gate | — | DEFERRED (evidence gathered, see below) |

No failures. First line of failure output: none to report.

## Raw captures (siblings of this file)

`check_custom_permissions.{stdout,stderr,exit}.txt`, `check_access_model.{stdout,stderr,exit}.txt`,
`check_outputs.{stdout,stderr,exit}.txt`, `xml.stdout.txt`, `manifest.stdout.txt`,
`manual-evidence.stdout.txt`.

## Manifest check detail

Derived from files → `CustomPermission: Bypass_Case_Intake_Validation`,
`PermissionSet: Case_Intake_Integration`. Declared in manifest → the same two, explicitly, no `*`.
Excluded from both directions: `package.xml` (the manifest itself) and `deploy-order.md` (no
source-format metadata suffix — a documentation artefact, not a component). No
`metadata-api-coverage-gaps` exclusion was needed: both types have standalone source files and are
fully supported by the Metadata API.

## Manual test — evidence for the human at the M2 gate

The tester does not tick this. Every file-checkable clause was asserted from disk and holds:

- `Case_Intake_Integration.permissionset-meta.xml` has exactly **4** top-level elements:
  `<label>`, `<description>`, `<hasActivationRequired>`, `<customPermissions>`.
- Of the 14 grant-bearing elements `PermissionSet` accepts, exactly one is present:
  `<customPermissions>{enabled=true, name=Bypass_Case_Intake_Validation}`. Absent:
  `objectPermissions`, `fieldPermissions`, `userPermissions`, `classAccesses`, `pageAccesses`,
  `recordTypeVisibilities`, `tabSettings`, `applicationVisibilities`, `flowAccesses`,
  `customSettingAccesses`, `customMetadataTypeAccesses`, `externalDataSourceAccesses`,
  `externalCredentialPrincipalAccesses`.
- `deploy-order.md` carries the post-deploy instruction ("Assign `Case_Intake_Integration` to the
  Email-to-Case / Web-to-Case automated-process identity only… No human user receives it") and a
  named owner ("Named owner for that assignment: the Security architect").

What remains genuinely human at the gate: confirming that the assignment described was actually
performed against the integration identity and no human user. `PermissionSetAssignment` is record
data, not metadata (`skills/devops/metadata-api-coverage-gaps` gotcha 3), so no artefact in a
design-only build can carry that evidence.
