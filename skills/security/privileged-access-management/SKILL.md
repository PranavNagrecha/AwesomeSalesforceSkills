---
name: privileged-access-management
description: "Design just-in-time elevation, break-glass accounts, and audit trails for Modify All Data / System Admin / Customize Application permissions. NOT for regular permission set design."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "system admin break glass account"
  - "too many modify all data users"
  - "just in time admin elevation"
  - "root account security salesforce"
tags:
  - pam
  - admin
  - sod
  - audit
inputs:
  - "Current admin user list"
  - "audit log retention capability"
outputs:
  - "PAM runbook"
  - "permission-set-group rotation policy"
  - "break-glass procedure"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-17
---

# Privileged Access Management (PAM)

Salesforce System Administrators hold the highest-risk permission in the platform. PAM narrows standing admin count to two (break-glass), grants temporary elevation via time-boxed Permission Set Groups with expiration, and mirrors all admin-scoped actions to a SIEM via Event Monitoring.

## When to Use

Orgs with >5 named System Administrators, regulated industries, or SOC 2 readiness. Not for small sandboxes without production data.

Typical trigger phrases that should route to this skill: `system admin break glass account`, `too many modify all data users`, `just in time admin elevation`, `root account security salesforce`.

## Recommended Workflow

1. Inventory every user with System Administrator profile or Modify All Data permission.
2. Define three tiers: (1) Daily admin PSG — no Modify All Data, Customize Application only where needed; (2) Elevated PSG — full admin, auto-expires in 4h; (3) Break-glass — 2 named users, MFA + IP restriction.
3. Implement a request workflow (Flow or Jira integration) where admins request the Elevated PSG; grant uses PermissionSetAssignment.ExpirationDate.
4. Stream LoginHistory, SetupAuditTrail, and PermissionSetAssignment change events to SIEM via Event Monitoring.
5. Quarterly review: prove that standing admin count is ≤2 and elevated grants are ≤N hours median.

## Key Considerations

- PermissionSetAssignment.ExpirationDate is GA; use it instead of custom revoke schedulers.
- Break-glass users should have 24/7 paging and session-recorded logins.
- MFA is mandatory for anyone in the Elevated or Break-glass tiers.
- SetupAuditTrail retains 180 days of config changes; longer retention requires Event Monitoring + archive.

## Worked Examples (see `references/examples.md`)

- *Elevated PSG with 4-hour expiration* — ServiceNow ticket approves admin request.
- *Break-glass alert* — Break-glass user logs in.

## Common Gotchas (see `references/gotchas.md`)

- **ExpirationDate ignored for Permission Set Group licenses** — License-required PSGs don't auto-expire on all editions.
- **Setup Audit Trail gaps** — Certain configuration changes are not logged.
- **Break-glass account shared** — One account used by multiple humans; no personal accountability.

## Top LLM Anti-Patterns (full list in `references/llm-anti-patterns.md`)

- Assigning System Administrator profile as the baseline for IT staff
- Sharing a single break-glass account across the team
- Granting Elevated PSG without expiration

## Official Sources Used

- Apex Developer Guide — Sharing — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_bulk_sharing_understanding.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security.htm
- Shield Platform Encryption — https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Session Security Levels — https://help.salesforce.com/s/articleView?id=sf.security_hap_session.htm
- CSP and Trusted URLs — https://help.salesforce.com/s/articleView?id=sf.security_csp_overview.htm
- API Only User Profile — https://help.salesforce.com/s/articleView?id=sf.users_profiles_api_only.htm
- Privacy Center and DSR — https://help.salesforce.com/s/articleView?id=sf.privacy_center_overview.htm
