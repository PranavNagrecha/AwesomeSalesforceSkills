---
name: scim-provisioning-integration
description: "Use when designing or reviewing SCIM-based user lifecycle provisioning into Salesforce from Okta, Azure AD / Entra, or another IdP — create/update/deactivate, group-to-permission-set mapping, attribute mapping, and deprovisioning semantics. Triggers: 'scim provisioning', 'okta scim salesforce', 'entra salesforce provisioning', 'user deactivation automation', 'group to permission set mapping'. NOT for SSO/authentication setup (see single-sign-on skills)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "scim provisioning from okta to salesforce"
  - "how should entra provision salesforce users"
  - "deactivation lag on salesforce users"
  - "group to permission set mapping strategy"
  - "scim attribute mapping for salesforce"
tags:
  - security
  - scim
  - provisioning
  - identity
  - permission-sets
inputs:
  - "identity provider and directory source of truth"
  - "target group-to-permission-set / role mapping"
  - "deprovisioning SLA and frozen-vs-deactivated policy"
outputs:
  - "SCIM attribute mapping document"
  - "group-to-entitlement mapping"
  - "deprovisioning runbook"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# SCIM Provisioning Integration

SCIM turns an IdP into the source of truth for who exists, what they are allowed to do, and when they leave. Done well, it eliminates the "orphan user" problem that every manual provisioning model produces. Done poorly, it creates silent license burn, privilege creep, or worse — users who still have active API tokens after HR thinks they were deprovisioned.

Salesforce accepts SCIM via the User SCIM 2.0 API (enabled per-org) and supports attribute mapping, group-to-Permission-Set-License mapping, and freeze/deactivate via standard SCIM patch semantics. Okta, Entra, OneLogin, and other major IdPs ship Salesforce SCIM connectors; the connector mechanics vary slightly, but the design decisions are the same.

The job is to decide: what's the source of truth, which attributes flow, which groups map to which entitlements, and what happens at termination.

---

## Before Starting

- Confirm which IdP is the source of truth and whether HR or IT owns the upstream data.
- Confirm the Permission Set License count and whether Salesforce licenses are a constraint.
- Confirm the deprovisioning SLA (same-day? within 15 minutes?).
- Confirm legal/compliance policy on user deletion vs deactivation (Salesforce generally deactivates; users cannot be deleted once they own records).

## Core Concepts

### What SCIM Covers

- **Create** — IdP triggers user creation when a user is added to an assigned group.
- **Update** — profile attribute changes flow from the IdP on change.
- **Deactivate** — user is set to `active = false` when removed from the assigned scope.
- **Group-to-entitlement** — IdP groups map to Salesforce Permission Sets, Permission Set Groups, or Public Groups.

### What SCIM Does Not Cover

- Profile selection (Salesforce requires a profile; most IdPs use a default-profile strategy with entitlement layered via Permission Sets).
- Role Hierarchy assignment (often still manual or handled by Apex downstream).
- Record ownership reassignment on termination.

### Deactivation Semantics

Salesforce does not delete users — it deactivates. A SCIM `DELETE` or `PATCH active=false` freezes login but does not reassign records or revoke tokens automatically. A complete deprovisioning runbook must also:

- Revoke active OAuth tokens for connected apps.
- Freeze the user first (instant effect) before deactivation (slower).
- Reassign ownership of open records, API tokens, queues, and scheduled jobs.

---

## Common Patterns

### Pattern 1: Single-Group-Per-PermissionSet

Each IdP group maps to exactly one Permission Set. Easy to audit, easy to reason about. Recommended default.

### Pattern 2: Role-Based Group Bundle

An IdP group maps to a Permission Set Group that bundles multiple Permission Sets. Fewer IdP groups to maintain; requires discipline in keeping the PSG membership current.

### Pattern 3: Birthright + Entitlement Layer

All users get a "birthright" baseline set via their IdP tenant. Additional entitlements layer via explicit group membership. Good for large orgs with common baseline access.

### Pattern 4: Freeze-First Deprovisioning

IdP deactivation fires a `freeze-user` call first (immediate login block), then a follow-up `deactivate` after a compensating runbook reassigns records and revokes tokens. Critical for regulated industries.

### Pattern 5: Two-IdP Topology

One IdP provisions employees, another provisions contractors. Clear boundary — each tenant owns a disjoint set of users; Salesforce sees both via two SCIM connections.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple org with linear entitlements | Single-group-per-PS (Pattern 1) | Easiest audit |
| Role-based access model in IdP | PSG bundles (Pattern 2) | Maps cleanly from roles |
| Regulated industry, strict deprov SLA | Freeze-first (Pattern 4) | Legally defensible |
| Mixed workforce (employee / contractor) | Two-IdP topology (Pattern 5) | Ownership clarity |
| Salesforce license constraints | Combine with JIT provisioning on login | Avoids pre-allocating licenses |

## Well-Architected Pillar Mapping

- **Security** — correct deprovisioning semantics close the window on departed-user access.
- **Reliability** — attribute drift between IdP and Salesforce is avoided by SCIM push rather than manual sync.
- **Operational Excellence** — group-to-entitlement mapping is auditable and version-controlled.

## Review Checklist

- [ ] Source of truth for each attribute is explicit.
- [ ] Group-to-entitlement mapping is documented.
- [ ] Deactivation runbook covers freeze + token revoke + record reassignment.
- [ ] Profile strategy is documented (default profile + PS layering vs dynamic profile).
- [ ] License count monitoring in place to catch provisioning leaks.
- [ ] Tested deprovisioning end-to-end against SLA.

## Recommended Workflow

1. Confirm IdP source of truth and attribute ownership.
2. Design group-to-entitlement mapping; produce the audit table.
3. Decide profile strategy (single default + PS layering is the usual choice).
4. Build the deprovisioning runbook (freeze → revoke tokens → reassign → deactivate).
5. Pilot with a small group; monitor license consumption and lag.
6. Document ownership between IT, HR, and Salesforce admin teams.

---

## Salesforce-Specific Gotchas

1. Salesforce does not delete users — SCIM `DELETE` deactivates.
2. OAuth tokens survive user deactivation unless explicitly revoked.
3. Permission Set License assignment is separate from Permission Set assignment — SCIM mapping must handle both.
4. Profile changes via SCIM are unusual; most orgs use a default profile and layer entitlements via PS/PSG.
5. Freezing is near-instant; deactivation propagation can lag a few minutes.

## Proactive Triggers

- Deprovisioning runbook with no OAuth token revoke step → Flag Critical.
- SCIM mapping maps IdP groups to Profiles directly → Flag High. PS layering is the common best practice.
- Deactivation without prior freeze in a regulated context → Flag High.
- Orphan permission set assignment not governed by SCIM → Flag Medium.
- License burn > planned rate → Flag High.

## Output Artifacts

| Artifact | Description |
|---|---|
| Attribute mapping document | IdP attribute → Salesforce User field |
| Entitlement mapping | IdP group → PS / PSG |
| Deprovisioning runbook | Freeze → revoke → reassign → deactivate |

## Related Skills

- `security/mfa-enforcement-strategy` — authentication posture.
- `security/oauth-token-management` — token lifecycle on deactivation.
- `security/privileged-access-management` — elevated-access controls layered on top.
- `admin/user-management-and-governance` — ongoing user operations.
