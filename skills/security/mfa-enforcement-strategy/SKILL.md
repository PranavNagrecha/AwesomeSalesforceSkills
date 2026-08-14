---
name: mfa-enforcement-strategy
description: "Org-wide MFA rollout strategy, phased enablement, exception governance, and audit. Triggers: MFA rollout plan, MFA policy, MFA governance. NOT for per-user-type enforcement patterns — use security/mfa-enforcement-patterns."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "We need an MFA enforcement strategy for our Salesforce org before we turn on org-wide MFA"
  - "How do we roll out Salesforce multi-factor authentication without breaking integrations and SSO users"
  - "Which verification methods count for Salesforce MFA and when does SAML SSO satisfy the MFA requirement"
  - "Who can be exempt from org-wide MFA enforcement and how do we document API-only integration users"
  - "Our security team wants a checklist for Salesforce MFA contractual requirement and production org defaults"
  - "What changes in the 2026 Salesforce MFA enforcement and which permissions require phishing-resistant MFA"
tags:
  - mfa-enforcement-strategy
  - multi-factor-authentication
  - org-wide-mfa
  - sso-mfa
  - security-settings
  - verification-methods
  - phishing-resistant-mfa
inputs:
  - "Identity model: SSO (SAML/OIDC) vs Salesforce local login, and whether direct login to Salesforce is still allowed"
  - "User populations: employees, contractors, service accounts, integration users, Experience Cloud or community logins in scope"
  - "Current verification methods registered and support model (help desk, device loss, travel)"
outputs:
  - "A phased rollout plan with communications, exception handling, and validation gates"
  - "Decision record for verification methods, IdP MFA posture, and exemption criteria aligned to official Salesforce guidance"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# MFA Enforcement Strategy

Use this skill when you are defining **how** an organization turns on and sustains **multi-factor authentication (MFA)** for Salesforce human and non-human identities—not when you are wiring conditional challenges, IP-based login rules, or Flow-based login experiences. It focuses on org-wide enforcement posture, supported verification methods, Single Sign-On (SSO) delegation, exemptions, and the operational work that keeps logins working under pressure.

---

## Before Starting

Gather this context before working on anything in this domain:

- **How users authenticate today:** Salesforce username and password only, hybrid SSO plus occasional direct login, or SSO-only with the Identity Provider (IdP) as the primary gate.
- **Integration surface:** Which workloads use UI sessions versus OAuth/JWT/API-only patterns, and which accounts are true automation principals versus humans using API access.
- **Regulatory or contractual drivers:** MFA is a baseline control in Salesforce contracts and security baselines; your program still needs a rollout plan, support playbooks, and exception governance regardless of what the platform enforces by default.

---

## Core Concepts

### The 2026 enforcement events

Salesforce is "enforcing Multi-Factor Authentication (MFA) for all employee logins, including direct UI and Single Sign-On (SSO), across both production and sandbox orgs." Two waves land on **different** dates, so a single "MFA deadline" on your program plan is already wrong:

| Enforcement | Sandboxes | Production |
|---|---|---|
| MFA for all employee users | Starting June 22, 2026, staggered over approximately 7 days | Starting July 20, 2026, staggered over approximately 30 days |
| Phishing-resistant MFA (PRMFA) for privileged users, including admins | Starting June 22, 2026, staggered over approximately 7 days | Starting July 1, 2026, staggered over approximately 30 days |

Two levers you may be relying on today disappear: the org-wide MFA setting becomes active and admins "no longer have the ability to deselect or disable it," and the **Waive Multi-Factor Authentication for Exempt Users** permission "no longer automatically exempt[s] users from MFA"—holders are "prompted to enroll and use an MFA verifier at login." Rewrite any exemption-dependent runbook against the **sandbox** date, which arrives first and is where you will discover what breaks.

**SSO does not clear the bar by itself.** An SSO login satisfies enforcement only where the IdP passes a standard-MFA or phishing-resistant-MFA signal to Salesforce via ACR (Authentication Context Class Reference) or AMR (Authentication Methods Reference, RFC 8176). Where the IdP sends no such signal, those users are "required to enroll an MFA verifier in the Salesforce UI"—so an IdP that enforces MFA but omits the claim still produces a visible change for every SSO user.

### Phishing-resistant MFA and the permissions that trigger it

PRMFA applies to users with the **System Administrator profile** or any one of **Modify All Data**, **View All Data**, **Customize Application**, or **Author Apex**. Those four permissions travel on ordinary permission sets and permission set groups, so the PRMFA population is routinely far larger than the admin headcount—enumerate it from effective permission assignments, never from the profile name alone.

| Counts as phishing-resistant | Does not count |
|---|---|
| Built-in authenticators (Touch ID, Windows Hello) | Salesforce Authenticator |
| Passkeys—device-bound, or cloud-synced through a password manager or keychain (1Password, Bitwarden, iCloud Keychain) provided that manager is FIDO2/WebAuthn-compliant | Mobile TOTP apps (for example, Google or Microsoft Authenticator) |
| External FIDO2/WebAuthn security keys (for example, YubiKey) | |
| Certificate-based authentication using x.509 client certificates | |
| Admin-generated temporary verification codes | |

Salesforce Authenticator and TOTP apps remain valid **standard** MFA. They simply do not satisfy the privileged-user requirement, which is the detail that strands admin populations who "already did MFA years ago."

### Org-wide enforcement versus user self-registration

Salesforce distinguishes **requiring MFA for direct logins to the Salesforce UI** from users casually adding a verification method. Org-wide enforcement changes the login outcome for every in-scope user until they satisfy the requirement or a documented exemption applies. Treat enforcement as a **program**: communications, help desk readiness, backup codes or device replacement, and executive sponsorship matter as much as the toggle in Setup.

### Supported verification methods (product surface)

Salesforce documents several strong factors suitable for most employees, including **Salesforce Authenticator** (push or code), **time-based one-time password (TOTP)** applications, **FIDO2/WebAuthn security keys**, and **platform authenticators** where supported. Pick a **small approved set** for the enterprise so help desk procedures stay consistent; avoid an unbounded list of consumer apps unless support teams are staffed for it.

### SSO and MFA delegation

When users access Salesforce exclusively through **SSO where the IdP enforces MFA**, Salesforce can treat that path as satisfying the MFA expectation for those users—**provided** direct Salesforce login is not a realistic bypass (for example, broad password-based login still enabled for the same population). The failure mode is familiar: SSO is “MFA protected” but a subset of users retains a Salesforce password path and never registers a second factor with Salesforce. Validate **both** the IdP authentication policy and **Salesforce login channels** together.

### Exemptions and integration identities

Some categories of users or flows may be excluded or handled differently under documented Salesforce exemption patterns (for example narrowly scoped automation or legacy constraints). Exemptions should be **time-bound, approved, and rare**—each one is debt that auditors and incident responders will ask about. Prefer modern patterns for integration users (OAuth flows designed for automation) over stretching human MFA policies across machine principals.

---

## Common Patterns

### Phased rollout by persona

**When to use:** Medium and large orgs where a single “big bang” cutover risks revenue or operations.

**How it works:** Pilot with IT and admins, then business units, then contractors. Run parallel reporting on who has not registered a verification method. Pair each phase with **office hours** and scripted recovery steps.

**Why not the alternative:** Flipping enforcement for everyone at once without inventorying SSO bypass and integrations produces preventable lockouts and emergency rollbacks.

### SSO-first with Salesforce direct login disabled for employees

**When to use:** Enterprise standard is SAML or OpenID Connect from a central IdP with strong MFA at the IdP.

**How it works:** Align IdP MFA with corporate policy, remove or tightly control Salesforce direct login for employee populations, and validate break-glass admin paths.

**Why not the alternative:** Leaving parallel login paths defeats the economic and security rationale of central MFA and complicates attestation.

### Verification method standardization plus security key program

**When to use:** High-assurance teams (finance, admins, developers with deployment rights).

**How it works:** Offer FIDO2 keys and documented provisioning; keep TOTP as fallback where keys are impractical.

**Why not the alternative:** Push-only reliance on a single mobile OS vendor stack can stall travelers or regulated sites where phones are restricted.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Majority on SSO with strong IdP MFA | Drive SSO-only access; eliminate unnecessary Salesforce passwords | Centralizes MFA evidence and reduces duplicate factors |
| Mixed SSO and Salesforce login | Enforce Salesforce MFA for password path; align IdP MFA for SSO path | Closes bypass where either path is realistic |
| Heavy API automation | Use OAuth/JWT patterns appropriate to integration users; avoid treating API keys like human MFA | Keeps automation reliable and auditable |
| User holds System Administrator, Modify All Data, View All Data, Customize Application, or Author Apex | Provision a built-in authenticator, security key, or certificate-based auth before the PRMFA date | TOTP apps and Salesforce Authenticator do not satisfy the PRMFA requirement |
| Users who cannot use phones | Standardize on security keys or TOTP on corporate-managed devices | Maintains MFA without consumer phone dependency |
| Temporary vendor access | Short-lived accounts, clear offboarding, minimal exemptions | Exemptions accumulate as shadow risk |

---

## Recommended Workflow

1. **Inventory authentication paths** — List IdP connections, remaining Salesforce-password users, Experience Cloud or external identity usage, and integration accounts.
2. **Read current org posture** — From Setup and, where available, retrieved `Security.settings` metadata, note org-wide MFA-related settings and session policies (without conflating unrelated session controls with MFA).
3. **Choose allowed verification methods** — Publish the approved set, procurement for keys if needed, and help desk scripts for device loss.
4. **Close bypasses before enforcement** — Address direct login, dormant passwords, and shared accounts that cannot complete MFA personally.
5. **Pilot and measure** — Track registration completion, failed logins, and integration errors; adjust communications and training.
6. **Enable enforcement with rollback owners** — Name who can act during an incident and rehearse break-glass; once the enforcement dates pass, rehearse verification-method recovery, because disabling the setting is no longer available.
7. **Run the local checker** — From repo root: `python3 skills/security/mfa-enforcement-strategy/scripts/check_mfa_enforcement_strategy.py` (add `--manifest-dir` for optional `Security.settings-meta.xml` review).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] SSO and direct-login posture documented; no silent bypass for the populations in scope
- [ ] Verification methods standardized; help desk trained on recovery
- [ ] Integration and automation accounts reviewed; exemptions documented with owners and expiry
- [ ] Executive and legal/compliance stakeholders aligned on timelines and residual risk
- [ ] Post-cutover monitoring for login failures and IdP saturation

---

## Salesforce-Specific Gotchas

1. **Trusted IP ranges do not replace MFA** — Network trust features address different threats; do not assume office IPs negate MFA expectations for human UI login.
2. **SSO “MFA” at the IdP does not help** if users can still complete a sensitive workflow via an unaudited Salesforce password session; channel inventory is essential.
3. **Automation accounts are not humans** — Applying human MFA workflows to integration users without redesigning the auth pattern causes outages; treat them as a separate workstream.
4. **"Turn MFA off" stops being a rollback path** — After enforcement, the org-wide MFA setting cannot be deselected and the exemption permission no longer waives MFA. Any runbook whose incident step is "disable the setting" is void; your levers become verification-method recovery—including admin-generated temporary verification codes—and access restoration.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| MFA rollout runbook | Phases, owners, communications, and rollback criteria |
| Exception register | Each exemption with business justification, approver, and review date |
| Authentication architecture note | SSO, direct login, and API flows in one diagram or table |

---

## Related Skills

- `ip-range-and-login-flow-strategy` — Login Flows, session policies, and IP-based login design (not org-wide MFA program management)
- `network-security-and-trusted-ips` — Trusted IP ranges and network-level controls
- `transaction-security-policies` — Targeted step-up and policy enforcement on events
- `integration-user-management` — Integration users, OAuth/JWT patterns, and MFA waivers where applicable
