# M1 — milestone acceptance test run

Run by `agents/milestone-verifier/AGENT.md` Step 6, from the build directory, at milestone scope.
`standards/build-orchestration.md` § 5: "At milestone level the scope is always `build`."

| # | type | command / runner | exit | result |
|---|---|---|---|---|
| 1 | `checker` | `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts` | 0 | pass vs declared `expected: exit 0`. `Scanned 7 metadata file(s): 2 record type(s), 2 layout(s); 2 finding(s)`, score 100, both findings `INFO`. |
| 2 | `manifest` | two-way member ↔ file check over the merged milestone manifest `reports/MILESTONE-M1-package.xml` | 0 | `verdict: consistent \| failures: 0`; 7 types, 12 members, no wildcards, no orphans in either direction. |
| 3 | `manual` | — | n/a | deferred to the human at G3; see `reports/MILESTONE-M1-REPORT.md` § 7. |

Files: `check_record_type_layouts.{stdout,stderr,exit}`, `manifest.{stdout,stderr,exit}`.

## The one number that differs from the plan's prediction

`milestones[M1].acceptance_tests[0].description` predicts
`'Scanned 7 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s)', exit 0`.
The file and component counts are exactly right. The finding count is **2, not 0** — both `INFO`,
both "marks no field behavior=Required", which is Q5's answer being honoured rather than a defect
(`decisions.md` O-M1S02-01 records the same stale prediction on the *step* test). The declared
`expected` still holds: `check_record_type_layouts.py` promotes `INFO` to a non-zero exit only under
`--strict`, which the plan does not declare.
