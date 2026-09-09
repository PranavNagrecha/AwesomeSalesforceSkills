# Mock deploy — milestone M1 (validation only, nothing deployed)

**Date:** 2026-09-05 · **Operator:** dry-run operator (Fable) on the owner's instruction
**Target:** `sfskills-dev` (developer org named for this repo; no client org was touched)
**Command:** `sf project deploy start --source-dir force-app --dry-run --target-org sfskills-dev`
(`--dry-run` = `checkOnly: true`; the org was validated against, not changed)
**Source tree:** the M1-S01 and M1-S02 artefacts copied verbatim into `force-app/main/default/` (12 files, `sourceApiVersion` 62.0)

## Run 1 — artefacts exactly as built

| Component | Result |
|---|---|
| `CustomField` Account.Region__c, Account.Support_Tier__c, Case.Severity__c | ok |
| `StandardValueSet` CaseOrigin | ok |
| `CustomObject` Case (Private OWD, compact layout assignment) | ok |
| `BusinessProcess` Case.Support Process, Case.Billing Process | ok |
| `RecordType` Case.Support, Case.Billing | ok |
| `CompactLayout` Case.Case_Intake | ok |
| `Layout` Case-Case Support Layout | **FAIL** — `Layout must contain an item for required layout field: ContactId` |
| `Layout` Case-Case Billing Layout | **FAIL** — same |

10 of 12 components validate. Both failures are the same platform rule.

## Runs 2–7 — scratch copy, one platform rule fixed per run (artefacts NOT edited)

| Run | Change applied to the scratch layouts / files | Result |
|---|---|---|
| 2 | `ContactId` added to both layouts | Failed — `required layout field: Description` |
| 3 | `Description` added | Failed — `required layout field: SuppliedEmail` |
| 4 | `SuppliedEmail` added | Failed — `Field:Status must be Required` |
| 5 | `Status` behavior set to `Required` | Failed — layouts pass; `BusinessProcess Case.Billing_Process / Case.Support_Process named in package.xml but not found` |
| 6–7 | business-process `<fullName>` aligned to the file stems (`Support_Process`, `Billing_Process`) and the record types' `<businessProcess>` references updated | **Succeeded — 12/12 components validate, `checkOnly: true`, 0 errors** |

Evidence: `reports/mock-deploy-fixes/` holds the scratch copies that validated (for the re-build of M1-S02 and M1-S01
to consult; they are not the build's artefacts).

## Findings

**F-09 (HIGH, new).** Case page layouts must carry the standard `ContactId` field or the deploy fails.
- M1-S02's builder omitted `AccountId`/`ContactId` deliberately because no cited skill named them
  (`artefacts/M1-S02/deploy-order.md` § "Elements this step could NOT ground").
- No declared checker knows the platform's required-layout-field rule; the step and milestone tests were all green.
- **Skill signal (contract § 8):** `admin/record-types-and-page-layouts/references/metadata-examples.md` should carry
  the required standard fields for Case layouts and its checker should flag a Case layout without `ContactId`.
- **Plan signal:** M1-S02 needs a re-build after the skill fix (or a v6 note grounding the required field), then
  re-test → re-document → M1 re-verify. Artefacts were NOT edited in place — the contract forbids it.

**F-10 (HIGH, new).** Case page layouts must also carry `Description` and `SuppliedEmail`, and `Status` must be
`behavior=Required` on the layout — three more platform rules no checker encoded. Q5's answer ("enforce Priority/Origin
at field/validation level, not layout Required") stands for those two fields; `Status` is the platform's own rule.

**F-11 (HIGH, new).** A `BusinessProcess` file's stem must equal its `<fullName>`: the CLI names the package member
from the stem (`Support_Process`) while the file said `Support Process`, so the member was "not found in zipped
directory". The M1-S01 runner recorded exactly this divergence as an ambiguity; the plan declared the stem form and
the step inputs the spaced form — the planner must pick one at v6 (stem form, since it deploys).

**F-02 (from the M1 report) did not fire:** both business processes validated, so the target org's `CaseStatus`
value set already carries New / Escalated / Closed. Reconcile again against any other target.

## What this proves

The orchestration loop's own tests are necessary but not sufficient: a platform rule the skills did not encode
passed every gate and was caught only by validating against a real org. The remedy is in the library (checker +
example), which is exactly where the loop puts it.

## Mock deploy #2 — 2026-09-09, rebuilt artefacts, unmodified

After the two skill fixes (`admin/record-types-and-page-layouts` v1.2.0 rules RL-REQ-01/02; `admin/case-management-setup`
v1.2.0 rules CMS-STEM-01/02) and rebuild #2 of M1-S02 and M1-S01 through the ordinary runner path
(`documented → running → built`), the artefacts under `artefacts/M1-S01` and `artefacts/M1-S02` were copied
**without any edits** into a source tree and validated again:

`sf project deploy start --source-dir force-app --dry-run --target-org sfskills-dev`

**Succeeded — 12/12 components validate, `checkOnly: true`, 0 errors.** CustomField ×3, StandardValueSet CaseOrigin,
CustomObject Case, BusinessProcess Case.Support_Process / Case.Billing_Process, RecordType Case.Support / Case.Billing,
CompactLayout Case.Case_Intake, Layout Case-Case Support Layout / Case-Case Billing Layout.

F-09, F-10 and F-11 are closed at the source: the checkers that were silent on run 1 now fail the run-1 artefacts
(RL-REQ-01/02 ×2 each; CMS-STEM-01/02 ×2 each) and pass these. Remaining for v6: the plan's step inputs still spell
`Support Process` with a space (F-11's planner half), and the M1 acceptance report / gate notes predate the rebuild.

## Mock deploy #3 — 2026-09-09, manifest-driven (F-13)

`sf project deploy start --manifest reports/MILESTONE-M1-package.xml --dry-run --target-org sfskills-dev` over the same
rebuilt source tree. **Failed, 1 of 13:** `An object 'Case_Intake' of type CompactLayout was named in package.xml, but
was not found in zipped directory`. The merged manifest carries the bare member `Case_Intake` (the form
`admin/list-views-and-compact-layouts` prescribes); the CLI resolves compact layouts as object-qualified
`Case.Case_Intake` — exactly what mock deploy #2's `--source-dir` run derived. **F-13 is confirmed, not theoretical.**
Fix belongs in `admin/list-views-and-compact-layouts` (member form + a checker rule), then M1-S01's `package.xml` at v6.
The 12 other components validated.
