# M1-S02 — deploy order

Written by `agents/metadata-builder` Step 7. Sourced from
`skills/admin/change-management-and-deployment/references/metadata-examples.md` § 1 (the admin-release
manifest shape and the `Layout` member form) and from
`skills/admin/record-types-and-page-layouts/references/gotchas.md` #6, #7, #8 and #11.

This step declares `depends_on: ["M1-S01"]` and produces two `Layout` components and nothing else.

## Order inside this step

| # | Component | Because |
|---|---|---|
| 1 | `Layout:Case-Case Support Layout` | No ordering constraint between the two layouts — neither references the other. Both are listed in one `<types>` block and deploy in a single request. |
| 2 | `Layout:Case-Case Billing Layout` | Same. |

## Dependencies on components outside this step

- **`Case.Severity__c` (M1-S01) must exist before this step deploys.** `Case-Case Support Layout`
  places `Severity__c` as a `layoutItems/field`. A layout naming a field that does not exist fails
  the deploy. M1-S01 declares `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml`.
- **Every other field on both layouts is a standard Case field** (`Subject`, `Priority`, `Origin`,
  `Status`, `OwnerId`, `CaseNumber`, `CreatedById`, `LastModifiedById`) and exists in any org, so
  they carry no ordering constraint.
- **Nothing in this step assigns either layout to anyone.** `layoutAssignments` lives only on
  `Profile`, never on `PermissionSet` — `record-types-and-page-layouts/references/metadata-examples.md`,
  "Making the record type visible and assigning the page". Until the M2 access steps write those
  profiles, both layouts deploy and neither is reachable by a user. That is expected at this point in
  the build and is why `check_record_type_layouts.py` makes no assignment cross-check here: with no
  `Profile` in the scanned tree there are no `layoutAssignments` to resolve.
- **The profile that later assigns these layouts must name them in the file-name form**
  `Case-Case Support Layout` / `Case-Case Billing Layout`, paired with `Case.Support` /
  `Case.Billing` from M1-S01. Recorded here so the M2 access step does not re-derive it.
- **Retrieve-time warning for whoever pulls this back down (gotchas #7):** retrieving a `Layout`
  makes it appear in any `Profile` or `PermissionSet` retrieved in the same package. Fix one
  manifest per object domain rather than retrieving these two layouts alone.

## Manifest member forms used

| Type | Member form | Source |
|---|---|---|
| `Layout` | `Case-Case Support Layout` — object, hyphen, layout name, literal space | `record-types-and-page-layouts/references/metadata-examples.md`, "Where the files live" table; `change-management-and-deployment/references/metadata-examples.md` § 1, quoting the guide's own `Idea-Idea Layout` example (api_meta L82285–L82289) |

`Layout` does support the `*` wildcard per the "Where the files live" table, but both members are
named explicitly so the manifest agrees with the files on disk in both directions.

## Elements this step could NOT ground, and what was written instead

- **Q24's "defaulted on" half.** Q24's answer asks for the "Assign using active assignment rule"
  checkbox to be *defaulted on* for manual case entry. The only element the cited skill's element
  inventory carries is `<showRunAssignmentRulesCheckbox>`, documented as controlling whether the
  checkbox is *shown* on Case, Lead and Account layouts. No element for pre-checking it appears
  anywhere in `record-types-and-page-layouts/references/metadata-examples.md`. Both layouts therefore
  set `<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>` and stop there. The
  select-by-default half of Q24 is **not written**, and is not inventable from the cited skill —
  it needs either a Setup step recorded for the human or a skill deepened to document the element,
  per `standards/build-orchestration.md` § 8.
- **No `AccountId` or `ContactId` on either layout.** The requirement is account-centric (Premier vs
  Standard tiers, `Account.Support_Tier__c` from M1-S01), but no cited source for this step names
  either lookup as a Case layout field, and no clarification answer supplies a field list. They are
  omitted rather than invented; a human adding them is a one-line change to each layout.
- **No `quickActionList` and no `relatedLists`.** Both elements exist in the skill's example, but the
  example's members (`LogACall`, `FeedItem.TextPost`, `RelatedActivityList`, the `TASK.*` retrieval
  aliases) are that example's content, not this build's. Nothing in `requirement.md` or the answered
  clarifications selects quick actions or related lists for these layouts, and
  `metadata-examples.md` warns that `relatedLists/fields` for standard fields use retrieval aliases
  rather than API names — hand-writing them is exactly the failure mode it names. Left out.
- **No field is marked `behavior=Required`.** Q5 settles this: `Priority` and `Origin` are enforced
  at field or validation-rule level, not by layout, because Email-to-Case and Web-to-Case create
  through the API where layout `Required` does not bind (gotchas #11). `check_record_type_layouts.py`
  check 4 reports one INFO per layout for this — "marks no field behavior=Required" — which is the
  correct output for this design, not a defect. Exit code is unaffected.

## Validate-only command for the human

`agents/metadata-builder` never runs this. It is text to copy.

```
sf project deploy validate --target-org <your-sandbox-alias> --manifest .sfskills/builds/case-onboarding/artefacts/M1-S02/package.xml
```
