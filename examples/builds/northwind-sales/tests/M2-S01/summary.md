# Test summary — M2-S01

Build: `northwind-sales` · Step: `M2-S01` (access) · Run by: `step-tester`

| Test | Type | Result | First line of output (if failure) |
|---|---|---|---|
| `xml` | always-on | PASS (3/3 files parse) | — |
| `manifest` | always-on | PASS (consistent, both directions) | — |
| `python3 skills/admin/custom-permissions/scripts/check_custom_permissions.py --manifest-dir artefacts` | checker | PASS (exit 0) | — |
| `python3 skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py --manifest-dir artefacts` | checker | PASS (exit 0) | — |
| `check-outputs` | precondition | PASS (`ok: true`, no missing/empty/malformed) | — |
| manual (Given/When/Then, one line) | manual | DEFERRED to M2 milestone gate | — |

**Overall: PASSED.** 4 runnable tests ran and passed, 1 manual test deferred (not counted toward pass/fail).

## Notes

- The custom-permissions checker's declared test description narrates a fixture that saw `1 info` and `Consumers 1`; this run saw `0 info` and `Consumers 0`. Both are consistent with the plan's own recorded facts (description trimmed under the 200-char INFO threshold; the consumer, M2-S03, isn't built yet) and do not change the declared `expected: exit 0`, which is met. Not treated as a failure — see `results.json.test_detail[2].divergence_from_plan_description` and metadata-builder's open item O-M2S01-02.
- Raw checker captures: `check_custom_permissions.std{out,err}.txt`, `check_permission_set_architecture.std{out,err}.txt`, `check_custom_permissions.exit.txt`, `check_permission_set_architecture.exit.txt`, `check_outputs.json`, `check_outputs_hashes.json` (all in this directory).
- Manual test text is carried verbatim into `results.json.skipped_manual[]` for `milestone-verifier`.
