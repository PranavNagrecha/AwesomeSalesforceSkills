# M4-S03 test summary (run 2026-10-02T20-04-17Z)

| Test | Type | Result | Detail |
|---|---|---|---|
| xml | xml (always-on) | pass | ran with zero files: a docs step compiles .md/.yaml only, no XML under artefacts/M4-S03 |
| manifest | manifest (always-on) | skipped, not applicable | docs step with no package.xml; the build-level manifest is M4-S04's output |
| check_workbook.py | checker | pass (exit 0) | OK: workbook passes all checks; INFO rows on Automation only |
| check_rtm.py | checker | pass (exit 0) | 28 rows, 0 coverage gaps, 0 orphans, 0 errors, 42 warnings (id-shape WARNs) |
| check_uat_case.py | checker | pass (exit 0) | OK - 73 cases, 87 criterion ids cross-checked |
| check_ac_format.py | checker | pass (exit 0) | 1 document checked, 0 errors, 0 warnings |
| manual 1-2 | manual | deferred to M4 gate | G/W/T shaped, each names an observable outcome |
| check-outputs | precondition | pass | ok:true, 4 outputs present, fresh hashes recorded |

passed: true (failed[] empty). Raw captures: check_*.stdout/stderr/exit.txt.
