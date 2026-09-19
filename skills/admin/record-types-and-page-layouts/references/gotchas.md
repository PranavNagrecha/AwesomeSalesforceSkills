# Gotchas: Record Types and Page Layouts

---

## 1. Changing a Record's Record Type Can Wipe Picklist Values

**What happens:** An admin bulk-reassigns 5,000 Opportunity records from "New Business" RT to "Renewal" RT (because the company restructured its sales motion). After the reassignment, users report that the Stage field on 3,000 records is now blank. "Prospecting" and "Discovery" exist on New Business RT but not on Renewal RT. When the RT changed, those picklist values were cleared because they're not valid on the new RT.

**When it bites you:** Any bulk Record Type reassignment, any workflow/flow that changes a record's RT, any migration combining business units that used different RTs.

**How to avoid it:**
1. Before ANY RT reassignment: run a SOQL to find all records with picklist values that don't exist on the target RT
2. Map the source picklist values to equivalent target values
3. Update picklist values BEFORE changing the RT, not after
4. Test the entire sequence in sandbox with a representative sample

SOQL to identify at-risk records:
```soql
-- Find Opportunities with "Prospecting" stage that will be affected
SELECT Id, Name, StageName, RecordType.Name
FROM Opportunity
WHERE RecordType.DeveloperName = 'New_Business'
AND ISPICKVAL(StageName, 'Prospecting')
-- Then check: does "Prospecting" exist on the target RT? If not, these records lose their Stage value.
```

---

## 2. Record Types and Person Accounts — Design Them Separately

**What happens:** An org enables Person Accounts. The admin creates Record Types for Business Accounts and assigns them. Later, someone creates a Person Account and gets an error or unexpected RT assignment. The RT model for Person Accounts and Business Accounts is governed by the same object but behaves differently — Person Account RTs must be designed with the Person Account user profile in mind, and Business Account RTs must be hidden from Person Account creation.

**When it bites you:** Any org that enables Person Accounts after the Account RT model is already built. Also: Community portals where external users are Person Accounts.

**How to avoid it:**
- Design RT models for Business and Person Accounts separately, as if they're two different objects
- Use separate Profiles/PSGs to control which users see which Account RT type
- Test Person Account creation with the portal user profile — not the System Administrator profile
- Document explicitly: "Person Account RTs" vs "Business Account RTs" in your permission model

---

## 3. New Profiles Don't Inherit Record Type Assignments

**What happens:** A managed AppExchange package is installed and creates a new custom Profile. Users assigned to that Profile try to create Accounts and can't select any Record Type (or are forced to the Master RT with all picklist values). The admin doesn't know until users report it because no alert fires when a new Profile is created with no RT assignments.

**When it bites you:** Package installations, profile cloning, new onboarding processes that create users with a profile the admin didn't configure.

**How to avoid it:**
- After any package installation, immediately check the profiles it creates and configure RT assignments
- Create a checklist item in your onboarding process: "Verify Record Type assignments on all Profiles used by this user role"
- Run this SOQL periodically to find profiles with users but no RT assignments (for key objects):

```soql
-- Profiles with active users — check if they have RT assignments
SELECT Profile.Name, COUNT(Id) UserCount
FROM User
WHERE IsActive = TRUE
GROUP BY Profile.Name
ORDER BY Profile.Name
-- Then cross-reference with RT assignments in Setup → Record Types
```

---

## 4. Reports Filter by Record Type Label — Labels Are Not Stable

**What happens:** A business analyst builds 20 reports filtered by "Opportunity Type = New Business". An admin renames the Record Type label from "New Business" to "New Logo" (rebranding). Every one of those 20 reports now returns zero results — they're filtering for "New Business" which no longer exists. The analyst doesn't notice immediately. A week later, an executive dashboard shows zero pipeline.

**When it bites you:** Any time a Record Type label is renamed. This is a support ticket waiting to happen.

**How to avoid it:**
- Before renaming a RT label: audit all reports that filter on that RT name
- Consider: only rename the label if necessary; the Developer Name (API name) is what code uses and is stable
- After renaming: search for the old label in report filters and update them
- Communicate RT renames to report owners BEFORE making the change

---

## 5. Page Layouts Are Not Security Controls

**What happens:** An admin hides the `Salary__c` field on the page layout for non-HR users, assuming this restricts access. A power user opens the field in a report or accesses it via the API. The field is visible. The admin says "I hid it on the layout." Yes, but the layout is a UX control — it affects what appears on the record detail page, not what the user can access through other means.

**When it bites you:** Any time a field contains sensitive data (PII, financial, compensation) and the only restriction is a page layout.

**How to avoid it:**
- Use FLS (Field-Level Security) to actually restrict field access — not page layouts
- Page layout: controls what appears on the record page
- FLS: controls whether the user can see or edit the field AT ALL, in any context
- Both are needed: FLS for security, page layout for UX

---

## 6. `businessProcess` Is Required on Four Objects and Forbidden on All Others

**What happens:** An admin copies a working Opportunity record type block as a starting point for a record type on `Warranty_Claim__c`, keeps the `<businessProcess>` element, and the deploy fails. Later the same admin writes a Case record type without a `<businessProcess>` element and that deploy fails too — with a different message. Neither failure mentions the pairing rule.

**When it bites you:** Any hand-written or LLM-generated record type XML; any copy-paste between objects; any scratch-org rebuild where the business process was created in Setup but never captured in source.

**How to avoid it:**
- The Metadata API guide states `businessProcess` "is required in record types for lead, opportunity, solution, and case, and not allowed otherwise". Treat that as a hard four-object list.
- The Object Reference states the narrower rule on the sObject side — `RecordType.BusinessProcessId` is "required for Opportunity and Lead record types in API version 17.0 and later". The two documents disagree on Case and Solution; supplying the process on all four satisfies both.
- Inside the `<CustomObject>` definition, use the **bare** process name (`Customer Support Process`). Object-qualify it (`Case.Customer Support Process`) only in `package.xml` members and retrieve results. The guide calls out this exact mistake: "As the record type is already defined within the object, don't prefix the object name."
- Deploy the `businessProcesses` block and the `recordTypes` block in the same `CustomObject` file. A record type naming a process that isn't in the org yet fails on the reference, not on the pairing rule, which sends you hunting in the wrong place.

---

## 7. Retrieving a Record Type or Layout Rewrites the Profiles in the Same Package

**What happens:** A developer retrieves just the Case object and its layouts to review a change, commits the diff, and the pull request shows large unrelated additions inside three profile files. On the next retrieve — this time without the layouts — the same profile files lose those blocks again. The team concludes profiles are "unstable" and starts ignoring profile diffs.

**When it bites you:** Every partial retrieve. The guide states the rule twice, once under `RecordType` and once under `Layout`: retrieving a component of that type "makes the component appear in any Profile and PermissionSet components that are retrieved in the same package."

**How to avoid it:**
- Profile and permission set content is a *function of what else is in the manifest*, not a fixed file. Fix one manifest per object domain and always retrieve with it, so consecutive retrieves are comparable.
- Never deploy a profile retrieved from a narrow manifest into an org configured from a wider one — the assignments absent from your file are absent because they weren't requested, and the deploy removes them.
- When reviewing a profile diff, check the manifest before the diff. A block that appeared or vanished is usually a manifest change, not an org change.

---

## 8. Deactivating a Record Type Makes Its Profile and Permission Set Assignments Untrackable

**What happens:** An admin deactivates a retired record type instead of deleting it (because records still reference it), then retrieves the profiles for a release. The `recordTypeVisibilities` entries for that record type are gone from every file. Someone assumes an unauthorised change removed them, reinstates them by hand, and the deploy fails or silently drops them.

**When it bites you:** Any lifecycle where a record type is deactivated rather than deleted. The guide is explicit on both types: `Profile.recordTypeVisibilities` "isn't retrieved or deployed for inactive record types" in API version 29.0 and later, and `PermissionSet.recordTypeVisibilities` "is never retrieved or deployed for inactive record types".

**How to avoid it:**
- Before deactivating, capture the current visibility matrix — a `RecordType` SOQL plus the profile files, committed as a snapshot — because after deactivation source control can no longer describe it.
- Do not attempt to re-add visibility entries for an inactive record type by hand. Reactivate first (`active` back to `true`), deploy, then deploy the visibility.
- Deactivation is not the safe half-measure it looks like: it makes the record type unselectable *and* unauditable, while existing records keep pointing at it. Prefer a full reassign-then-delete plan (gotchas #1) when the record type is genuinely retired.

---

## 9. The Metadata API Does Not Round-Trip the Whole Record-Type Picklist Matrix

**What happens:** A team treats the retrieved `CustomObject` file as the authoritative record of which picklist values each record type exposes. They rebuild a scratch org from source, and Person Account record types come back with only the standard values on a Contact-sourced picklist. Custom values that existed in the source org are simply missing, and nothing in the retrieve reported a gap.

**When it bites you:** Person Account orgs, and any object where a picklist is shared with Contact. The guide carries two separate notes under `RecordType`: Metadata API "doesn't retrieve custom picklist values on person account record types, if the picklist exists on a contact" — retrieving standard picklist values only — and it "doesn't retrieve specific picklist fields that are associated with a record type."

**How to avoid it:**
- Do not use "it's in source control" as evidence that the picklist matrix is complete on a Person Account object. Verify in Setup, per record type, per picklist.
- Keep a written picklist-by-record-type matrix (the design template in this skill has one) as the human-readable source of truth, and diff it against the org rather than against the retrieved XML.
- On scratch-org rebuilds of Person Account orgs, add an explicit post-build verification step for record-type picklist values; it is the one part of the model the retrieve will not tell you is wrong.

---

## 10. Record Type Labels, Names, and Descriptions Are Readable by Every User With Object Access

**What happens:** An admin creates record types named `VIP_Executive_Escalation` and `Layoff_Severance_Case`, and writes descriptions explaining who the confidential process applies to. A user with plain read access on the object — no create access, not assigned to those record types — enumerates all of them through the API and learns the whole taxonomy.

**When it bites you:** Any org where record type naming encodes something confidential: a customer tier, an internal investigation type, an unannounced product line, an HR process. The `RecordType` metadata type and the `RecordType` standard object both carry the same warning: "Users with access to an object can read all record type information for that object. We strongly recommend against storing sensitive information in the record type description, name, or label." `BusinessProcess` carries the identical warning for its description, name, and picklist values.

**How to avoid it:**
- Name record types after the process shape, not after the sensitive attribute. `Escalated_Case` rather than `VIP_Executive_Escalation`.
- Profile assignment governs create and edit access for a record type, not read access. A user not enabled for a record type "can't create records with that record type, but can access records associated with that record type" — record type assignment restricts nothing about reading.
- Sensitive attributes belong in a separate object or in fields with real access controls, which is the guide's own recommendation.

---

## 11. `Required` on a Page Layout Is a Property of the Layout, Not of the Field

**What happens:** A business analyst marks `Subject` as required on the Customer Support layout and reports the requirement as done. Cases created through the API, through a Flow, through the Internal IT layout, and through a quick action that uses a different layout all save with a blank `Subject`. Nothing errors; the analyst discovers it in a report months later.

**When it bites you:** Every time layout-level `Required` is used as a data-quality control — which is the default assumption, because the Setup UI presents it as a property of the field on that page.

**How to avoid it:**
- `LayoutItem.behavior` has three values — `Edit`, `Required`, `Readonly` — and the guide defines `Required` as "the layout field can be edited and is required". Its scope is that layout item, on that layout. Every other entry point is unaffected.
- Enforce the requirement where it actually binds: `required` on the field definition (all contexts), or a validation rule scoped by `RecordType.DeveloperName` (all save paths, but selectively by process). Layout `Required` on top of either is a UX affordance, not the control.
- Explicitly setting `behavior` on a Knowledge article layout raises an exception, per the guide — the one object where you must leave it out entirely.
- The same scoping trap applies in reverse: a field that is `Readonly` on one layout is fully editable on another, and read-only on a layout is not field-level security (gotchas #5).
- One exemption, and it runs the other way: a handful of standard fields are required *by the platform* on the layout, and there `Required` is not the analyst's choice to make (gotchas #12, #13).

---

## 12. Layout-Required Standard Fields Fail the Deploy, Not the Checker

**What happens:** A build generates two Case page layouts from the fields the requirement named — Subject, Priority, Origin, Status, Owner, a custom Severity — passes every static check in the pipeline, passes the step tests, passes the milestone verification, and then fails `sf project deploy start --dry-run` on the first component with `Layout must contain an item for required layout field: ContactId`. Adding `ContactId` produces `Layout must contain an item for required layout field: Description`. Adding that produces `SuppliedEmail`. Adding that produces `Field:Status must be Required`. Four runs, four messages, one at a time, none of them predicted by anything upstream.

That is not a hypothetical. It is `examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`, runs 1–5: verified by `sf project deploy start --dry-run` against a Summer '26 developer org on 2026-09-05. Ten of twelve components validated on run 1; both failures were the same platform rule.

**When it bites you:** Any hand-written or LLM-generated `Layout` file — that is, any layout that was composed from a requirement rather than retrieved from an org. A layout retrieved and round-tripped already carries the required items, so the whole class of failure is invisible to teams who never author one from scratch. It bites hardest in a design-only pipeline, where a green board of checkers implies deployability and nothing in the pipeline has ever talked to an org.

**Why nothing upstream catches it:** the Metadata API guide does not state the rule. `LayoutItem.behavior` (api_meta L82844–82851) presents `Edit` / `Required` / `Readonly` as an author's choice, the `Layout` type (api_meta L82275+) lists no required-item set, and the phrase `required layout field` appears nowhere in the guide. A checker cannot derive the rule from the documentation; it has to be seeded from a deploy.

**How to avoid it:**
- On Case, put `ContactId`, `Description`, and `SuppliedEmail` on every layout as `layoutItems` and give `Status` `<behavior>Required</behavior>`. That is the verified set — see `references/metadata-examples.md` § "Layout-required standard fields".
- Run `python3 scripts/check_record_type_layouts.py --manifest-dir force-app/main/default` before the deploy. RL-REQ-01 and RL-REQ-02 are ERROR-severity and exit 1 on exactly these four conditions.
- On any object other than Case, the membership of the set is `UNVERIFIED (2026-09-09)` — do not assume a list. Discover it by iterating `--dry-run` (grounded), or seed from a retrieved layout of that object and then still iterate.
- Budget for several `--dry-run` rounds. The deploy names one missing field per run, so a layout short of three fields costs three round trips before it even reaches the `must be Required` message.
- `--dry-run` (`checkOnly: true`) is the cheap way to buy this information: it validates against a real org and changes nothing.

---

## 13. `Status` Must Be `Required` on Case Layouts Even When the Org Enforces It Elsewhere

**What happens:** An admin reads gotcha #11, correctly concludes that layout `Required` binds only to that layout, and moves the enforcement where it actually binds — a validation rule scoped by `RecordType.DeveloperName`, or `required` on the field. They then set every layout item to `Edit` for consistency, including `Status`. The Case layout stops deploying: `Field:Status must be Required`. The rule they wrote is correct, enforced, and completely irrelevant to the error — the platform is not asking whether the value is enforced, it is asking what this layout item's `behavior` says.

**When it bites you:** Precisely when someone has internalised the *right* lesson about layout `Required`. This is the failure mode of a good answer applied one step too far: Q5 in the skill's Questions table ("Is a field being marked Required on the layout meant to be enforced everywhere?") pushes toward field-level or validation-rule enforcement, and that answer is right for `Priority`, `Origin`, `Subject`, and every custom field — and wrong for `Status` on Case, where `behavior=Required` is a deploy precondition rather than a data-quality control.

Verified by `sf project deploy start --dry-run` against a Summer '26 developer org on 2026-09-05 (`examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`, run 4 → run 5).

**How to avoid it:**
- Split the question in two before answering it. *Does the platform require this item to be `Required` on this object's layout?* comes first; only if the answer is no does *where should this requirement be enforced?* apply.
- Answer the first question empirically — `--dry-run` — not from the Metadata API guide, which does not carry the rule.
- On Case, `Status` is `<behavior>Required</behavior>`, full stop. A validation rule on `Status` may still be worth having for API and Flow save paths (gotchas #11 is unaffected), but it does not buy an exemption from the layout behavior.
- Which fields carry this constraint on objects other than Case is `UNVERIFIED (2026-09-09)`. Do not generalise `Status` to `StageName` on Opportunity or `Status` on Lead without a dry run against the target org.
- When reviewing a generated answer to "enforce at field/validation level, not on the layout", check whether the fields it demotes to `Edit` include a platform-required one. That is the regression this gotcha exists to catch.

**Opportunity now has an answer too (org-verified 2026-09-18).** The bullet above said not to generalise `Status` to `StageName` on Opportunity without a dry run. The dry run has been done — `sfskills-dev`, validate-only at API 62.0, `.sfskills/builds/northwind-sales/reports/MOCK-DEPLOY-M1.md` runs 1–4 — and it answered in two parts:

- Run 1: `Layout must contain an item for required layout field: Probability`. Every Opportunity layout must carry a `Probability` **item**, whatever its behavior. `RTL-REQ-01` (HIGH).
- Run 2, once `Probability` was present: `Field:Name must be Required`. Run 3: the same for `StageName`. `RTL-REQ-02` (HIGH) for those two fields.
- `CloseDate` went `Required` in the same pass as `StageName` and the org **never named it**. Run 4 succeeded, which proves the four-item set is *accepted*, not that `CloseDate` is *required* — the platform reports one required field per run, so a passing run cannot distinguish "required" from "harmless". `RTL-REQ-02` therefore emits an INFO carrying `UNVERIFIED (2026-09-18)` for `CloseDate`, never a HIGH. Flip it to `Edit` and re-run `--dry-run` if you want the real answer.

Fixtures: `scripts/fixtures/req-probability-positive|negative/`, `scripts/fixtures/req-name-positive|negative/`, `scripts/fixtures/req-closedate-unverified/`. Case and Opportunity are now the two objects with a verified set; every other object stays `UNVERIFIED (2026-09-09)` and `RL-REQ-03` stays the advisory heuristic it was.

---

## 14. Identical Page Layouts After a Record-Type Split With Nothing Differentiating Them

**What happens:** A requirement asks for two Opportunity record types — Enterprise and Renewal — and the answers never say which fields, sections, or related lists differ. The build ships two layout files with different names and byte-identical (or only whitespace / element-order different) content. Users pick a record type and see the same page either way; the only cost is twice the layout assignment matrix and a merge nobody scheduled.

**When it bites you:** Any record-type split justified by "different process" without a field-, picklist-, or related-list-level answer. Mode 2 of this skill already calls identical layouts merge candidates (workflow step 2); the checker encodes that as REVIEW `RTL-MERGE-01`.

**How to avoid it:**
- Before authoring a second layout, write the one sentence that differentiates it (a field, a section, a related list). If you cannot, share one layout across both record types or drop a record type.
- Run `python3 scripts/check_record_type_layouts.py --manifest-dir force-app/main/default` — `RTL-MERGE-01` names every layout in an identical group after normalisation.
- Whitespace and child-element order do not count as a difference; a single differing field, section, or related list does.

---

## 15. An Unassigned Record Type Deploys Cleanly and Nobody Can Select It

**What happens:** A milestone deploys two active record types with no Profile `layoutAssignments` entry naming them and no Profile/PermissionSet `recordTypeVisibilities` entry at all. The package validates. In the org, the create dialog never offers those types. The assignment was "planned for a later step"; only a human note in the build log carried that, and the first person who asks where the new type went asks in production.

**When it bites you:** Step-scoped builds that author objects and layouts before profiles, package installs that add record types without touching profiles, and any LLM output that creates a record type and stops. Deployable ≠ selectable.

**How to avoid it:**
- Treat assignment as part of the same deliverable, or say explicitly in `deploy-order.md` that visibility and layout assignment land in a later step.
- Run the checker over a tree that includes Profile/PermissionSet metadata. `RTL-ASSIGN-01` (INFO by default; REVIEW under `--require-assignment`) flags each active record type that neither a layout assignment nor a visibility entry names. When the scanned tree has no Profile or PermissionSet file at all, the checker emits one INFO — `no Profile/PermissionSet in scope — assignment coverage not checked` — instead of one line per type, so a metadata-only step is not spammed.
- Do not confuse this with check 3 (active but not visible): that only runs when visibility entries exist and looks at visibility alone. `RTL-ASSIGN-01` requires both layout assignment and visibility to be absent.
