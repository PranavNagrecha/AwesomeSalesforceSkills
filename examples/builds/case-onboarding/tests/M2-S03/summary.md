# M2-S03 test summary — re-run after Rebuild #2 (description-length fix, F-15)

Run: `step-tester`, 2026-09-12T01-23-34Z. Step status at start of this run: `built` (post Rebuild #2, run `2026-09-12T01-17-55Z`). The prior `results.json` in this directory (written 2026-09-12T01:00Z) predates Rebuild #2 and covered the pre-fix artefacts that mock-deploy #1 rejected (F-15) — it is superseded by this run.

| Test | Type | Result | First line of output |
|---|---|---|---|
| `xml` (always-on) | xml | PASS | 4/4 files parsed (`package.xml` + 3 `.profile-meta.xml`) |
| `manifest` (always-on) | manifest | PASS | Profile members `Acme Support Tier 1`, `Acme Support Tier 2`, `Acme Billing` — bare names derived from file stems — all present in `package.xml`; every named member has a file; no orphan file |
| `check_access_model.py --manifest-dir artefacts/M2-S03` | checker | PASS (exit 0) | `{"score": 100, "findings": [], "summary": "Scanned 3 access-model metadata file(s); 0 finding(s) detected."}` — PSVP-DESC-01/02 clean |
| `check_record_type_layouts.py --manifest-dir artefacts --strict` | checker | PASS (exit 0) | `{"score": 100, "findings": [], "summary": "Scanned 15 metadata file(s): 2 record type(s), 2 layout(s); 0 finding(s) detected."}` |
| `check-outputs plan.json M2-S03` | precondition | PASS | `{"ok": true, "missing": [], "empty": [], "malformed": []}` |

Raw stdout/stderr captures: `check_access_model.stdout.txt` / `.stderr.txt`, `check_record_type_layouts.stdout.txt` / `.stderr.txt`, `check_outputs.stdout.txt` / `.stderr.txt` (all in this directory).

## File-checkable facts verified directly (not just checker pass/fail)

Read all three `.profile-meta.xml` files and parsed with ElementTree / regex to confirm:

| Fact | Acme Support Tier 1 | Acme Support Tier 2 | Acme Billing |
|---|---|---|---|
| `objectPermissions` entries | 0 | 0 | 0 |
| `fieldPermissions` entries | 0 | 0 | 0 |
| `userPermissions` entries | 0 | 0 | 0 |
| `recordTypeVisibilities` with `<default>true</default>` | 1 (`Case.Support`) | 1 (`Case.Support`) | 1 (`Case.Billing`) |
| `layoutAssignments` count | 3 | 3 | 3 |
| `<description>` length (chars) | 152 | 152 | 147 |

All three descriptions are under both the PSVP-DESC-01 ERROR ceiling (255) and the PSVP-DESC-02 WARN threshold (200) — matches the lengths `artefacts/M2-S03/deploy-order.md` § Rebuild #2 records for the post-edit files.

No manual acceptance tests are declared on this step (`acceptance_tests[]` in `plan.json` lists two `checker` entries, `xml`, `manifest` only) — `skipped_manual` is empty, not because a manual test was skipped but because none exists.
