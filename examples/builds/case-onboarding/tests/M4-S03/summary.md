# M4-S03 — test summary

Re-run after the third build (F-38 corrected: FlowTest Start test point now carries
`InputTriggeringRecordInitial` only, per `reports/MOCK-DEPLOY-M4.md` run 3). Flow, Flow.settings,
package.xml, flow-governance-policy.yaml and no-account-fallback-note.md are byte-identical to
build 1 per the builder's own SHA-256 note; only the flowtest and deploy-order.md changed.

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| xml | always-on | PASS | — (4 files parsed: flow, flowtest, package.xml, Flow.settings) |
| manifest | always-on | PASS | — Flow / FlowTest / Settings:Flow each named explicitly; every member has a file; no member without a file; flow-governance-policy.yaml, deploy-order.md, no-account-fallback-note.md correctly excluded as non-deployable |
| `check_record_triggered_flow_patterns.py` | checker | PASS | exit 0, "No issues found." |
| `check_flow_element_naming_conventions.py` | checker | PASS | exit 0, 4 W-FAULT-TARGET warnings (fault-target naming is WARN-by-design per this step's own acceptance-test description, no `--strict` declared) |
| `check_flow_governance.py` | checker | PASS | exit 0, "0 error(s), 2 advisory" — the documented Flow.settings-naming advisory (checker globs metadata-format `Flow.settings`, build uses DX `-meta.xml` naming) and the fault-path delegation NOTE, both expected outcomes per the plan |
| `check-outputs` | precondition | OK | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| manual (Given/When/Then, well-formed) | manual | deferred to milestone gate | Case.EntitlementId / BusinessHoursId / Priority stamping + no-match fallback + S3 governance-field checks (description Owner: marker >=60 chars, interviewLabel present, apiVersion >=59, runInMode DefaultMode) |

**passed: true** (failed: 0; 1 manual test deferred, not counted as a failure)

Raw checker captures: `check_record_triggered_flow_patterns.{stdout,stderr,exit}`,
`check_flow_element_naming_conventions.{stdout,stderr,exit}`,
`check_flow_governance.{stdout,stderr,exit}`, `check_outputs.json` (this directory).
