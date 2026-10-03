# Test summary - M3-S03 (re-run after the N3-F-08 repair)

Step: `Apex service, @AuraEnabled controller and @InvocableMethod action that submit one Opportunity into Discount_Approval, plus the test class`
Run from: `.sfskills/builds/northwind-sales/` (build directory, via the `skills` symlink). Supersedes the 2026-09-19T17-22-41Z results: only `OpportunityApprovalServiceTest.cls` changed, so only its artefact hash differs.

| Test | Type | Result | First line of output |
|---|---|---|---|
| xml | always-on | pass | 5 of 5 `*-meta.xml` files parsed |
| manifest | always-on | skipped-not-applicable | Apex exception (build-orchestration.md Section 5): members land in the build-level manifest at M4-S04 |
| `check_approval_process_apex_patterns.py --manifest-dir artefacts artefacts` | checker (scope: build) | pass (exit 0) | `Scanned 1 approval-process file(s) and 5 Apex file(s); 0 finding(s) detected.` |
| `check_invocable_methods.py --manifest-dir artefacts/M3-S03` | checker (scope: step) | pass (exit 0) | `Scanned 5 Apex class file(s) under artefacts/M3-S03; 0 invocable-contract finding(s) in 0 file(s).` |
| `check_test_class_standards.py --manifest-dir artefacts/M3-S03` | checker (scope: step) | pass (exit 0) | `Scanned 5 Apex class file(s); audited 2 @IsTest artifact(s); 0 finding(s).` |
| `check-outputs M3-S03 --hashes` | precondition | ok | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |

Manual (deferred to the M3 milestone gate, never ticked here): 2 lines, both Given/When/Then-shaped with an observable outcome; see `results.json.skipped_manual[]`.

Not run: `check_apex_security_patterns.py` (cited, undeclared by decision). `evidence_apex_security_patterns.txt` is from the earlier run and is stale.

These checkers are static: none of them executes the repaired test. Whether the six test methods now pass is for the org dry run (reports/mock-deploy/), not this tester.

**passed: true**

Raw captures: `checker1_approval_process.txt`, `checker2_invocable.txt`, `checker3_test_class_standards.txt`, `xml_check.txt`, `check_outputs.txt`, `check_outputs_hashes.json`.
