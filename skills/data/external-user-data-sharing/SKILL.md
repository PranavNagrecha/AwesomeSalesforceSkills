---
name: external-user-data-sharing
description: "Configure record visibility for external users (Customer Community, Customer Community Plus, Partner Community) using External OWDs, Sharing Sets, and external sharing rules. Trigger keywords: sharing data with external users, portal user record visibility, Experience Cloud sharing model, sharing set configuration, external OWD setup, Customer Community data access, High-Volume Portal sharing. NOT for internal sharing model configuration. NOT for internal user roles and hierarchies. NOT for guest user profile hardening."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "portal user cannot see their own account or cases in Experience Cloud"
  - "how do I share records with Customer Community or Partner Community users"
  - "sharing set vs sharing rule for external users — which one do I use"
  - "external OWD setup — how is it different from the internal org-wide default"
  - "High-Volume Portal user cannot access records because criteria-based sharing rules do not fire"
  - "Customer Community data access — records not visible to community members"
  - "partner community sharing model — three-tier role hierarchy per account"
tags:
  - external-users
  - experience-cloud
  - sharing-model
  - sharing-set
  - external-owd
  - portal
  - customer-community
  - partner-community
inputs:
  - "External user license type (Customer Community, Customer Community Plus, Partner Community)"
  - "Objects that external users must read or write"
  - "Internal OWD settings for those objects"
  - "Whether High-Volume Portal (HVP) users are involved"
  - "Relationship from external user's Contact/Account to the target records"
outputs:
  - "External OWD configuration guidance per object"
  - "Sharing Set configuration (object, access level, mapped account/contact field)"
  - "External sharing rule configuration for CC Plus and Partner Community"
  - "Decision table for choosing the right sharing mechanism per license type"
  - "Review checklist confirming correct visibility before go-live"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# External User Data Sharing

This skill activates when configuring record visibility for authenticated external users in Experience Cloud (Customer Community, Customer Community Plus, or Partner Community). It covers External OWDs, Sharing Sets, and external sharing rules, and produces the correct mechanism selection based on the user license type.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify every external user license type in the org: Customer Community (High-Volume Portal), Customer Community Plus, or Partner Community. The mechanism set differs fundamentally per license type.
- Confirm the internal OWD for every object the external users need to access. External OWD can only be set to the same value or more restrictive than the internal OWD — never more permissive.
- Determine the relationship path from the external user's Contact or Account to the target records. Sharing Sets require a direct lookup or the Account field to exist on the object.
- Know whether the external user volume will be high (hundreds of thousands). High-Volume Portal users have restricted sharing mechanisms — Sharing Sets only.

---

## Core Concepts

### External Org-Wide Defaults (External OWD)

External OWD is a separate org-wide default that applies exclusively to external users: portal users, community users, and guest users. It is configured per object in Setup > Security > Sharing Settings, in the "External Access" column alongside the standard OWD.

Key platform behavior:
- External OWD can be set to Public Read Only or Private when internal OWD is Public Read/Write. It cannot be set more permissive than the internal OWD.
- When External OWD is tighter than the internal OWD, Salesforce enforces the stricter value for external users. Internal users are not affected.
- Changing External OWD triggers a background sharing recalculation job for the entire org. During recalculation, external user access may be temporarily inconsistent.
- External OWD does not exist for all objects. It is available on standard objects that support portal sharing (Account, Contact, Case, Opportunity, Lead, Custom Objects, etc.).
- External OWD defaults to the internal OWD value when external OWD is first enabled. This means turning on communities without explicitly reviewing external OWD can expose records unintentionally.

### Sharing Sets (High-Volume Portal / Customer Community)

Sharing Sets are the ONLY sharing mechanism for High-Volume Portal (HVP) users, which corresponds to the Customer Community license. Standard Apex managed sharing, criteria-based sharing rules, manual sharing, and role-hierarchy-based sharing do not apply to HVP users.

How Sharing Sets work:
- A Sharing Set grants access to records that share a lookup relationship with the user's Account or Contact.
- Configuration: Setup > Digital Experiences > Settings > Sharing Sets. Select the HVP profile, the object, the relationship path (e.g., `Account` field on Case maps to the user's Account), and the access level (Read Only or Read/Write).
- A single Sharing Set supports multiple objects and multiple relationship paths per object.
- Sharing Sets grant read or read/write access. They cannot grant Owner-level access.
- Sharing Sets do not support formula fields or picklist-filtered criteria — they are purely relationship-based.

### Customer Community Plus — Full Sharing Model with One Role

Customer Community Plus users participate in the full Salesforce sharing model but are placed in a single role per account (no role hierarchy below that role). This means:
- Criteria-based sharing rules fire for CC Plus users.
- Manual sharing is available.
- External Sharing Rules can grant additional record access beyond OWD.
- Role hierarchy-based access is limited: CC Plus has one role per account, not a multi-tier hierarchy.
- Sharing Sets do not apply to CC Plus users. Use criteria-based sharing rules or external sharing rules instead.

### Partner Community — Three-Tier Role Hierarchy Per Account

Partner Community users participate in a full role hierarchy with three tiers per account: Partner Executive, Partner Manager, and Partner User. Records owned by a lower-tier role are visible to higher-tier roles within the same account.

- Criteria-based sharing rules apply.
- Manual sharing is available.
- External sharing rules work.
- Partner Community can use Apex managed sharing.
- Sharing Sets do not apply to Partner Community users.
- The role hierarchy is per account, not org-wide. A Partner Executive at Account A cannot see records of a Partner User at Account B through the hierarchy alone.

### Portal Account Sharing Model

External users inherit record access through the Account they are associated with. When an external user's Contact is associated with an Account:
- The user can see the Account record and related records that share the Account field — subject to External OWD and any Sharing Set or sharing rule granting access.
- By default, external users can only see records that belong to their Account. Records owned by contacts at other accounts are not visible unless explicitly shared.
- An Account owner who is an internal user does not automatically grant portal users access to all records associated with that account — only records explicitly granted via the sharing model.

---

## Common Patterns

### Pattern: Sharing Set for Customer Community (High-Volume Portal) Case Access

**When to use:** You have Customer Community (HVP) users who need to read and update Cases associated with their Account or Contact.

**How it works:**
1. Set External OWD on Case to Private.
2. Navigate to Setup > Digital Experiences > Settings > Sharing Sets.
3. Create a Sharing Set. Select the Customer Community HVP profile(s).
4. In the "Configure Access" section, add the Case object.
5. Set "Grant Access Based On" to the relationship path: User > Account > Account (matches the Account field on Case).
6. Set Access Level to Read/Write.
7. Save and allow the sharing recalculation to complete.

**Why not criteria-based sharing rules:** Criteria-based sharing rules do not fire for HVP users. Attempting to use them results in the rule being created successfully but having no effect for HVP users — a silent failure.

### Pattern: Criteria-Based External Sharing Rule for Customer Community Plus

**When to use:** You have Customer Community Plus users who need access to records based on a field value (e.g., region, status) rather than a direct account relationship.

**How it works:**
1. Confirm the users are on Customer Community Plus license (not Customer Community / HVP).
2. Set External OWD on the object to Private.
3. Navigate to Setup > Security > Sharing Settings > Object Sharing Rules > New.
4. Choose "Based on criteria". Set criteria (e.g., Region__c = "West").
5. In "Share With", select "Customer Portal Users" or the specific community role group.
6. Set access level to Read Only or Read/Write.
7. Save. The rule fires for CC Plus users during sharing recalculation.

**Why not a Sharing Set:** Sharing Sets are relationship-based only. They cannot filter on picklist values, formula results, or status fields. Criteria-based sharing rules cover field-based access scenarios.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Customer Community (HVP) users need access to their own Cases | Sharing Set with Account→Account or Contact→Contact path | Only sharing mechanism for HVP; criteria rules are ignored |
| Customer Community Plus users need field-filtered access | Criteria-based external sharing rule | CC Plus participates in full sharing model; Sharing Sets do not apply |
| Partner Community users need access within their account hierarchy | External OWD + role hierarchy (already provided by partner roles) | Three-tier hierarchy provides access within account automatically |
| All external users need read access to a reference object | External OWD set to Public Read Only | Single OWD change grants access without per-user configuration |
| External users must not see records that internal users can see publicly | External OWD set to Private (tighter than internal OWD) | External OWD enforces stricter access independently |
| Customer Community Plus users need access to records owned by internal users in a specific group | External Sharing Rule with "Share With Portal Users in Role" | Grants access from internal group to external role group |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify license type and volume** — Confirm whether the external users are Customer Community (HVP), Customer Community Plus, or Partner Community. Confirm expected user count. This determines which mechanism is available.
2. **Audit current External OWD settings** — For every object the external users need to access, note the current External OWD value. Verify it is not more permissive than the internal OWD. Tighten or open External OWD as needed for baseline access.
3. **Select the correct sharing mechanism** — Use the Decision Guidance table above. HVP → Sharing Set. CC Plus → criteria-based sharing rule or external sharing rule. Partner Community → sharing rules or rely on role hierarchy.
4. **Configure the mechanism** — For Sharing Sets: select the HVP profile, object, relationship path, and access level. For criteria-based rules: define criteria, share-with target, and access level. Document the exact configuration.
5. **Validate access in a sandbox** — Log in as a test external user of the correct license type. Confirm the target records appear with correct access level. Confirm records outside the sharing scope are not visible.
6. **Check sharing recalculation status** — After saving Sharing Sets or changing External OWD, check Setup > Background Jobs for a pending sharing recalculation. Do not mark the work complete until the job finishes and access is confirmed stable.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External OWD for each relevant object reviewed and intentionally set (not left as default)
- [ ] License type confirmed as HVP, CC Plus, or Partner Community — and the correct mechanism used for that license type
- [ ] Sharing Set configured with the correct relationship path (not a mismatched field)
- [ ] For CC Plus / Partner Community: criteria-based sharing rules confirmed to be firing (verify via "Recalculate" and test user login)
- [ ] Sharing recalculation job completed with no errors before sign-off
- [ ] Test user login confirmed correct records visible and no over-sharing outside the account

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sharing Sets silently do nothing for CC Plus and Partner Community users** — Sharing Sets only apply to High-Volume Portal (Customer Community) users. If a Sharing Set is configured and associated with a CC Plus or Partner Community profile, Salesforce does not raise an error, but the Sharing Set has no effect. Practitioners discover this only when test logins fail.
2. **External OWD defaults to internal OWD value — not to Private** — When a Salesforce org first activates communities, external OWD inherits the current internal OWD value for each object. If internal OWD is Public Read Only, external users immediately get the same access. This is a common unintentional data exposure path that goes unnoticed until a security review.
3. **Criteria-based sharing rules do not fire for HVP users** — Criteria-based sharing rules and manual sharing are not evaluated for High-Volume Portal users. A rule may exist and appear correctly configured, yet HVP users will not receive access. There is no error or warning in Setup.
4. **Changing External OWD triggers an org-wide sharing recalculation** — Any External OWD change queues a background recalculation job across the entire org. For large data volumes, this can take hours. During recalculation, external user record access may be temporarily inconsistent. Plan External OWD changes during maintenance windows.
5. **Portal users only see records under their own Account by default** — Even if External OWD is set to Public Read Only for an object, portal users see all records regardless of account. If the intent is to restrict to their account's records only, External OWD must be Private and access granted via a Sharing Set or sharing rule scoped to the account relationship.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| External OWD configuration table | Per-object external OWD settings with rationale |
| Sharing Set configuration spec | Profile, object, relationship path, access level for each Sharing Set |
| External sharing rule spec | Criteria, share-with target, access level for each rule |
| Validated test user access report | Confirmed records visible / not visible for each external user type |

---

## Related Skills

- experience-cloud-security — guest user hardening, site-level security settings, and security review checklist for Experience Cloud
- sharing-and-visibility — internal org sharing model, internal OWD, sharing rules for internal users (use this for non-external sharing questions)
- data-access-patterns — broader data access design including large data volumes, SOQL visibility, and row-level security architecture
