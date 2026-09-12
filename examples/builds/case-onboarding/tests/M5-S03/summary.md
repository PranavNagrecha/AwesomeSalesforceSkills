# step-tester — M5-S03 — test summary

Step: `M5-S03` — INVEST story backlog with per-story acceptance criteria for the three intake channels (type `docs`, agent `story-drafter`).

| Test | Type | Result | First line of failure output |
|---|---|---|---|
| `xml` | always-on | ran, 0 files | — (no `*.xml`/`*-meta.xml` under `artefacts/M5-S03/`; expected for a docs-only step) |
| `manifest` | always-on | skipped-not-applicable | Step type `docs`, no `package.xml` declared in `outputs[]`; story-drafter's Output Contract produces one markdown document and no metadata |
| `skills/admin/user-story-writing-for-salesforce/scripts/check_invest.py` | checker | **pass** (exit 0) | `Summary: 11/11 stories passed (0 ERROR, 10 WARN).` |
| `check-outputs` | precondition | ok | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |
| manual (Q77/Q84/Q80 channel-and-persona check) | manual | deferred to milestone gate | shape checked — usable (names 3 observable outcomes) |

**Overall: `passed: true`** — 0 failing runnable tests, 1 manual test deferred (never counted as a failure).

Raw checker output: `tests/M5-S03/check_invest.stdout.txt`, `tests/M5-S03/check_invest.stderr.txt`. `check-outputs` output: `tests/M5-S03/check-outputs.json`. Machine record: `tests/M5-S03/results.json`.
