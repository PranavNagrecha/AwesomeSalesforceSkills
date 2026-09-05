# M1-S01 — Record-type decision record

Step: `M1-S01` (type `object-model`, owner `metadata-builder`, build `case-onboarding`, plan v5).
Written by `agents/metadata-builder` Step 5/rule 3. Every element name and enum value below is
copied from a cited skill's metadata reference; nothing is invented.

## 1. Are record types warranted at all? — Q1, A26

**Yes, two: `Support` and `Billing`.**

Q1 asked which picklist values differ between the support and finance case processes, and warned
that if nothing differs the requirement is a layout problem, not a record type. The accepted answer
carries a conditional ("if only the reply address and queue differ, use one record type plus
Origin-driven routing instead"). Assumption **A26** resolves that conditional in favour of two,
because decision D5's criteria-based sharing rule keys on `RecordTypeId`: with a single record type
there is no record-level criterion that keeps Billing cases away from Tier 1 (assumption A1).

Two is also well inside the checker's complexity thresholds
(`check_record_type_layouts.py` warns at 9 record types and escalates at 14).

## 2. Support Processes — Q2, A28

Q2 settled that the object is `Case`, so a `BusinessProcess` is **required** on every record type:
`skills/admin/record-types-and-page-layouts/references/metadata-examples.md` quotes the Metadata API
guide — `businessProcess` "is required in record types for lead, opportunity, solution, and case, and
not allowed otherwise", and both directions are deploy failures.

| Record type | Support Process | Status values exposed |
|---|---|---|
| `Support` | `Support Process` | New (default), Escalated, Closed |
| `Billing` | `Billing Process` | New (default), Closed |

Grounding for the value names: the same reference states that a `BusinessProcess` drives
`Case.Status`, quoting the Object Reference — "the status of the case, such as New, Closed, or
Escalated". Those three names are the whole vocabulary this step had for `Case.Status`.

Grounding for the split: the requirement escalates untouched cases to **Tier 2 (4 engineers)**, and
describes Billing as **2 finance staff** working finance queries. Engineering escalation is therefore
a support-side state, so `Escalated` is exposed on the Support process and withheld from Billing.

**A28 holds:** no `StandardValueSet:CaseStatus` file is deployed by this step, and no new Status
value was added. Both processes carry a value named `Closed`, so
`check_case_management_setup.py`'s closed-status rule is satisfied
(`references/gotchas.md` #10 — `Case.IsClosed` is driven entirely by Status).

> **Open item, MEDIUM confidence.** Q1's answer says the two record types differ "on Status/Reason"
> but enumerates no values, and A28 itself records that. The subsets above are the smallest split
> consistent with the requirement, not a customer-confirmed one, and no `CaseStatus` value set was
> available to author against — which is exactly what
> `skills/admin/case-management-setup/references/gotchas.md` #10 tells you not to do from memory.
> Before deploy: retrieve `StandardValueSet:CaseStatus` from the target org, confirm that `New`,
> `Escalated` and `Closed` are live values, and confirm the split with the process owner.
> `Case.Reason` is named in Q1's answer and is **not** configured here — no clarification enumerates
> its values, so no `picklistValues` block for `Reason` was written.

## 3. `Case.Origin` values — Q19, W01

The three Origin values are **defined** by `standardValueSets/CaseOrigin.standardValueSet-meta.xml`,
not by the record types. `skills/admin/record-types-and-page-layouts/references/metadata-examples.md`
is explicit that a `picklistValues` block only *exposes* values that already exist; and
`skills/admin/case-management-setup/references/metadata-examples.md` § 1 maps `CaseOrigin` →
`Case.Origin` (api_meta L141974–141982) and makes the value set a hard prerequisite of everything
downstream.

| Value | Exposed on | Default on that record type |
|---|---|---|
| `Email-Support` | `Support` | yes |
| `Web` | `Support` | no |
| `Email-Billing` | `Billing` | yes |

`Web` carries `<default>true</default>` in the value set itself, matching the shape of § 1's own
sample and the value `CaseSettings.webToCase.caseOrigin` will point at in M3. Exactly one value in
the set is default, per the same reference ("`default` … is Required, defaulting to `true`" —
omitting it on every value produces several defaults).

No `Phone` value is defined: the requirement states "There is no phone channel."

## 4. Compact layout — B02/B03

`Case_Intake` is authored here, not in M1-S02, and is assigned in two scopes —
`CustomObject.compactLayoutAssignment` and `RecordType.compactLayoutAssignment` on both record
types. `skills/admin/list-views-and-compact-layouts/references/metadata-examples.md` § 4: "A compact
layout that is never assigned is inert."

Field order is the design: identifier first, state second
(`CaseNumber`, `Status`, `Priority`, `Origin`, `Severity__c`). None of the five is a text area, long
text area, rich text area or multi-select picklist, which are the four types the guide says compact
layouts do not support.

## 5. Org-wide default — B01, A1, deferred Q13

`objects/Case/Case.object-meta.xml` carries `<sharingModel>Private</sharingModel>` and
`<externalSharingModel>Private</externalSharingModel>` as direct children of `<CustomObject>`.
`skills/admin/object-creation-and-design/references/metadata-examples.md`: `sharingModel` is the
internal OWD and `externalSharingModel` "determines the access level for external users"; `Private`
is a valid `SharingModel` value for accounts, opportunities and custom objects
(api_meta.txt L45801–45814).

This is the element that makes "a Tier 1 agent cannot open a Billing case" true, and it rests on
**A1**, an assumption standing in for deferred **Q13** at `risk: high`. The `step:M1-S01` human gate
was approved on that basis for the dry run; a real deployment needs the security owner's signature.

## 6. Fields created here

| Field | Type | Values | Grounded by |
|---|---|---|---|
| `Case.Severity__c` | restricted Picklist | `Severity 1` | requirement: "Severity 1 outages are 24/7 and never pause"; consumed by M4-S04's `businessHoursSource: None` escalation entry |
| `Account.Region__c` | restricted Picklist | `EMEA`, `US` | requirement (London / New York calendars) + Q40 |
| `Account.Support_Tier__c` | restricted Picklist | `Premier`, `Standard` | requirement + Q38 (4 business hours vs 1 business day) |

> **Open item, MEDIUM confidence — `Severity__c` has one value.** The requirement names exactly one
> severity level. Levels 2, 3 and 4 are the obvious rest of the scale and are deliberately **not**
> written: no clarification enumerates them, and `agents/metadata-builder` forbids inventing a
> picklist value. Confirm the full scale with the customer before deploy.

`Region__c` and `Support_Tier__c` carry no default value on purpose: Q40's "unknown accounts default
to US" is the calendar-stamping flow's fallback, and stamping `US` as a field default would make an
unknown account indistinguishable from a genuine US one.
