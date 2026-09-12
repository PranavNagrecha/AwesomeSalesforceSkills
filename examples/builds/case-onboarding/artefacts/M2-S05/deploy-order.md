# Deploy order — M2-S05 (Case sharing rule)

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was deployed.

## Order inside this step

| # | Component | Type | Why it must come at this point |
|---|---|---|---|
| 1 | `Case` | `SharingRules` | The only deployable component this step produces. It has no internal ordering — one file, one criteria rule. Everything that must precede it is outside this step (next section) |

`case-visibility-model.md` and this note are documentation, not metadata; they are not in
`package.xml` and nothing deploys them.

## Dependencies on components OUTSIDE this step

`skills/admin/change-management-and-deployment/references/llm-anti-patterns.md` puts sharing rules
at **position 6 of 7** in dependency order, "which depend on OWD and object existence", and
`skills/admin/sharing-and-visibility/references/metadata-examples.md` § 6 says the same in its own
words: "Deploy order matters: OWD and roles first, then groups, then the rules that reference
them." Three things must already be in the target org when this manifest lands:

| # | Must be deployed first | Step | What breaks without it |
|---|---|---|---|
| 1 | `Case.object-meta.xml` carrying `<sharingModel>Private</sharingModel>` | **M1-S01** | The rule's `Edit` grant is only meaningful above a `Private` default. Under `Read` it still grants; under `ReadWrite` it grants nothing at all and Setup still shows it as active. `check_sharing_model.py` fires HIGH on exactly this pairing, which is why this step's acceptance test reads `artefacts` and not `artefacts/M2-S05` |
| 2 | `Case.Support.recordType-meta.xml` | **M1-S01** | `criteriaItems.value` is the record type's developer name. Deploy the rule first and the criterion matches nothing, silently |
| 3 | `Support_Tier_2.group-meta.xml` | **M2-S04** | `sharedTo.group` names it. UNVERIFIED (`sharing-and-visibility/references/metadata-examples.md` § 6): the guide does not state what happens when a `sharedTo` group is absent from the target org — "treat a missing referent as a likely deployment failure and ship the group in the same package rather than testing the assumption in production" |

Nothing downstream in this build references this rule. M3's assignment rules, M4's escalation rules
and M5's tests read the *access* it produces, not the file.

## The post-deploy step without which this rule grants nobody anything

**`Support_Tier_2` deploys empty.** The Metadata API guide, quoted in the cited skill: "Members of
the public group aren't migrated when you deploy the group type." The group deploys, the rule
deploys, both show active in Setup, and zero Tier 2 engineers gain access until the `GroupMember`
rows for the 4 engineers (Q8) are loaded in the target org. That load is a **data** step with a
named owner (CRM admin lead), tracked in `artefacts/M2-S04/queue-retirement-runbook.md` § 6.
A green deploy here is not a working grant.

## Decisions worth reading before deploy

1. **`package.xml` names `SharingRules` with the object as the member — and the cited skill
   recommends the other form.** This is a real divergence, recorded rather than smoothed over.
   `sharing-and-visibility/references/metadata-examples.md` § 6 says "`SharingRules` itself does
   not support the wildcard and is not what you address. Manifest the concrete rule types:
   `SharingCriteriaRule` and `SharingOwnerRule`, with members shaped `Object.RuleName`" — which
   here would be `<members>Case.Support_Cases_To_Tier_2</members>` under
   `<name>SharingCriteriaRule</name>`. Two other skills in the library manifest the container form
   instead, with an object as the member: `admin/experience-cloud-guest-access`
   (`references/metadata-examples.md`, `FAQ_Article__c` under `SharingRules`) and
   `admin/data-skew-and-sharing-performance` (`references/metadata-examples.md`, `Loan__c`). The
   container form is written here for one mechanical reason: this step's declared `manifest`
   acceptance test names "SharingRules:Case as its own `<name>` block", and the tester derives the
   member from the file name (`sharingRules/Case.sharingRules-meta.xml` → `SharingRules` : `Case`),
   so the rule-type form would leave the file uncovered *and* declare a member with no file of its
   own. **Both forms deploy the same file.** If a mock deploy rejects the container form, the
   one-line fix is to swap the `<types>` block for the rule-type form and amend the step's manifest
   test in the same change.
2. **`includeRecordsOwnedByAll` is `true`, and it cannot be changed later.** The guide: "You can't
   edit this field after the sharing rule is created." The value is grounded, not defaulted:
   `Case_Intake_Integration` (M2-S01) exists precisely because an automated-process identity owns
   the case at creation, before M3-S04's assignment rules transfer it. With `false`, every case
   still sitting with the intake identity would be outside the rule. Getting this wrong means
   deleting and recreating the rule in the target org.
3. **`criteriaItems.value` is the bare developer name `Support`, and the value *format* is
   UNVERIFIED.** `admin/duplicate-management/references/metadata-examples.md` carries the marker
   verbatim for the same field on a different type: "whether `RecordTypeId` accepts the record
   type's **developer name** (as written above) or requires an 18-character Id is not established
   by the Metadata API guide. Deploy this filter to a sandbox and re-read the retrieved XML before
   promoting it." The bare name is the form the library documents, it is what
   `artefacts/M1-S01/objects/Case/recordTypes/Support.recordType-meta.xml` carries as its
   `fullName`, and a hard-coded 18-character Id would not survive the move between orgs anyway.
   **This is the single most likely thing in this step to come back from a mock deploy.** If it
   does, the candidates in order are `Support`, `Case.Support`, then the 18-character Id — and only
   the first two are portable.
4. **No `<booleanFilter>`.** The cited skill's worked example carries `1 AND 2` because it has two
   `criteriaItems`. This rule has one, so there is nothing to combine and the element is omitted
   rather than written as `1`. Adding a second criterion later means adding the element.
5. **No `<fullName>` prefix on the rule.** `<fullName>Support_Cases_To_Tier_2</fullName>` is bare
   inside the file; the object appears only in the file stem (`Case.sharingRules-meta.xml`) and,
   in the rule-type manifest form, before the dot. The skill's worked example shows exactly this:
   `High_Value_Rooms_To_Deal_Desk` inside `Deal_Room__c.sharingRules-meta.xml`. This is the M1
   mock-deploy F-11 rule — file stem equals `fullName` — applied to the container: the stem is the
   object, because the object is what the container is named for.
6. **`doesIncludeBosses` on `Support_Tier_2` is `true` (set in M2-S04) and it widens this grant.**
   The gotcha: it "is set once on the group and applies retroactively to every rule that ever
   targets it." Nobody sits above a Tier 2 engineer in this build because no role exists yet, so
   the effect is inert today and stops being inert the day a role hierarchy is loaded. If Tier 2's
   Support-case access must not travel up a future hierarchy, the file to change is
   `artefacts/M2-S04/groups/Support_Tier_2.group-meta.xml`, not this one.
7. **`<description>` is 169 characters.** Kept under 200 deliberately. `SharingBaseRule.description`
   is documented at a 1,000-character maximum, but the M1 mock deploy (finding F-15) had the org
   reject a longer description at 255, so the shorter ceiling is the one this build writes to.

## Elements this step could NOT ground

Recorded rather than invented, per `standards/build-orchestration.md` § 8.

1. **No sharing rule grants `Billing_Team` access to Billing cases, and none should be read into
   this step's absence of one.** Billing reaches its own cases as **owner**, through the `Billing`
   queue (M2-S04). A criteria rule targeting `Billing_Team` was not written because this step's
   declared manual acceptance test asserts the opposite — "the only criteria-based rule shares
   Support-record-type cases to the `Support_Tier_2` public group, no rule names the Billing record
   type or the `Billing_Team` group as a target". If Billing must also see Billing cases they do
   **not** own (a second finance reviewer, a manager), that grant does not exist yet and needs a
   plan amendment, not an edit here.
2. **No role, and therefore no hierarchy assumption.** No role developer name appears in
   `requirement.md`, in any of the 97 clarifications, or in an upstream artefact. Writing
   `roleAndSubordinatesInternal` would mean naming a hierarchy nobody has described.
3. **Q13 is DEFERRED.** The whole shape of this step rests on assumption A1 reading the Billing
   restriction as record-level. D5's own stated consequence: "If the answer turns out to be
   field-level masking, M2-S05 is re-planned, not patched."

## Validate-only command for a human to run

Never run by an agent in this loop. Copy the artefacts into a DX source tree first — the path below
is relative to that tree, not to the build directory. Deploy M1-S01 and M2-S04 first, or include
them in the same request.

```bash
sf project deploy start \
    --manifest manifest/package.xml \
    --dry-run \
    --target-org <your-sandbox-alias>
```

Then prove the access rather than reading the rule list — the two queries are in
`case-visibility-model.md` under "Verification a human runs after deploy". Confirm in Setup →
Security → Sharing Settings that `Case` reads *Private / Private* and that
`Support Cases to Tier 2` appears, and check that sharing recalculation has finished before
believing either answer.
