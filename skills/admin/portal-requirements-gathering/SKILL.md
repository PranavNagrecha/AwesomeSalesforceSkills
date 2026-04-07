---
name: portal-requirements-gathering
description: "Use when gathering requirements for a customer portal, partner community, or self-service Experience Cloud site. Triggers: 'gathering requirements for customer portal', 'planning Experience Cloud site', 'what license for community portal', 'portal user journey mapping', 'self-service requirements'. NOT for Experience Cloud implementation or configuration. NOT for post-launch portal optimization or redesign."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - User Experience
triggers:
  - "gathering requirements for customer portal"
  - "planning Experience Cloud site"
  - "what license for community portal"
  - "portal user journey mapping"
  - "self-service requirements"
tags:
  - experience-cloud
  - portal
  - requirements-gathering
  - self-service
  - customer-community
  - partner-community
inputs:
  - "Existing support channel data: case volume, channel mix, top contact reasons (60–90 days minimum)"
  - "Audience definition: customer vs. partner vs. internal vs. public/anonymous"
  - "Business goal: deflection target, partner enablement, account self-service, or combination"
  - "Existing Salesforce org context: licenses owned, orgs in scope, connected systems"
outputs:
  - "Signed-off access architecture decision (public / authenticated / hybrid)"
  - "User license selection per audience segment with rationale"
  - "Top-3 high-volume job list with success criteria"
  - "Content taxonomy and ownership matrix"
  - "Feature scope document: in-scope, deferred, and out-of-scope items"
  - "Deflection baseline and measurable goal"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Portal Requirements Gathering

This skill activates when a BA, admin, or architect needs to elicit, structure, and lock in the decisions required before building a Salesforce Experience Cloud portal. It covers contact reason analysis, access architecture, license selection, user journey definition, and content taxonomy. It does not cover site configuration, theme setup, or post-launch optimization.

---

## Before Starting

Gather this context before working on anything in this domain:

- Pull at minimum 60–90 days of support contact data segmented by channel (phone, email, chat, web form). Without this baseline, feature prioritization is opinion-driven rather than data-driven.
- Identify the distinct audience segments the portal must serve. A portal that tries to serve customers, partners, and anonymous visitors under a single access model will require major rework later because access architecture is set at the Experience Cloud site level and is difficult to change post-launch.
- Confirm which Salesforce licenses the org currently owns. License type determines what objects, features, and sharing configurations are available. Recommending a portal design that requires a license the org does not own creates a hard blocker at build time.

---

## Core Concepts

### Contact Reason Analysis (Answers / Status / Actions Framework)

Before defining any portal features, categorize 60–90 days of support contacts into three buckets:

- **Answers** — contacts where the customer needed information (e.g., "How do I reset my password?", "What is my contract end date?"). These are deflectable via knowledge articles and FAQ content.
- **Status** — contacts where the customer needed to check on something (e.g., "Where is my order?", "What is the status of my open case?"). These are deflectable via self-service visibility into records.
- **Actions** — contacts where the customer needed to do something (e.g., "I need to update my billing address", "I want to raise a return request"). These require transactional self-service capabilities.

The ratio of Answers : Status : Actions determines the portal's feature priority stack. A portal heavy in Answers needs a strong knowledge base. A portal heavy in Actions needs a robust case management and record-update layer. Skipping this analysis results in building features that do not reduce support volume.

### Access Architecture Decision

Experience Cloud sites have three access models:

- **Public / Unauthenticated** — any visitor can see content without logging in. Appropriate for knowledge bases, product documentation, and community forums with no personalization.
- **Authenticated** — visitors must log in to access the site. Required for any personalized content, record visibility, or transactional self-service.
- **Hybrid** — some pages are public, others require login. Requires careful sharing rule and page-level access design to avoid accidental data exposure.

This decision must be locked before any other design work begins. It governs the license model, the sharing architecture, the guest user profile configuration, and the data exposure risk posture. Changing from authenticated to hybrid after launch is a significant rework.

### License Type Selection Per Audience

Experience Cloud user licenses determine which standard and custom objects users can access and what features are available. The primary license types for portal use are:

- **Customer Community** — suitable for B2C self-service portals. Provides access to standard Case, Contact, and Knowledge objects. Does not support Leads or Opportunities.
- **Customer Community Plus** — adds advanced sharing (criteria-based and manual sharing on custom objects), reports, and dashboards. Required when customers need to view or manage complex data sets.
- **Partner Community** — designed for indirect sales and PRM. Includes access to Leads, Opportunities, and partner-specific features. Required for deal registration and pipeline visibility use cases.
- **External Apps** — the most flexible license for custom portal experiences; provides object access comparable to internal users at higher cost. Use when none of the community licenses cover the required object set.

License selection is difficult and costly to change after user records are provisioned at scale. It must be locked during requirements, not during build.

### Top-3 High-Volume Jobs Model

Rather than building a feature list from wishlist conversations, the requirements process should identify the top 3 jobs customers most frequently need to complete. A "job" is defined as a task the customer is trying to accomplish, not a feature. Example jobs:

- "Check the status of my open support case"
- "Download my invoice"
- "Request a change to my service plan"

Each job should have a measurable success criterion (e.g., "customer can complete task without contacting support") and a baseline deflection target. Defer social features, gamification, idea exchanges, and community forums until the three core jobs are delivered and the deflection loop is validated.

---

## Common Patterns

### B2C Self-Service Support Portal

**When to use:** The primary goal is to reduce inbound support contact volume by enabling customers to find answers, check case status, and raise new cases without calling or emailing.

**How it works:**
1. Run contact reason analysis. Identify top 10 contact reasons; categorize as Answers, Status, or Actions.
2. Map each top contact reason to an Experience Cloud capability: Knowledge (Answers), case feed visibility (Status), web-to-case or case management (Actions).
3. Define authenticated access model. Customers log in with a Customer Community or Customer Community Plus license.
4. Set deflection baseline (current self-service containment rate) and target.
5. Defer idea exchange, chatter, and gamification to phase 2 after deflection goal is validated.

**Why not the alternative:** Building from a feature wishlist (search, FAQ, chat, forums, notifications) without contact reason grounding produces a portal with high feature count but low actual deflection, because the features do not map to the real reasons customers contact support.

### Partner Relationship Management (PRM) Portal

**When to use:** The portal must support indirect channel: deal registration, pipeline visibility, MDF requests, partner onboarding, or co-selling.

**How it works:**
1. Define partner tiers and what each tier needs to see and do (different job sets per tier).
2. Select Partner Community license. Confirm org has Sales Cloud enabled; PRM requires access to Lead and Opportunity objects.
3. Map access architecture: partners must be authenticated. Determine if partner account hierarchy is required (child partner accounts under master partner account).
4. Define content taxonomy: product enablement, partner agreements, co-marketing assets, deal registration forms.
5. Lock sharing model early — Partner Community uses role hierarchy and sharing rules. Confirm partner users should NOT see each other's opportunities (the default is account-scoped sharing).

**Why not the alternative:** Using Customer Community Plus for a PRM use case lacks Lead and Opportunity access, forcing workarounds that create data model debt and break standard Salesforce partner reporting.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| B2C customers need to view cases, download invoices, update contact info | Customer Community or Customer Community Plus | Standard objects covered; no Lead/Opp access needed |
| B2C customers need to share reports with each other or see complex custom object data | Customer Community Plus | Advanced sharing (manual + criteria-based on custom objects) required |
| Indirect sales channel: deal registration, pipeline, MDF | Partner Community | Lead and Opportunity access mandatory for PRM |
| Portal requires access to objects beyond standard community object set | External Apps license | Most flexible; evaluate cost vs. object coverage gap |
| Portal will have anonymous (non-logged-in) visitors AND authenticated users | Hybrid access model | Requires careful guest user profile lockdown; plan sharing rules for both populations |
| Deflection is primary goal; gamification/forums in scope | Defer social features | Validate deflection loop first; gamification adds scope without improving core self-service |
| Less than 60 days of contact reason data available | Delay feature scoping | Feature decisions made without data will misalign with actual customer needs |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Collect contact reason data** — Pull 60–90 days of support contact records segmented by contact reason. Categorize each reason as Answers, Status, or Actions. Identify the top 10 reasons by volume. This step is non-negotiable; it replaces stakeholder opinion with evidence.
2. **Lock access architecture** — Decide: public, authenticated, or hybrid. Document the rationale and have it signed off by a technical lead. Record the guest user profile requirements if hybrid or public pages are in scope.
3. **Select user license per audience segment** — Map each audience segment (B2C customer, B2B account user, partner, internal user, anonymous visitor) to the appropriate license. Confirm the org owns the required licenses. Record the decision and its rationale.
4. **Define top-3 high-volume jobs** — Translate the top contact reasons into customer jobs. Write a success criterion for each job. Set a deflection baseline (current self-service containment rate) and target for each job.
5. **Build content taxonomy and ownership matrix** — Identify every content type the portal will surface (knowledge articles, FAQs, product documentation, co-marketing assets, portal announcements). Assign an owner for each content type. Define the publication and review cadence.
6. **Produce the scoped requirements document** — Capture all locked decisions, in-scope features, deferred features, and out-of-scope items. Mark social, gamification, and idea exchange features as explicitly deferred until the deflection loop is validated.

---

## Review Checklist

Run through these before marking requirements complete:

- [ ] Contact reason analysis completed with 60–90 days of real data
- [ ] Each top contact reason categorized as Answers, Status, or Action
- [ ] Access architecture decision documented and signed off (public / authenticated / hybrid)
- [ ] License type selected and confirmed as owned by the org for each audience segment
- [ ] Top-3 high-volume jobs defined with measurable success criteria
- [ ] Deflection baseline and target recorded
- [ ] Content taxonomy documented with content owners named
- [ ] Deferred features listed explicitly (social, gamification, idea exchange)
- [ ] Out-of-scope items recorded to prevent scope creep at build time
- [ ] Requirements document reviewed with at least one technical stakeholder

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **License selection is a one-way door at scale** — Once thousands of partner or customer users are provisioned under a given license type, changing the license requires reprovisioning every user record. This is a bulk DML operation with significant risk and effort. The license decision must be final before any user provisioning begins.
2. **Guest user profile is shared across all public pages** — In a hybrid access model, the guest user profile applies to every public page on the site. Overly permissive guest user object access (e.g., read access on Account) creates data exposure risk that is invisible during requirements if access architecture is not locked early.
3. **Customer Community does not support manual sharing or role hierarchy on custom objects** — Teams that choose Customer Community and later discover they need to share custom object records selectively must upgrade to Customer Community Plus. This surprises teams who assumed all community licenses had equivalent sharing capabilities.
4. **Contact reason analysis is almost never done** — The most common failure mode in portal projects is skipping the data pull and jumping directly to feature selection. The result is a portal with search, chat, and a knowledge base that does not contain answers to the actual questions customers ask, achieving near-zero deflection.
5. **Gamification and social features defer deflection validation** — Adding idea exchange, chatter, and leaderboards to phase 1 shifts engineering effort away from the core self-service loop. Deflection is measurable; community engagement metrics are vanity metrics at the requirements stage.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Contact Reason Analysis | Spreadsheet or document showing top 10 contact reasons, volume, and Answers/Status/Actions classification |
| Access Architecture Decision Record | Single-page document recording the access model decision, rationale, and technical sign-off |
| License Selection Matrix | Table mapping each audience segment to a license type with cost and coverage rationale |
| Top-3 Jobs Document | Three customer jobs with success criteria, deflection baseline, and target |
| Content Taxonomy and Ownership Matrix | List of content types, owners, and review cadence |
| Portal Requirements Scope Document | Full requirements document: in-scope features, deferred features, out-of-scope items |

---

## Related Skills

- requirements-gathering-for-sf — Use for general Salesforce project requirements gathering; this skill is the portal-specific extension
- experience-cloud-security — Use after requirements are locked to design the sharing model, guest user lockdown, and data exposure controls
