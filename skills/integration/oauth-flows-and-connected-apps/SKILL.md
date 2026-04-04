---
name: oauth-flows-and-connected-apps
description: "Use when choosing or reviewing Salesforce OAuth flows and connected-app policy for integrations, including client credentials, JWT bearer, authorization code, device flow, scopes, and token lifecycle controls. Triggers: 'OAuth flow', 'connected app', 'client credentials', 'JWT bearer', 'refresh token', 'integration user'. NOT for record-level sharing design or for simple Named Credential usage when the auth-flow decision is already settled."
category: integration
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - oauth
  - connected-apps
  - client-credentials
  - jwt-bearer
  - auth-code
triggers:
  - "which OAuth flow should this Salesforce integration use"
  - "connected app scope and policy review"
  - "client credentials versus JWT bearer in Salesforce"
  - "refresh token or invalid grant troubleshooting"
  - "username password flow should we use it"
inputs:
  - "traffic direction such as system to Salesforce, Salesforce to external system, or user delegated access"
  - "whether user context is required"
  - "scope, token lifetime, IP policy, and integration-user constraints"
outputs:
  - "OAuth flow recommendation"
  - "connected-app review findings"
  - "token lifecycle and governance checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Oauth Flows And Connected Apps

Use this skill when the success or failure of an integration depends on picking the right trust model up front. OAuth flow choice is not protocol trivia. It determines whether the integration respects user context, how secrets rotate, how outages behave when tokens expire, and whether security review becomes easy or painful.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the traffic inbound to Salesforce, outbound from Salesforce, or user delegated?
- Does the use case require a human user's authority, or is it machine-to-machine with a dedicated integration principal?
- What scopes, token lifetime, revoke process, and IP/session controls are required by policy?

---

## Core Concepts

### Flow Choice Starts With Identity

Use Authorization Code when a user must grant access and their permissions matter. Use Client Credentials or JWT bearer when the workload is system-to-system. Device flow is for constrained-user-input experiences, not a shortcut around better integration design.

### Connected App Policy Is Part Of The Architecture

A connected app is not just a client ID. Scopes, token settings, IP rules, and ownership determine how the integration behaves operationally and under incident response.

### Integration Principals Need Least Privilege

Even a perfect OAuth flow is unsafe if the integration user has broad object access or sysadmin-level power. The flow and the permission model must line up.

### Token Lifecycle Is An Operations Problem

Rotation, revocation, monitoring repeated auth failures, and handling `invalid_grant` should be decided before production, not during the first outage.

---

## Common Patterns

### Client Credentials For Server-To-Server Access

**When to use:** A system needs Salesforce API access and no end-user context is required.

**How it works:** Use a connected app and a dedicated integration principal with narrow scopes and permission sets.

**Why not the alternative:** Username-password flow is weaker operationally and worse for security review.

### JWT Bearer For Certificate-Managed Server Auth

**When to use:** The organization has mature certificate management and wants server authentication without interactive consent.

**How it works:** The external system signs the assertion and exchanges it for access under a controlled principal.

### Authorization Code For Delegated Access

**When to use:** A user must explicitly authorize the app and user-level access should be preserved.

**How it works:** The app obtains consent, receives an authorization code, and manages the token lifecycle according to policy.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Machine-to-machine integration into Salesforce | Client Credentials or JWT bearer | No end-user context required |
| Enterprise-grade server auth with certificate operations already in place | JWT bearer | Strong fit for managed key posture |
| User authorizes an app to act on their behalf | Authorization Code | Preserves user context and consent |
| Legacy proposal uses username and password | Usually reject | Poor security and operability compared with OAuth-based patterns |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The chosen flow matches the actor and trust model.
- [ ] Connected app scopes and policies are intentionally narrow.
- [ ] A dedicated integration principal exists with least privilege.
- [ ] Secret or certificate rotation is documented and testable.
- [ ] Refresh token and revoke behavior are understood before go-live.
- [ ] Weak legacy patterns such as username-password flow are challenged.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Scopes do not replace user and permission-set design** - a connected app can still be overpowered through the principal behind it.
2. **Refresh token behavior is policy-sensitive** - auth works in the sandbox until token lifetime and revocation rules surface in production.
3. **User-Agent and username-password proposals linger in legacy designs** - challenge them instead of accepting them as defaults.
4. **Connected-app ownership matters during incidents** - no owner means no accountable revoke and rotation path.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OAuth decision table | Recommended flow, principal, and policy model |
| Connected-app review | Findings on scopes, secrets, policies, and weak legacy choices |
| Token operations checklist | Rotation, revocation, and outage-handling actions |

---

## Related Skills

- `admin/connected-apps-and-auth` - use when the org-wide auth inventory and setup governance are the main concern, not just integration flow selection.
- `integration/graphql-api-patterns` - use when API shape is the design issue after authentication is settled.
- `apex/callouts-and-http-integrations` - use when outbound callout handling in Apex is the real implementation problem.
