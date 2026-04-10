---
name: multi-bu-marketing-architecture
description: "Use this skill when designing or evaluating a Marketing Cloud Engagement multi-Business-Unit hierarchy — covering Enterprise 2.0 parent/child BU structure, Shared Data Extensions, cross-BU user provisioning, and data segregation governance. NOT for single-BU setup, Marketing Cloud Account Engagement (Pardot) standalone configuration, or CRM-side campaign hierarchy design."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Scalability
triggers:
  - "We need to support multiple brands or regions in Marketing Cloud — how should we structure our Business Units?"
  - "Our child BUs need access to a suppression list managed by the parent — how do we share a Data Extension across BUs?"
  - "Users are set up in the parent BU but cannot see anything in child BUs — do roles flow down automatically?"
  - "We are planning deeply nested child Business Units for each country market — is that the right approach?"
  - "How do we enforce data segregation between two brands that share a single Marketing Cloud instance?"
tags:
  - marketing-cloud
  - multi-bu
  - enterprise-2-0
  - business-units
  - shared-data-extensions
  - data-segregation
  - user-provisioning
  - governance
inputs:
  - Number of brands, regions, or markets that need logical separation
  - Data sharing requirements between BUs (suppression lists, shared audiences, content)
  - User and role requirements per BU (dedicated admins vs. central team)
  - Regulatory or contractual data residency or segregation requirements
  - Existing org edition (Enterprise 2.0 vs. legacy)
outputs:
  - BU hierarchy recommendation with rationale
  - Shared Data Extension folder permission map
  - User provisioning and role assignment plan per BU
  - Data segregation governance checklist
  - Risk register for hierarchy anti-patterns
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Multi-BU Marketing Architecture

This skill activates when a practitioner needs to design or govern a Marketing Cloud Engagement multi-Business-Unit implementation. It covers Enterprise 2.0 parent/child hierarchy setup, cross-BU data sharing via Shared Data Extensions, user provisioning rules, and governance patterns that prevent data leakage or operational complexity from escalating.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the Marketing Cloud org is on the **Enterprise 2.0** edition — only Enterprise 2.0 supports a Parent BU with unlimited Child BUs. Legacy Enterprise has a fixed child limit and different sharing mechanics.
- Identify whether the requirement is for **data isolation** (brands must never share data), **selective sharing** (some assets shared, others not), or **full sharing** (all BUs operate as one logical unit with separate sending identities).
- Determine how many layers of hierarchy are genuinely required. Deeply nested hierarchies (parent → regional BU → country BU → brand BU) are cautioned against: admin complexity compounds at each level and send attribution reporting becomes difficult to trace accurately.
- Understand the user management model: will each BU have a dedicated local admin, or will a central team manage all BUs from the parent? This affects whether roles need to be assigned explicitly at each child level.

---

## Core Concepts

### Enterprise 2.0 Parent BU and Child BU Structure

Marketing Cloud Engagement Enterprise 2.0 organizations have exactly one **Parent Business Unit** (also called the Enterprise BU or top-level account). The Parent BU is the administrative root: it controls account-wide settings, sends From addresses, and acts as the container for all Child BUs.

Child BUs are fully operational marketing units — each has its own Data Extensions, email sends, subscriber lists, automations, and sender profiles. Child BUs are scoped by default: a Data Extension created in a Child BU is visible only within that Child BU. There is no automatic sharing of assets between siblings or from child to parent.

The Parent BU can create and manage an unlimited number of Child BUs. Salesforce does not publish a hard ceiling on Child BU count, but operational overhead grows with each BU added, particularly around user administration and reporting.

### Shared Data Extensions and Folder-Level Permissions

The primary mechanism for cross-BU data sharing in Enterprise 2.0 is the **Shared Data Extension**, which lives in the Parent BU. By itself, placing a Data Extension in the Parent BU does not make it accessible to Child BUs. Access is configured explicitly:

1. In the Parent BU, create or move the Data Extension into a folder designated for sharing.
2. Navigate to the folder's properties and configure **Shared Data Extension Permissions** — select which Child BUs are granted read or read/write access to that folder.
3. Only Child BUs explicitly listed in the folder permissions can query or send against those Data Extensions.

This means a suppression list, a global master subscriber record, or a shared audience segment can be maintained centrally in the Parent BU and surfaced selectively to the Child BUs that need it, without exposing it to the entire hierarchy.

Shared DEs appear in the Child BU's Data Extensions interface under a "Shared" folder. Child BU users cannot modify folder permissions — that is a Parent BU admin function.

### User Provisioning and Role Non-Cascading

User accounts in Marketing Cloud are provisioned per Business Unit. A user who exists in the Parent BU has **no automatic access to any Child BU**. Role assignments do not cascade downward. If a central admin must manage five Child BUs, they must be explicitly provisioned in each of those five BUs and have a role assigned at each level.

This is a frequent source of support escalations: a newly created Child BU appears empty of users even though the parent admin team is fully staffed. The resolution is always explicit provisioning — there is no "inherit parent roles" toggle.

Roles available at the Child BU level mirror the standard Marketing Cloud role hierarchy (Administrator, Marketing Cloud Administrator, Marketing Cloud Viewer, etc.). Custom roles created in the Parent BU can be applied at the Child BU level, but the assignment itself must be made explicitly for each BU.

Marketing Cloud Account Engagement (Pardot) has its own user management system separate from Marketing Cloud Engagement BU provisioning and is out of scope for this skill.

### Data Segregation Between Business Units

BU-scoping of Data Extensions, Automations, and Content is the primary data segregation mechanism. Because DEs are BU-local by default, two brands in separate Child BUs cannot read each other's subscriber data even if they share the same Marketing Cloud org. This is enforced at the platform level — there is no cross-BU SQL query path for a journey or automation running in one Child BU to access a DE in another Child BU unless a Shared DE has been configured.

For organizations with strict regulatory requirements (GDPR data residency, contractual brand separation), BU-level segregation is generally sufficient but must be confirmed against specific compliance requirements. Marketing Cloud does not offer tenant-level data isolation within a single org — if true data isolation at the infrastructure level is needed, separate Marketing Cloud orgs are required.

### Governance Patterns for Multi-BU Organizations

Successful multi-BU implementations establish explicit governance early:

- **Naming conventions**: BU names, DE folder names, and sender profile names should follow a consistent taxonomy that identifies the owning brand and region at a glance.
- **Shared asset register**: Maintain documentation (or a dedicated Parent BU folder) of which DEs are shared, which Child BUs have access, and who is the data steward.
- **Centralized suppression management**: Global unsubscribe and suppression lists belong in the Parent BU and should be shared to all Child BUs that send to the same subscriber population.
- **BU creation checklist**: Each new Child BU should go through a provisioning runbook covering: sender authentication (SAP, DKIM, Reply Mail Management), reply mail setup, role assignment for the local team, and initial shared DE permissions.
- **Hierarchy depth limit**: Keep hierarchies flat — ideally a single Parent + one tier of Child BUs. A second tier (grandchild BUs) multiplies admin surface area and complicates send attribution in Analytics Builder reports, which aggregate by BU and do not automatically roll up grandchild sends to the grandparent.

---

## Common Patterns

### Centralized Suppression with Selective Child BU Access

**When to use:** A global brand with regional Child BUs needs a single master suppression/unsubscribe list to ensure that an opt-out in one region is honored by all sending BUs.

**How it works:**
1. Create the suppression Data Extension in the Parent BU.
2. Configure the containing folder's Shared DE Permissions to grant read access to all relevant Child BUs.
3. In each Child BU's Email Studio or Journey Builder send activities, reference the Shared DE as the suppression list.
4. Opt-out processing writes back to the Parent BU's All Subscribers list; the Shared DE is refreshed from that list via a scheduled Automation in the Parent BU.

**Why not the alternative:** Maintaining separate suppression lists per Child BU creates the risk of a global opt-out being honored in one BU but not others, creating regulatory and reputational exposure.

### Strict Brand Data Segregation

**When to use:** Two brands share a Marketing Cloud org but have separate data ownership requirements — neither brand's subscriber data, send history, or suppression data should be visible to the other.

**How it works:**
1. Assign each brand its own Child BU.
2. Do not configure any Shared DE permissions between the two brand BUs.
3. Provision separate user accounts for each brand's team — do not give Brand A's team access to Brand B's Child BU.
4. Configure separate SAP/DKIM and Reply Mail Management per Child BU so sending identities remain distinct.
5. For analytics, run reports scoped to each Child BU independently. Do not use Parent BU consolidated reports if brand data must not be co-mingled in reporting exports.

**Why not the alternative:** Attempting to separate brands within a single BU using folder permissions and user role restrictions is fragile — a misconfigured role can expose data across brands with no platform-level enforcement barrier.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Multiple brands need full data isolation | Separate Child BUs, no cross-BU Shared DEs | Platform-enforced BU scoping provides the segregation boundary |
| Global suppression list needed across all BUs | Shared DE in Parent BU, read permission granted to all Child BUs | Centralizes opt-out truth; changes propagate without duplicating data |
| Central admin team managing all Child BUs | Explicit provisioning at each Child BU with appropriate role | Roles do not cascade; manual assignment is the only mechanism |
| Country-level sub-regions within a region | Evaluate if a single regional Child BU suffices; avoid grandchild BUs | Nested hierarchies increase admin overhead and complicate attribution |
| Brand teams need their own admin capability | Provision a Marketing Cloud Administrator role at the Child BU level | Child BU Administrators can manage their BU without Parent BU access |
| Regulatory requirement for infrastructure isolation | Separate Marketing Cloud orgs | Multi-BU within a single org does not provide infrastructure-level isolation |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org edition and hierarchy requirements**: Verify the org is Enterprise 2.0. Document the number of BUs needed, their relationship (brand, region, market), and whether any require strict data isolation or selective sharing.
2. **Design the BU hierarchy**: Map out Parent BU and Child BUs. Resist adding a second tier unless there is a concrete operational reason — document the reason if a nested hierarchy is chosen and note the attribution reporting trade-off.
3. **Identify shared assets**: Catalogue which Data Extensions (suppression lists, seed lists, shared audiences) must be accessible across BUs. Plan their location in the Parent BU and which Child BUs require read or read/write access.
4. **Configure Shared DE folder permissions**: In the Parent BU, create or designate a shared folder, move shared DEs into it, and configure folder-level permissions for each Child BU explicitly.
5. **Plan user provisioning**: For each Child BU, list the users who need access and the role they require. Create a provisioning runbook covering role assignment at each BU level — do not assume inheritance.
6. **Configure per-BU sender authentication**: Set up SAP, DKIM, and Reply Mail Management for each Child BU. Confirm IP assignment aligns with sending volume expectations per BU.
7. **Document and govern**: Produce a shared asset register, naming convention guide, and BU creation checklist. Establish who owns Parent BU admin and who owns each Child BU admin to prevent configuration drift.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org confirmed as Enterprise 2.0; hierarchy depth is one tier (Parent + Children) unless a specific second-tier need is documented
- [ ] Each Child BU has dedicated SAP/DKIM and Reply Mail Management configured
- [ ] Shared DE folder permissions are set explicitly per Child BU — no assumption of automatic sharing
- [ ] Users provisioned with explicit role assignment in every Child BU they need to access
- [ ] Global suppression list (if applicable) is in Parent BU as a Shared DE accessible to all sending Child BUs
- [ ] Brand or market data that must remain segregated is confirmed to have no cross-BU Shared DE permissions
- [ ] Naming conventions and a shared asset register are documented and agreed

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Roles do not cascade from Parent BU to Child BUs** — A user provisioned as an Administrator in the Parent BU has zero visibility into any Child BU unless explicitly provisioned there. This is the most common onboarding mistake in multi-BU implementations and is not surfaced as a warning during BU creation.
2. **Deeply nested hierarchies break send attribution** — Analytics Builder reports aggregate send data by BU. Grandchild BU sends do not automatically roll up to the grandparent in standard reports, making cross-hierarchy performance comparison difficult without custom SQL Activity or third-party BI tooling.
3. **Shared DEs require explicit folder-level permission — placing a DE in the Parent BU alone is not enough** — A Data Extension in the Parent BU root or an unshared folder is not visible to any Child BU. The sharing mechanism is the folder's permission configuration, not the DE's location alone. This causes confusion because the UI does not warn when a "shared" DE is not actually reachable from child accounts.
4. **All Subscribers list is org-wide but BU sends are scoped** — The All Subscribers list at the Enterprise level tracks subscriber status across the org, but each Child BU has its own subscriber count and status record. An unsubscribe processed in one Child BU will suppress future sends from that BU but may not automatically suppress sends in sibling BUs unless a global suppression Data Extension is configured and referenced.
5. **SAP and IP assignment are per-BU** — A shared IP pool at the Parent BU level does not automatically apply to new Child BUs. Each Child BU must have its sender authentication package configured individually, and IP warming may need to be repeated if a Child BU is new and has its own IP assignment.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| BU hierarchy diagram | Visual map of Parent and Child BUs with sending identities and ownership |
| Shared DE permission matrix | Table of shared DEs, owning BU, and which Child BUs have read vs. read/write access |
| User provisioning plan | Per-BU list of users, roles, and provisioning owner |
| Data segregation checklist | Confirmation that regulated or brand-separated data has no unintended cross-BU sharing |
| BU creation runbook | Step-by-step checklist for onboarding new Child BUs consistently |

---

## Related Skills

- `marketing-data-architecture` — Use alongside this skill when designing the Data Extension schema and folder structure within each BU
- `marketing-consent-architecture` — Use when determining how opt-outs and consent records flow across BUs and back to CRM
