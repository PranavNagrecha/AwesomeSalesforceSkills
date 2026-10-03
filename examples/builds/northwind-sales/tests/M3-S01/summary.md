# M3-S01 test summary

Step: Sales Approvals email folder and the three Classic templates the approval process and its alerts send. Type `ui`, agent `metadata-builder`, status `built` at run start.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `check_email_templates.py --manifest-dir artefacts/M3-S01` | checker | PASS (exit 0) | — |
| `check-outputs M3-S01` | checker precondition | PASS (ok: true) | — |
| xml (always-on) | xml | PASS (5/5 parse) | — |
| manifest (always-on) | manifest | PASS (consistent) | — |
| Rejected-email / addressee manual criterion | manual | deferred to M3 gate | — |
| Classic-template field-shape manual criterion | manual | deferred to M3 gate | — |

**Verdict:** `passed: true`. No failures. Two `manual` acceptance tests deferred to the M3 milestone gate, not counted as failures.

Raw checker stdout/stderr: `tests/M3-S01/checker_check_email_templates.stdout.txt`, `tests/M3-S01/checker_check_email_templates.stderr.txt`. `check-outputs` captures: `tests/M3-S01/check_outputs.json`, `tests/M3-S01/check_outputs_hashes.json`. XML/manifest derivation: `tests/M3-S01/xml_check.json` and the `manifest` block in `tests/M3-S01/results.json`.
