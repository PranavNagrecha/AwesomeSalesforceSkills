---
name: oauth-token-management
description: "Use when work depends on how Salesforce OAuth access and refresh tokens are issued, refreshed, rotated, revoked, or introspected for a Connected App or API client—including unexpected logouts, invalid_grant after refresh, or designing token incident response. NOT for choosing which OAuth grant or Connected App flow to implement (use integration/oauth-flows-and-connected-apps), Named Credential packaging (use integration/named-credentials-setup), or broad Connected App IP and PKCE policy hardening without a token-lifecycle angle (use security/connected-app-security-policies)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "Our integration suddenly gets invalid_grant when the refresh token used to work—what changed on the Salesforce side?"
  - "Does revoking the user's OAuth access token in Salesforce also kill every API session that integration opened?"
  - "We need to rotate or invalidate refresh tokens after a suspected credential leak—what is the correct order of operations?"
  - "How long do Salesforce OAuth access tokens actually live when the Connected App session timeout differs from org session settings?"
  - "Can we call an endpoint to see whether an access token is still valid before we call the REST API?"
tags:
  - oauth-token-management
  - oauth-2
  - refresh-token
  - token-revocation
  - connected-app
  - token-introspection
  - session-timeout
inputs:
  - "Connected App name or metadata, OAuth scopes in use, and which grant type produced the tokens (authorization code, refresh token, JWT bearer, device, etc.)."
  - "Whether the problem appears at token issuance, refresh, API call, or after admin or security action (revocation, password reset, policy change)."
outputs:
  - "A clear model of access vs refresh token lifetime, rotation behavior, and what each revocation target invalidates."
  - "Concrete next steps: which Setup policies to inspect, which revoke or introspection calls apply, and what clients must do to obtain a new grant."
dependencies:
  - integration/oauth-flows-and-connected-apps
  - security/connected-app-security-policies
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# OAuth Token Management

Use this skill when the hard part is no longer “getting OAuth to work once,” but keeping tokens correct over time: refresh failures, security incidents, policy tightening, or explaining why one revocation action behaved differently than another. Salesforce ties access token lifetime to Connected App and org session settings, models refresh tokens under Connected App OAuth policies, and exposes programmatic revocation and (where licensed) introspection endpoints. Misunderstanding any of those layers produces flaky integrations, false “random” logouts, and incomplete incident cleanup.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Which tokens exist:** access token only (some server-to-server grants), or access plus refresh (offline-style integrations).
- **Where policies are set:** the specific Connected App’s OAuth settings, org-wide Session Settings, and any login policies that force re-authentication.
- **What changed recently:** refresh token policy edits, session timeout reductions, user password or MFA resets, IP relaxations, or secret rotation—each can surface as `invalid_grant` or `401` on the next refresh or API call.

---

## Core Concepts

### Access token lifetime is the tighter of two clocks

An OAuth access token’s usable lifetime is bounded by the **Connected App session timeout** and the **org session timeout** from Setup session settings. The effective value is the **minimum** of the two, within the platform-supported range described in Salesforce Help for Connected App session policies. Treat documentation as authoritative when quoting exact bounds; do not assume a fixed two-hour lifetime in every org.

### Refresh tokens are a separate credential with their own policy

When the client requests offline access (`refresh_token` / `offline_access` scopes as applicable), Salesforce issues a refresh token subject to the Connected App **refresh token policy** (for example immediate expiry, fixed lifetime, or valid-until-revoked). That policy determines how often users or headless processes must re-run the interactive or initial grant—not the access token TTL alone.

### Revocation is target-specific: access token vs refresh token

Calling the OAuth **revoke** endpoint with an access token ends the session represented by that token. Revoking a **refresh token** invalidates the refresh credential and, per Salesforce documentation for token revocation, also invalidates outstanding access tokens issued under that OAuth grant for that user and Connected App combination. Teams that only revoke access tokens during an incident can leave long-lived refresh paths active if they do not also address refresh credentials.

### Refresh token rotation hardens replay of stolen refresh tokens

Salesforce documents **refresh token rotation** (see release notes for your edition) so that a consumed refresh token cannot be replayed: the authorization server returns a new refresh token alongside the new access token, and the client must persist the latest refresh secret. Clients that ignore the newly issued refresh token appear “randomly” broken after the first rotation event.

---

## Common Patterns

### Pattern: Incident response—remove stolen credentials cleanly

**When to use:** A client secret, refresh token, or integration user credential may have leaked.

**How it works:** Rotate or revoke the compromised artifact using the revoke endpoint or Setup actions documented for your scenario; force affected users or the integration user through a controlled re-authorization if refresh tokens were revoked; verify no long-lived `valid until revoked` refresh tokens remain where policy now requires shorter exposure.

**Why not the alternative:** Rotating only the access token while leaving a compromised refresh token in the wild leaves a silent re-entry path for an attacker.

### Pattern: Long-running jobs that must survive access token expiry

**When to use:** Batch or middleware holds an access token for longer than the effective session timeout.

**How it works:** Obtain refresh-capable scopes only when appropriate, persist the latest refresh token when rotation is enabled, refresh before expiry, and keep the Connected App refresh policy aligned with operational reality (immediate expiry is rarely compatible with unattended jobs).

**Why not the alternative:** Extending Connected App session timeout to “avoid refresh logic” widens the blast radius of a single stolen access token.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|-----------|----------------------|--------|
| User reports “logged out of integration everywhere” after admin revoked OAuth | Confirm whether refresh token was revoked; if yes, expect full re-consent or re-login | Refresh revocation invalidates dependent access tokens for that grant |
| `invalid_grant` right after policy change | Compare old vs new refresh token policy and session timeouts | Stricter policy often invalidates existing refresh tokens |
| Need to verify a token before a sensitive server action | Use documented **token introspection** where available and permitted | Avoid home-grown “call `/limits` as a ping” checks that do not reflect token state semantics |
| Headless integration should never hold a refresh token | Prefer JWT bearer or another flow that matches the trust model | Fewer long-lived bearer artifacts to protect |

---

## Recommended Workflow

1. **Confirm the token path:** Identify grant type, scopes, and whether refresh tokens are in play for this Connected App.
2. **Read effective timeouts:** Inspect Connected App OAuth session policy and org Session Settings; record the implied access token lifetime behavior from official Help rather than guessing.
3. **Reproduce the failure class:** Distinguish HTTP 401 from Salesforce API, `invalid_grant` from the token endpoint, and UI-driven re-authentication prompts—each maps to different fixes.
4. **Choose the smallest revocation surface:** Decide whether to revoke access only, refresh only, or reset the entire grant; document impact on parallel sessions.
5. **Update clients for rotation:** If rotation is enabled, verify the client persists the newest refresh token on every refresh response before closing the incident.
6. **Validate in a lower environment:** Re-run the integration’s token lifecycle (issue, refresh, API call, revoke) against a sandbox copy of policies.

---

## Review Checklist

- [ ] Connected App refresh token policy matches the integration’s unattended vs interactive needs.
- [ ] Access token lifetime assumptions are aligned with org + Connected App session settings.
- [ ] Incident or rotation playbooks state whether refresh tokens are rotated or revoked, not only access tokens.
- [ ] Clients handle `invalid_grant` by re-establishing the grant rather than infinite blind retries.
- [ ] Any use of introspection or revoke endpoints follows current OAuth endpoint documentation (HTTPS, correct token type parameters).

---

## Salesforce-Specific Gotchas

1. **Tighter session wins** — A conservative org-wide session timeout caps a permissive Connected App timeout; debugging “why is my token short” requires both settings.
2. **Policy changes invalidate existing refresh tokens** — Moving from long-lived to stricter refresh behavior can invalidate outstanding refresh tokens immediately; plan maintenance windows.
3. **Rotation requires client discipline** — Enabling rotation without updating middleware to store the new refresh token fails at the next refresh in ways that look like Salesforce “instability.”

---

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Token lifecycle diagram | Who holds access vs refresh, when each expires, and what revocation clears |
| Runbook snippet | Ordered steps for revoke, re-auth, and verification queries after an incident |
| Policy audit table | Connected App refresh policy, session timeout, and org session row for each integration |

---

## Related Skills

- **integration/oauth-flows-and-connected-apps** — Selecting and implementing the correct grant and Connected App model up front.
- **security/connected-app-security-policies** — IP relaxation, PKCE, high assurance, and consumer secret rotation patterns around the app shell.
- **security/session-management-and-timeout** — Org-wide session and login behavior that interacts with OAuth access token lifetime.
- **security/api-security-and-rate-limiting** — Scope minimization and API consumption patterns once valid tokens exist.
