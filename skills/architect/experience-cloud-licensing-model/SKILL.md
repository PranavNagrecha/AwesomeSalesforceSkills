---
name: experience-cloud-licensing-model
description: "Use this skill to select the correct Experience Cloud external user license type for a portal or community. Trigger keywords: Customer Community vs Partner Community, login-based vs member-based license, External Apps license, external user license selection, Experience Cloud license tiers. NOT for internal Salesforce employee licensing. NOT for Marketing Cloud licensing. NOT for ISV or OEM licensing."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "choose Experience Cloud license type for a portal"
  - "Customer Community vs Partner Community vs Customer Community Plus"
  - "login-based vs member-based license for Experience Cloud"
  - "external user license selection for community or portal"
  - "External Apps license Experience Cloud — which tier do I need"
tags:
  - experience-cloud
  - licensing
  - community
  - external-users
  - architect-decision
inputs:
  - Portal audience type (B2C customer, B2B partner, combination)
  - Expected concurrent and total external user volume
  - Sharing model requirements (Sharing Sets vs sharing rules vs role hierarchy)
  - CRM object access requirements (Leads, Opportunities, Contracts, etc.)
  - Reporting and dashboard requirements for external users
  - Login frequency pattern (infrequent logins vs daily active users)
outputs:
  - License tier recommendation with rationale
  - Member-based vs login-based variant guidance
  - Sharing model feasibility confirmation per license tier
  - Economic model comparison (login vs member unit economics)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud Licensing Model

This skill activates when a practitioner needs to select the correct Experience Cloud external user license for a portal or community. It provides a structured decision framework covering all four license tiers, member-based vs login-based variants, sharing model constraints per tier, and CRM object access gates.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the portal audience: pure B2C self-service customers, B2B channel partners, or a mixed audience requiring separate communities.
- Confirm which CRM objects external users must read or write — Leads, Opportunities, and Contracts are gated to Partner Community and above.
- Determine whether external users need reports or dashboards — Customer Community does not support them.
- Establish approximate user volumes and login frequency to model login-based vs member-based economics.
- Confirm the required sharing model: Sharing Sets only, criteria-based sharing rules, or a per-account role hierarchy.

---

## Core Concepts

### The Four License Tiers

Salesforce provides four main Experience Cloud external user license tiers, listed from most restricted to most flexible:

**Customer Community** — Designed for high-volume B2C portals where users need access to cases, knowledge, and basic account/contact data. Key constraints: no roles (sharing via Sharing Sets only), no reports or dashboards, limited object access. Available in member-based and login-based variants.

**Customer Community Plus** — Extends Customer Community with one portal role per user (enables criteria-based sharing rules) and grants access to reports and dashboards. Still no access to sales CRM objects such as Leads or Opportunities. Available in member-based and login-based variants.

**Partner Community** — Designed for B2B channel partners. Provides a three-tier per-account role hierarchy (Partner Executive, Partner Manager, Partner User), full access to sales CRM objects including Leads, Opportunities, Contracts, and PRM (Partner Relationship Management) features such as deal registration and market development funds. Available in member-based and login-based variants.

**External Apps (formerly Communities license)** — Most flexible tier. Access to all standard objects, custom objects, and full sharing model capabilities. Use when no other tier meets the requirement and when the portal use case is highly custom (e.g., a vendor management portal needing custom object hierarchies). Highest per-user cost.

### Member-Based vs Login-Based Variants

Every tier above is available in two billing variants:

**Member-based** — A fixed seat license. The user is assigned a license and can log in as many times as they want. Cost scales with total user count regardless of activity. Economical when users log in frequently (daily or near-daily).

**Login-based** — Billed per daily unique login. Each unique user login on a calendar day consumes one login credit from the org's purchased pool. Unused logins do not roll over to the next month. Economical when users log in infrequently (weekly or less) and total user count is large. The crossover point is typically around 25% daily active users as a fraction of total users — below that threshold, login-based is usually cheaper.

### Sharing Model Constraints Per Tier

License tier determines the maximum sharing model complexity available:

| License Tier | Sharing Mechanism | Notes |
|---|---|---|
| Customer Community | Sharing Sets only | No roles; Sharing Sets grant access based on account/contact lookup |
| Customer Community Plus | Criteria-based sharing rules + Sharing Groups | One role per user; Share Groups extend access among portal users |
| Partner Community | Per-account role hierarchy (3 tiers) | Account executive → manager → user hierarchy per partner account |
| External Apps | Full sharing model | All sharing mechanisms available |

A portal design that requires criteria-based sharing rules immediately eliminates Customer Community. A design that requires per-account role hierarchies requires Partner Community or External Apps.

---

## Common Patterns

### B2C Customer Self-Service Portal

**When to use:** High-volume consumer portal. Users submit cases, read knowledge articles, update contact info, and view order history on custom objects. No sales pipeline objects needed. Reports/dashboards not required by end customers.

**How it works:** Select Customer Community (member-based or login-based based on volume economics). Configure Sharing Sets to grant account-based record access. Use guest profile for unauthenticated browsing where required.

**Why not Customer Community Plus:** If reports and dashboards are genuinely not needed, Customer Community costs less per user and the simpler sharing model (Sharing Sets) is sufficient. Upgrade only if a future requirement surfaces for reports — but note that upgrading requires migrating user profiles.

### B2B Channel Partner Portal

**When to use:** Partner portal for resellers or distributors. Partners need to register deals (Opportunities/Leads), view their pipeline, track MDF requests, and see partner-tier-based pricing. Per-account hierarchy matters because partner managers need visibility into their team's deals.

**How it works:** Select Partner Community. The per-account three-tier role hierarchy grants managers upward visibility into subordinate users' records without custom Apex sharing. Enable PRM features (Partner Accounts, Channel Account Managers) in Experience Cloud setup. Configure Lead and Opportunity sharing through partner role hierarchy.

**Why not Customer Community Plus:** Customer Community Plus has no access to Leads or Opportunities and provides only one role per user — it cannot support a partner manager hierarchy or deal registration.

---

## Decision Guidance

| Situation | Recommended License | Reason |
|---|---|---|
| B2C portal, cases + knowledge only, no reports | Customer Community | Lowest cost; Sharing Sets sufficient |
| B2C portal with external-facing reports/dashboards | Customer Community Plus | Reports require a role; CCP minimum tier |
| B2B partners need Leads or Opportunities | Partner Community | Gated object access to sales CRM objects |
| Complex custom object hierarchy, none of above fits | External Apps | Maximum flexibility, highest cost |
| Large user base, infrequent logins (<25% DAU ratio) | Login-based variant of chosen tier | Cheaper than member seats at low activity |
| Frequent logins (daily users, always-on portal) | Member-based variant of chosen tier | Predictable cost; no usage risk |
| Mixed audience (B2C + B2B partners on same org) | Separate communities per license type | Different license types require different profiles |

---

## Recommended Workflow

Step-by-step decision framework for license selection:

1. **Identify CRM object requirements.** If Leads, Opportunities, or Contracts must be accessible to external users, the minimum tier is Partner Community. Document any sales-pipeline object access in the requirements. Stop if the requirement list contains only cases, knowledge, contacts, accounts, or custom objects — those can be served by lower tiers.

2. **Assess sharing model complexity.** Determine whether record visibility needs are simple (account-based lookup → Sharing Sets), moderate (criteria-based rules → Customer Community Plus minimum), or hierarchical per partner account (three-tier role per account → Partner Community minimum). Map the complexity gate to the minimum required tier.

3. **Confirm report and dashboard requirements.** If external users need to view reports or dashboards, Customer Community is eliminated. Minimum tier becomes Customer Community Plus.

4. **Model login-based vs member-based economics.** Estimate total portal users and expected daily active user percentage. If fewer than ~25% of users log in on any given day, run a login-based cost model. Compare login credit pool purchase cost against equivalent member seat cost at projected volumes. Document the break-even calculation and recommended variant.

5. **Validate the selected tier against org limits and future roadmap.** Confirm the license type is available in the current org edition. Check whether planned features (e.g., Leads in 18 months) would require a tier upgrade — if so, consider starting at the higher tier to avoid a profile migration. Record the decision and rationale.

6. **Document the decision with upgrade path.** Produce a license selection summary including the chosen tier, variant, sharing model approach, and the conditions under which an upgrade would be required. Include the user profile migration requirement as a risk item for any future tier change.

---

## Review Checklist

Run through these before finalizing a license recommendation:

- [ ] CRM object access requirements confirmed — sales objects present means Partner Community minimum
- [ ] Sharing model mapped to license tier capability — Sharing Sets vs sharing rules vs role hierarchy
- [ ] Report and dashboard requirements confirmed — any report access eliminates Customer Community
- [ ] Login economics modeled — login-based vs member crossover calculated at projected user volumes
- [ ] Upgrade path risk documented — profile migration requirement called out explicitly if future tier change is likely
- [ ] Mixed-audience scenario handled — separate communities confirmed if portal serves both B2C and B2B users
- [ ] License availability verified for org edition

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Login credits do not roll over** — Login-based credits are consumed per daily unique login and expire at the end of the monthly period. An org that purchases 500 login credits but only uses 200 in a month loses the remaining 300. Overpurchasing during ramp is a common cost waste; start conservative and add credits rather than buying headroom upfront.

2. **Customer Community cannot display reports or dashboards** — This is a hard platform constraint, not a configuration option. Stakeholders who assume all community users can see dashboards are regularly surprised during UAT. Establish this constraint in requirements workshops before committing to a license tier.

3. **License type is locked per user profile** — Experience Cloud license type is tied to the profile assigned to the user. Upgrading a user from Customer Community to Customer Community Plus (or Partner Community) requires changing their profile, which affects all users on that profile unless a new profile is created for the upgrade cohort. A mid-project license tier upgrade for 10,000 users is a significant administrative operation. Model the future state upfront.

4. **External Apps license does not automatically grant all object permissions** — The External Apps license provides the most flexible access model, but object-level permissions must still be explicitly configured on the profile or permission sets. The license tier unlocks the ceiling; profile/permission set configuration determines actual access.

5. **Sharing Sets are account-based only by default** — Sharing Sets grant access to records where a lookup field on the shared object points to the user's Account (or a related account). They cannot directly implement more complex sharing criteria. If business logic requires criteria beyond a single account lookup, the minimum tier is Customer Community Plus with criteria-based sharing rules.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| License selection recommendation | Chosen tier and variant with rationale mapped to requirements |
| Login vs member economics model | Break-even calculation at projected user volumes |
| Sharing model feasibility confirmation | Confirmation that the chosen tier supports the required sharing complexity |
| Upgrade risk register entry | Documents conditions triggering a future tier change and the profile migration cost |

---

## Related Skills

- architect/license-optimization-strategy — Use alongside this skill when auditing or right-sizing an existing org's license mix across all license types, not just Experience Cloud external users
- security/experience-cloud-security — Applies after license selection to configure guest user hardening, profile permissions, Sharing Sets, and CRUD/FLS on the chosen license tier
