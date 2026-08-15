---
name: mfa-enforcement-patterns
description: "Design MFA enforcement: auto-enablement, Authenticator rollout, exceptions, API-only users, SSO interop. Triggers: MFA enforcement, MFA exception, api-only MFA, MFA SSO. NOT for org-wide MFA policy sequencing — use security/mfa-enforcement-strategy."
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
  - Elevated-access register with review date and phishing-resistant verifier
  - Integration-user posture (connected apps / OAuth instead of MFA)
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# MFA Enforcement Patterns

MFA is not a decision. It is a contractual requirement with a platform default behind
it:

> "To protect users from security threats like phishing, credential stuffing, and
> account takeovers, Salesforce requires MFA for logins to Salesforce products. This
> contractual requirement applies equally to direct logins with a Salesforce username
> and password and to logins via single sign-on (SSO)."
>
> "To help customers satisfy the MFA requirement, MFA is a default part of the direct
> login experience for production orgs."
> — Salesforce Security Guide

Two clauses carry the work. **"Applies equally to … SSO"** means delegating
authentication to an identity provider does not delegate the obligation. **"A default
part of the direct login experience"** means the interactive population is already
handled — so the remaining work is everything that is *not* an interactive login.

This skill covers the enforcement mechanics: population segmentation, integration
migration, SSO coverage and evidence, session-level enforcement, and exception
governance. Org-wide policy *sequencing* — waves, comms plans, org-level rollout
strategy — is `security/mfa-enforcement-strategy`.

---

## Read this before designing any MFA exception

The 2026 enforcement waves removed the platform's exemption lever. Anything in this
skill that looks like a bypass is a **governance and evidence** construct, not a way
to keep a user off MFA.

Per [`security/mfa-enforcement-strategy`](../mfa-enforcement-strategy/SKILL.md),
which owns the enforcement timeline:

| Enforcement | Sandboxes | Production |
|---|---|---|
| MFA for all employee users | Starting June 22, 2026, staggered over approximately 7 days | Starting July 20, 2026, staggered over approximately 30 days |
| Phishing-resistant MFA (PRMFA) for privileged users, **including admins** | Starting June 22, 2026, staggered over approximately 7 days | Starting July 1, 2026, staggered over approximately 30 days |

**These dates are in the past.** For any org reading this today the waves have
already landed, so the question is never "how do we prepare an exemption" — it is
"which of our controls stopped working, and what replaced them."

> ⚠ **The sandbox row may have shifted, and this skill does not assert the
> revision.** Secondary sources report that Salesforce paused the all-employee wave
> on 2026-07-01 and restarted the sandbox rollout on 2026-07-06, with production
> still landing 2026-07-20 over a longer stagger. That was not confirmable against a
> primary source in this pass — the MFA enforcement Help page does not serve its text
> to a fetcher — so the table above carries the originally published dates. Before
> quoting any of these to an auditor, read the Help page yourself.

Two levers disappeared:

1. **The org-wide MFA setting can no longer be deselected.** Admins "no longer have
   the ability to deselect or disable it." Any runbook whose incident step is
   "turn MFA off" is void.
2. **The "Waive Multi-Factor Authentication for Exempt Users" permission no longer
   waives MFA.** The permission exists — Salesforce Help documents it under
   *Exclude Exempt Users from MFA for Salesforce Orgs* — but it "no longer
   automatically exempt[s] users from MFA," and holders are "prompted to enroll and
   use an MFA verifier at login." Assigning it today changes nothing about whether
   a user is challenged.

**The consequence for exception design.** A break-glass administrator is a
*privileged* user, so they are in the PRMFA population and need a
phishing-resistant verifier — a built-in authenticator, a passkey, a FIDO2 security
key, or certificate-based auth. Salesforce Authenticator and TOTP apps do not
satisfy it. An `MFA_Elevated_Access__c` register (Example 4) is still worth
building, but its job changed: it records *who holds elevated access, under what
justification, with which compensating controls, and when that is reviewed*. It
does not, and after these dates cannot, exempt anyone from the challenge.

The recovery levers that remain are verification-method recovery — including
admin-generated temporary verification codes, which are themselves
phishing-resistant — and access restoration. Rehearse those, not deactivation.

---

## Before Starting

1. **Segment the population before doing anything.** Every failed rollout fails on a
   population nobody listed, and it is never the interactive users.

2. **Build the integration inventory from Login History, not from memory.** The
   query in [`references/examples.md`](references/examples.md) Example 1 surfaces
   every identity still using a username-password flow.

3. **Get the IdP coverage statement in writing**, specifically naming which
   populations the MFA policy *excludes*.

4. **Identify populations without a mobile device.** Security keys and desktop TOTP
   need procurement lead time — this is a T-30 decision, not a cutover discovery.

---

## Core Concepts

### What counts as a factor

> "One factor is something the user knows, such as their username and password. Other
> factors include something the user has, such as an authenticator app or security
> key."

A **security token is not a second factor**: it is something the user knows, sent in
the same channel as the password.

### The population matrix

| Population | Who enforces | Mechanism |
|---|---|---|
| Direct interactive login | Salesforce | Default in production orgs — already handled |
| SSO users | The IdP | IdP policy; the obligation stays with you |
| Non-human integration | N/A | Token-based OAuth — no interactive login exists |
| Human using username/password against an API | Salesforce | Treat as an interactive user |
| Break-glass admin | Salesforce | Phishing-resistant MFA (privileged user) + register row + compensating control. No exemption is available |
| Experience Cloud / external | Configured separately | Separate decision, separate owner |

### `HIGH_ASSURANCE` is the enforceable control

> "Session security levels control access to certain types of resources based on the
> type of authentication used for logging in to the current session. For example,
> username and password authentication requires the standard session security level.
> Multi-factor authentication (MFA) requires `HIGH_ASSURANCE`."

```xml
<ProfileSessionSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <profile>Finance Users</profile>
    <requiredSessionLevel>HIGH_ASSURANCE</requiredSessionLevel>
    <sessionTimeout>60</sessionTimeout>
</ProfileSessionSetting>
```

API 40.0 and later. `LOW` is not a lighter option — "It's used at the API level, but
users assigned to this level experience unpredictable and reduced functionality."

**The side effect that outlives the decision:** a per-profile `sessionTimeout`
"overrides the org-wide timeout value" and "Changes to the org-wide timeout value
don't apply to users of this profile." That profile is permanently out of future
org-wide session policy changes.

### SSO evidence is not automatic

> "Salesforce pulls the authentication method from JSON strings in the OpenID Connect
> token returned by your provider. **Work with your provider to define the values used
> in the JSON strings.**"

Without that agreement, Login History cannot show which logins met MFA.

### Integrations migrate; they do not get exempted

```xml
<isClientCredentialEnabled>true</isClientCredentialEnabled>
<oauthClientCredentialUser>etl.warehouse@example.com</oauthClientCredentialUser>
```

The platform enforces the design: `oauthClientCredentialUser` "must have the API Only
permission." MFA then stops applying because there is no interactive login.

---

## Common Patterns

### Pattern A — matrix first, then mechanism per segment

Build the population matrix, then assign an owner and a mechanism to each row. The
matrix is the deliverable; the toggles follow from it.

### Pattern B — integration migration as the long pole

Client credentials or JWT bearer, parallel-run, with completion measured as thirty
days with no username-password subtype in Login History — then block the legacy flows
org-wide. Example 2.

### Pattern C — SSO coverage plus Salesforce-side enforcement

A written coverage statement from the IdP owner, Authentication Method References
configured and verified, and `requiredSessionLevel = HIGH_ASSURANCE` where a control
must depend on login strength rather than report on it. Example 3.

### Pattern D — an exception register that records rather than exempts

Required `Review_Due__c` capped by a validation rule, a required approver, a required
compensating control, a required phishing-resistant `Verifier_Type__c`, and renewal
as a **new record with a new approval** — never an edit to the date. Example 4.

Since the 2026 waves this register grants nothing. It is the evidence trail for
elevated access and its compensating controls, and the 180-day cap is a *review*
cadence, not a period of validity — there is no underlying platform waiver left for
it to bound. Treat any row that reads as "this user is excused from MFA until
`Review_Due__c`" as a defect in the register, not a control.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| Interactive users in a production org | Already covered by the platform default; focus elsewhere |
| Nightly job using username + password + token | Migrate to client credentials or JWT bearer |
| No shared secret may cross the wire | JWT bearer |
| SSO in place | Written coverage statement + Authentication Method References + `HIGH_ASSURANCE` where it matters |
| Sensitive data population | `requiredSessionLevel = HIGH_ASSURANCE` — enforce, do not report |
| Analyst running scripts with a password | Interactive user — MFA applies regardless of API Only |
| Break-glass admin | Phishing-resistant verifier (built-in authenticator, passkey, FIDO2 key, or certificate) — they are a privileged user. Plus a register row with approver, review date, and named compensating controls. Not an exemption; none is available |
| Someone proposes assigning "Waive Multi-Factor Authentication for Exempt Users" | It no longer waives MFA. Provision a verifier instead |
| Device-prohibited facility | Security keys, procured at T-30 |
| Experience Cloud users | Separate matrix row, separate owner, separate decision |
| Writing a SIEM rule on MFA events | Search for both "MFA" and "TwoFa" |

---

## Recommended Workflow

1. **Build the population matrix** and assign every user and every integration in the
   org to exactly one row, with a named owner per row.
2. **Run the Login History query** to find every identity still using a
   username-password flow, and give each one an owner and a target date.
3. **Migrate integrations** to client credentials or JWT bearer, running in parallel
   with the existing credential rather than replacing it.
4. **Close the SSO gap**: obtain the written coverage statement naming exclusions,
   configure Authentication Method References with the provider, and verify they
   populate for a real login.
5. **Enforce where reporting is not enough**: set `requiredSessionLevel` to
   `HIGH_ASSURANCE` on the profiles whose data warrants it, accepting the per-profile
   session timeout side effect.
6. **Provision phishing-resistant verifiers for every privileged identity** —
   including break-glass admins — and rehearse verification-method recovery, since
   deactivating MFA is no longer a rollback path. Then **stand up the elevated-access
   register** with a structural review date, a required approver, and a required
   compensating control, and route the review-due report to the approvers.
7. **Cut over, then finish**: monitor login failures hourly on day one, close every
   exception opened during the cutover window at T+7, and at T+30 confirm no
   username-password subtype remains before blocking the legacy flows org-wide.

---

## Review Checklist

- [ ] Every user and integration assigned to exactly one matrix row, with an owner
- [ ] Integration inventory built from Login History, not from memory
- [ ] No integration is handled by an exemption rather than a flow migration
- [ ] `oauthClientCredentialUser` identities hold the API Only permission
- [ ] Written IdP coverage statement naming the excluded populations
- [ ] Authentication Method References configured and verified on a real login
- [ ] `requiredSessionLevel = HIGH_ASSURANCE` on sensitive-data profiles
- [ ] Per-profile session timeouts recorded in the org-wide session policy doc
- [ ] No security token counted as a second factor anywhere in the assessment
- [ ] Exception register has required review date, validation cap, approver, and
      compensating control; renewal creates a new record
- [ ] No row in the register is described, to anyone, as exempting a user from the
      MFA challenge — the platform waiver no longer exists
- [ ] Break-glass and other privileged identities hold a **phishing-resistant**
      verifier, not Salesforce Authenticator or a TOTP app
- [ ] Incident runbooks contain no "disable org-wide MFA" step; recovery is
      verification-method recovery and access restoration
- [ ] Expiring-soon report routed to approvers, not to the security team
- [ ] Non-mobile populations identified and hardware procured before cutover
- [ ] Experience Cloud and external users present in the matrix
- [ ] Legacy flows blocked org-wide only after 30 clean days of evidence

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **A security token is not a second factor.**
2. **SSO delegates the authentication, not the obligation.**
3. **Salesforce cannot see that an SSO login used MFA** unless Authentication Method
   References are configured with the provider.
4. **`HIGH_ASSURANCE` is the enforceable control**, and it is per profile.
5. **A per-profile session timeout opts that profile out of org-wide changes,
   permanently.**
6. **The API-Only permission does not exempt a human from MFA.**
7. **Experience Cloud and external users are a separate configuration.**
8. **Exceptions without a structural review date become permanent** — and since the
   2026 waves they exempt nobody in the first place. The "Waive Multi-Factor
   Authentication for Exempt Users" permission exists but no longer waives MFA.
9. **Users without a mobile device are a population, not an edge case.**
10. **"TwoFa" still appears in the data** — search for both spellings.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Population matrix | Every user and integration in exactly one row, with the enforcing party, the mechanism, and a named owner |
| Integration migration plan | Per identity: current flow from Login History, target flow, owner, target date, and the 30-day evidence window |
| IdP coverage statement | Written, from the IdP owner, naming the populations the MFA policy covers **and excludes** |
| Session-level enforcement record | Which profiles carry `HIGH_ASSURANCE`, and which now sit outside org-wide session policy because of a custom timeout |
| Elevated-access register | Object with a structural review date, approver, compensating control, and a phishing-resistant `Verifier_Type__c`, plus the monthly review-due report routed to approvers. Evidence, not an exemption — the platform waiver no longer exists |
| Cutover evidence | Day-one login failure rate, exceptions opened during the window, and the T+30 Login History confirmation before blocking legacy flows |

---

## Related Skills

- `security/mfa-enforcement-strategy` — org-wide policy sequencing, waves, and the
  communications plan this skill's mechanics sit inside
- `security/api-only-user-hardening` — the token-based identity that integrations
  migrate onto
- `security/session-management-and-timeout` — session security levels and the
  org-wide timeout policy that per-profile settings opt out of
- `security/ip-relaxation-and-restriction` — the network-layer control that covers
  what MFA cannot, and vice versa
