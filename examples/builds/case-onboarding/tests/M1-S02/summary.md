# M1-S02 — molecular test run

Run id `2026-09-06T04-45-00Z`, agent `step-tester`. Every command below was run
verbatim, from the build directory, after clearing the § 5 deny-list. Nothing was
rewritten: the declared checker takes `--manifest-dir`, which is the form the plan
declared and the form its own `argparse` defines. Raw captures are the sibling
`*.stdout` / `*.stderr` / `*.exit` files.

| Test | Type | Runner invoked | Exit | Result |
|---|---|---|---|---|
| `check_record_type_layouts.py` | checker | `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts/M1-S02` | 0 | pass — `Scanned 2 metadata file(s): 0 record type(s), 2 layout(s); 2 finding(s) detected.` Both findings are `INFO`; the plan's `expected` is `exit 0` and the checker exits non-zero on INFO only under `--strict`, which is not declared |
| `check-outputs` | precondition | `python3 scripts/build_plan.py check-outputs .sfskills/builds/case-onboarding/plan.json M1-S02` | 0 | ok — 3 declared outputs, 0 missing / empty / malformed |
| `xml` | always-on | ElementTree over `artefacts/M1-S02/**` | 0 | pass — 3 XML files scanned, 3 parsed, 0 failed |
| `manifest` | always-on | two-way derivation vs `artefacts/M1-S02/package.xml` | 0 | consistent — 2 members ↔ 2 metadata files, no wildcards, no orphans in either direction |
| manual (Q24 / A13) | manual | not runnable here | — | deferred to the M1 gate. Given/When/Then shape ok, observable outcome named. Disk evidence gathered (`manual-evidence.stdout`); read the two caveats below before ticking |

Tests run: 3 executable (1 checker + `xml` + `manifest`), plus the `check-outputs`
precondition the checker's pass condition rests on. Failed: 0. Manual deferred: 1.

## Why the 2 INFO findings are not failures

`check_record_type_layouts.py` check 4 reports one INFO per layout — "marks no
field behavior=Required". That is the intended design, not a defect: Q5 settles
that `Priority` and `Origin` are enforced at field / validation-rule level rather
than by layout, because Email-to-Case and Web-to-Case create through the API where
layout `Required` does not bind (`record-types-and-page-layouts/references/gotchas.md`
#11). `artefacts/M1-S02/deploy-order.md` anticipates both findings by name. The
checker's exit code is unaffected — `--strict` is what promotes INFO to exit 1, and
the plan does not declare it — and the plan's `expected` is `exit 0`. Pass.

## Manual-test evidence gathered from disk

Evidence only — this agent does not tick a manual test. The criterion has two
halves and they land differently.

**Half 1 — the assignment-rule checkbox.** Both layouts carry
`<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>`. Two
caveats the gate needs:

- *Element order is the reverse of the criterion's wording.* On both files the
  child order is `layoutSections, layoutSections, showEmailCheckbox,
  showRunAssignmentRulesCheckbox, showKnowledgeComponent` — the checkbox **follows**
  the layout sections, it does not precede them. The cited skill's canonical Layout
  example (`record-types-and-page-layouts/references/metadata-examples.md`, "Page
  layout with two sections and one required field") places all three `show*`
  elements after the final `</layoutSections>`, and the artefacts match that example
  exactly. A **presence** reading of the criterion passes; a literal **positional**
  reading fails, and it would fail against the only element ordering the cited skill
  documents. This run applied the presence reading and records the disagreement as a
  defect in the plan's test text, not in the artefacts.
- *"Default set on" is not proven, and is not provable from the cited skill.* The
  skill documents `showRunAssignmentRulesCheckbox` as controlling whether the
  checkbox is **shown** on Case, Lead and Account layouts — not whether it is
  pre-checked. No element that pre-checks it appears in the artefacts or in the
  skill's element inventory. `deploy-order.md` § "Elements this step could NOT
  ground" records exactly this and says the select-by-default half is not written.
  So even under the presence reading, the criterion's words "default set on" are
  satisfied only in the weaker sense of "the checkbox is surfaced". The gate should
  either accept that narrowing explicitly or route the remainder to a Setup step.

**Half 2 — A13's validation-rule fields.** Not file-checkable at M1-S02 time. No
`ValidationRule` metadata exists anywhere under `artefacts/`; A13's other step,
`M3-S01` (type `validation`), is still `pending`, so there is no `errorDisplayField`
to resolve against a layout. For the gate's later use, the fields on disk are:

- `Case-Case Support Layout`: CaseNumber, CreatedById, LastModifiedById, Origin,
  OwnerId, Priority, Severity__c, Status, Subject
- `Case-Case Billing Layout`: CaseNumber, CreatedById, LastModifiedById, Origin,
  OwnerId, Priority, Status, Subject

`Severity__c` is on the Support layout only. If a Case validation rule written in
M3-S01 attaches its error to `Severity__c`, A13 fails on the Billing layout — worth
carrying forward to M3-S01 rather than discovering at the M3 gate.

## Notes on the checkers themselves

- **The checker's declared `description` misreports its own output.** The plan says
  the checker prints `0 finding(s)`; it prints `2 finding(s)`. The exit code the
  test actually asserts is unaffected, and `deploy-order.md` gets it right, so this
  is a stale sentence in `plan.json`, not a broken test.
- **The scope claim holds.** The test declares `"scope": "step"` and the command
  carries `--manifest-dir artefacts/M1-S02`. Declared intent and executed path agree,
  so nothing had to be run against a wider tree or recorded as a disagreement.
- **The checker sees `0 record type(s)` here**, so its record-type-to-layout
  cross-reference is not exercised at this scope. The plan says M1's milestone test
  at `--manifest-dir artefacts` carries it — the reciprocal of M1-S01, where the same
  checker saw 2 record types and 0 layouts. Neither step scope has yet exercised the
  cross-reference; only the milestone test will.
- `artefacts/M1-S02/deploy-order.md` is written by `metadata-builder` but is not in
  the step's `outputs[]`. An undeclared extra file is not a failure: `check-outputs`
  confirms declared paths exist and says nothing about undeclared ones. Reported, not
  failed — same disposition as M1-S01's.
