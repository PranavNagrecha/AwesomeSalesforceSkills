# Test summary — M4-S05

Re-run after F-59–F-62 (the prior `results.json` at this path was stale against
the repaired tree — F-62 was the first repair to touch shipped code,
`CaseMilestoneService`). This run reads the tree as it stands after F-62.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py --manifest-dir artefacts/M4-S05` | checker | PASS (exit 0) | `scanned 5 Apex file(s) under artefacts/M4-S05: 0 ERROR, 0 WARN` |
| `check-outputs` (precondition for the checker test) | checker precondition | PASS | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| `xml` (always-on) | xml | PASS — 5/5 parsed | ElementTree parse, all files |
| `manifest` (always-on) | manifest | SKIPPED — not applicable | Apex exception (`standards/build-orchestration.md` § 5): this `automation` step is owned by `apex-builder`, which declares no `package.xml`; the build-level manifest step **M5-S05** aggregates this step's `ApexClass`/`ApexTrigger` members. Matches the step's own `acceptance_tests[2]`. |
| Given/When/Then manual test (identifier provenance + `CompletionDate` non-null assertion) | manual | DEFERRED to milestone gate | Checked against Given/When/Then shape first: has one Given, one When, one Then naming two observable outcomes (quoted-identifier provenance, and the test's non-null assertion) — usable, not flagged unusable. Never ticked by this agent. |

Raw captures: `checker.stdout.txt`, `checker.stderr.txt`, `checker.exit.txt`, `check-outputs.json`.

## Undeclared extra (not a plan-declared acceptance test — informational only, does not affect `passed`)

`python3 skills/apex/test-class-standards/scripts/check_test_class_standards.py --manifest-dir artefacts/M4-S05/classes`
— exit 0. `Scanned 4 Apex class file(s); audited 3 @IsTest artifact(s); 0 finding(s). ERROR=0 WARN=0` (score 100).
Raw captures: `undeclared-check_test_class_standards.stdout.txt`, `.stderr.txt`, `.exit.txt`.

This checker is not in `plan.json` `steps[M4-S05].acceptance_tests[]`, so it is not counted in
`ran[]`/`failed[]` above. It was run at the caller's request as an informational cross-check only.
Note in passing: `classes/TestUserFactory.cls` (added in F-59) is on disk but not in this step's
declared `outputs[]`, and is not yet a member of the build-level `package.xml` that M5-S05 owns —
that is M5-S05's obligation to pick up when it aggregates this step's Apex members, not a defect
of this step or a failure of this test run.

## Verdict

`passed: true` — every runnable declared test passed (checker + both always-on checks), the one
manual test is correctly deferred, not counted as a failure.
