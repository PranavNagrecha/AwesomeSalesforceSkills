# Gotchas — Nonprofit Cloud vs NPSP Migration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The target objects are standard objects with no `__c`, and half the mapping vocabulary is wrong

**What happens:** NPSP is a managed package, so everything in it is namespaced and suffixed — `npsp__General_Accounting_Unit__c`, `npe03__Recurring_Donation__c`. Nonprofit Cloud is native, and its objects carry
no suffix at all. The Nonprofit Cloud Developer Guide (Version 67.0, Summer '26) names them precisely:

- Fundraising: `GiftTransaction` ("a completed transaction from a gift", API 59.0+), `GiftCommitment` ("the commitment
  made by a donor", 59.0+), `GiftCommitmentSchedule` ("the schedule for fulfilling the commitment", 59.0+),
  `GiftDesignation` and `GiftTransactionDesignation` (59.0+), `GiftSoftCredit` ("the soft credit attributed to a person
  or organization for the gift transaction", 59.0+), `GiftEntry`, `GiftBatch`, `GiftRefund`, `GiftTribute` (all 59.0+),
  and later additions including `GiftAgreement` (64.0+), `GiftStewardship` (65.0+), and `GiftActuarialEntry` (65.0+).
- Program Management: `Program` ("the enrollment and disbursement of benefits in a program", 57.0+),
  `ProgramEnrollment` ("details of enrollment for benefits in a program", 57.0+), `Benefit`, `BenefitAssignment`,
  `BenefitDisbursement`, `BenefitSchedule`, `BenefitSession`, `BenefitType`, `RecurrenceSchedule` (57.0+),
  `ProgramCohort` and `ProgramCohortMember` (61.0+), `CaseProgram` (57.0+).

The single most common mapping error is `ProgramEngagement`. That is the NPSP Program Management Module's object; the
Nonprofit Cloud equivalent is **`ProgramEnrollment`**. A mapping spreadsheet built from memory will carry the NPSP name
into the target column and survive review, because both names are plausible and only one exists.

**When it occurs:** During mapping, months before anything is built. It surfaces at the first deployment, or worse, in
an integration spec handed to a payment processor.

**How to avoid:** Populate the target column of the mapping spreadsheet from the Nonprofit Cloud Developer Guide's
standard-object lists, not from recollection, and record the API version each object became available in — that column
is what tells you whether the target org can actually hold the data.

---

## Gotcha 2: Object availability is gated per object by API version, and the two modules have different edition floors

**What happens:** Nonprofit Cloud is not one release. Each object carries its own availability, and the guide states it
per object: `Program` and the Benefit family from API version 57.0, the core Fundraising objects from 59.0,
`ProgramCohort` from 61.0, `GiftAgreement` from 64.0, `GiftStewardship` from 65.0, `GratefulPersonInvolvement` from
67.0. A design that assumes "Nonprofit Cloud has it" is making a claim about a specific API version.

Editions differ between the two modules. Fundraising is documented as "Available in: Enterprise, Unlimited, and
Developer Editions." Program Management is documented as "Available in: Enterprise and Unlimited Editions" — Developer
Edition is absent from that list.

**When it occurs:** When the team spins up a Developer Edition org to prototype the program-management model and finds
the objects are not there, then loses days assuming a provisioning fault.

**How to avoid:** Check availability per object before scoping, and choose the prototype environment against the
module you are prototyping. Where an object is newer than the target org's API version, that is a sequencing
constraint on the migration plan, not a detail.

---

## Gotcha 3: Soft credits change shape, so the migration is a conversion

**What happens:** In NPSP a soft credit is a record on a package object. In Nonprofit Cloud, `GiftSoftCredit`
"represents the soft credit attributed to a person or organization for the gift transaction" and is a first-class
standard object related to `GiftTransaction`. There is also `GiftDefaultSoftCredit` (API 62.0+), which "represents the
default allocation for soft credits on gift commitment transactions that are created by a recurrence engine and
credited to constituents who influenced the commitment" — that is behaviour the target platform generates, not data you
migrate.

**When it occurs:** In the transactional phase of the migration, after constituents have loaded cleanly. The
attribution numbers do not reconcile, and because soft credits drive recognition and stewardship, the discrepancy is
visible to donors.

**How to avoid:** Treat soft credits and recurring commitments as conversions with their own reconciliation report, run
before and after, at the level fundraising actually reports on — donor, campaign, designation, and period. Determine
which soft credits the recurrence engine will generate on its own and exclude them from the load, or you will
double-count exactly the attributions the organisation cares about most.

---

## Gotcha 4: Every NPSP customisation is a dependency on a package that is not the target

**What happens:** NPSP's value is the automation layer — rollups, recurring-donation processing, household naming —
implemented as package Apex, package triggers, and package fields. Customisations built on top reference package
namespaces (`npsp__`, `npe01__`, `npe03__`, `pmdm__`). None of those namespaces exist in a Nonprofit Cloud org, so
every reference in a custom trigger, formula, validation rule, report type, or integration payload is a compile-time or
run-time break at cutover.

**When it occurs:** During the inventory, if you are lucky. During UAT, if you are not. Integrations are the worst
category, because the break is on someone else's side of the wire and shows up as a silent field mismatch rather than
an error.

**How to avoid:** Grep the entire metadata tree for the package namespaces and enumerate every hit before estimating
the migration — including formula fields, report types, list-view filters, and any external system's field mapping. The
count of namespace references is the single best predictor of effort, and it is cheap to produce on day one.

## Official Sources Used

- Nonprofit Cloud Developer Guide, Version 67.0 (Summer '26) — *Fundraising Standard Objects*: exact API names and
  per-object availability for `GiftTransaction`, `GiftCommitment`, `GiftCommitmentSchedule`, `GiftDesignation`,
  `GiftTransactionDesignation`, `GiftSoftCredit`, `GiftDefaultSoftCredit`, `GiftEntry`, `GiftBatch`, `GiftRefund`,
  `GiftTribute`, `GiftAgreement`, `GiftStewardship`, `GiftActuarialEntry`, `DonorGiftConcept`,
  `GratefulPersonInvolvement`; and the "Available in: **Enterprise**, **Unlimited**, and **Developer** Editions."
  statement.
  https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_fundraising_standard_objects.htm (verified 2026-08-14)
- Nonprofit Cloud Developer Guide, Version 67.0 — *Program Management Standard Objects*: `Program`,
  `ProgramEnrollment`, `ProgramCohort`, `ProgramCohortMember`, `Benefit`, `BenefitAssignment`, `BenefitDisbursement`,
  `BenefitSchedule`, `BenefitScheduleAssignment`, `BenefitSession`, `BenefitType`, `CaseProgram`, `RecurrenceSchedule`,
  and the "Available in: **Enterprise** and **Unlimited** Editions." statement (Developer Edition absent).
  https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_pm_standard_objects.htm (verified 2026-08-14)
- Nonprofit Cloud Developer Guide, Version 67.0 — per-object pages carrying the descriptions and "available in API
  version" statements quoted above: `GiftTransaction` (59.0), `GiftCommitment` (59.0), `GiftSoftCredit` (59.0),
  `GiftDefaultSoftCredit` (62.0), `Program` (57.0), `ProgramEnrollment` (57.0).
  https://developer.salesforce.com/docs/atlas.en-us.nonprofit_cloud.meta/nonprofit_cloud/npc_fundraising_api_objects_gifttransaction.htm (verified 2026-08-14)
