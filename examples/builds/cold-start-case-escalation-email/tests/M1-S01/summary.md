# Test summary — M1-S01

| Test | Type | Result | First line of output |
| --- | --- | --- | --- |
| xml (2 files) | xml | pass | both `flows/Case_Escalation_Notify_Account_Owner.flow-meta.xml` and `package.xml` parse |
| manifest | manifest | pass | `Flow: Case_Escalation_Notify_Account_Owner` present in package.xml, file found on disk, direction confirmed both ways |
| `skills/flow/record-triggered-flow-patterns/scripts/check_record_triggered_flow_patterns.py --manifest-dir artefacts/M1-S01` | checker | pass (exit 0) | `No issues found.` |
| `check-outputs` | (always-on, paired with the checker test) | pass | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |

No manual tests are declared on this step (the one manual acceptance test in this build belongs to milestone M1, not to M1-S01, and is out of scope for step-level testing -- milestone-verifier collects it).

Result: passed. 3 tests ran, 0 failed, 0 skipped-manual at step level.
