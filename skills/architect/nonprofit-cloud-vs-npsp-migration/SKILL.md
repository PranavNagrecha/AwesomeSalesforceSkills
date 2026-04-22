---
name: nonprofit-cloud-vs-npsp-migration
description: "Nonprofit Cloud vs NPSP decision and migration: choose NPSP (managed package) or Nonprofit Cloud (native), plan data migration, Account Model differences, Program Management, fundraising. NOT for nonprofit accounting (use revenue-cloud-foundation). NOT for generic Sales Cloud setup (use sales-cloud-core-setup)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Nonprofit Cloud vs NPSP Migration

Activate when choosing between NPSP (the managed-package Nonprofit Success Pack) and Nonprofit Cloud (the native platform product), or when planning an NPSP → Nonprofit Cloud migration. This is an architect decision with a long tail: the choice determines the data model, the upgrade cadence, and the integration contract for a decade.

## Before Starting

- **Understand Salesforce's direction.** Nonprofit Cloud is the forward-looking native offering. NPSP remains supported but new investment and AI features target Nonprofit Cloud.
- **Inventory current NPSP customizations.** Custom objects, triggers, and Process Builder flows depending on NPSP internals will NOT migrate automatically.
- **Classify the data.** Households vs organizations, soft credits, recurring donations, grants, program enrollments — each has a different mapping.
- **Set the clock.** A migration is 6-12 months minimum for a mid-size org; greenfield Nonprofit Cloud is months faster than bolting onto NPSP.

## Core Concepts

### NPSP (Nonprofit Success Pack)

Managed package on top of Sales Cloud. Uses `Account` (Household), `Contact`, `Opportunity` (gift), and custom objects like `npsp__General_Accounting_Unit__c`. Rich community, many AppExchange integrations.

### Nonprofit Cloud (native)

Built on Industries stack. Uses native objects: `PersonAccount` or `Person`, `Gift__c`/`GiftCommitment`, `ProgramEngagement`, `Case` for services. Industries Data Kit handles the core model. Native Einstein capabilities.

### Account models: NPSP vs Nonprofit Cloud

NPSP offers Household, One-to-One, and Individual. Nonprofit Cloud uses Person Accounts or a Person-centric model with native household relationships. Migrating means deciding how households map.

### Program Management

NPSP has Program Management Module (PMM) with `Program__c`, `Service__c`, `ProgramEngagement__c`. Nonprofit Cloud has native equivalents but the schema differs — direct field mapping is rarely 1:1.

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
7. Run a cutover rehearsal; measure downtime; document rollback.

## Review Checklist

- [ ] Nonprofit Cloud vs NPSP decision documented with rationale
- [ ] NPSP customization inventory complete
- [ ] Object-level mapping spreadsheet approved by fundraising and programs leads
- [ ] Data migration tested end-to-end with representative volume
- [ ] Integration re-points planned (payment processors, email, constituent portal)
- [ ] Reports and dashboards re-built for target model
- [ ] Training plan for development, admin, and end-users

## Salesforce-Specific Gotchas

1. **NPSP triggers cannot be disabled selectively without care.** Data loads into NPSP without disabling triggers can silently corrupt rollups.
2. **Soft credits in NPSP are a custom object; in Nonprofit Cloud they are a native relationship.** The migration requires conversion, not copy.
3. **Household ownership differs.** NPSP's `Account` Household has a Primary Contact; Nonprofit Cloud households are derived differently — update reports and automations.

## Output Artifacts

| Artifact | Description |
|---|---|
| Decision record | NPSP vs Nonprofit Cloud rationale |
| Customization inventory | NPSP extensions with migration disposition |
| Object mapping spreadsheet | Source → target field map |
| Migration runbook | Phased plan with cutover + rollback |

## Related Skills

- `architect/cross-cloud-data-deployment` — multi-cloud data handoff
- `data/nonprofit-npsp-data-model` — NPSP data-model details
- `integration/integration-pattern-selection` — fundraising integration
