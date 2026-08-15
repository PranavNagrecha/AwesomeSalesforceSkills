# Gotchas — MFA Enforcement

Non-obvious behaviours when enforcing multi-factor authentication in Salesforce.
Grounded in the Salesforce Security Guide and the Metadata API Developer Guide
(Summer '26, API 67.0).

## Gotcha 1: A Security Token Is Not a Second Factor

**What happens:** An integration or a user appends a security token to a password, and
a compliance record shows them as multi-factor authenticated.

Salesforce's own definition rules this out:

> "Multi-factor authentication (MFA) is a secure authentication method that requires
> users to prove their identity by supplying two or more pieces of evidence (or
> factors) when they log in. One factor is something the user knows, such as their
> username and password. Other factors include something the user has, such as an
> authenticator app or security key."

A security token is something the user *knows*, transmitted in the same channel as the
password. Two secrets in one channel is one factor.

**When it occurs:** In compliance self-assessments, and in any inventory that
classifies logins by whether a token was present rather than by the authentication
method.

**How to avoid:** Classify by mechanism, not by the number of strings sent.
Authenticator app, security key, or an IdP assertion that genuinely required a second
factor count. Password plus token does not, and the fix is to remove the interactive
login rather than to relabel it.

---

## Gotcha 2: SSO Delegates the Authentication, Not the Obligation

**What happens:** An org federates to an IdP and records "MFA is handled upstream."
Some population — contractors, a legacy group, service accounts — is outside the IdP's
MFA policy, and Salesforce cannot tell.

> "This contractual requirement applies equally to direct logins with a Salesforce
> username and password and to logins via single sign-on (SSO)."
> — Salesforce Security Guide

**When it occurs:** Whenever the IdP is owned by a different team, which is the normal
case, and the Salesforce team infers coverage from the existence of a policy rather
than from its scope.

**How to avoid:** Get the IdP owner to enumerate in writing which populations the MFA
policy covers **and which it excludes**. Coverage is about the exclusions. Then close
the loop with a Salesforce-side control (Gotcha 3) rather than relying on the written
assurance alone.

---

## Gotcha 3: Salesforce Cannot See That an SSO Login Used MFA Unless You Configure It

**What happens:** MFA genuinely happens at the IdP, and Login History shows nothing
distinguishing those logins. An auditor asks for evidence and there is none.

> "**Authentication Method References.** Monitor how your OpenID providers
> authenticate users that log in to your org through OpenID Connect. For example, see
> which users log in with multi-factor authentication (MFA). To show you how your
> OpenID provider is authenticating users, Salesforce pulls the authentication method
> from JSON strings in the OpenID Connect token returned by your provider. **Work with
> your provider to define the values used in the JSON strings.**"
> — Salesforce Security Guide, *Monitor Login History*

The visibility is not automatic. It requires agreeing values with the provider.

**When it occurs:** At the first audit, months after the SSO rollout, when nobody
remembers whether the claim was configured.

**How to avoid:** Make "Authentication Method References populate in Login History for
a real login" an acceptance criterion of the SSO rollout, verified by observation
rather than by configuration review. Where a control must *depend* on login strength
rather than merely report it, use session security levels — the platform enforces
those at resource-access time.

---

## Gotcha 4: `HIGH_ASSURANCE` Is the Enforceable Control, and It Is Per Profile

**What happens:** A team builds a report to find users who logged in without MFA and
follows up manually. The gap between the login and the follow-up is the exposure.

The platform can refuse instead:

> "Session security levels control access to certain types of resources based on the
> type of authentication used for logging in to the current session. For example,
> username and password authentication requires the standard session security level.
> Multi-factor authentication (MFA) requires `HIGH_ASSURANCE`."
> — Metadata API Developer Guide, `SessionSecurityLevel`

```xml
<ProfileSessionSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <profile>Finance Users</profile>
    <requiredSessionLevel>HIGH_ASSURANCE</requiredSessionLevel>
    <sessionTimeout>60</sessionTimeout>
</ProfileSessionSetting>
```

**When it occurs:** When a control is designed as detective because the preventive
option was not known.

**How to avoid:** Use `requiredSessionLevel` for populations where a non-MFA session
must not reach the data. Note the third enum value while you are there: "The `LOW`
level isn't available or used in the Salesforce UI. It's used at the API level, but
users assigned to this level experience unpredictable and reduced functionality" — it
is not a lighter-touch option, it is a broken one.

`ProfileSessionSetting` is API 40.0 and later.

---

## Gotcha 5: A Per-Profile Session Timeout Opts That Profile Out of Org-Wide Changes, Permanently

**What happens:** A profile is given a 60-minute timeout during an MFA hardening
exercise. Two years later the org tightens its session policy from 8 hours to 2, and
that profile stays at 60 minutes — or, in the inverse case, a profile set to 1440
minutes silently stays there while everyone else tightens.

> "This session timeout value applies to users of the profile and overrides the
> org-wide timeout value. **Changes to the org-wide timeout value don't apply to users
> of this profile.**"
> — Metadata API Developer Guide, `ProfileSessionSetting.sessionTimeout`

**When it occurs:** At the *second* session policy change, which is usually years
after the first and made by different people.

**How to avoid:** Set a per-profile timeout only where the profile genuinely needs to
differ, and record every profile that has one in the session policy documentation —
they are the profiles a future org-wide change will silently miss. Valid values are
0, 15, 30, 60, 90, 120, 240, 480, 720, and 1440 minutes; anything else fails to
deploy.

---

## Gotcha 6: The API-Only Permission Does Not Exempt a Human From MFA

**What happens:** A person who uses a script to query Salesforce is marked API Only,
and the org treats them as an integration outside the MFA population.

API Only governs *where* the identity can go — "they can access Salesforce only via
APIs, regardless of their other permissions" — not *how* they authenticate. If the
authentication is a username and password, it is a direct login by a human, and it
carries the same obligation and the same phishing exposure.

**When it occurs:** With analysts, data scientists, and consultants who were
provisioned as "integration users" because that was the nearest available shape.

**How to avoid:** Classify by *who authenticates*, not by which permission is set. A
human authenticating with a username and password is an interactive user regardless of
the flag. Either give them a normal user with MFA, or move their tooling onto a
token-based flow bound to a genuine, unattended service identity — which the platform
will insist has the API Only permission anyway, since
`oauthClientCredentialUser` "must have the API Only permission."

---

## Gotcha 7: Experience Cloud and External Users Are a Separate Configuration

**What happens:** An internal MFA rollout completes and is reported as org-wide. The
customer community, partner portal, and external identity users were never in scope
and nothing about the internal rollout touched them.

**When it occurs:** In every org with an Experience Cloud site, because "our users"
usually means employees to the person writing the plan.

**How to avoid:** Put external populations in the matrix explicitly, with their own
owner, their own mechanism, and their own decision — which may legitimately be
different from the internal one, since the risk profile and the friction tolerance
differ. What must not happen is that they are absent from the matrix and therefore
assumed covered.

---

## Gotcha 8: The MFA Exemption You Are Designing Around No Longer Exists

**What happens:** Two failures, and the second is now the more common one.

The classic failure: a handful of exceptions are granted during the cutover "until
we sort out X." Two years later they are still open, nobody can say what X was, and
removing them feels risky because nobody knows what depends on them.

The 2026 failure: a team designs a break-glass path around the **"Waive
Multi-Factor Authentication for Exempt Users"** permission, or around "we'll just
turn the org-wide setting off if this goes wrong." Neither works any more. The
permission still exists and is still assignable — which is why this is easy to miss
— but it "no longer automatically exempt[s] users from MFA," and holders are
"prompted to enroll and use an MFA verifier at login." The org-wide MFA setting can
no longer be deselected. Dates and quotes:
[`security/mfa-enforcement-strategy`](../../mfa-enforcement-strategy/SKILL.md).

**When it occurs:** The classic one immediately after go-live — exceptions opened
during the cutover window are the ones that survive, because they were granted under
pressure with the least documentation. The 2026 one whenever a runbook, a policy
document, or an LLM-generated design predates the enforcement waves. It surfaces at
the worst possible moment: an incident, with the break-glass administrator at a
login screen they cannot pass.

**How to avoid:** Two things, in this order.

1. **Provision a real verifier for the identity.** A break-glass admin is a
   privileged user, so it must be *phishing-resistant*: a built-in authenticator, a
   passkey, a FIDO2 security key, or certificate-based auth. Salesforce
   Authenticator and TOTP apps are valid standard MFA and do not satisfy this.
   Rehearse recovery — admin-generated temporary verification codes are the
   phishing-resistant fallback.
2. **Keep the register, and be honest about what it is.** It records who holds
   elevated access, why, approved by whom, with which compensating controls, and
   when that is next examined. Make the review structural rather than procedural: a
   required `Review_Due__c` with a validation rule capping it, a required approver,
   a required compensating control — and renewal as a **new record with a new
   approval**, never an edit to the date. An edit is invisible; a new record with a
   new approver is an event someone has to defend.

Run the review-due report to the **approvers**, not to the security team. The
approver is the person who has to justify it.

---

## Gotcha 9: Users Without a Mobile Device Are a Population, Not an Edge Case

**What happens:** A rollout assumes the authenticator app. Call-centre staff with no
phone on the floor, users in secure facilities where devices are prohibited, and
shared-workstation populations cannot enrol, and they arrive at the help desk on day
one as a surprise.

The platform's own framing already allows for this: other factors include "something
the user has, such as an authenticator app **or security key**."

**When it occurs:** At cutover, in exactly the populations least able to self-serve.

**How to avoid:** Identify these populations during the matrix step and budget the
hardware. Security keys are the answer for device-prohibited environments; a
desktop-based TOTP application can serve others. Both need procurement and
distribution lead time, which is why this is a T-30 decision, not a T-0 discovery.

---

## Gotcha 10: "TwoFa" Still Appears in the Data

**What happens:** A query or a SIEM rule filters MFA-related events on a string
containing "MFA" and silently returns nothing, because the underlying values use the
older naming.

> "Multi-factor authentication was previously called two-factor authentication. Some
> MFA-related values reference 'TwoFa'."
> — Salesforce Security Guide

**When it occurs:** When building transaction security policies, event-monitoring
queries, or SIEM correlation rules against MFA-related events.

**How to avoid:** Search for both spellings when writing any rule or query over
MFA-related values, and test the rule against a real event rather than against the
documentation's terminology. A rule that matches nothing looks identical to a rule
that matches nothing because there is nothing to match.
