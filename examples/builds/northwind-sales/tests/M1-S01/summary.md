# Test summary — M1-S01

Build: `northwind-sales` · Scale: `project` · Step type: `object-model` · Agent: `metadata-builder`

Re-run after the N3-F-01 repair (`reports/MOCK-DEPLOY-M1.md` run 1;
`artefacts/M1-S01/deploy-order.md` § 6; repair envelope
`envelopes/M1-S01/2026-09-18T13-40-27Z.md`) — `<default>true</default>` was
removed from the opening stage of both `BusinessProcess` files. The step's
other seven outputs are unchanged from the prior test pass.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `xml` (8 files under `artefacts/M1-S01/`) | always-on | PASS | all 8 `*.xml`/`*-meta.xml` files parsed with `xml.etree.ElementTree` |
| `manifest` | always-on | PASS | `package.xml` names exactly the 7 members this step produces (StandardValueSet, 2×BusinessProcess, 2×RecordType, 2×CustomField); no member without a file, no file without a member |
| `skills/admin/opportunity-management/scripts/check_opportunity_management.py --manifest-dir artefacts/M1-S01` | checker | PASS (exit 0) | `No issues found.` |
| `skills/admin/picklist-and-value-sets/scripts/check_picklist_and_value_sets.py --manifest-dir artefacts/M1-S01` | checker | PASS (exit 0) | `No findings.` |
| `skills/admin/object-creation-and-design/scripts/check_object_creation_and_design.py --manifest-dir artefacts/M1-S01` | checker | PASS (exit 0) | `No issues found across 0 object file(s) and 2 field file(s).` |
| `check-outputs M1-S01` | precondition | PASS | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| Manual: deploy-order.md retrieve-and-merge instruction (D1/A24) | manual | DEFERRED | not runnable here — carried to `skipped_manual[]` for the M1 milestone gate |
| Manual: stage/probability/forecastCategory table + no "Commit" token (Q5/Q6) | manual | DEFERRED | not runnable here — carried to `skipped_manual[]` for the M1 milestone gate |

**Overall: passed = true.** All 3 declared checkers plus both always-on checks passed on the post-repair artefacts; `artefact_hashes` in `results.json` are recomputed for this run so a `set-status … tested` against a further-changed artefact will correctly refuse as stale. 2 manual tests deferred to the human at the M1 milestone gate (never counted toward pass/fail here).

Raw checker stdout/stderr/exit code captures: `check_opportunity_management.{stdout,stderr,exit}.txt`, `check_picklist_and_value_sets.{stdout,stderr,exit}.txt`, `check_object_creation_and_design.{stdout,stderr,exit}.txt`, all in this directory.
