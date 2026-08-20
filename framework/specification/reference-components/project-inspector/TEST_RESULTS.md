# Test results

Test date: 2026-08-19

## Standalone add-on tests

```text
Command: ./run_standalone_tests.sh
Result: PASS
Tests: 19
Failures: 0
Errors: 0
```

The script also executed the CLI in standalone mode and received a valid JSON result with exit code 0.

## Integration against uploaded SfSkills repository snapshot

The supplied repository-relative files were copied into a temporary copy of the uploaded `AwesomeSalesforceSkills-main` snapshot.

```text
Command: python3 -m unittest discover -s tests -p 'test_*.py' -v
Result: PASS
Tests: 291
Failures: 0
Errors: 0
```

The original snapshot contained 272 tests; this add-on contributes 19 tests.

## Python compilation

```text
Command: python3 -m compileall -q repo-files/pipelines/product repo-files/scripts/sf_project_inspector.py repo-files/tests/product
Result: PASS
```

## Not tested here

- Cursor IDE discovery of the subagent.
- Integration with the current V2 plugin builder branch.
- A live deployment-triage run.

The Cursor prompt requires those checks after integration because this package does not contain the current local V2 branch.
