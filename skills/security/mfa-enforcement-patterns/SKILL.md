---
name: mfa-enforcement-patterns
description: "Design MFA enforcement: auto-enablement, Salesforce Authenticator rollout, exceptions, service accounts, API-only users, SSO interop, and audit. Trigger keywords: MFA, multi-factor, two-factor, Salesforce Authenticator, MFA exception, MFA SSO, api-only MFA. Does NOT cover: end-user password policies, device-trust posture, or non-Salesforce IdP configuration."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "mfa enforcement plan"
  - "mfa exception policy"
  - "mfa for api only user"
  - "mfa with sso"
  - "salesforce authenticator rollout"
tags:
  - security
  - mfa
  - authentication
  - sso
inputs:
  - User population breakdown (standard, SSO, integration, API-only)
  - SSO provider in use (if any)
  - Existing MFA exceptions (if any)
outputs:
  - MFA enforcement plan
  - Exception register with expiry
  - Integration-user posture (connected apps / OAuth instead of MFA)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# MFA Enforcement Patterns

## The Baseline

Salesforce auto-enables MFA for direct logins. The work is not
"turn on MFA" — it is:

- Getting SSO users covered at the IdP.
- Handling integration / API-only users without breaking jobs.
- Managing exception requests so they do not turn permanent.
- Rolling out Salesforce Authenticator without a support-desk flood.

## User Population Matrix

| Population | MFA Responsibility | Mechanism |
|---|---|---|
| Standard direct-login user | Salesforce | Salesforce Authenticator / TOTP / security key |
| SSO user | IdP (Okta, Azure AD, etc.) | IdP MFA — must meet Salesforce MFA requirement |
| Integration user (OAuth) | N/A (token-based) | Connected App with client credentials / JWT |
| API-only human | Salesforce | MFA still required unless connected-app-only |
| Guest / Experience | Out of scope | — |

If a human uses a username/password to call an API, treat them as a
standard user for MFA purposes.

## Exception Policy

Exceptions are allowed in narrow cases — break-glass accounts, legacy
integrations being retired, etc. Every exception must have:

- A business justification.
- An owner.
- An **expiry date**, not "permanent."
- A review cadence.

Store exceptions in a custom object with required expiry validation.
Run a monthly report; auto-notify owners 14 days before expiry.

## SSO Interop

If you use SSO, Salesforce delegates MFA enforcement to the IdP, but
Salesforce still needs to **know** the login met MFA. Configure the SAML
assertion or OpenID claim to reflect the authentication context:

- SAML `AuthnContextClassRef` should be an MFA-level context.
- OIDC `amr` or `acr` should include the MFA indicator.

Without this, Salesforce may believe the login was single-factor even
though the IdP did MFA.

## Service Accounts

For non-human workloads:

- Prefer **Connected App + OAuth 2.0 JWT Bearer Flow** or **Client
  Credentials Flow**. These do not require MFA (token-based).
- For legacy Soap/REST with username/password, plan the migration —
  MFA-exempted integration users are the most common source of
  compromise.

## Recommended Workflow

1. Inventory users by type (direct, SSO, integration, API-only).
2. Verify SSO asserts MFA via AuthnContext / amr.
3. Migrate username/password integrations to Connected App + JWT or
   Client Credentials.
4. Set up an exception object with mandatory expiry.
5. Communicate to users 2-4 weeks before cutover; ship Authenticator
   setup guidance.
6. Enable MFA; monitor the login error dashboard for failures.
7. Run the monthly exception review.

## Audit

- Login History report filtered by `Authentication Method`.
- Alert on integration users that suddenly start MFA-failing (likely
  password use or leaked creds).
- Review connected apps quarterly.

## Official Sources Used

- MFA Overview —
  https://help.salesforce.com/s/articleView?id=sf.mfa_require_user_to_login.htm
- Connected App OAuth Flows —
  https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm
- MFA with SSO —
  https://help.salesforce.com/s/articleView?id=sf.mfa_with_sso.htm
