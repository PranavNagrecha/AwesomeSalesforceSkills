# M1-S02 — test summary (run 2026-09-09T19-50-27Z, after rebuild #2)

Step `M1-S02` — "Page layouts per Case record type", type `ui`, owner `metadata-builder`,
status on entry `built` (rebuild #2, `2026-09-09T19-38-37Z`).

Every command below was deny-list checked against `standards/build-orchestration.md` § 5
constraint 1 before it reached a shell, and each ran **verbatim as declared** from this build
directory (the `skills` symlink resolves `skills/…`, and `artefacts/M1-S02` resolves as written).

## Results

| Test | Type | Runner invoked | Exit | Result |
|---|---|---|---|---|
| `xml` | always-on (§ 5) | `ElementTree` parse of every `*.xml` / `*-meta.xml` under `artefacts/M1-S02/` | 0 | **pass** — 3 files scanned, 0 failed |
| `manifest` | always-on (§ 5) | two-way consistency, `artefacts/M1-S02/package.xml` vs files on disk | 0 | **pass** — consistent, 0 failures |
| `check_record_type_layouts.py` | `checker`, `scope: step` | `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts/M1-S02` | 0 | **pass** — `Scanned 2 metadata file(s): 0 record type(s), 2 layout(s); 0 finding(s) detected.` |
| `check-outputs` | § 5 precondition | `python3 scripts/build_plan.py check-outputs <plan> M1-S02` | 0 | **pass** — `{"ok": true, missing: [], empty: [], malformed: []}` |
| manual (Q24 / A13) | `manual` | not runnable here | — | **deferred** to the M1 milestone gate |

`passed: true` — `failed[]` is empty. The manual test is deferred, never counted as a failure.

## What changed against build #1's test run

Same four runnable tests, same commands, same exit codes — but the checker's output changed
because the checker itself changed. Build #1 scored `2 finding(s)`: two INFO lines saying each
layout "marks no field behavior=Required". Rebuild #2 scores `0 finding(s)`, because `Status` is
now `behavior=Required` on both layouts. The checker also gained rules **RL-REQ-01** (a `Case`
layout with no `layoutItems` entry for `ContactId` / `Description` / `SuppliedEmail`) and
**RL-REQ-02** (a `Case` layout whose `Status` item is missing or is not `behavior=Required`), both
ERROR, on 2026-09-09 — so this run's exit 0 asserts strictly more than build #1's exit 0 did.
Findings F-09 / F-10 in `reports/MOCK-DEPLOY-M1.md` are what those rules encode.

## Manifest detail

`package.xml` is unchanged from build #1 — two explicit `Layout` members, no wildcard. Both
directions clean:

- **file → manifest**: `Case-Case Billing Layout` and `Case-Case Support Layout` each covered by an
  explicit member.
- **manifest → file**: both explicit members resolve to a file.
- **excluded**: `package.xml` (the manifest itself) and `deploy-order.md` (not a source-format
  metadata file — no metadata-type folder + suffix pair, so it carries no manifest member). Neither
  exclusion is a `metadata-api-coverage-gaps` type carve-out; no coverage-gap exclusion was needed.

Raw captures: `xml.stdout`, `manifest.stdout`, `check_record_type_layouts.stdout` / `.stderr`,
`check-outputs.stdout`, and the per-test `.exit` files in this directory.

## Manual test — deferred, with the evidence the gate needs

Verbatim, for the milestone checklist:

> Given Q24, when each layout file is read, then `<layoutSections>` is preceded by the
> assignment-rule checkbox default set on, and every field a validation rule attaches an error to
> (assumption A13) is present on both layouts.

Read against Given/When/Then (`skills/admin/acceptance-criteria-given-when-then`) it has all three
clauses and names an observable, so it is tickable rather than unusable. Two carry-overs from
build #1's run stand unchanged after rebuild #2 — `manual-evidence.stdout` holds the readings:

1. **Half 1 is true on the presence reading and false on the positional one.** Both layouts carry
   `<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>`. In document order that
   element sits at index 3, *after* the last `layoutSections` at index 1 — so "preceded by" is
   false as written and true as meant. Separately, and more materially: no element in either file
   *pre-checks* the box. `showRunAssignmentRulesCheckbox` controls whether the checkbox is
   **shown**, not whether it is **defaulted on**, and `artefacts/M1-S02/deploy-order.md`
   ("Elements this step could NOT ground") records that the select-by-default half of Q24 is not
   written and is not inventable from the cited skill. The ticker is being asked to confirm
   something the artefact deliberately does not implement.
2. **Half 2 is not file-checkable at M1-S02 time.** No `ValidationRule` metadata exists anywhere
   under `artefacts/`; A13's referenced validation step `M3-S01` is still `pending`, so there is no
   `errorDisplayField` to resolve a field list against.

Field lists on each layout, for the gate:

- `Case-Case Billing Layout`: CaseNumber, ContactId, CreatedById, Description, LastModifiedById,
  Origin, OwnerId, Priority, Status, Subject, SuppliedEmail
- `Case-Case Support Layout`: the same plus `Severity__c`

The three new fields (`ContactId`, `Description`, `SuppliedEmail`) are on both layouts because the
platform requires them there, not because the requirement asked for them.
