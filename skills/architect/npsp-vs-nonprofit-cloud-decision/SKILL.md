---
name: npsp-vs-nonprofit-cloud-decision
description: "Use this skill when an organization must decide whether to stay on NPSP (Nonprofit Success Pack) or move to Nonprofit Cloud (NPC), evaluate the timeline for that move, and understand what the migration entails at an architectural level. Trigger keywords: NPSP vs Nonprofit Cloud, upgrade NPSP, migrate to NPC, nonprofit platform decision, NPSP end of life, Nonprofit Cloud vs NPSP comparison. NOT for implementation — does not cover post-decision NPC build, NPSP customization, or data migration execution."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
  - Reliability
triggers:
  - "should we stay on NPSP or move to Nonprofit Cloud"
  - "what is the difference between NPSP and Nonprofit Cloud"
  - "is NPSP being retired or end of lifed by Salesforce"
  - "how do we upgrade from NPSP to Nonprofit Cloud"
  - "our nonprofit is on NPSP and wants to evaluate NPC"
  - "can we migrate our existing NPSP org to Nonprofit Cloud"
  - "NPSP versus NPC feature comparison and migration timeline"
tags:
  - npsp
  - nonprofit-cloud
  - npc
  - migration
  - decision-framework
  - nonprofit
  - platform-strategy
  - data-model
  - person-accounts
  - household-accounts
inputs:
  - "Current Salesforce platform (NPSP version, installed packages, managed packages)"
  - "Organization's constituent and donation data volume"
  - "Degree of NPSP customization (custom fields, triggers, process automations)"
  - "Timeline constraints and appetite for a net-new org provisioning"
  - "Whether the org uses Program Management Module (PMM) or other add-on packages"
  - "Executive priorities — innovation roadmap vs. operational stability"
outputs:
  - "Structured go/stay decision recommendation with rationale"
  - "High-level migration readiness assessment"
  - "Key architectural risks for the recommended path"
  - "Prioritized list of discovery questions to validate the recommendation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# NPSP vs. Nonprofit Cloud Decision

Use this skill when a nonprofit organization on Salesforce must evaluate whether to remain on the Nonprofit Success Pack (NPSP) or migrate to Nonprofit Cloud (NPC), and needs a structured framework to make and justify that decision. This skill produces a decision recommendation with rationale; it does not implement the migration itself.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Current platform state:** Confirm the org is on NPSP (the open-source managed package) vs. already on Nonprofit Cloud (the Spring 2023+ native product). These are architecturally separate products — not versions of the same product.
- **Most common wrong assumption:** Practitioners and AI assistants frequently assume there is an in-place upgrade path from NPSP to Nonprofit Cloud. There is no such path. NPC requires provisioning a new Salesforce org, rebuilding configurations, and performing a formal data migration. Telling a client otherwise is incorrect.
- **Platform constraints in play:** Salesforce ended all new NPSP feature development in March 2023 when Nonprofit Cloud launched. NPSP receives only critical bug fixes and security patches. No Salesforce-announced hard end-of-life date for NPSP exists as of April 2026, but no innovation pipeline exists either.

---

## Core Concepts

### 1. NPSP Is Feature-Frozen — Not End-of-Lifed

The Nonprofit Success Pack (NPSP) is an open-source managed package that Salesforce acquired via its acquisition of the Nonprofit Starter Pack. In March 2023, Salesforce launched Nonprofit Cloud as the successor product and simultaneously stopped all new NPSP feature development. NPSP remains installable and supported with critical security and bug patches, but no new capabilities will be added. Organizations on NPSP are trading stability for an increasingly widening feature gap against NPC.

The absence of a hard EOL date does not mean NPSP is safe indefinitely. Managed package support lifecycles can be affected by Salesforce API version deprecations, platform changes, and third-party dependency updates. Organizations should treat NPSP as a platform in slow wind-down, not as a stable long-term foundation.

### 2. Nonprofit Cloud Is a Different Data Model — Not an Upgrade

Nonprofit Cloud is not a newer version of NPSP. It is a separate Salesforce product built on different foundational objects:

- **NPSP** uses the **Household Account model** — individual Contacts are associated with a Household Account (a standard Account record typed as Household). Giving is tracked on Opportunity records associated with Accounts or Contacts via NPSP custom objects (Allocations, General Accounting Units, etc.).
- **Nonprofit Cloud** uses **Person Accounts by default** — each constituent is a single Person Account record that merges Contact and Account data. NPC introduces new first-class objects: Fundraising (Gift Transactions, Gift Commitments, Designations), Program Management (Programs, Benefits, Benefit Assignments), and Case Management.

This data model divergence is the primary reason no in-place migration path exists. Converting a Household Account org to a Person Account org requires a full data re-architecture, not a configuration change.

### 3. Migration Requires a Net-New Org and Formal Data Migration

There is no Salesforce-provided tool to convert an existing NPSP org into an NPC org. The migration path is:

1. Provision a new Salesforce org with NPC licenses
2. Rebuild all configurations (page layouts, record types, flows, custom objects, integrations) in the new org
3. Extract constituent, donation, program, and relationship data from the NPSP org
4. Transform data to match NPC's object model (e.g., convert Household Contacts to Person Accounts)
5. Load data into the new NPC org using ETL tooling (Data Loader, MuleSoft, Informatica, etc.)
6. Validate data integrity and run parallel operations during cutover

This is a full reimplementation project, not a configuration migration. Organizations should budget 6–18 months depending on complexity and data volume.

### 4. Feature Gap and When NPC Wins

NPC offers capabilities unavailable in NPSP:
- **Gift Entry Manager** — structured batch gift entry with matching gift support
- **Elevate** payment processing (available in both but deepening NPC integration)
- **Actionable Intelligence and Einstein features** built natively for nonprofit use cases
- **Program Management** and **Case Management** as first-class objects (replacing the add-on Program Management Module in NPSP)
- Native Salesforce Flow integration without NPSP trigger conflicts
- **Salesforce Grantmaking** (for foundations) available only on NPC

Organizations that need any of these capabilities have no path to obtain them on NPSP.

---

## Common Patterns

### Pattern 1: The "Stay on NPSP" Decision

**When to use:** Organization has deep NPSP customizations, is operationally stable, has no immediate need for NPC-exclusive features, and has limited implementation budget or internal change capacity.

**How it works:**
- Audit current NPSP customizations and integrations to confirm they remain supportable
- Document which NPC features are materially absent from NPSP (if none are needed, the move has low urgency)
- Establish a review trigger: define specific conditions that would force a re-evaluation (e.g., Salesforce announces an EOL date, a critical integration breaks, a new feature requirement emerges that only NPC can serve)
- Ensure a data export and backup strategy is in place in case forced migration becomes necessary later

**Why not move now:** A migration with no business driver creates disruption, cost, and risk without corresponding value. Premature migration is an anti-pattern. The stay decision is valid as long as NPSP meets operational needs.

### Pattern 2: The "Move to NPC" Decision

**When to use:** Organization needs a NPC-exclusive feature (Gift Entry Manager, native Program Management, Grantmaking, deeper AI integration), is undergoing a major org consolidation, or is a new-to-Salesforce nonprofit that has not yet launched on NPSP.

**How it works:**
- Inventory all NPSP customizations: custom fields, Apex triggers, Process Builders, Flows, installed packages
- Document all data model dependencies: Household Account relationships, NPSP rollup fields (CRLP), General Accounting Units, Allocations
- Identify integration points: payment processors, marketing automation, volunteer management tools
- Engage a Salesforce Nonprofit implementation partner with NPC certification
- Plan a phased migration: pilot with a data subset, validate in sandbox, then run production cutover

**Why not wait:** Organizations that delay migration accumulate more NPSP-specific technical debt, making the eventual migration more expensive. New Salesforce investments (AI features, Einstein, Agentforce for Nonprofits) are being built exclusively on NPC.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New nonprofit organization evaluating Salesforce for the first time | Implement Nonprofit Cloud directly | No migration cost; immediate access to full NPC innovation roadmap |
| Existing NPSP org, stable, no NPC-exclusive feature need, limited budget | Stay on NPSP with a formal re-evaluation trigger | No business driver for disruptive migration; NPSP still receives security patches |
| Existing NPSP org that needs Gift Entry Manager, native Program Management, or Grantmaking | Plan migration to NPC | Required features are NPC-exclusive; NPSP will never receive them |
| Existing NPSP org undergoing an org consolidation or CRM re-platform | Consolidate onto NPC | Migration is already required; NPC is the correct destination for a net-new build |
| Existing NPSP org heavily customized with Apex, CRLP rollups, and third-party packages | Conduct migration readiness assessment before deciding | Complexity must be quantified; migration is possible but expensive — ROI analysis required |
| NPSP org with PMM (Program Management Module) installed | Evaluate NPC Program Management fit carefully | NPC's native Program Management replaces PMM but has feature parity gaps; validate before committing |
| NPSP org using Elevate for payment processing | NPC migration preferred long-term | Salesforce is deepening Elevate–NPC integration; NPSP Elevate support will not evolve |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the current platform.** Verify the org is on NPSP (installed managed package, API name `npsp`) and not already on Nonprofit Cloud. Check Setup > Installed Packages. This step prevents recommendations based on a wrong premise.
2. **Assess NPC-exclusive feature needs.** Produce a feature requirements list from stakeholder interviews. Map each requirement to NPSP vs. NPC availability. If any requirement is NPC-exclusive, the migration case exists regardless of other factors.
3. **Inventory NPSP customizations and integrations.** Document custom fields, Apex triggers, Process Builders, active Flows, installed packages, and external integrations. Score complexity on a low/medium/high scale. High-complexity orgs need a professional migration assessment before a go/stay decision is finalized.
4. **Assess data volume and model complexity.** Count Contacts, Household Accounts, Opportunities, Allocations, and Recurring Donations. Map out relationship structures. Large data volumes and complex relationship hierarchies extend migration timelines significantly.
5. **Produce the decision recommendation.** Use the Decision Guidance table above. Document the primary driver for the recommendation and the top three risks of the recommended path. If uncertainty is high, recommend a formal migration readiness assessment as the next step rather than a final go/stay.
6. **Define next steps for the chosen path.** For Stay: document the re-evaluation triggers. For Move: outline a high-level migration project structure (discovery, sandbox build, data migration, UAT, cutover) and identify required partner or internal resources.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed the org is on NPSP, not already on NPC
- [ ] Verified whether any required features are NPC-exclusive
- [ ] Documented current NPSP customization complexity level
- [ ] Decision recommendation includes explicit rationale (not just a conclusion)
- [ ] Recommendation correctly states that NPC requires a net-new org — no in-place upgrade
- [ ] If recommending migration, a high-level project structure or partner engagement is noted
- [ ] If recommending staying, a re-evaluation trigger is defined

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **No in-place upgrade path exists** — There is no Salesforce tool or process to convert an NPSP org to an NPC org. Any guidance suggesting otherwise (including AI-generated suggestions) is incorrect. Migration always requires provisioning a net-new org with NPC licenses and performing a full data migration.
2. **NPSP and NPC use different default Account models** — NPSP defaults to Household Accounts (standard Accounts typed as Household); NPC defaults to Person Accounts. These are mutually exclusive org-level settings. An org with Person Accounts enabled cannot use the NPSP Household model without serious conflicts, and vice versa.
3. **NPSP is feature-frozen, not end-of-lifed** — No hard Salesforce-announced EOL date exists for NPSP as of April 2026. However, no new features will ever be added. Practitioners who tell clients "NPSP is still being actively developed" are incorrect. The correct statement is: NPSP receives security and critical bug patches only.
4. **PMM (Program Management Module) does not map 1:1 to NPC Program Management** — Organizations running the NPSP Program Management Module must validate NPC's native Program Management against their specific use cases before committing to migration. Feature parity is not guaranteed, and configuration differences are significant.
5. **CRLP rollup fields do not migrate automatically** — NPSP uses Customizable Rollup Summaries (CRLP) to calculate total giving, last gift date, and similar metrics on Accounts and Contacts. These rollup definitions do not transfer to NPC. Each must be rebuilt using NPC's native rollup framework or recalculated post-migration.
6. **Recurring Donation records require data model transformation** — NPSP Recurring Donations are managed package custom objects. NPC uses Gift Commitments as the native recurring giving object. A data migration must transform each Recurring Donation record and its installment Opportunities to the NPC Gift Commitment and Gift Transaction model.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Decision Recommendation | Go/Stay recommendation with primary driver, top risks, and immediate next steps |
| Feature Gap Analysis | Table mapping the organization's feature requirements to NPSP vs. NPC availability |
| Customization Inventory | List of NPSP customizations that would require migration effort, scored by complexity |
| Migration Readiness Score | Low/Medium/High assessment of migration complexity based on data volume and customization depth |

---

## Related Skills

- `admin/npsp-household-accounts` — Use after a Stay decision to configure NPSP Household Account behavior correctly within an NPSP org
- `admin/recurring-donations-setup` — Use for NPSP Recurring Donation configuration; relevant to migration planning to understand what data must be transformed
