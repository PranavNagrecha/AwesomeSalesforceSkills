# Test summary — M2-S02

Build: `northwind-sales` · Step: `M2-S02` (access) · Built by `metadata-builder` (repair pass, 2026-09-19T15-22-09Z) · Tested by `step-tester`

This run supersedes the stale `2026-09-19T14-39-24Z` step-tester run: the repair dropped both
`recordTypeVisibilities` blocks from the `Sales User` profile overlay (org refused it on mock-deploy
dry run 1, N3-F-05) and added two `fieldPermissions` blocks to `Enterprise_Sales_Record_Types`
(closing HIGH open item O-M2S02-01). Artefact hashes changed for both metadata files; `package.xml`
is unchanged.

| Test | Type | Result | First line of output |
|---|---|---|---|
| xml | always-on | pass | all 3 files parse |
| manifest | always-on | pass | PermissionSet + Profile consistent both directions, no exclusion |
| `check_permission_set_architecture.py --manifest-dir artefacts` (scope: build) | checker | pass (exit 0) | `No issues found.` |
| `check_record_type_layouts.py --manifest-dir artefacts` (scope: build) | checker | pass (exit 0) | `Scanned 9 metadata file(s): 2 record type(s), 2 layout(s); 1 finding(s) detected.` (REVIEW RTL-MERGE-01, pre-adjudicated O-M1S02-03) |
| `check_access_model.py --manifest-dir artefacts/M2-S02` (scope: step) | checker | pass (exit 0) | `Scanned 2 access-model metadata file(s); 1 finding(s) detected.` (WARN PSVP-FLS-02, accepted by design O-M2S02-02) |
| manual 1/2 (Q4/Q9, profile file shape) | manual | deferred — **STALE as worded** | asserts "two `recordTypeVisibilities` blocks" the profile no longer carries |
| manual 2/2 (Q19, persona access source) | manual | deferred | unaffected by the repair; Given/When/Then still usable |

**Result: `passed: true`** — 5/5 runnable tests pass, 2 manual tests deferred to the M2 milestone gate
(never counted as failures). `check-outputs` ok (no missing/empty/malformed).
`check-outputs --hashes` recorded in `results.json.artefact_hashes`.

## Notes

- **Manual test 1 is stale against the repaired artefact.** Its `Then` clause asserts the profile
  "contains exactly two `layoutAssignments` blocks and two `recordTypeVisibilities` blocks, every
  `recordTypeVisibilities` carries `<default>false</default>`". The `layoutAssignments` half is still
  true; the `recordTypeVisibilities` half is now false — both blocks were removed in the repair
  (`artefacts/M2-S02/deploy-order.md` § 6.1), and visibility for both record types is now carried
  solely by the permission set. The rest of the `Then` (no `userPermissions` /
  `objectPermissions` / `fieldPermissions` / `applicationVisibilities` / `classAccesses` in the
  profile) is still true. Not ticked, not failed — carried into `skipped_manual[]` verbatim per this
  agent's no-rewrite rule, flagged here for the M2 gate reviewer and for whoever next amends the
  step's acceptance-test text.
- Manual test 2 was re-checked against the repaired files and is unaffected: it never asserted the
  permission set carries no field permissions, so the new `fieldPermissions` blocks do not
  contradict it.
- Two checkers (`check_permission_set_architecture.py`, `check_record_type_layouts.py`) run at
  `scope: build` per `standards/build-orchestration.md` § 5's cross-referential-checker list, reading
  the whole `artefacts/` tree as the literal `--manifest-dir artefacts` command directs. The third
  (`check_access_model.py`) runs at `scope: step`.
- `PSVP-FLS-01` (permission-sets-vs-profiles) stays silent as expected: `Enterprise_Sales_Record_Types`
  still declares no `objectPermissions` element after the repair, so the object-CRUD-with-zero-FLS
  shape that rule fires on is still absent — adding `fieldPermissions` alone does not create it.
- Raw checker stdout/stderr captures: `tests/M2-S02/check_permission_set_architecture.{stdout,stderr}.txt`,
  `tests/M2-S02/check_record_type_layouts.{stdout,stderr}.txt`,
  `tests/M2-S02/check_access_model.{stdout,stderr}.txt`.
- Full detail: `tests/M2-S02/results.json`.
