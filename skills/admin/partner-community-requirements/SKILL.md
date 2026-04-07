---
name: partner-community-requirements
description: "Use this skill to define and validate the requirements for a Salesforce Partner Relationship Management (PRM) implementation: deal registration flows, lead distribution models, partner tier hierarchies, MDF budget tracking, and co-marketing content entitlement. Trigger keywords: partner community requirements, PRM deal registration setup, channel partner portal requirements, lead distribution partner, partner tier management, MDF tracking, co-marketing entitlement. NOT for partner portal technical configuration (Experience Cloud site builder, Visualforce pages, LWC development). NOT for partner account management (account hierarchy or channel account teams)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "partner community requirements for deal registration and lead distribution"
  - "PRM deal registration setup with approval flow and opportunity conversion"
  - "channel partner portal requirements — tier management, MDF, co-marketing assets"
  - "lead distribution to partners using assignment rules"
  - "partner tier management Gold Silver Bronze feature access"
tags:
  - partner-community
  - prm
  - deal-registration
  - lead-distribution
  - partner-tiers
  - mdf
  - co-marketing
  - experience-cloud
inputs:
  - "Number and types of partner tiers (e.g., Gold / Silver / Bronze)"
  - "Deal registration business rules — who can register, approval chain, duplicate prevention"
  - "Lead distribution criteria — geography, product line, partner tier, capacity"
  - "MDF budget allocation model — whether tracked in Salesforce or external system"
  - "Co-marketing asset entitlement rules per tier"
  - "Existing Experience Cloud org edition and license inventory"
outputs:
  - "PRM requirements document covering license model, tier hierarchy, deal registration flow, lead distribution rules"
  - "Partner tier decision matrix with feature access and MDF eligibility per tier"
  - "Deal registration approval workflow specification"
  - "Lead distribution assignment rule specification"
  - "Review checklist confirming configuration readiness before build"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Partner Community Requirements

Use this skill when a project needs to define the functional and configuration requirements for a Salesforce PRM implementation built on Experience Cloud. It covers the full requirements surface: license selection, partner tier hierarchy, deal registration approval flow, lead distribution assignment rules, MDF budget tracking, and co-marketing content entitlement per tier.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org has Partner Community or Partner Community Plus licenses. Customer Community licenses do not support deal registration or PRM features — this is the single most common scoping error.
- Establish the partner tier model upfront (names, count, promotion/demotion criteria). Tier drives sharing rules, feature access, MDF eligibility, and content entitlement — retrofitting tiers after build is expensive.
- Clarify whether deal registration is gated by a formal approval process and who approves (channel manager, regional VP, automated). Approval chain length directly affects flow design.
- Understand whether MDF budgets will live in Salesforce custom objects or in an external finance system. In-Salesforce tracking requires custom object design before PRM build begins.
- Determine the lead distribution model: push (Salesforce assigns leads to partners) vs. pull (partners claim leads from a pool). Each model uses different configuration primitives.

---

## Core Concepts

### Partner Central Template and License Requirements

PRM is delivered through the Partner Central Experience Cloud template. The site must use either:

- **Partner Community license** — member-based pricing, includes access to deal registration, lead distribution, and MDF features.
- **Partner Community Plus license** — adds CRM-level record access (more sharing rule flexibility, reports, dashboards). Required when partners need deep pipeline visibility.

Customer Community and Customer Community Plus licenses do not unlock PRM-specific features. Assigning the wrong license results in silent feature unavailability rather than clear errors.

Partner users are Person Contacts with `IsPartner = true` on their Account. The partner Account must have the Partner Account checkbox enabled before Experience Cloud user creation.

### Deal Registration Flow: Lead → Approval → Opportunity

Deal registration in Partner Central follows a defined object lifecycle:

1. Partner submits a deal registration record (backed by the `Lead` object in standard PRM, or a custom object in some implementations).
2. The submitted Lead enters an approval process. The approval process routes to the channel manager or an automated queue based on criteria (territory, deal size, product).
3. On approval, the Lead is converted to an Opportunity. The partner is stamped on the Opportunity via a lookup to the partner Account and tracked through the sales cycle.
4. On rejection, the partner receives a notification and may resubmit with updated information.

Key constraint: deal registration requires the Lead record to exist before conversion. You cannot register against an existing Opportunity directly in standard PRM. Any requirement to register deals that are already past the Lead stage requires a custom solution or the Channel Revenue Management product.

Duplicate prevention relies on Lead duplicate rules. These must be configured before launch — otherwise partners can register the same deal multiple times, creating channel conflict.

### Lead Distribution

Lead distribution delivers inbound or marketing-generated leads to qualified partners. There are two models:

- **Push (assignment rule-based):** Salesforce evaluates lead assignment rules on lead creation or reassignment. Rules match on criteria such as geography (state/country fields), product interest (lead source or product picklist), partner tier, and capacity (custom formula-based logic). The lead is assigned to a partner queue or directly to a partner user.
- **Pull (lead pool / lead inbox):** Leads are placed in a shared queue visible to eligible partners. Partners claim leads from the pool. Pull requires careful sharing rule design so that only eligible partners (by tier or territory) can see the pool.

Lead distribution does not function correctly without a defined partner tier and territory model. Criteria-based rules that reference partner tier require a lookup from the Lead to the partner Account tier field, which requires a cross-object formula or a trigger/flow to stamp tier on the lead at assignment time.

### Partner Tier Management

Partner tiers (commonly Gold / Silver / Bronze or Registered / Authorized / Premier) are the structural backbone of a PRM implementation. Tier drives:

- **Feature access:** Gold partners may have access to deal registration and the lead pool; Bronze partners may only have access to co-marketing assets.
- **MDF eligibility:** Higher tiers receive larger MDF allocations. MDF tracking requires a custom object (commonly `MDF_Request__c` and `MDF_Claim__c`) linked to the partner Account.
- **Co-marketing content entitlement:** Content visibility in the portal is controlled by sharing rules scoped to a tier-based public group or a record-level share. Profile or permission set alone is insufficient because content entitlement varies within the same license type.
- **Approval routing:** Approval processes can route differently based on tier — Gold deals may auto-approve below a threshold while Silver deals always require manual review.

Tier is typically stored as a picklist on the partner Account record and referenced by assignment rules, sharing rules, approval criteria, and content entitlement settings.

### MDF and Co-Marketing

Market Development Funds (MDF) are budget allocations made to partners to fund co-marketing activities. In Salesforce, MDF tracking requires custom objects because there is no standard MDF object in the core PRM product outside of Channel Revenue Management.

A standard custom object model includes:
- `MDF_Budget__c` — linked to the partner Account and fiscal year; stores total allocation.
- `MDF_Request__c` — partner-submitted request for use of funds; includes amount, activity type, target dates.
- `MDF_Claim__c` — post-activity claim for reimbursement; linked to an approved request.

Co-marketing assets (templates, brand assets, campaign collateral) are surfaced in the portal via CMS Content or Salesforce Files with sharing rules based on partner tier. Content entitlement rules must be defined before the portal build begins.

---

## Common Patterns

### Pattern 1: Multi-Tier Deal Registration with Differential Approval Routing

**When to use:** The org has 3+ partner tiers with different deal registration privileges (e.g., Gold auto-approves deals under $50K; Silver always goes to manual review).

**How it works:**
1. Store partner tier as a picklist on the partner Account (`Tier__c`).
2. Create a cross-object formula field on Lead: `Partner_Tier__c` that references the partner Account's tier via the partner lookup.
3. Build an approval process on Lead with entry criteria `Status = Submitted for Registration`.
4. Add approval steps: Step 1 checks `Partner_Tier__c = Gold AND Amount < 50000` and routes to auto-approve; Step 2 routes all other leads to channel manager queue.
5. On final approval, a Flow converts the Lead to Opportunity and stamps the partner Account on the Opportunity.
6. On rejection, a Flow sends a notification to the submitting partner user with rejection reason.

**Why not the alternative:** A single-step approval process with no tier differentiation creates a manual review bottleneck for high-volume Gold partners and degrades partner experience. Auto-approval criteria require the tier field to exist on the Lead at approval time — which requires the formula field in step 2.

### Pattern 2: Criteria-Based Lead Distribution to Partner Queue

**When to use:** The org distributes inbound leads to partners based on geography and product interest and wants assignments to respect partner tier eligibility.

**How it works:**
1. Define partner tier eligibility for lead distribution (e.g., only Gold and Silver partners receive distributed leads).
2. Create a partner queue for each tier-territory combination (e.g., `Gold_West_Queue`, `Silver_East_Queue`). Keep queue count manageable — excessive queues become an administrative burden.
3. Build Lead assignment rules with criteria ordered by specificity: state match + product interest + tier eligibility.
4. Stamp the matched partner queue on the Lead Owner field.
5. Configure portal Lead list views scoped to the partner user's queue membership so partners only see their assigned leads.
6. If pull model is required, expose a shared Lead list view for the eligible tier group (use a public group share on the Lead record rather than a queue).

**Why not the alternative:** Assigning leads directly to partner user records (rather than queues) breaks when partner users are inactive or at capacity. Queue-based assignment provides an auditable routing layer and allows partner admins to manage queue membership without reconfiguring assignment rules.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Partner needs deal registration and lead distribution | Partner Community or Partner Community Plus license | Customer Community license does not include PRM features |
| Partners need deep pipeline reporting and dashboard access | Partner Community Plus license | Standard Partner Community has limited report/dashboard access for partner users |
| Deal registration volume is high and most Gold deals auto-qualify | Criteria-based auto-approval for top tier, manual for others | Reduces channel manager workload while preserving governance on mid-market deals |
| Leads should be claimed by partners, not pushed automatically | Pull model with shared queue and tier-scoped list view | Push assignment requires capacity logic that is expensive to maintain; pull gives partners agency while respecting tier eligibility |
| MDF tracking must be auditable and tied to campaign outcomes | Custom MDF Request + Claim objects in Salesforce | External spreadsheet tracking lacks the audit trail and portal visibility that partners expect |
| Co-marketing assets should only be visible to Gold partners | Sharing rules on CMS Content or Files tied to Gold public group | Profile-only visibility does not vary within a license type; sharing rules are required |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **License and org audit** — Confirm the org edition supports Experience Cloud. Verify Partner Community or Partner Community Plus licenses are provisioned and available. Document the license count and whether login-based or member-based pricing is in use. Check whether the Partner Central template is available in the org.

2. **Tier hierarchy definition** — Document the full partner tier model: tier names, promotion/demotion criteria, and which features each tier unlocks (deal registration eligibility, lead pool access, MDF allocation, co-marketing content). Produce a tier decision matrix. This drives all downstream configuration.

3. **Deal registration requirements** — Define the deal registration object model (Lead-based standard vs. custom object). Map the approval chain: who approves at each tier, what the auto-approval thresholds are, how duplicates are prevented, and what happens on rejection. Produce a flow diagram of the Lead → Approval → Opportunity conversion path.

4. **Lead distribution requirements** — Decide push vs. pull model. For push: define assignment rule criteria (geography fields, product interest, tier eligibility) and the queue structure. For pull: define the shared pool structure and the sharing rule model for tier-scoped visibility. Document the lead capacity model if applicable.

5. **MDF and co-marketing requirements** — Determine whether MDF tracking will be in Salesforce or external. If in Salesforce, specify the custom object data model (Budget, Request, Claim) and approval process for claim reimbursement. Define co-marketing asset categories and which tiers can access which categories.

6. **Review checklist and handoff** — Walk through the review checklist below. Confirm all requirements are documented before handing off to the Experience Cloud configuration team. Flag any open decisions that would block configuration.

---

## Review Checklist

Run through these before marking requirements work complete:

- [ ] Partner Community or Partner Community Plus licenses confirmed — Customer Community explicitly ruled out
- [ ] Partner tier hierarchy documented with tier names, promotion criteria, and feature access matrix
- [ ] Deal registration object model selected (Lead-based standard PRM or custom object)
- [ ] Approval chain fully mapped per tier including auto-approval thresholds and rejection flow
- [ ] Lead duplicate rules defined to prevent multi-registration of the same deal
- [ ] Lead distribution model selected (push or pull) with assignment rule criteria documented
- [ ] Queue structure defined for push model OR shared pool sharing model defined for pull model
- [ ] MDF custom object model specified (or external system integration documented)
- [ ] Co-marketing asset entitlement rules defined per tier
- [ ] Sharing rule model documented — profile/permission set vs. sharing rule distinction confirmed
- [ ] Open decisions logged with owner and target resolution date

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deal registration requires Lead before Opportunity** — Standard PRM deal registration is built on the Lead object. Partners submit a Lead record which is converted to an Opportunity on approval. You cannot register a deal against an existing Opportunity in standard PRM. If the business requires registration of deals already past the Lead stage (e.g., partner-identified opportunities already in the pipeline), a custom solution or the Channel Revenue Management product is required. Attempting to work around this with a custom field on Opportunity breaks the standard conversion flow and audit trail.

2. **Tier-based visibility requires sharing rules, not just profiles** — All partner users in a tier share the same license type. Profile and permission set alone cannot vary content or record visibility within a tier. Sharing rules scoped to a tier-based public group are required for co-marketing asset entitlement, lead pool visibility, and MDF record access. Administrators who rely only on profiles to control tier-differentiated access will find that all partners see all content.

3. **MDF budget tracking has no standard object in core PRM** — There is no standard `MDF_Budget__c` or `MDF_Claim__c` object in the base PRM product. Projects that discover this mid-build must pause to design, build, and test custom objects before continuing. This object model must be specified in the requirements phase, not discovered during configuration.

4. **Lead assignment rules do not natively reference partner tier** — Assignment rules evaluate fields on the Lead record. Partner tier lives on the partner Account. To route leads by partner tier, a cross-object formula or a Flow must stamp the tier value onto the Lead at assignment time. Projects that skip this end up with assignment rules that cannot filter by tier eligibility.

5. **Partner user creation requires Partner Account checkbox** — A Contact cannot be enabled as a partner Experience Cloud user unless the parent Account has `IsPartner = true`. If Accounts are created in bulk without this flag, partner user provisioning fails silently or produces a generic error. Bulk partner onboarding scripts must set the flag before user creation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PRM requirements document | Full written specification covering license model, tier hierarchy, deal registration flow, lead distribution rules, MDF model, and co-marketing entitlement |
| Partner tier decision matrix | Table mapping each tier to its feature access, MDF eligibility, lead pool access, and co-marketing content categories |
| Deal registration flow diagram | Lead → Approval → Opportunity conversion path with approval routing criteria per tier |
| Lead distribution rule specification | Assignment rule criteria table (push model) or shared pool sharing model (pull model) |
| MDF custom object data model | Entity definitions for MDF Budget, Request, and Claim with field list and approval process notes |

---

## Related Skills

- experience-cloud-security — use alongside this skill to define the sharing model and guest user access boundaries for the partner portal
- license-optimization-strategy — use to evaluate whether Partner Community vs. Partner Community Plus licensing is cost-effective given the required feature set
