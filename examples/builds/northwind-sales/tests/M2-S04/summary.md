# Test summary — M2-S04

Re-test after the N3-F-06 repair (envelope `envelopes/M2-S04/2026-09-19T15-08-49Z.md`): the
`<description>` element was rewritten from 766 to 205 characters; every other element of the
validation rule, and `package.xml`, are byte-identical to the run this step's first test pass covered.
This run supersedes and overwrites the prior `results.json` (run `2026-09-19T14-59-39Z`), whose
`artefact_hashes` were stale against the repaired file.

| Test | Type | Result | First line of output |
|---|---|---|---|
| xml | xml | pass | all 2 files parse |
| manifest | manifest | pass | ValidationRule member `Opportunity.Opportunity_Products_Required_At_Propose` consistent both directions, no wildcard |
| `check_validation_rules.py --manifest-dir artefacts` (scope: build) | checker | pass (exit 0) | `Scanned 2 validation rule(s) across 2 file(s); 1 finding(s) detected.` — 1 REVIEW (blank guard), 0 blocking |
| `check_products_and_pricebooks.py --manifest-dir artefacts/M2-S04` (scope: step) | checker | pass (exit 0) | `No issues found.` — asserts nothing demonstrable; tree has no Product2/Pricebook2/PricebookEntry metadata for it to inspect |
| manual (GWT-checked) | manual | deferred | Both Then-clause facts hold in `deploy-order.md`; Given's premise ("two UNVERIFIED claims") is now stale — see Process Observations |

`check-outputs`: ok (nothing missing/empty/malformed). `check-outputs --hashes`: recorded above; the
validation-rule file and `deploy-order.md` hashes changed from the prior tested run's, `package.xml`
did not.

**Result: passed = true (4/4 runnable tests pass; 1 manual deferred to the M2 gate).**

Raw checker captures: `check_validation_rules.stdout.txt` / `.stderr.txt` / `.exit.txt`,
`check_products_and_pricebooks.stdout.txt` / `.stderr.txt` / `.exit.txt`, `xml_parse.stdout.txt`,
`check_outputs.stdout.txt` / `.json`, `check_outputs_hashes.stdout.txt` / `.json`.
