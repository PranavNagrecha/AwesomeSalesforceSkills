---
name: connected-app-security-policies
description: "Managing OAuth policies, IP relaxation, session security, PKCE, and credential rotation for Salesforce Connected Apps. Use when hardening Connected App security, rotating client secrets, configuring IP restrictions, or requiring high-assurance sessions. NOT for basic Connected App setup or creation. NOT for OAuth flow implementation (use oauth-flows-and-connected-apps)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "how do I restrict which IPs can use my Connected App"
  - "rotating client secret without breaking integrations"
  - "JWT Bearer flow returning invalid_grant error"
  - "require high assurance session for sensitive operations"
  - "PKCE configuration for web server flow"
tags:
  - connected-app
  - oauth
  - ip-relaxation
  - pkce
  - high-assurance-session
inputs:
  - Connected App name and current policy settings
  - OAuth flow type in use
  - Security requirements (IP ranges, session requirements)
outputs:
  - Configured OAuth access policies
  - IP relaxation setting recommendation
  - Session policy configuration
  - PKCE/credential rotation guidance
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Connected App Security Policies

This skill activates when a practitioner needs to harden, audit, or troubleshoot the OAuth access policies attached to an existing Salesforce Connected App — covering IP relaxation modes, PKCE, high-assurance sessions, JWT Bearer clock drift, and zero-grace-period client secret rotation.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the Connected App by name and the OAuth flow type it uses (Web Server / JWT Bearer / User-Agent / Device / Refresh Token).
- Confirm whether the org has Login IP Ranges set on profiles or network access settings — IP relaxation interacts with both.
- Note the API version of any automated tooling touching this Connected App; ECA (External Client Apps) policy model became default in API v65 and promotes credential rotation instantly with no grace period.

---

## Core Concepts

### IP Relaxation — Three Distinct Security Postures

The **oauthPolicy.ipRelaxation** field on a Connected App has exactly three values. Each carries a meaningfully different security posture:

| Value | Label in UI | Effect |
|---|---|---|
| `enforceIpRanges` | Enforce IP Restrictions | Token requests are rejected if the caller IP is outside the org's trusted IP ranges or the user's profile ranges. Strictest posture. |
| `relaxIpRangesWithSecondFactor` | Relax IP Restrictions, Enforce 2FA | Callers outside trusted IPs are challenged with a second factor rather than blocked outright. Balances security and usability. |
| `relaxIpRanges` | Relax IP Restrictions | IP restrictions are not checked at all. Appropriate only for server-to-server flows where the integration user has no IP range constraint and no human login is involved. |

Choosing `relaxIpRanges` for a Connected App used by human users eliminates a meaningful layer of defense; audit regularly to ensure this is intentional.

### PKCE and the Require Secret Constraint

PKCE (Proof Key for Code Exchange) prevents authorization code interception attacks in public clients. To enable PKCE on the Web Server flow in Salesforce:

1. Edit the Connected App → OAuth Settings → enable **Require Proof Key for Code Exchange (PKCE) Extension for Supported Authorization Flows**.
2. **You must simultaneously disable** "Require Secret for Web Server Flow" (`oauthPolicy.requireSecretForWebServerFlow = false`). These two settings are mutually exclusive: PKCE replaces the client_secret challenge; keeping Require Secret enabled will cause token exchange to fail even with a valid code_verifier.

PKCE is recommended for all public clients (mobile, SPA) regardless of whether a client secret is technically available.

### JWT Bearer Flow — 60-Second Clock Drift Window

The JWT Bearer flow authenticates without user interaction using a signed JWT. The assertion's `iat` and `exp` claims must satisfy `exp - iat <= 3 minutes` and the JWT must reach Salesforce within 60 seconds of `iat`. Any clock skew on the signing server beyond 60 seconds produces an `invalid_grant` error with no other indication of the cause. Resolution: synchronize server clocks with NTP, keep JWT TTL short (≤ 3 minutes), and log the `iat` timestamp on every issued assertion for debugging.

### High-Assurance Sessions — Three States

Salesforce session security levels apply to Connected Apps through the **High Assurance Session Required** policy. The policy has three states:

- **High Assurance** — the access token is only valid if the user authenticated at a High Assurance level (e.g. MFA). Low-assurance tokens trigger re-authentication.
- **Switch to High Assurance** — Salesforce prompts the user to step up their session to High Assurance at next login. Enforcement is deferred until step-up completes.
- **Blocked** — users whose session security level cannot satisfy High Assurance are denied access to the Connected App entirely.

Use **Blocked** for Connected Apps that access sensitive data and have no legitimate low-assurance use case. Use **Switch to High Assurance** during migration periods where legacy integrations need time to update.

### Client Secret Rotation — No Grace Period in ECA Model

In the External Client Apps (ECA) credential model (default from API v65 / Spring '25), rotating a consumer secret using the ECA API promotes the new secret **immediately**. There is no overlap window where both old and new secrets are valid. This is a breaking change from the legacy Connected App behavior where some tools provided rotation helpers with brief coexistence windows. Plan rotations as a coordinated deployment: update all consumers before or immediately after rotation; use short-lived tokens where possible to minimize the impact window.

---

## Common Patterns

### Pattern: Hardening a Server-to-Server Integration

**When to use:** A Named Credential or external system uses the JWT Bearer or Client Credentials flow to call Salesforce APIs without user context.

**How it works:**
1. Set IP Relaxation to `enforceIpRanges` and add the integration server's egress IPs to the Connected App's IP ranges (or to the integration user's profile ranges).
2. Enable "Require Secret for Web Server Flow" only if the Web Server flow is also in use; for pure JWT Bearer leave it unchecked.
3. Set High Assurance to **Blocked** since no human session is involved — this prevents credential stuffing via a stolen token.
4. Restrict OAuth scopes to the minimum required (e.g. `api` instead of `full`).
5. Schedule client secret rotation; document the zero-grace-period constraint in the runbook.

**Why not relax IP restrictions:** A compromised token combined with relaxed IP restrictions grants an attacker full API access from any network. The IP check is a cheap, effective second barrier.

### Pattern: PKCE for a Single-Page App or Mobile Client

**When to use:** A React/LWC OSS SPA or a mobile app uses the Web Server (Authorization Code) flow. The client cannot securely store a client secret.

**How it works:**
1. Generate a cryptographically random `code_verifier` (43–128 characters, URL-safe base64 per RFC 7636).
2. Compute `code_challenge = BASE64URL(SHA256(code_verifier))`.
3. Include `code_challenge` and `code_challenge_method=S256` in the authorization URL.
4. In the Connected App, enable PKCE and disable "Require Secret for Web Server Flow".
5. Submit `code_verifier` in the token request body in place of `client_secret`.

**Why not skip PKCE:** Authorization codes intercepted via redirect URI hijacking or browser history can be exchanged for tokens. PKCE binds the code to the original requester, eliminating this attack vector.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Server-to-server with known IP egress | `enforceIpRanges` | Eliminates network-level abuse of leaked tokens |
| Human SSO where IP ranges are unpredictable | `relaxIpRangesWithSecondFactor` | Preserves 2FA as the security gate without blocking roaming users |
| Public client (SPA, mobile) | PKCE + disable Require Secret | No safe place to store a client secret; PKCE is the correct substitute |
| Sensitive data API, MFA-mandatory org | High Assurance = Blocked | Ensures only MFA-verified sessions can access the Connected App |
| Credential rotation in ECA model | Coordinated same-deployment swap | No grace period exists; old secret is immediately invalid after rotation |
| JWT Bearer `invalid_grant` with no obvious cause | Check clock drift on signing server | 60-second window; NTP sync resolves most cases |

---

## Recommended Workflow

1. **Identify the Connected App and its flow type.** Pull the ConnectedApp metadata XML or review Setup > App Manager > Edit to confirm the OAuth flow, current IP relaxation value, session policy state, and whether PKCE or Require Secret is enabled.
2. **Assess IP relaxation posture.** Map the integration's source IPs. Choose `enforceIpRanges` for server-to-server, `relaxIpRangesWithSecondFactor` for human-facing flows, and document any deliberate use of `relaxIpRanges`.
3. **Configure session security.** Set High Assurance Required to **Blocked** for API-only Connected Apps. Set **Switch to High Assurance** as a migration state for human-facing apps moving toward MFA enforcement.
4. **Apply PKCE where applicable.** For public clients, enable PKCE and confirm "Require Secret for Web Server Flow" is disabled. For confidential server clients, enable Require Secret and disable PKCE.
5. **Plan client secret rotation.** Confirm whether the org is on the ECA model (API v65+). If yes, treat rotation as an atomic operation: update all consumers in the same deployment window. Document the no-grace-period behavior in the runbook.
6. **Validate JWT Bearer clock sync.** If the flow uses JWT Bearer, verify NTP sync on the signing host and ensure JWT TTL is set to ≤ 3 minutes.
7. **Run validate_repo and confirm metadata is committed.** After any Connected App metadata change, deploy via change set or SFDX and confirm the retrieved metadata matches intent.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] IP Relaxation value is documented and justified for the flow type
- [ ] PKCE enabled and Require Secret disabled (if public client), or vice versa for confidential client
- [ ] High Assurance session policy set to Blocked for API-only apps, or documented exception recorded
- [ ] Client secret rotation procedure documented with zero-grace-period warning
- [ ] JWT Bearer signing host NTP sync verified if flow is in use
- [ ] OAuth scopes restricted to minimum required

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **PKCE and Require Secret are mutually exclusive** — Enabling both causes token exchange failures with a cryptic `invalid_client_credentials` error. Salesforce does not warn you at save time; the error only appears at runtime.
2. **ECA rotation has zero grace period** — In the ECA model (v65+), rotating the consumer secret via the API promotes the new value instantly. Any active integrations using the old secret break immediately, with no overlap window. Legacy tooling that assumed a rotation buffer will cause outages.
3. **High Assurance "Switch to High Assurance" does not enforce immediately** — The "Switch" state prompts but does not block. If the intent is enforcement, it must be changed to **Blocked** after the migration window. Orgs have left integrations in "Switch" indefinitely, thinking they are enforcing MFA.
4. **JWT Bearer 60-second clock drift silently produces invalid_grant** — The error message `invalid_grant` is shared with many other JWT validation failures. Clock drift is the most common and least obvious cause. Log the JWT `iat` claim on every request to isolate this.
5. **IP Relaxation applies to the Connected App, not the user** — Setting `relaxIpRanges` on a Connected App overrides the user's profile IP range restrictions for that app's token requests. Practitioners often assume profile IP ranges are always enforced regardless of Connected App settings.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OAuth policy configuration | IP relaxation value, session security level, PKCE/Require Secret state, and scope list for the Connected App |
| Rotation runbook | Step-by-step credential rotation procedure noting zero-grace-period constraint and consumer update sequence |
| JWT Bearer validation checklist | Clock sync status, JWT TTL, claim log format |

---

## Related Skills

- `security/oauth-flows-and-connected-apps` — Use when the question is about OAuth flow types, token exchange mechanics, or initial Connected App creation rather than hardening existing policies.
- `security/api-security-and-rate-limiting` — Use alongside this skill when scope minimization and rate limit enforcement on API consumers is also required.
- `architect/security-architecture-review` — Use when a full org-level security review is needed beyond individual Connected App policies.
