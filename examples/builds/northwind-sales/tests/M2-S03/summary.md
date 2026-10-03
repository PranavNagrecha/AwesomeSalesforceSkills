# Test summary — M2-S03

Build: `northwind-sales` · Step: `M2-S03` (validation) · Run by: `step-tester`

| Test | Type | Result | First line of output (if failure) |
|---|---|---|---|
| `xml` | always-on | PASS (2/2 files parse) | — |
| `manifest` | always-on | PASS (consistent, both directions) | — |
| `python3 skills/admin/validation-rules/scripts/check_validation_rules.py --manifest-dir artefacts` | checker (build scope) | PASS (exit 0) | — |
| `python3 skills/admin/opportunity-management/scripts/check_opportunity_management.py --manifest-dir artefacts/M2-S03` | checker (step scope) | PASS (exit 0, 1 INFO — not-in-scope, not a positive validation) | — |
| `check-outputs --hashes` | precondition | PASS (`ok: true`, no missing/empty/malformed) | — |
| manual × 2 (Given/When/Then) | manual | DEFERRED to M2 milestone gate | — |

**Overall: PASSED.** 4 runnable tests ran and passed, 2 manual tests deferred (not counted toward pass/fail).

## Notes

- `check_validation_rules.py` printed `Scanned 1 validation rule(s) across 1 file(s); 0 finding(s) detected.` at the plan's declared build scope (`--manifest-dir artefacts`), matching the plan's own fixture description verbatim — it actually resolved `Discount__c`, `Approval_Status__c`, `errorDisplayField` and the `$Permission` token against M1-S01's fields and M2-S01's custom permission.
- `check_opportunity_management.py` exited 0 with one INFO: `No Opportunity stage value set, business process, record type or pathAssistant found. Nothing in this tree is in scope for this checker.` The declared `expected: exit 0` is met and this counts as a pass, but it is recorded here honestly as a **not-in-scope** result, not as a positive validation of the rule's content — this step's only artefact is a `ValidationRule`, and there is nothing of the type this checker inspects (stage values, business process, record type definitions, path assistants) inside `artefacts/M2-S03/` for it to find. Do not read the green exit as evidence the validation rule's Opportunity-management correctness was checked.
- The two manual tests were both checked against the Given/When/Then shape before being deferred: both name a precondition (D8/A35, and Q15), one observable action, and checkable `Then` facts — both are usable at the gate. As a courtesy this run also read the shipped XML against both `Then` clauses without ticking them: the formula reads `Discount__c > 0.20` (not `> 20`), the bypass `NOT($Permission.Bypass_Opportunity_Sales_Validation)` is the first argument of the outer `AND`, and both `RecordType.DeveloperName` comparisons use `=` rather than `ISPICKVAL`; `errorMessage` is 132 characters (under the 255 limit, though the plan's own `inputs.note` says 129 — a minor discrepancy in the plan's prose, not in the shipped file) and `errorDisplayField` is `Discount__c`.
- Raw checker captures: `check_validation_rules.std{out,err}.txt`, `check_validation_rules.exit.txt`, `check_opportunity_management.std{out,err}.txt`, `check_opportunity_management.exit.txt`, `check_outputs.json`, `check_outputs_hashes.json` (all in this directory).
- Manual test text is carried verbatim into `results.json.skipped_manual[]` for `milestone-verifier`.
