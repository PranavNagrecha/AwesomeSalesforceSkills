# Test summary — M1-S01

Amount_Locked_After_Closed_Won validation rule, with a Sales Ops bypass (rebuild after amendment).

| Test | Type | Result | First line of output |
|---|---|---|---|
| xml | xml | pass (4/4 files parsed) | n/a |
| manifest | manifest | pass (consistent) | 3 types, 3 members, 3 files, 1:1, no wildcards |
| `check_validation_rules.py --manifest-dir artefacts/M1-S01` | checker | pass (exit 0) | `{"score": 100, "findings": [{"severity": "INFO", "location": "field references", ...}], ...}` |
| `check_custom_permissions.py --manifest-dir artefacts/M1-S01` | checker | pass (exit 0) | `Custom permissions defined:        1` |
| `check-outputs plan.json M1-S01` | precondition (run once, covers both checker tests) | ok | `{"ok": true, "step": "M1-S01", "missing": [], "empty": [], "malformed": []}` |

`passed`: **true**. `failed`: none. `skipped_manual`: none — the step itself declares no `manual` acceptance test.

Raw captures: `check_validation_rules.stdout.txt` / `.stderr.txt`, `check_custom_permissions.stdout.txt` / `.stderr.txt`, `check_outputs.stdout.json`, `xml_check.json`, `manifest_check.json` (all in this directory).

## Note on the milestone's manual UAT line

M1's own `acceptance_tests[]` (not M1-S01's) declares one `manual` test — the Given/When/Then UAT script for the block-then-bypass scenario. It is well-formed against `admin/acceptance-criteria-given-when-then` (names the persona with and without the bypass permission, the Closed Won precondition, the save action, and two observable Then outcomes with the exact error string). It is milestone-scoped, not step-scoped, so it is out of this run's `acceptance_tests[]` dispatch and is not counted in this step's `failed[]` or `skipped_manual[]`. Recorded here for continuity into `milestone-verifier`'s checklist.

## Note on the mid-edit checker

`skills/admin/validation-rules/scripts/check_validation_rules.py` was flagged as possibly mid-edit by another agent adding rule `VR-PICK-01`. The version run here already contains `VR-PICK-01` (`grep -c VR-PICK-01` → 5 matches) and ran cleanly on the first attempt — no import or syntax error, no retry needed. VR-PICK-01 did not fire against this step's formula, which is expected: the rebuild's blank guard is `NOT(ISBLANK(TEXT(StageName)))`, not a raw `ISBLANK(StageName)` on a picklist.
