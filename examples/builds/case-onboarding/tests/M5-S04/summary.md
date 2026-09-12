# M5-S04 — test summary

Re-run against the artefacts produced by the 2026-09-12T13-15-00Z re-compile
(`envelopes/M5-S04/2026-09-12T13-15-00Z.json`), which closed
`reports/MILESTONE-M5-REPORT.md` § 8 findings F-52/53/54/56/57. The prior
`tests/M5-S04/results.json` (written 2026-09-12 07:51-07:52, before the
re-compile) is superseded by this run.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `xml` | always-on | ran, 0 files | Step type `docs`; no `*.xml`/`*-meta.xml` files under `artefacts/M5-S04/` — expected, all five outputs are `.md`/`.yaml`. |
| `manifest` | always-on | skipped — not applicable | Step type `docs` produces no `package.xml` (the build-level manifest is `M5-S05`, not a dependency of this step); no manifest exists in this step's own or `M5-S03`'s artefacts. |
| `check_workbook.py --workbook artefacts/M5-S04/configuration-workbook.md` | checker | **PASS** (exit 0) | `OK: workbook … passes all checks.` (8 INFO-level automation-citation notes, no ERROR/WARN) |
| `check_rtm.py --file artefacts/M5-S04/traceability.md --manifest-dir artefacts` (scope: build) | checker | **PASS** (exit 0) | `traceability.md: 58 row(s), build schema, 4 coverage gap(s), 0 orphan(s), 0 error(s), 4 warning(s)` |
| `check_uat_case.py --manifest-dir artefacts/M5-S04` | checker | **PASS** (exit 0) | `OK — 45 case(s), 0 run-sheet row(s), 118 criterion id(s) cross-checked.` |
| `check_ac_format.py --file artefacts/M5-S04/acceptance-criteria.md` | checker | **PASS** (exit 0) | `2 document(s) checked — 0 error(s), 111 warning(s).` |
| `check-outputs plan.json M5-S04` | precondition (bundled with each `checker`) | **PASS** | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |

All four declared checkers exited 0 **and** `check-outputs` reported `ok: true` — both required for a checker test to pass (`standards/build-orchestration.md` § 5, `agents/step-tester/AGENT.md` Step 4). `passed: true` in `results.json`.

## Manual tests (deferred to the milestone gate)

Both pass the Given/When/Then shape check (`skills/admin/acceptance-criteria-given-when-then` — each names an observable Then clause) and are carried into `skipped_manual[]` verbatim for `milestone-verifier`:

1. *Given 25 clarifications were deferred at G1 … all 25 appear as named rows with an owner …* — note for the human ticking this: the re-compile's own envelope (`2026-09-12T13-15-00Z.json`) states it rendered **28** assumptions (not only the 25 deferred), and that owner is a compile-time join (`assumptions[].because` -> `clarifications[].id` -> `owner_role`/`owner_hint`), not a `plan.json` `owner` field — 0 of 28 assumptions carry one natively. Read `configuration-workbook.md`'s new Assumptions Register section against that disclosure before ticking.
2. *Given two steps ship nothing in this phase … M3-S05 and M5-S02 each appear with their blocked reason verbatim … and the UAT pack carries no case that depends on either.* — note: `uat-test-cases.yaml` now marks `TC-M3-S05-2` and `TC-M5-S02-2` with `phase: 2` / `blocked_on: <step>` (F-53) rather than removing them; confirm that structural marker reads, to a human, as "does not depend on" in the sense the test asks for.

No checker asserts either of these two things structurally — see the re-compile envelope's own Concerning observation: all of F-52 through F-57 were shapes no declared checker catches.
