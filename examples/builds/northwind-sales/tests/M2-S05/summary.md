# Test summary — M2-S05

Build: `northwind-sales` · Step: M2-S05 (`ui` — Enterprise and Renewal Opportunity Paths + org PathAssistant setting) · Tester: `step-tester`

**Result: PASSED** (5/5 runnable tests passed; 2 manual tests deferred to the M2 milestone gate)

| # | Test | Type | Result | First line of output |
|---|---|---|---|---|
| 1 | XML well-formedness | `xml` | PASS | 4/4 files parsed (package.xml, settings, 2 pathAssistants) |
| 2 | package.xml <-> artefacts consistency | `manifest` | PASS | 2 PathAssistant + 1 Settings member, each with a file; no orphans either direction |
| 3 | `check_path_and_guidance.py --manifest-dir artefacts` (scope: build) | `checker` | PASS | exit 0 - "Checked 2 path(s): no issues found." |
| 4 | `check_opportunity_management.py --manifest-dir artefacts/M2-S05` (scope: step) | `checker` | PASS | exit 0 - "No issues found." |
| 5 | `check_sales_process_mapping.py --manifest-dir artefacts/M2-S05` (scope: step) | `checker` | PASS (exit 0), asserts nothing | exit 0 - "Scanned 0 file(s) - nothing asserted; check --manifest-dir" |
| 6 | Enterprise path exit-criteria manual check | `manual` | DEFERRED | ticked at M2 milestone gate |
| 7 | deploy-order.md "path != feature on" manual check | `manual` | DEFERRED | ticked at M2 milestone gate |

`check-outputs M2-S05` (repo root): `{"ok": true, "missing": [], "empty": [], "malformed": []}` - all 5 declared outputs present, non-empty, well-formed.

## On test 5 - read it honestly

`check_sales_process_mapping.py` exited 0 over `artefacts/M2-S05`, but its own stdout says why that
0 is not a content pass: `Scanned 0 file(s) - nothing asserted; check --manifest-dir`. That checker
lints `*.yaml`/`*.yml`/`*.csv` sales-process maps and a retrieved `OpportunityStage` value set -
this step ships neither. Its subject matter (the stage ladder) belongs to M1-S01. Per the step's own
`deploy-order.md` section 7, this is a plan defect (the checker's assertions are not satisfiable inside this
step's output), not an artefact defect, and it is not this tester's or the builder's to fix while the
step is being tested. Recorded as `passed` on the declared `"expected": "exit 0"` condition, and
flagged in Process Observations - not represented as a pass on the paths' content.

## Manual tests - spot-checked, not ticked

This agent does not tick manual tests. Both are recorded verbatim in `results.json.skipped_manual[]`
for the milestone gate. As a courtesy cross-check (not a substitute for human sign-off), both claims
were verified against the artefacts they cite:

- Test 6: the Enterprise path's `Discover` step `info` does read "...at least one product line added
  from the price book..." and "...booked Next Step..."; the `Propose` step `info` does name "a primary
  contact with the Decision Maker contact role"; the `Negotiate` step's `fieldNames` are exactly
  `Discount__c`, `Approval_Status__c`, `CloseDate`. Matches.
- Test 7: `deploy-order.md` section 3 states, verbatim, that a green deploy "proves neither that Path is
  enabled in the org, nor that the Path component is on the record page," and names `M3-S05` as the
  step that puts the component on the record page. Matches.

Both are Given/When/Then-shaped with a named observable outcome per
`admin/acceptance-criteria-given-when-then`, so neither is flagged as unusable.

## Artefact hashes

Recorded in `results.json.artefact_hashes` from `build_plan.py check-outputs --hashes`, so `tested`
is refused if the artefacts change under it later without a re-test.

Raw checker stdout/stderr: `check_path_and_guidance.out`, `check_opportunity_management.out`,
`check_sales_process_mapping.out`, `check-outputs.out` (this directory).
