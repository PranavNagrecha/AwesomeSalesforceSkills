---
name: partner-data-access-patterns
description: "Use this skill when designing or troubleshooting data visibility for partner (channel) users in a Salesforce Experience Cloud Partner Community. Triggers: partner user data visibility, PRM data access model, partner role hierarchy sharing, deal registration data access partner, channel partner analytics. NOT for internal data access patterns. NOT for customer community data sharing (see admin/sharing-and-visibility or external-user-data-sharing for customer portal scenarios)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - partner-community
  - prm
  - partner-role-hierarchy
  - sharing-rules
  - deal-registration
  - channel-analytics
  - experience-cloud
triggers:
  - "partner user data visibility"
  - "PRM data access model"
  - "partner role hierarchy sharing"
  - "deal registration data access partner"
  - "channel partner analytics visibility"
  - "partner community user cannot see records"
  - "how do partner managers see their team deals"
inputs:
  - Partner Community license type in use (Partner Community vs Customer Community Plus vs Customer Community)
  - Objects that need to be shared with partners (Leads, Opportunities, Deal Registration, custom objects)
  - Partner account structure (single-tier vs multi-tier partner accounts)
  - Whether channel analytics or manager visibility across sub-partners is required
outputs:
  - Data visibility architecture decision and rationale
  - Sharing model design (role hierarchy + sharing rules + manual sharing plan)
  - Checklist of configuration steps and validation gates
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Partner Data Access Patterns

Use this skill when you need to design or debug how channel partner users see data in Salesforce. It covers the auto-generated partner role hierarchy, PRM object access, cross-account sharing rules, manual sharing, and channel analytics visibility. Do not use this skill for internal employee data access design or for customer-facing community portals.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License type**: Confirm whether users hold a Partner Community license, Customer Community Plus license, or basic Customer Community license. The license type determines which sharing mechanisms are available.
- **Account ownership**: Identify who owns the partner Account record in Salesforce. Account ownership is the root of the auto-generated role hierarchy for each partner account; changing ownership restructures the hierarchy.
- **PRM object requirements**: Determine whether Leads, Opportunities, Deal Registration, or other PRM-specific objects must be visible. These are only accessible to Partner Community licensees.
- **Cross-account scenarios**: Identify whether partner users from different accounts need to see each other's records (co-sell, alliance partners). The hierarchy alone does not provide this; sharing rules or manual sharing are required.
- **Org-wide defaults (OWDs)**: Check the OWD for every object in scope, especially the External OWD. The external OWD controls visibility for all external (community) users independent of the internal OWD.

---

## Core Concepts

### Auto-Generated 3-Tier Partner Role Hierarchy

When a user is enabled as a Partner Community user, Salesforce automatically creates a 3-tier role hierarchy scoped to that user's partner account:

- **Executive** (top): sees records owned by Manager and User roles within the same account
- **Manager** (middle): sees records owned by User roles within the same account
- **User** (bottom): sees only records they own, subject to OWD and sharing rules

This hierarchy is generated per partner account — each account gets its own isolated 3-tier tree. Role-based visibility flows upward within the account's tree: Managers see User records; Executives see both. Executives do not automatically see records from a different partner account's hierarchy.

The hierarchy is **auto-generated and cannot be customized**. You cannot add tiers, rename the roles, or restructure the tree. If a business requires a different shape, the only workaround is sharing rules or manual sharing.

### License Tier and Sharing Mechanism Availability

| License | Role Hierarchy | Sharing Rules | Manual Sharing | Sharing Sets |
|---------|---------------|--------------|---------------|-------------|
| Partner Community | 3-tier auto-generated | Yes | Yes | No |
| Customer Community Plus | 1 role per account | Yes | Yes | No |
| Customer Community (basic) | None | No | No | Yes (Sharing Sets only) |

This distinction is critical: **Customer Community Plus only gets one role** — there is no Manager/Executive layering. Designing a PRM access model for a Customer Community Plus licensee and expecting hierarchical visibility will fail at runtime.

### PRM-Specific Object Access

Objects used in Partner Relationship Management — Leads, Opportunities, Deal Registration (`PartnerFundRequest`, `PartnerFundClaim`, and the `Lead` and `Opportunity` objects surfaced via the PRM app) — are only accessible to **Partner Community licensees**. Customer Community and Customer Community Plus licenses do not include access to PRM objects. Attempting to share these objects with non-Partner Community users results in access errors or invisible records.

### External OWD and Sharing Rules

The External OWD on each object independently controls baseline access for all external (community) users. A Private external OWD means partner users only see records they own (or records explicitly shared via hierarchy, rules, or manual sharing). Sharing rules can open access between groups of partner users — for example, sharing all Opportunities owned by users in Account A's partner role with users in Account B's partner role to enable co-sell. Public Group-based sharing rules work for cross-account scenarios; role-based sharing rules work within a single account's hierarchy subtree.

---

## Common Patterns

### Pattern 1: Regional Partner Manager Visibility

**When to use:** A regional partner account has multiple sub-users (field reps) who create Leads and Opportunities. Their regional manager needs visibility across all sub-user records within the same account.

**How it works:**
1. Ensure all field reps are provisioned as Partner Community users — Salesforce auto-assigns them to the User tier of their account's role hierarchy.
2. Enable the regional manager as a Partner Community user on the same account — Salesforce auto-assigns them to the Manager tier.
3. Set Lead OWD (External) to Private. The Manager role inherits visibility over User-owned records automatically via the role hierarchy — no sharing rules needed.
4. Validate in Setup > Sharing Settings that "Grant Access Using Hierarchies" is enabled for the objects in scope.

**Why not an alternative:** Do not create sharing rules for within-account manager visibility. The hierarchy already provides this access. Adding sharing rules on top creates redundancy and can trigger performance issues during recalculations when record counts are large.

### Pattern 2: Cross-Account Sharing for Co-Sell Opportunities

**When to use:** Two independent partner accounts collaborate on a deal. Users from Account A need to see a specific Opportunity owned by a user from Account B.

**How it works:**
1. Identify the specific Opportunity records or the criteria (e.g., Opportunity Type = "Co-Sell", Partner_Account__c = Account B).
2. For ongoing structural access: create a criteria-based sharing rule on Opportunity that shares records matching the criteria to the public group containing Account B's partner role.
3. For one-off exceptions: use Manual Sharing on the individual Opportunity record (Share button). Assign the specific partner user or a public group.
4. Document which mechanism is in use — manual sharing is invisible in sharing rule lists and is commonly missed during audits.

**Why not the alternative:** Do not change Opportunity OWD to Public Read/Write to solve cross-account co-sell. This opens all Opportunities to all partner users, violating data separation requirements between competing partners.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Manager at same partner account needs to see reps' records | Auto-generated role hierarchy (no action needed) | Hierarchy provides upward visibility within account by default |
| Partner users across different accounts need shared visibility | Criteria-based sharing rules or manual sharing | Hierarchy is account-scoped; cross-account access requires explicit sharing |
| PRM objects (Leads, Deal Registration) must be visible | Partner Community license required | PRM objects are inaccessible to Customer Community / CC+ licensees |
| Single partner account, no hierarchical visibility needed | Customer Community Plus is sufficient | Saves license cost; 1 role per account is adequate for flat teams |
| Channel analytics: manager sees team pipeline | Role hierarchy provides this natively for same-account managers | Executive and Manager tiers see owned records in lower tiers |
| Competing partners must not see each other's records | Private External OWD + no cross-account sharing rules | Default separation is enforced by Private OWD; do not create open sharing rules |
| Partner account ownership changes | Re-audit role assignments and hierarchy | Account ownership change triggers hierarchy reconstruction; verify user-to-role mapping |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm license type and hierarchy availability** — Before designing any sharing model, verify the license type for each partner user segment. Partner Community = 3-tier hierarchy available. Customer Community Plus = 1 role, no hierarchy depth. Customer Community = no roles, Sharing Sets only. Mismatching design to license is the most common source of failure.
2. **Audit External OWDs for all in-scope objects** — Navigate to Setup > Sharing Settings. Record the External OWD for Leads, Opportunities, and any custom objects. A Public Read/Write External OWD means partners already see everything; a Private OWD requires explicit sharing grants.
3. **Map partner account structure to hierarchy tiers** — For each partner account, identify which users are Executives, Managers, and Users. Confirm that account ownership is stable — the account owner drives the hierarchy root. Document any accounts where ownership is shared or frequently reassigned.
4. **Design sharing rules for cross-account scenarios** — List every cross-account data-sharing requirement. For each, decide between criteria-based sharing rules (for ongoing structural access) and manual sharing (for exceptions). Create the rules in a sandbox first and validate with a test user in each role.
5. **Validate PRM object access** — If Deal Registration, Lead, or Opportunity visibility is in scope, confirm the user holds a Partner Community license. Run a quick SOQL query in Developer Console (`SELECT Id, Name FROM Lead LIMIT 1`) as a test partner user via User Switcher to validate visibility.
6. **Document and audit manual shares** — Manual shares do not appear in sharing rule lists. After any manual sharing grant, log the Opportunity/Lead ID, the user or group granted access, and the reason. Schedule a quarterly review to prune stale manual shares.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] License type confirmed for every partner user segment; Partner Community license verified for PRM object access
- [ ] External OWD reviewed for all in-scope objects; no unintended Public OWD on sensitive objects
- [ ] Partner role hierarchy tiers mapped to business roles for every active partner account
- [ ] Cross-account sharing rules (if any) created with criteria that correctly scope access; no overly broad rules
- [ ] Account ownership is stable or a process is in place to re-audit hierarchy after ownership changes
- [ ] Manual shares documented and scheduled for periodic review
- [ ] End-to-end validation completed by logging in as a test user in each partner tier

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Hierarchy is auto-generated and cannot be customized** — The 3-tier Executive/Manager/User structure is generated by Salesforce when a user is enabled as a partner. You cannot add a fourth tier, rename the roles, or reorganize the tree. Business requests for a 4-level hierarchy must be solved with sharing rules, not role restructuring.
2. **Account ownership change reconstructs the hierarchy** — If the Salesforce Account record's owner changes (e.g., a CSM leaves and records are reassigned), Salesforce rebuilds the partner role hierarchy for that account. Users may temporarily lose or gain access during recalculation. This can trigger large-scale sharing recalculation jobs in orgs with many partner records.
3. **Customer Community Plus has only ONE role, not three** — A Customer Community Plus user is assigned a single role per account. There is no Manager or Executive tier. Designs that assume hierarchical visibility for CC+ users will not work. If hierarchical visibility is required, a Partner Community license is mandatory.
4. **PRM objects are inaccessible outside Partner Community license** — Deal Registration records (`PartnerFundRequest`, `PartnerFundClaim`) and PRM-surfaced Leads/Opportunities are only available to Partner Community licensees. Assigning a Customer Community or CC+ user and then trying to share PRM records will silently fail — the records are either invisible or throw access errors.
5. **External OWD is independent of internal OWD** — The External OWD controls partner user baseline access separately from the internal OWD. Setting the internal OWD to Private does not automatically make the External OWD Private. Always audit both settings when designing partner sharing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Sharing model design document | Documents OWD settings, role hierarchy mapping, sharing rules, and manual sharing decisions for each in-scope object |
| Partner tier mapping table | Maps each partner account's users to Executive/Manager/User roles with business role alignment |
| Sharing rule specification | Criteria and target groups for each cross-account sharing rule, ready for implementation |
| Manual share log template | Tracks manual sharing grants (record ID, user/group, reason, review date) |

---

## Related Skills

- **admin/sharing-and-visibility** — Use for internal record sharing design; covers OWDs, sharing rules, and role hierarchy fundamentals that also apply to partner contexts.
- **admin/data-skew-and-sharing-performance** — Use when partner account records are high-volume or sharing recalculations are slow; covers account ownership skew and sharing performance patterns.
