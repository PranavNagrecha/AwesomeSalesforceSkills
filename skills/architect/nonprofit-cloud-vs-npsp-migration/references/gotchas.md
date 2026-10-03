# Gotchas: Nonprofit Cloud vs NPSP Migration

Non-obvious platform behaviours that cause real production problems in this domain. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "NPC Guide" means the Nonprofit Cloud Developer Guide, Version 67.0, Summer '26 (PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/nonprofit_cloud.pdf). NPSP object and field names are taken from the package source published by Salesforce.org at https://github.com/SalesforceFoundation/NPSP (namespace `npsp`; dependencies `npo02` with `npe01`, `npe03`, `npe4`, `npe5`), and Program Management Module names from https://github.com/SalesforceFoundation/PMM (namespace `pmdm`). Installed package versions differ between orgs, so confirm every source name against the source org.

## Gotcha 1: The Target Objects Are Standard Objects With No `__c`, And Half The Mapping Vocabulary Is Wrong

**What happens:** NPSP is a managed package, so everything in it is namespaced and suffixed: `npsp__General_Accounting_Unit__c`, `npe03__Recurring_Donation__c`. Nonprofit Cloud is native, and its objects carry no suffix at all. The NPC Guide names them precisely:

- Fundraising: `GiftTransaction` ("a completed transaction from a gift", API 59.0+), `GiftCommitment` ("the commitment made by a donor", 59.0+), `GiftCommitmentSchedule` ("the schedule for fulfilling the commitment", 59.0+), `GiftDesignation` and `GiftTransactionDesignation` (59.0+), `GiftSoftCredit` ("the soft credit attributed to a person or organization for the gift transaction", 59.0+), `GiftEntry`, `GiftBatch`, `GiftRefund`, `GiftTribute` (all 59.0+), and later additions including `GiftAgreement` (64.0+), `GiftStewardship` (65.0+), and `GiftActuarialEntry` (65.0+).
- Program Management: `Program` ("the enrollment and disbursement of benefits in a program", 57.0+), `ProgramEnrollment` ("details of enrollment for benefits in a program", 57.0+), `Benefit`, `BenefitAssignment`, `BenefitDisbursement`, `BenefitSchedule`, `BenefitSession`, `BenefitType`, `RecurrenceSchedule` (57.0+), `BenefitScheduleAssignment` (59.0+), `ProgramCohort` and `ProgramCohortMember` (61.0+), `CaseProgram` (57.0+).

The single most common mapping error is `ProgramEngagement`. That is the Program Management Module's object (`pmdm__ProgramEngagement__c`); the Nonprofit Cloud equivalent is **`ProgramEnrollment`**. A mapping built from memory carries the package name into the target column and survives review, because both names are plausible and only one exists in the target. This skill's own SKILL.md previously listed `Gift__c` and `ProgramEngagement` as Nonprofit Cloud objects; both were wrong and are corrected.

**When it occurs:** During mapping, months before anything is built. It surfaces at the first deployment, or worse, in an integration spec handed to a payment processor.

**How to avoid:** Populate the target column of the mapping from the NPC Guide's standard-object lists, not from recollection, and record the API version each object became available in. That column tells you whether the target org can hold the data.

**Source:** NPC Guide, Fundraising Standard Objects and Program Management Standard Objects (object descriptions and "available in API version" statements). PMM source: `force-app/main/default/objects` lists `Program__c`, `ProgramEngagement__c`, `Service__c`, `ServiceDelivery__c`, `ServiceSchedule__c`, `ServiceSession__c`, `ServiceParticipant__c`, `ProgramCohort__c`.

---

## Gotcha 2: Object Availability Is Gated Per Object By API Version, And The Modules Have Different Edition Floors

**What happens:** Nonprofit Cloud is not one release. Each object carries its own availability: `Program` and the Benefit family from API version 57.0, the core Fundraising objects from 59.0, `ProgramCohort` from 61.0, `GiftAgreement` from 64.0, `GiftStewardship` from 65.0, `GratefulPersonInvolvement` from 67.0. A design that assumes "Nonprofit Cloud has it" is making a claim about a specific API version. Editions differ by module. Nonprofit Cloud as a whole is "Available in: Enterprise and Unlimited Editions." Fundraising and Group Membership and Households list Enterprise, Unlimited, and Developer Editions. Program Management lists Enterprise and Unlimited only.

**When it occurs:** When the team spins up a Developer Edition org to prototype the program-management model, finds the objects missing, and loses days assuming a provisioning fault.

**How to avoid:** Check availability per object before scoping, and choose the prototype environment against the module being prototyped. Where an object is newer than the target org's API version, treat it as a sequencing constraint on the plan.

**Source:** NPC Guide, Chapter 1 edition box; Chapter 3 Fundraising edition box ("Enterprise Unlimited and Developer Editions"); Chapter 4 Program Management edition box ("Enterprise and Unlimited Editions"); Chapter 10 Group Memberships and Households edition box; per-object availability statements.

---

## Gotcha 3: Soft Credits Change Shape, So The Migration Is A Conversion

**What happens:** NPSP keeps soft credits on two package objects: `npsp__Partial_Soft_Credit__c` (contact, with `npsp__Amount__c`, `npsp__Role_Name__c`, `npsp__Opportunity__c`) and `npsp__Account_Soft_Credit__c` (organization, with `npsp__Account__c`, `npsp__Role__c`). In Nonprofit Cloud, `GiftSoftCredit` is one standard object related to `GiftTransaction`, with `RecipientId` (an Account), a restricted `Role` picklist (Honoree, Household Member, Influencer, Matched Donor, Other, Soft Credit, Solicitor, Third Party Donor), and `PartialAmount` or `PartialPercent`; "Soft Credit percent values don't need to total to 100%." There is also `GiftDefaultSoftCredit` (API 62.0+), the default allocation "on gift commitment transactions that are created by a recurrence engine": behaviour the target generates, not data to migrate.

**When it occurs:** In the transactional phase, after constituents have loaded cleanly. Attribution totals do not reconcile, and because soft credits drive recognition and stewardship, donors notice.

**How to avoid:** Convert both NPSP soft-credit objects into `GiftSoftCredit`, mapping each `Role_Name__c` or `Role__c` value to one of the eight target `Role` values in a reviewed table. Run a reconciliation report before and after, at the level fundraising reports on: donor, campaign, designation, and period. Exclude soft credits the recurrence engine will generate itself.

**Source:** NPC Guide, GiftSoftCredit (fields `GiftTransactionId`, `RecipientId`, `Role` values, `PartialAmount`, `PartialPercent` and the 100% note) and GiftDefaultSoftCredit. NPSP source: `objects/Partial_Soft_Credit__c/fields` and `objects/Account_Soft_Credit__c/fields`.

---

## Gotcha 4: Every NPSP Customisation Is A Dependency On A Package That Is Not The Target

**What happens:** NPSP's value is the automation layer (rollups, recurring-donation processing, household naming) implemented as package Apex, triggers, and fields. Customisations built on top reference package namespaces (`npsp__`, `npe01__`, `npo02__`, `npe03__`, `npe4__`, `npe5__`, `pmdm__`). None exist in a Nonprofit Cloud org that never installed the packages, so every reference in a custom trigger, formula, validation rule, report type, or integration payload breaks at cutover.

**When it occurs:** During the inventory, if you are lucky. During UAT, if not. Integrations are the worst category, because the break is on someone else's side of the wire and shows up as a field mismatch rather than an error.

**How to avoid:** Search the entire metadata tree for the package namespaces and enumerate every hit before estimating, including formula fields, report types, list-view filters, and every external system's field mapping (Example 2 in `references/examples.md`). The count of namespace references predicts effort better than record counts.

**Source:** NPSP `cumulusci.yml` (package namespace `npsp`; dependencies Households `npo02` including `npe01`, Recurring Donations `npe03`, Relationships `npe4`, Affiliations `npe5`); PMM `sfdx-project.json` (namespace `pmdm`).

---

## Gotcha 5: A Household Becomes A Party Relationship Group Mastered By An Account, With No Primary Contact Field

**What happens:** NPSP households are Household Accounts (with the legacy `npo02__Household__c` object still in the package) plus household naming settings (`npsp__Household_Naming_Settings__c`). Nonprofit Cloud models a household as a `PartyRelationshipGroup` ("a group of people living together such as a household", API 56.0+) whose `AccountId` is the master Account, with membership and relationships held on `AccountContactRelation` (56.0+), `ContactContactRelation` (57.0+), `AccountAccountRelation` (57.0+), and `PartyRoleRelation` (57.0+). `PartyRelationshipGroup` carries address, size, income, and status fields but no primary-contact field, so reports, salutations, and automation keyed on NPSP's household primary contact have nothing to point at.

**When it occurs:** When household rows are loaded as plain Accounts and the household-level reports and mail merges are rebuilt last.

**How to avoid:** Decide the household representation in the decision record before loading: one Account plus one `PartyRelationshipGroup` per household, members as `AccountContactRelation` rows, and a stated rule for which member plays the old primary-contact role (a `PartyRoleRelation` role or a custom field). Rebuild household reports against the new objects in the pilot, not after cutover.

**Source:** NPC Guide, Chapter 10 Group Memberships and Households: object list and API versions; PartyRelationshipGroup fields (`AccountId` "the master object", `GroupSize`, `GroupIncome`, `PrimaryAddress` fields, `Status`). NPSP source: `objects/npo02__Household__c`, `objects/Household_Naming_Settings__c`.

---

## Gotcha 6: Rollups Do Not Migrate; Customizable Rollups Become Record Rollup Definitions With Their Own Licence

**What happens:** NPSP calculates donor and household totals with its Customizable Rollups engine (`npsp__Rollup__mdt`, `npsp__Customizable_Rollup_Settings__c`). Nonprofit Cloud uses Record Rollup Definitions: metadata type `RecordAggregationDefinition` (API 59.0+, suffix `.RecordAggregationDefinition` in the `RecordAggregationDefinitions` folder) and results in `RecordAggregationResult`. Both require "the Record Aggregation permission set license and the Record Aggregation Access permission." Loading NPSP's calculated totals into target fields as data freezes them on day one.

**When it occurs:** When the mapping lists rollup fields (lifetime giving, last gift date, largest gift) as ordinary fields to copy.

**How to avoid:** List every NPSP rollup as a definition to rebuild, not a value to load. Provision the Record Aggregation permission set license for the users and the deployment user. Reconcile recalculated totals against the NPSP values for a sample of donors before sign-off. UNVERIFIED (2026-10-03): how and when Record Rollup Definitions recalculate after a bulk load is documented in Salesforce Help only; schedule a recalculation check in the cutover rehearsal.

**Source:** NPC Guide, Chapter 11 Record Rollup Definitions: RecordAggregationResult (API 59.0, Special Access Rules), RecordAggregationDefinition (file suffix and folder, version, special access rules, `aggregateFromObject`, `aggregateToObject`, `aggregationType`). NPSP source: `objects/Rollup__mdt`, `objects/Customizable_Rollup_Settings__c`.

---

## Gotcha 7: Fundraising Objects Are Invisible Without The Fundraising Access Licence And Permission

**What happens:** The migration user, or an integration user, cannot see `GiftTransaction`, `GiftDesignation`, and the other fundraising objects, although Nonprofit Cloud is provisioned. Each of these objects "is available only if the Fundraising Access license is enabled and the Fundraising User system permission is assigned to users." The standard fundraising invocable actions carry the same condition.

**When it occurs:** At the first load into the pilot sandbox, and again at cutover if the production integration user was set up from an old profile.

**How to avoid:** Put the Fundraising Access licence and the Fundraising User permission on the data-migration user, every integration user (payment processor, email, portal), and every fundraising user, through a permission set group deployed with the release. Test the payment processor's user in the pilot.

**Source:** NPC Guide, Special Access Rules on the fundraising standard objects (for example GiftTransaction, GiftDefaultDesignation, GiftTransactionDesignation) and Manage Gift Transaction Designations Action ("available in API version 59.0 and later for users in orgs where the Fundraising Access license is enabled and the Fundraising User system permission is assigned").

---

## Gotcha 8: Parallel-Run Deltas Into NPSP Still Fire Package Triggers Through TDTM

**What happens:** During a parallel run, late corrections are loaded into the NPSP org or extracted after bulk fixes. NPSP's Table-Driven Trigger Management fires package handlers on every insert and update, recalculating rollups, renaming households, and creating payments, so the source drifts while it is being reconciled.

**When it occurs:** Any bulk data operation in the NPSP org during the migration window.

**How to avoid:** Freeze the NPSP org for data changes during the final extraction. Where loads into NPSP cannot be avoided, exclude the load user through the trigger handler records (`npsp__Trigger_Handler__c`, fields `npsp__Active__c`, `npsp__Object__c`, `npsp__Class__c`, `npsp__Usernames_to_Exclude__c`) and run the rollup recalculation deliberately afterwards. UNVERIFIED (2026-10-03): the exact behaviour of `Usernames_to_Exclude__c` is documented in NPSP materials outside the fetched package source.

**Source:** NPSP source: `force-app/tdtm/objects/Trigger_Handler__c` and its fields (`Active__c`, `Asynchronous__c`, `Class__c`, `Load_Order__c`, `Object__c`, `Trigger_Action__c`, `User_Managed__c`, `Usernames_to_Exclude__c`).

---

## Gotcha 9: Grant Data Has Two Target Models, And One Gets No Future Enhancements

**What happens:** Organisations that award grants with the Outbound Funds Module (namespace `outfunds`; objects `Funding_Program__c`, `Funding_Request__c`, `Funding_Request_Role__c`, `Disbursement__c`, `Requirement__c`, `Review__c`) map requests to `IndividualApplication` because it is the object older guidance names. Spring '26 introduced a Grantmaking data model built on Application Form objects; Individual Application "won't receive future platform enhancements."

**When it occurs:** When the grants workstream reuses a mapping written before Spring '26.

**How to avoid:** Decide the grantmaking target model in the decision record. For new builds, map funding requests to the Application Form model (Applicant, Application Form, Application Form Evaluation and related objects) and record why if Individual Application is kept. Note that the Outbound Funds Module describes itself as a community-developed Open Source Commons project, so its support position differs from NPSP's. Detailed grantmaking setup is `admin/grant-management-setup`.

**Source:** NPC Guide, Chapter 2 Grantmaking Data Model ("In Spring '26 a new Grantmaking data model that uses Application Form objects was introduced"; Individual Application "won't receive future platform enhancements"; the objects unique to each model; edition box). Outbound Funds Module repository (https://github.com/SalesforceFoundation/OutboundFundsModule): `cumulusci.yml` namespace `outfunds`, repository description, and `force-app/main/default/objects`.
