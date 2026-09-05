# M1-S01 — deploy order

Written by `agents/metadata-builder` Step 7. Sourced from
`skills/admin/change-management-and-deployment` (admin-release manifest shape) and from the deploy
order table in `skills/admin/case-management-setup/references/metadata-examples.md` § 5.

This step is the first in the build and depends on nothing (`depends_on: []`).

## Order inside this step

| # | Component | Because |
|---|---|---|
| 1 | `CustomField` — `Case.Severity__c`, `Account.Region__c`, `Account.Support_Tier__c` | § 5 row 1: "a `picklistValues` block or a rule criterion on a field that does not exist fails the deploy". `Severity__c` is also named by the compact layout in step 4. |
| 2 | `StandardValueSet:CaseOrigin` | § 5 row 2: the record types' `picklistValues` blocks and, later, `CaseSettings.webToCase.caseOrigin` both reference values that must already exist. A `picklistValues` block exposes values; it does not create them. |
| 3 | `BusinessProcess` — `Case.Support Process`, `Case.Billing Process` | § 5 row 3: a Case record type is rejected without its support process. |
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
| `BusinessProcess` | object-qualified, `Case.Support Process` | record-types-and-page-layouts, "Where the files live"; the bare name is used *inside* the record type |
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
