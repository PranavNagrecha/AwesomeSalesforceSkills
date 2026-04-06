---
name: experience-cloud-security
description: "Use when configuring access controls, sharing, or site security for authenticated or guest Experience Cloud (community) users: external OWD, Sharing Sets, Share Groups, CSP, clickjack protection, guest user record access. NOT for internal sharing model configuration (use sharing-and-visibility)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "how do I restrict which records external portal users can see in Experience Cloud"
  - "guest user can access records they should not see in my community"
  - "how does sharing work for authenticated portal users versus guest users"
  - "external OWD and sharing sets configuration for community"
  - "how to secure an Experience Cloud site against unauthorized data access"
tags:
  - experience-cloud
  - external-sharing
  - guest-user
  - sharing-sets
  - portal-security
inputs:
  - "Site type: authenticated portal, guest-access site, or hybrid"
  - "Objects and records external users need access to"
  - "Whether guest user access is required and to which objects"
outputs:
  - "External OWD configuration recommendation per object"
  - "Sharing Set or Share Group configuration steps"
  - "Guest user profile hardening checklist"
  - "CSP and clickjack protection configuration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Experience Cloud Security

This skill activates when configuring security controls for an Experience Cloud site (formerly Community Cloud), covering external org-wide defaults, Sharing Sets, Share Groups, guest user record access restrictions, and site-level security headers. It does NOT cover internal org sharing model design.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify whether the site serves authenticated external users, guest (unauthenticated) users, or both — the security model differs significantly between these cases.
- Understand which Salesforce objects external users need to read, create, or edit — this drives external OWD and Sharing Set design.
- Confirm whether guest user access is intentional — since Spring '21, guest user record access defaults to private (all objects), and the Secure Guest User Record Access setting enforces this.

---

## Core Concepts

### External Org-Wide Defaults (External OWD)

External OWD is a separate org-wide default that applies exclusively to external users (portal users, community users, guest users). It is configured per object in Setup > Sharing Settings alongside the internal OWD. External OWD can be equal to or more restrictive than internal OWD — it can never be more permissive than the internal OWD for the same object. For example, if internal OWD is Public Read/Write, external OWD can be Public Read/Write, Public Read Only, or Private — but not more permissive.

When external OWD is set to Private for an object, external users can only access records via explicit sharing mechanisms (Sharing Sets, manual sharing, Apex sharing, or profile-level permissions with "View All").

### Sharing Sets

A Sharing Set grants access to records based on a lookup field relationship between the external user's Contact/Account record and the target record. Sharing Sets are available for Customer Community and Customer Community Plus license types only. Guest users cannot be included in Sharing Sets.

Example: A Sharing Set grants read access to Case records where `Case.AccountId = User.AccountId` — the portal user sees all cases belonging to their account.

Key constraints:
- Sharing Sets do NOT use the role hierarchy — they are purely relationship-based.
- Sharing Sets do not support all objects — only standard objects that have a supported lookup relationship to Account or Contact.
- Each Sharing Set can include multiple access mapping entries for the same site.

### Secure Guest User Record Access

The "Secure Guest User Record Access" org preference (Setup > Sharing Settings) forces all-private external OWD for guest users on all objects, regardless of what the external OWD is set to. When this toggle is enabled:
- Guest users can only access records explicitly shared via Apex sharing, guest sharing rules, or public list views.
- The toggle is enabled by default for orgs created after Spring '21 and is strongly recommended for all orgs.

### Share Groups

Share Groups allow portal users (Customer Community Plus and Partner Community licenses) to share records among themselves. A Share Group is defined per portal role and grants portal users access to records owned by users in that group. This is distinct from Sharing Sets — Share Groups address peer-to-peer sharing within the portal, not data originating from the internal org.

---

## Common Patterns

### Sharing Set for Account-Based Record Access

**When to use:** An authenticated Customer Community portal where users should see records belonging to their account — e.g., all Cases, Contracts, or Orders linked to their Account.

**How it works:**
1. Set external OWD for the target object (e.g., Case) to Private.
2. Navigate to Setup > Digital Experiences > Sharing Settings > Sharing Sets.
3. Create a Sharing Set associated with the Experience Cloud site.
4. Add an access mapping: Object = Case, Access = Read Only, User = User.Contact.Account, Target = Case.Account.
5. Save. Portal users can now see all cases where Case.AccountId matches their Contact's AccountId.

**Why not internal OWD:** Setting Case internal OWD to Public Read/Write would expose all cases to all users including internal ones — overly broad. The Sharing Set provides least-privilege access scoped to the portal context.

### Guest User Hardening

**When to use:** Any site that has a guest user profile — even sites intended only for authenticated users may have guest access enabled by default.

**How it works:**
1. Confirm "Secure Guest User Record Access" is enabled in Setup > Sharing Settings.
2. Review the Guest User profile — remove all object and field permissions that are not required for unauthenticated page display.
3. Set external OWD to Private for all objects where guest users should have no access.
4. Audit Apex classes marked `global` or `without sharing` that are accessible to the guest profile — guest users calling Apex inherit the `without sharing` context by default.
5. Enable CSP (Content Security Policy) for the site and configure trusted sites explicitly.

**Why not rely on page-level security alone:** The guest profile interacts with the Salesforce data layer directly through Apex, SOSL, and SOQL. A guest user calling an `without sharing` Apex class can potentially access records the page was never designed to expose if object permissions are too broad.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Authenticated portal users need access to account-related records | Sharing Set with account lookup mapping | Least-privilege, relationship-based, no role hierarchy required |
| Authenticated portal users need to share records with each other | Share Group (Customer Community Plus or Partner) | Peer-to-peer sharing scoped to portal role |
| Guest users need to create a record (e.g., case submission form) | Guest user profile Apex class with sharing enforced on insert + explicit field access | Guest can create via Apex; don't grant broad object-level Create on guest profile |
| Guest users should see NO records | Enable Secure Guest User Record Access; set external OWD to Private for all objects | Enforces platform-level restriction regardless of page configuration |
| Portal site needs to embed content from external domains | Configure CSP trusted sites in Setup > CSP Trusted Sites | CSP headers block unapproved domain resource loading |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify the site type and user population: authenticated portal users, guest users, or both. Confirm which license types are in use (Customer Community, Customer Community Plus, Partner Community).
2. Review external OWD for all objects the portal touches — set to Private unless there is an explicit business requirement for broader access.
3. Verify "Secure Guest User Record Access" is enabled in Setup > Sharing Settings — if not, assess guest user record exposure and enable unless there is a documented exception.
4. Configure Sharing Sets for each object where authenticated portal users need relationship-based access — map lookup fields from the portal user's Contact/Account to the target record.
5. Audit the guest user profile — remove all object permissions not required for unauthenticated display. Review Apex classes accessible to guest with `without sharing` keyword.
6. Enable site-level security headers: clickjack protection (Allow framing from same origin only), CSP with trusted sites explicitly listed, Lightning Web Security (LWS) enabled.
7. Run Security Health Check and review community-specific findings.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] External OWD is set to Private or more restrictive for all objects not explicitly required to be broader
- [ ] "Secure Guest User Record Access" is enabled
- [ ] Sharing Sets are configured for each object that authenticated portal users need access to
- [ ] Guest user profile has minimal object and field permissions — only what is needed for unauthenticated rendering
- [ ] Apex classes accessible to guest profile reviewed for `without sharing` keyword usage
- [ ] CSP trusted sites configured and clickjack protection is set to same-origin

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **External OWD cannot be more permissive than internal OWD** — If you try to set external OWD to Public Read/Write when internal OWD is Private, Salesforce will not allow it. The UI will appear to set it but the effective value reverts. Always set internal OWD first, then configure external OWD within the allowed range.
2. **Guest users are excluded from Sharing Sets** — Sharing Sets only apply to authenticated portal users (Customer Community, Customer Community Plus, Partner Community). Attempting to grant guest users access via Sharing Sets has no effect — guest access requires explicit profile permissions, guest sharing rules, or Apex sharing.
3. **CSP and clickjack settings apply per site, not org-wide** — A change to CSP trusted sites in one Experience Cloud site does not affect other sites. Each site must be configured independently. LWS is also per-site.
4. **Changing external OWD triggers sharing recalculation** — Changing an external OWD from Public Read/Write to Private triggers a background sharing recalculation job that can take minutes to hours in large orgs. During recalculation, users may see stale sharing results.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| External OWD configuration recommendation | Per-object table of recommended internal and external OWD values |
| Sharing Set configuration steps | Object, access level, and lookup mapping for each Sharing Set |
| Guest user profile audit | List of object and field permissions to remove from the guest profile |
| Site security header configuration | CSP, clickjack, and LWS settings per site |

---

## Related Skills

- guest-user-security — hardening the guest user profile itself beyond site-level controls
- sharing-and-visibility — internal org sharing model, OWD, sharing rules for internal users
- network-security-and-trusted-ips — CSP, CORS, and trusted IP configuration at the org level
