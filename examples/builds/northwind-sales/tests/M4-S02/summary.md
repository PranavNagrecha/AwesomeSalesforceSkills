# M4-S02 test summary (run 2026-10-02T18-05-36Z, after repair 2)

| Test | Type | Result | Detail |
|---|---|---|---|
| xml | xml (always-on) | pass | 7 files parsed, 0 failures |
| manifest | manifest (always-on) | pass | Group, ReportType, Report (folder + report), Dashboard (folder + dashboard): 6 members, 6 files, no gaps either direction |
| check_report_inventory.py | checker | pass (exit 0) | 6 findings: 5 RPT-COL-01 INFO + 1 MEDIUM SpecifiedUser with no runningUser (A29); stderr WARN is the lenient-exit notice |
| manual 1-3 | manual | deferred to M4 gate | G/W/T shaped |
| check-outputs | precondition | pass | ok:true, fresh hashes recorded |

Prose drift (not a failure): the test description predicts 7 findings / six RPT-COL-01; live run gives 6 / five.
passed: true (failed[] empty).
