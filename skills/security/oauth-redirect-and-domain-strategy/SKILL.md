---
name: oauth-redirect-and-domain-strategy
description: "Design Connected App OAuth callback URLs, My Domain naming, Enhanced Domains cutover, and cross-environment redirect handling. Trigger keywords: oauth redirect uri, connected app callback, my domain, enhanced domains, sandbox url change, oauth login host. Does NOT cover: end-user login flow UX, Experience Cloud branding, or SAML-only SSO configuration."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "configure oauth callback url"
  - "connected app redirect uri"
  - "enhanced domains cutover"
  - "my domain strategy"
  - "sandbox oauth endpoint"
tags:
  - security
  - oauth
  - my-domain
  - connected-app
inputs:
  - List of Connected Apps and their client redirect URIs
  - Environment inventory (prod, UAT, dev sandboxes)
  - Current My Domain / Enhanced Domains state
outputs:
  - Redirect URI matrix per Connected App per environment
  - Enhanced Domains cutover plan
  - Login host strategy (login.salesforce.com vs My Domain)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# OAuth Redirect And Domain Strategy

## The Moving Parts

- **My Domain** — every org has one. Login host is now
  `acme.my.salesforce.com` (prod) or `acme--sandbox.sandbox.my.salesforce.com`
  (sandbox). Classic `login.salesforce.com` and `test.salesforce.com`
  still work for initial auth but redirect to My Domain.
- **Enhanced Domains** — enforced on all orgs. URL format stabilises
  across orgs; old URL patterns may break.
- **Connected App Callback URLs** — whitelist of exact match redirect
  URIs. Mismatch at runtime = `redirect_uri_mismatch` error.
- **Login host** — what the client sends token requests to.
  `login.salesforce.com` works for prod; for sandboxes prefer the
  sandbox My Domain directly.

## Callback URL Design

- **Exact match, not prefix**. `https://app.example.com/callback` does
  NOT match `https://app.example.com/callback?x=1` automatically.
- Put the callback URLs for **every environment** the Connected App
  serves into the Connected App definition — prod callback AND uat AND
  dev. Missing one at cutover = downtime.
- Do not use wildcards — they are not supported.

## Per-Environment Pattern

| Environment | Login Host | Client Callback |
|---|---|---|
| Production | login.salesforce.com | https://app.example.com/callback |
| UAT | test.salesforce.com | https://uat.example.com/callback |
| Developer sandbox | test.salesforce.com | https://dev.example.com/callback |

Clients usually have a per-env config toggle for base URL + login host.

## My Domain Naming

- Short, lowercased, no dashes where avoidable.
- Keep it the same across refreshes — rename = client updates.
- For sandboxes: Salesforce appends `--<sandboxname>`. Clients should
  read the host from an env var, not hardcode.

## Enhanced Domains Cutover

- Old URL patterns (`c.na123.visual.force.com`, etc.) change.
- Inventory hardcoded URLs in:
  - Apex (string literals, metadata mention).
  - LWC/Aura (fetch targets).
  - External systems (webhook registrations, integrations).
  - Email templates (absolute links).
- Run the pre-cutover "known issues" scanner Salesforce provides.
- Rehearse in a sandbox first.

## Login Host Strategy

- **Prod clients:** either `login.salesforce.com` or the org's My Domain
  directly. My Domain is preferred (no redirect bounce).
- **Sandbox clients:** the sandbox My Domain directly.
  `test.salesforce.com` redirects and some OAuth libraries handle that
  redirect awkwardly.

## Recommended Workflow

1. Enumerate Connected Apps + environments.
2. Build the redirect URI matrix (exact URLs per env).
3. Audit hardcoded URLs across Apex, LWC, metadata, email templates,
   and external registrations.
4. Standardise My Domain name; avoid renames.
5. Point OAuth clients at the org's My Domain as the login host.
6. Rehearse Enhanced Domains cutover in a sandbox.
7. Monitor `redirect_uri_mismatch` rates post-change.

## Official Sources Used

- Connected App OAuth Configuration —
  https://help.salesforce.com/s/articleView?id=sf.connected_app_create_api_integration.htm
- My Domain Overview —
  https://help.salesforce.com/s/articleView?id=sf.domain_name_overview.htm
- Enhanced Domains —
  https://help.salesforce.com/s/articleView?id=sf.domain_name_enhanced_domains_overview.htm
