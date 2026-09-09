# M1-S01 — deploy order

Written by `agents/metadata-builder` Step 7. Sourced from
`skills/admin/change-management-and-deployment` (admin-release manifest shape) and from the deploy
order table in `skills/admin/case-management-setup/references/metadata-examples.md` § 5.

This step is the first in the build and depends on nothing (`depends_on: []`).

## Rebuild history

**Rebuild #2 — 2026-09-09, `documented → running → built`.** Cause: finding **F-11** in
`reports/MOCK-DEPLOY-M1.md` (HIGH). `sf project deploy start --dry-run` rejected this step's
business processes in source format because each `*.businessProcess-meta.xml` carried a spaced
`<fullName>` (`Support Process`) while the CLI names the package member from the **file stem**
(`Support_Process`) — so the member resolved to nothing and the deploy failed with "An object
'Case.Support_Process' of type BusinessProcess was named in package.xml, but was not found in
zipped directory".

The rule is now in the library rather than only in a report: `admin/case-management-setup` v1.2.0
states it in `references/metadata-examples.md` § 2.1 ("Every `<fullName>` below is written in stem
form … each decomposed file's stem has to be its own `fullName`"), and its checker enforces it as
**CMS-STEM-01** (stem must equal `<fullName>`, no spaces) and **CMS-STEM-02** (a record type's
`<businessProcess>` must name an existing process file stem). Against this step's artefacts before
the rebuild that checker printed 4 `ERROR:` lines and exited 1.

Rebuilt in this pass, and nothing else:

| File | Change |
|---|---|
| `objects/Case/businessProcesses/Support_Process.businessProcess-meta.xml` | `<fullName>` `Support Process` → `Support_Process` |
| `objects/Case/businessProcesses/Billing_Process.businessProcess-meta.xml` | `<fullName>` `Billing Process` → `Billing_Process` |
| `objects/Case/recordTypes/Support.recordType-meta.xml` | `<businessProcess>` → `Support_Process` (bare stem, never object-qualified) |
| `objects/Case/recordTypes/Billing.recordType-meta.xml` | `<businessProcess>` → `Billing_Process` |
| `package.xml` | `BusinessProcess` members → `Case.Support_Process`, `Case.Billing_Process` |
| `deploy-order.md` | the two member-name cells above, plus this section |

`Case.object-meta.xml` (the Private OWD), `standardValueSets/CaseOrigin.standardValueSet-meta.xml`,
`compactLayouts/Case_Intake.compactLayout-meta.xml`, the three `CustomField` files and
`record-type-decision.md` are byte-identical to rebuild #1. The readable wording survives in each
process's `<description>` and in `record-type-decision.md`, which is where § 2.1 says to put it.

**Open item for the planner, not for this step.** `plan.json.steps[M1-S01].inputs.business_processes`
still reads `["Support Process", "Billing Process"]` — the spaced form. The plan's `outputs[]` always
declared the stem-form *file* paths, so the divergence is between the step's inputs and its outputs,
and it is what F-11 calls out: "the plan declared the stem form and the step inputs the spaced form —
the planner must pick one at v6 (stem form, since it deploys)." `build-step-runner` does not edit
`plan.json` beyond the status transitions it owns, so this note is the whole of the action available
here. The artefacts on disk are the stem form regardless; the input string is now documentation of an
earlier intent rather than a value anything reads.

## Order inside this step

| # | Component | Because |
|---|---|---|
| 1 | `CustomField` — `Case.Severity__c`, `Account.Region__c`, `Account.Support_Tier__c` | § 5 row 1: "a `picklistValues` block or a rule criterion on a field that does not exist fails the deploy". `Severity__c` is also named by the compact layout in step 4. |
| 2 | `StandardValueSet:CaseOrigin` | § 5 row 2: the record types' `picklistValues` blocks and, later, `CaseSettings.webToCase.caseOrigin` both reference values that must already exist. A `picklistValues` block exposes values; it does not create them. |
| 3 | `BusinessProcess` — `Case.Support_Process`, `Case.Billing_Process` | § 5 row 3: a Case record type is rejected without its support process. |
| 4 | `CompactLayout:Case_Intake` | The `compactLayoutAssignment` elements in step 5 resolve by name at deploy time; `skills/admin/object-creation-and-design/references/metadata-examples.md` states the referenced `CompactLayout` "must be in the same deployment". |
| 5 | `CustomObject:Case` + `RecordType` — `Case.Support`, `Case.Billing` | The object file carries the object-level `compactLayoutAssignment` and the org-wide default; each record type names its business process and its compact layout. |

A single `package.xml` deployment preserves this order within one request, so the manifest in this
directory is deployable as one unit.

## Dependencies on components outside this step

- **Nothing upstream.** `depends_on` is empty; every name this step references either exists in the
  target org already (`Case`, `Account`, `Case.Status`, `Case.Priority`, `Case.Origin`,
  `Case.CaseNumber`) or is created here.
- **`StandardValueSet:CaseStatus` is deliberately NOT in this manifest** (assumption A28). Both
  support processes select `New`, `Escalated` and `Closed` from the value set the org already has.
  If any of those three is not a live `CaseStatus` value in the target org, this deploy fails on the
  business processes — retrieve `StandardValueSet:CaseStatus` and reconcile before deploying.
- **Downstream consumers of this step's artefacts:** M1-S02 (page layouts per record type),
  M2-S05 (the criteria-based sharing rule keyed on `RecordTypeId`, checked against this file's
  `sharingModel` by `check_sharing_model.py` at build scope), M3 (`CaseSettings.webToCase.caseOrigin`
  and the Email-to-Case routing addresses, which stamp the `CaseOrigin` values defined here),
  M4-S02 (`Account.Support_Tier__c` selects the entitlement process) and M4-S04
  (`Case.Severity__c` selects the 24/7 escalation entry).
- **Record types are not selectable until a Profile or Permission Set grants visibility.** Nothing
  in this step makes them pickable; `recordTypeVisibilities` is M2-S02's. Until then
  `check_record_type_layouts.py` reports no visibility cross-reference because there is none to make.

## Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `StandardValueSet` | `CaseOrigin` (the enum name, not the field) | case-management-setup § 1 and § 5 |
| `CustomObject` | `Case` | record-types-and-page-layouts, "Where the files live" |
| `CustomField` | `Object.Field__c` | `skills/devops/metadata-api-retrieve-deploy/references/examples.md` (`Account.HealthScore__c`) |
| `BusinessProcess` | object-qualified, `Case.Support_Process` | record-types-and-page-layouts, "Where the files live"; the bare name is used *inside* the record type |
| `RecordType` | object-qualified, `Case.Support`; no `*` wildcard | record-types-and-page-layouts, "Where the files live" |
| `CompactLayout` | `Case_Intake` — the bare compact layout name | `skills/admin/list-views-and-compact-layouts/references/metadata-examples.md`, "Where the files live" table |

> The `CompactLayout` member form is the thinnest grounding in this manifest: the cited skill's table
> states "compact layout name" but its own `package.xml` sample uses only `*`, so no non-wildcard
> example exists to copy. Verify against a retrieve before deploying.

## Validate-only command for the human

`agents/metadata-builder` never runs this. It is text to copy.

```
sf project deploy validate --target-org <your-sandbox-alias> --manifest .sfskills/builds/case-onboarding/artefacts/M1-S01/package.xml
```
