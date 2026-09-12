# Test summary — M4-S01

Step type `sla`, status precondition `built` confirmed before this run. Run from the build directory
so `skills/` (symlink) and `artefacts/M4-S01` resolve exactly as `plan.json` declares them.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `xml` (always-on) | xml | PASS | 2 files parsed OK (`artefacts/M4-S01/package.xml`, `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml`) |
| `manifest` (always-on) | manifest | PASS | `Settings:BusinessHours` derived from `settings/BusinessHours.settings-meta.xml` matches the sole `<members>BusinessHours</members>` under `<name>Settings</name>` in `package.xml` — no member without a file, no file without a member |
| `check_business_hours_and_holidays.py --manifest-dir artefacts/M4-S01` | checker | PASS | `INFO: … always-open calendar 'Severity 1 24x7': SLA clocks on it never pause — intended for 24/7 severity tiers; confirm it is not attached to entitlements that expect business-hour pauses.` — exit 0 |
| `check-outputs` | precondition (bundled with `checker`) | PASS | `{"ok": true, "step": "M4-S01", "missing": [], "empty": [], "malformed": []}` |
| Manual GWT (three named calendars) | manual | DEFERRED to milestone gate | Given/When/Then all present; Then names an observable outcome (three named calendars with specific hours) — usable, not rejected |

**Verdict: passed = true. 0 failed. 1 manual test deferred to the milestone gate.**

Raw captures: `tests/M4-S01/checker-business-hours-and-holidays.stdout.txt`,
`tests/M4-S01/check-outputs.json`.

## Notes on the checker-policy history

This step was previously blocked (`checker-policy`, run `2026-09-12T06:31:35Z`) because
`check_business_hours_and_holidays.py` rejected the `Severity 1 24x7` calendar's midnight-to-midnight
shape as the shipped-24/7 default pattern. Commit `5b206697a` (`admin/business-hours-and-holidays`
v1.0.1) scoped that rule to fire as an ERROR only on the org default calendar or one literally named
`Default`; a deliberately named non-default always-open calendar now produces the INFO line above and
exits 0. The artefact under test is byte-for-byte unchanged from the blocked run — the checker's rule
changed, not the metadata. This run re-executed the declared command verbatim (no rewriting, no flag
substitution) and observed exit 0 independently of the builder's own re-run at `2026-09-12T06:52:00Z`.
