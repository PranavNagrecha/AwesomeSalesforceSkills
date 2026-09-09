# M1-S02 — deploy order

Written by `agents/metadata-builder` Step 7. Sourced from
`skills/admin/change-management-and-deployment/references/metadata-examples.md` § 1 (the admin-release
manifest shape and the `Layout` member form) and from
`skills/admin/record-types-and-page-layouts/references/gotchas.md` #6, #7, #8, #11, #12 and #13.

This step declares `depends_on: ["M1-S01"]` and produces two `Layout` components and nothing else.

## Rebuild #2 — why this step was built a second time

**Build #1** ran 2026-09-06T04:05:00Z and was tested, documented and carried into the accepted M1
milestone. **Rebuild #2** ran 2026-09-09T19:38:37Z. Nothing about the requirement changed; the
artefacts were wrong and every gate in the loop said they were right.

- **What proved it.** `reports/MOCK-DEPLOY-M1.md` — `sf project deploy start --dry-run` against
  `sfskills-dev` on 2026-09-05. Run 1: 10 of 12 components validated; both layouts failed with
  `Layout must contain an item for required layout field: ContactId`. Runs 2–5 surfaced
  `Description`, then `SuppliedEmail`, then `Field:Status must be Required` — one message per run,
  because the platform reports one field at a time. Findings **F-09** and **F-10**.
- **Why build #1 missed it.** Four platform rules that no cited source carried. Build #1's own
  deploy-order note said so in as many words: it omitted `ContactId` because "no cited source for
  this step names either lookup as a Case layout field", and it set no field `behavior=Required`
  on the strength of Q5. Q5's answer is right for `Priority`, `Origin` and `Subject` and wrong for
  `Status`, which is a deploy precondition rather than a data-quality control — the failure mode
  `record-types-and-page-layouts/references/gotchas.md` #13 now exists to name.
- **What was fixed before this rebuild, and where.** The library, not the artefact.
  `skills/admin/record-types-and-page-layouts` v1.2.0 (2026-09-09) now carries the deployable Case
  layout in `references/metadata-examples.md` ("Page layout with two sections, the layout-required
  Case fields, and one design-required field"), the `## Layout-required standard fields` section
  behind it, gotchas #12 and #13, and checker rules **RL-REQ-01** (a Case layout with no
  `layoutItems` entry for `ContactId` / `Description` / `SuppliedEmail`) and **RL-REQ-02** (a Case
  layout whose `Status` item is missing or is not `behavior=Required`), both ERROR.
- **The rebuild is the whole change.** Build #1's artefacts were never edited in place — the
  contract forbids it, and `standards/build-orchestration.md` § 8 makes a knowledge gap a signal to
  deepen a skill. The skill was deepened first; this step was then re-run against it.
- **Evidence the fix is the org's answer and not this agent's.** The item set and behaviors of both
  rebuilt layouts are identical to the scratch copies that validated 12/12 in mock-deploy run 5,
  committed at `reports/mock-deploy-fixes/Case-Case Support Layout.layout-meta.xml` and
  `…/Case-Case Billing Layout.layout-meta.xml`.
- **Checker evidence, before and after.** Same command, verbatim, from this build directory:
  `python3 skills/admin/record-types-and-page-layouts/scripts/check_record_type_layouts.py --manifest-dir artefacts/M1-S02`.
  Against build #1's layouts it now exits **1** with four ERRORs (RL-REQ-01 ×2, RL-REQ-02 ×2);
  against rebuild #2's it exits **0** with `0 finding(s)`.

**What did not change:** the field set (including `Severity__c` on Support only), both layouts'
`<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>`, the two `layoutSections`,
and `package.xml` (same two `Layout` members). Rebuild #2 adds three `layoutItems` entries per
layout and changes one `behavior`.

## Order inside this step

| # | Component | Because |
|---|---|---|
| 1 | `Layout:Case-Case Support Layout` | No ordering constraint between the two layouts — neither references the other. Both are listed in one `<types>` block and deploy in a single request. |
| 2 | `Layout:Case-Case Billing Layout` | Same. |

## Dependencies on components outside this step

- **`Case.Severity__c` (M1-S01) must exist before this step deploys.** `Case-Case Support Layout`
  places `Severity__c` as a `layoutItems/field`. A layout naming a field that does not exist fails
  the deploy. M1-S01 declares `artefacts/M1-S01/objects/Case/fields/Severity__c.field-meta.xml`.
- **Every other field on both layouts is a standard Case field** (`SuppliedEmail`, `Description`,
  `ContactId`, `Subject`, `Priority`, `Origin`, `Status`, `OwnerId`, `CaseNumber`, `CreatedById`,
  `LastModifiedById`) and exists in any org, so they carry no ordering constraint. The first three
  are on the layouts because the platform requires them there, not because the requirement asked
  for them — see Rebuild #2 above.
- **`ContactId` is a lookup to `Contact`, which is a standard object.** It needs nothing from this
  build to resolve. Whether a support agent can *see* the contact is a record-access question the
  M2 access steps answer; it is not a deploy ordering constraint.
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
named explicitly so the manifest agrees with the files on disk in both directions. `package.xml` is
unchanged from build #1: rebuild #2 added no component, only items inside two existing ones.

## Elements this step could NOT ground, and what was written instead

- **Q24's "defaulted on" half — still open after rebuild #2.** Q24's answer asks for the "Assign
  using active assignment rule" checkbox to be *defaulted on* for manual case entry. The only
  element the cited skill's element inventory carries is `<showRunAssignmentRulesCheckbox>`,
  documented as controlling whether the checkbox is *shown* on Case, Lead and Account layouts. No
  element for pre-checking it appears anywhere in
  `record-types-and-page-layouts/references/metadata-examples.md`, including at v1.2.0. Both layouts
  therefore set `<showRunAssignmentRulesCheckbox>true</showRunAssignmentRulesCheckbox>` and stop
  there. The select-by-default half of Q24 is **not written**, and is not inventable from the cited
  skill — it needs either a Setup step recorded for the human or a skill deepened to document the
  element, per `standards/build-orchestration.md` § 8. The v1.2.0 fix addressed F-09/F-10 and did
  not touch this.
- **`AccountId` is still absent; `ContactId` is now present, and not for the requirement's reason.**
  The requirement is account-centric (Premier vs Standard tiers, `Account.Support_Tier__c` from
  M1-S01). Build #1 omitted both lookups because no cited source named them. `ContactId` is now on
  both layouts because RL-REQ-01 and the mock deploy say the platform requires it there — that is a
  deploy precondition, not evidence that the requirement wanted a contact lookup. `AccountId` is
  still omitted: no source names it, and the platform does not require it. A human adding it is a
  one-line change to each layout.
- **No `quickActionList` and no `relatedLists`.** Both elements exist in the skill's example, but the
  example's members (`LogACall`, `FeedItem.TextPost`, `RelatedActivityList`, the `TASK.*` retrieval
  aliases) are that example's content, not this build's. Nothing in `requirement.md` or the answered
  clarifications selects quick actions or related lists for these layouts, and
  `metadata-examples.md` warns that `relatedLists/fields` for standard fields use retrieval aliases
  rather than API names — hand-writing them is exactly the failure mode it names. Left out.
- **`Status` is the only field marked `behavior=Required`, and it is not a design decision.** Q5
  still settles the design question: `Priority` and `Origin` are enforced at field or
  validation-rule level, not by layout, because Email-to-Case and Web-to-Case create through the API
  where layout `Required` does not bind (gotchas #11). `Subject` is unchanged at `Edit` for the same
  reason. `Status` is outside that question entirely — `Field:Status must be Required` is what the
  deploy returns without it (mock-deploy run 4 → run 5; gotchas #13). Build #1 read Q5 one step too
  far and demoted `Status` with the rest; rebuild #2 separates the two questions in the order
  gotcha #13 prescribes. `check_record_type_layouts.py` no longer emits the two INFO lines about
  layouts marking no field `behavior=Required`, because both now mark one.

## Validate-only command for the human

`agents/metadata-builder` never runs this. It is text to copy.

```
sf project deploy validate --target-org <your-sandbox-alias> --manifest .sfskills/builds/case-onboarding/artefacts/M1-S02/package.xml
```
