---
id: my-domain-and-session-security-auditor
class: runtime
version: 1.1.0
status: deprecated
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-17
deprecated_in_favor_of: audit-router
---
# My Domain & Session Security Auditor — DEPRECATED (Wave 3b-2)

Replaced by [`audit-router`](../audit-router/AGENT.md) with `--domain=my_domain_session_security`. The full rule set spanning My Domain (enhanced-domain deployment, legacy-hostname traffic, Experience Cloud site hosts, SSO IDP URLs), MFA (coverage, bypass grants, passkey readiness), session (timeout, re-auth, HTTPS, clickjack, browser-close, concurrent-session cap), password policy (length, complexity, expiration, lockout, history, MFA-on-reset), IP + login hours, and Connected Apps (auth policies, refresh-token expiration, HTTP callbacks, high-privilege inactive owners) is preserved verbatim in [`classifiers/my_domain_session_security.md`](../_shared/harnesses/audit_harness/classifiers/my_domain_session_security.md). Legacy alias `/audit-identity-and-session` ships until Wave 7's `docs/MIGRATION.md` removal window.

## Plan

Deprecated — route to `/audit-router --domain my_domain_session_security --target-org <alias> [--focus <area>] [--benchmark baseline|high-trust]`.

## What This Agent Does NOT Do

Anything — it's deprecated. Use the router.
