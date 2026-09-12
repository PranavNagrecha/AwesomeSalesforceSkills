# Test results — M4-S04 (Case escalation rules)

Run by `agents/step-tester`, post-F-36 rebuild (`admin/escalation-rules` v1.1.2, commit `9ae71856d`,
rule E10). Supersedes the pre-rebuild `2026-09-12T07-35-25Z` step-tester run.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `check_escalation_rules.py --manifest-dir artefacts` (scope: build) | checker | **PASS** (exit 0) | `WARN  W1  [Case.escalationRules-meta.xml] no rule in this file is active. Nothing escalates until one is.` |
| `check-outputs` | precondition | **ok** | `{"ok": true, "step": "M4-S04", "missing": [], "empty": [], "malformed": []}` |
| `xml` | always-on | **PASS** (2/2 files parse) | — |
| `manifest` | always-on | **PASS** (consistent) | — |
| manual: activation at sandbox sign-off | manual | deferred to milestone gate | Given/When/Then, names an observable outcome (escalation count recorded) — usable |
| manual: 480-minute / clock / queue assertion | manual | deferred to milestone gate | Given/When/Then, names four observable field values — usable |

`passed: true` — `failed` is empty. Full checker stdout/stderr in `checker_stdout.txt` /
`checker_stderr.txt`; xml and manifest detail in `xml_results.json` / `manifest_results.json`.

## Notes

- W1 (no rule active) is the intended state under Q47, not a defect — the plan's own test
  description says so and the checker's exit code (0) already reflects it (`main()` returns 1 on
  ERROR only).
- The two `I3` notes (480 minutes = 8h, one per entry) are informational and non-failing; the
  480-vs-8 assertion itself is carried by the second manual test, not by this checker's exit code.
- Checker command ran exactly as declared (`--manifest-dir artefacts`, build scope) from the build
  directory, per the plan's stated reason: E7 (assignedTo-vs-queue-developer-name) only fires where
  `M2-S04`'s queue file is visible, i.e. at build scope. No flag was added, removed or reordered.
- Both manual tests carry a Given/When/Then shape and name an observable outcome, so both are
  reported as usable rather than unusable.
