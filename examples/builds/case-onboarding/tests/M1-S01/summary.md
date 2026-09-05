# M1-S01 — molecular test run

Run id `2026-09-05T20-00-00Z`, agent `step-tester`. Every command below was run
verbatim, from the build directory, after clearing the § 5 deny-list. Raw
captures are the sibling `*.stdout` / `*.stderr` / `*.exit` files.

| Test | Type | Runner invoked | Exit | Result |
|---|---|---|---|---|
| `check_record_type_layouts.py` | checker | `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts/M1-S01` | 0 | pass — `2 record type(s), 0 layout(s); 0 finding(s) detected.` |
| `check_list_views_and_compact_layouts.py` | checker | `python3 skills/admin/list-views-and-compact-layouts/scripts/check_list_views_and_compact_layouts.py --manifest-dir artefacts/M1-S01` | 0 | pass — `No issues found.` |
| `check_object_creation_and_design.py` | checker | `python3 skills/admin/object-creation-and-design/scripts/check_object_creation_and_design.py --manifest-dir artefacts/M1-S01` | 0 | pass — `No issues found across 1 object file(s).` |
| `check_record_type_id_management.py` | checker | `python3 skills/admin/record-type-id-management/scripts/check_record_type_id_management.py --manifest-dir artefacts/M1-S01` | 0 | pass — `No record-type ID anti-patterns detected.` |
| `check-outputs` | precondition | `python3 scripts/build_plan.py check-outputs .sfskills/builds/case-onboarding/plan.json M1-S01` | 0 | ok — 12 declared outputs, 0 missing / empty / malformed |
| `xml` | always-on | ElementTree over `artefacts/M1-S01/**` | 0 | pass — 11 XML files scanned, 11 parsed, 0 failed |
| `manifest` | always-on | two-way derivation vs `artefacts/M1-S01/package.xml` | 0 | consistent — 10 members ↔ 10 metadata files, no wildcards, no orphans in either direction |
| manual (B01 business processes) | manual | not runnable here | — | deferred to the M1 gate; Given/When/Then shape ok, observable outcome named |
| manual (B01 Case OWD) | manual | not runnable here | — | deferred to the M1 gate; Given/When/Then shape ok. Disk evidence gathered (`manual-evidence.stdout`) supports a tick |

Tests run: 7 executable (4 checkers + `check-outputs` + `xml` + `manifest`).
Failed: 0. Manual deferred: 2.

## Manual-test evidence gathered from disk

Evidence only — this agent does not tick a manual test.

- `objects/Case/Case.object-meta.xml` direct children of `<CustomObject>` are
  `compactLayoutAssignment=Case_Intake`, `externalSharingModel=Private`,
  `sharingModel=Private`. Both OWD elements present with value `Private`.
- No `*.settings-meta.xml` exists anywhere under `artefacts/`, so nothing else
  in the build claims to carry the Case OWD. The two other files mentioning
  `sharingModel` (`record-type-decision.md`, `deploy-order.md`) are prose notes
  describing this decision, not metadata asserting it.
- Two `businessProcess-meta.xml` files sit beside two `recordType-meta.xml`
  files. `Support.recordType` carries `<businessProcess>Support Process</businessProcess>`
  and `Billing.recordType` carries `<businessProcess>Billing Process</businessProcess>`
  — both bare, no `Case.` prefix. `package.xml` lists BusinessProcess as
  `Case.Support Process` / `Case.Billing Process` — object-qualified.

## Notes on the checkers themselves

- `check_object_creation_and_design.py` and `check_record_type_id_management.py`
  both exit 0 over an empty directory (W09, recorded in the plan's own test
  descriptions). Their exit codes here are load-bearing only because the
  always-on `manifest` and `xml` checks independently confirm the files exist.
- `check_record_type_layouts.py` reports `0 layout(s)` — the record-type-to-layout
  cross-reference is not exercised at this scope. The plan says M1's milestone
  test at `--manifest-dir artefacts` carries it.
- `artefacts/M1-S01/deploy-order.md` is written by `metadata-builder` but is not
  in the step's `outputs[]`. It is an undeclared extra file, not a failure: the
  contract fails a *declared* output that is absent, and says nothing about an
  undeclared file that is present. Reported, not failed.
