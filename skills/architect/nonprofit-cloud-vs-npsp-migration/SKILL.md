---
name: nonprofit-cloud-vs-npsp-migration
description: "Nonprofit Cloud vs NPSP decision and migration: choose NPSP (managed package) or Nonprofit Cloud (native), plan data migration, Account Model differences, Program Management, fundraising. NOT for the go/stay decision alone, with no migration to plan - use architect/npsp-vs-nonprofit-cloud-decision. NOT for designing the NPC module and platform architecture - use architect/nonprofit-platform-architecture."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Security
  - Reliability
tags:
  - nonprofit-cloud
  - npsp
  - fundraising
  - program-management
  - account-model
  - migration
triggers:
  - "should we use nonprofit cloud or npsp for our salesforce implementation"
  - "how do we migrate from npsp to nonprofit cloud"
  - "nonprofit cloud account model household vs one-to-one"
  - "npsp contact to nonprofit cloud data migration plan"
  - "nonprofit cloud program management versus npsp program"
  - "fundraising data model nonprofit cloud decision"
  - "nonprofit cloud vs npsp migration decision"
  - "map our NPSP soft credits, recurring donations and households to Nonprofit Cloud objects"
  - "plan the cutover from NPSP to Nonprofit Cloud without breaking recurring gifts"
inputs:
  - Current state (greenfield, on NPSP, or on legacy Nonprofit Success Pack)
  - Scope of nonprofit capability needed (fundraising, programs, grants, volunteers)
  - Integration footprint (payment processors, payroll, accounting)
  - Data volume (constituents, gifts, grants, households)
outputs:
  - Nonprofit Cloud vs NPSP recommendation with rationale
  - Data model mapping (NPSP objects → Nonprofit Cloud objects)
  - Migration phasing and data conversion plan
  - Readiness checklist and risk register
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Nonprofit Cloud vs NPSP Migration

Activate when choosing between NPSP (the managed-package Nonprofit Success Pack) and Nonprofit Cloud (the native platform product), or when planning an NPSP → Nonprofit Cloud migration. This is an architect decision with a long tail: the choice determines the data model, the upgrade cadence, and the integration contract for a decade.

## Before Starting

- **Understand Salesforce's direction.** Nonprofit Cloud is the forward-looking native offering. NPSP remains supported but new investment and AI features target Nonprofit Cloud. UNVERIFIED (2026-10-03): the investment statement comes from Salesforce marketing and Help pages, which do not fetch; the NPC Guide documents only what Nonprofit Cloud contains.
- **Inventory current NPSP customizations.** Custom objects, triggers, and Process Builder flows depending on NPSP internals will NOT migrate automatically.
- **Classify the data.** Households vs organizations, soft credits, recurring donations, grants, program enrollments — each has a different mapping.
- **Set the clock.** A migration is 6-12 months minimum for a mid-size org; greenfield Nonprofit Cloud is months faster than bolting onto NPSP.

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which NPSP modules and add-ons are installed: Recurring Donations, Allocations, Customizable Rollups, PMM, Outbound Funds?" | Each package namespace is rework, and each module maps to a different target model (Gotchas 4, 9) | A namespace inventory with counts per metadata type | An estimate built on the customisation layer, not on record counts |
| "How do you report households today, and who is the primary contact used for?" | Households become `PartyRelationshipGroup` records with no primary-contact field (Gotcha 5) | A household representation rule and the reports that depend on it | Household reports and salutations rebuilt in the pilot, not after cutover |
| "Which totals do fundraisers trust: lifetime giving, last gift, soft-credit totals?" | Rollups are rebuilt as Record Rollup Definitions, and soft credits are converted (Gotchas 3, 6) | A reconciliation list by donor, campaign, designation, and period | Fundraising signs off totals that match, so donor recognition does not change at go-live |
| "What edition and API version will the target org run, and where will you prototype Program Management?" | Objects arrive per API version, and Program Management is not in Developer Edition (Gotcha 2) | The edition, the API version, and a pilot sandbox on that edition | No lost week prototyping in an org that cannot hold the objects |
| "Which users and systems touch gifts: payment processor, email, portal, finance?" | Fundraising objects need the Fundraising Access licence and Fundraising User permission (Gotcha 7) | A list of integration users and their permission set groups | Integrations work on cutover day instead of failing on object access |
| "Can the NPSP org be frozen for data changes during the final extraction?" | Package triggers keep changing data while it is reconciled (Gotcha 8) | A freeze window and a rule for unavoidable loads | A reconciliation baseline that holds still |

What proper configuration adds over "just moving the data": a mapping whose target names exist, totals that reconcile before fundraising relies on them, and integrations that keep taking gifts through cutover.

## Core Concepts

### NPSP (Nonprofit Success Pack)

Managed package on top of Sales Cloud. Uses `Account` (Household), `Contact`, `Opportunity` (gift), and custom objects like `npsp__General_Accounting_Unit__c`, `npsp__Allocation__c`, `npsp__Partial_Soft_Credit__c`, and `npe03__Recurring_Donation__c` (names from the Salesforce.org NPSP package source). Rich community, many AppExchange integrations.

### Nonprofit Cloud (native)

Built on Industries stack. Uses native standard objects with no `__c` suffix: `GiftTransaction`, `GiftCommitment`, `GiftCommitmentSchedule`, `GiftSoftCredit`, and `GiftDesignation` for fundraising; `Program`, `ProgramEnrollment`, and the `Benefit` family for programs; `PartyRelationshipGroup` with `AccountContactRelation` for households; `CarePlan` and `Case` for services. (Corrected: the earlier text named `Gift__c` and `ProgramEngagement`, which are not Nonprofit Cloud objects; see `references/gotchas.md` Gotcha 1.) UNVERIFIED (2026-10-03): the "Industries Data Kit" name and the Person Account prerequisite are not stated in the NPC Guide; its field descriptions do refer to person accounts for individual donors.

### Account models: NPSP vs Nonprofit Cloud

NPSP offers Household, One-to-One, and Individual (UNVERIFIED (2026-10-03): option names from NPSP documentation; the setting lives on `npe01__Contacts_And_Orgs_Settings__c`). Nonprofit Cloud uses a person-centric model with households as `PartyRelationshipGroup` records mastered by an Account. Migrating means deciding how households map (Gotcha 5).

### Program Management

NPSP has Program Management Module (PMM, namespace `pmdm`) with `pmdm__Program__c`, `pmdm__Service__c`, `pmdm__ProgramEngagement__c`, and `pmdm__ServiceDelivery__c`. Nonprofit Cloud has native equivalents (`Program`, `ProgramEnrollment`, `Benefit`, `BenefitAssignment`, `BenefitDisbursement`) but the schema differs: direct field mapping is rarely 1:1.

## Common Patterns

### Pattern: Greenfield — start on Nonprofit Cloud

New implementations default to Nonprofit Cloud. Use the Nonprofit Cloud Data Kit, set up the Person + Household model on day one. Avoid NPSP unless a specific AppExchange integration is NPSP-only.

### Pattern: NPSP in place, augment with Nonprofit Cloud capabilities

Keep NPSP as the transactional system. Use Nonprofit Cloud features (Intelligent Needs Assessment, Care Plans) only in the Service Cloud portion of the org. Pros: no migration. Cons: two data models.

### Pattern: Phased NPSP → Nonprofit Cloud migration

Phase 1: inventory NPSP usage. Phase 2: greenfield Nonprofit Cloud in a sandbox, map objects. Phase 3: data migration of constituents, then gifts, then history. Phase 4: flip fundraising workflows. Phase 5: retire NPSP. 9-18 month program for a large nonprofit.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Greenfield nonprofit, no NPSP | Nonprofit Cloud | Forward-looking, native |
| NPSP with heavy customization, low change budget | Stay on NPSP | Migration risk exceeds value |
| NPSP with limited customization, growth plans | Plan NPSP → Nonprofit Cloud | Future-proof the investment |
| Need Einstein / AI fundraising features | Nonprofit Cloud | NPSP has limited AI integration |
| Global multi-country deployment | Evaluate Nonprofit Cloud carefully | Localization coverage varies |

## Recommended Workflow

1. Classify the organization: greenfield, on-NPSP-and-stable, or on-NPSP-and-migrating.
2. Inventory NPSP customizations if applicable: triggers, validation rules, custom objects, Process Builder, integrations.
3. Map NPSP objects to Nonprofit Cloud equivalents in a spreadsheet with gaps flagged.
4. Decide household representation (Person + Account, Person Account, or retained NPSP Household).
5. Plan data migration: lead objects (Contacts, Accounts), transactional (Opportunities/Gifts), history (soft credits, recurring).
6. Build a pilot in a sandbox with 1,000 representative constituents; validate reports and dashboards.
7. Run a cutover rehearsal; measure downtime; document rollback. Record the outcome in a decision record with its release manifest (`references/examples.md`, Example 3).

## Review Checklist

- [ ] Nonprofit Cloud vs NPSP decision documented with rationale
- [ ] NPSP customization inventory complete
- [ ] Object-level mapping spreadsheet approved by fundraising and programs leads
- [ ] Data migration tested end-to-end with representative volume
- [ ] Integration re-points planned (payment processors, email, constituent portal)
- [ ] Reports and dashboards re-built for target model
- [ ] Training plan for development, admin, and end-users

## Salesforce-Specific Gotchas

The full list with sources is in `references/gotchas.md`. The three that most often derail a plan:

| Gotcha | Consequence |
|---|---|
| NPSP triggers fire on every load through TDTM (Gotcha 8) | Loads without handling `npsp__Trigger_Handler__c` silently change rollups during reconciliation |
| Soft credits are converted, not copied (Gotcha 3) | Two NPSP objects become one `GiftSoftCredit` object with a restricted `Role` picklist (corrected: it is a standard object, not "a native relationship") |
| Households change shape (Gotcha 5) | `PartyRelationshipGroup` has no primary-contact field, so household reports and automation must be rebuilt |

## Output Artifacts

| Artifact | Description |
|---|---|
| Decision record | NPSP vs Nonprofit Cloud rationale |
| Customization inventory | NPSP extensions with migration disposition |
| Object mapping spreadsheet | Source → target field map |
| Migration runbook | Phased plan with cutover + rollback |

## Related Skills

- `architect/cross-cloud-data-deployment` — multi-cloud data handoff
- `data/npsp-data-model`: NPSP data-model details (the earlier `data/nonprofit-npsp-data-model` path does not exist)
- `admin/grant-management-setup`: grantmaking objects once the target model is chosen
- `architect/npsp-vs-nonprofit-cloud-decision`: the go/stay decision without a migration plan
- `architect/fundraising-integration-patterns`: fundraising integration (the earlier `integration/integration-pattern-selection` path does not exist; the general selector is `admin/integration-pattern-selection`)
