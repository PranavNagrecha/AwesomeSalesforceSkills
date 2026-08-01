# Gotchas — Session High Assurance Policies

## Gotcha 1: A High Assurance login requirement breaks asynchronous Apex

**What happens:** `@future`, Batch, and Scheduled Apex owned by the affected user stop working. There is no login error to correlate against — the job simply fails.

**When it occurs:** The user's profile or permission set has **Session Security Level Required at Login** set to **High Assurance**. Salesforce documents High Assurance session settings as intended for synchronous and UI-based processing only; they do not support asynchronous processing contexts such as future, batch, or scheduled jobs.

**How to avoid:** Set **Session Security Level Required at Login** to **None** for anyone who owns asynchronous Apex, and enforce the second factor with the **Multi-Factor Authentication for User Interface Logins** permission instead. If you need the login-level requirement across the whole team, re-own the scheduled jobs to a dedicated automation user first.

---

## Gotcha 2: The session-level value has two different literal forms

**What happens:** A comparison that works in a Visualforce controller returns the wrong answer when the same logic is ported to a report or an audit query, so the gate quietly passes.

**When it occurs:** Apex `Auth.SessionManagement.getCurrentSession()` documents its returned value as `SessionSecurityLevel=STANDARD` — an upper-case token. The `AuthSession` object documents its `SessionSecurityLevel` picklist as "Standard or High". They are different surfaces with different literals, and the Apex value when the session is elevated is not spelled out in the reference at all.

**How to avoid:** Never compare case-sensitively, and never write the gate as "elevated if the value equals the high literal". Write it as "elevated if the value is not blank and is not `STANDARD`", so an unrecognised value fails closed. Test both branches with a real Standard session.

---

## Gotcha 3: High Assurance is a session attribute, not a per-action authorization

**What happens:** Once a user steps up, the whole session is elevated. Every subsequent page, report, and API call in that session inherits the level until they log out. Reviewers who read "requires MFA to view SSN" assume a per-view challenge; there is not one.

**When it occurs:** Any time the design treats step-up as if it re-prompts per record. `setSessionLevel` is documented as influencing the level of all sessions linked to the existing session, including Visualforce and other UI entry points, which widens the blast radius further.

**How to avoid:** Keep field-level security, sharing, and (where warranted) Shield Platform Encryption as the actual access controls. Use the session level to raise the bar on *reaching* the surface, and say so explicitly in the design doc so nobody removes an FLS control believing the session gate replaced it.

---

## Gotcha 4: The whole scheme can be silently disabled from Session Settings

**What happens:** Every High Assurance policy in the org stops enforcing. No error, no notification, no failed login — sensitive Setup areas simply become reachable again.

**When it occurs:** Someone moves **Two-Factor Authentication** out of the High Assurance column in Setup → Session Settings → Session Security Levels, or an IdP stops sending the SAML `SessionLevel` attribute that was upgrading SAML sessions. The documented defaults put Username and Password, Delegated Authentication, Activation, Lightning Login, Passwordless Login, Authentication Provider, and SAML at Standard — only Two-Factor Authentication defaults to High Assurance.

**How to avoid:** Treat the Session Security Levels mapping as a controlled configuration item: capture it in the change record, and monitor it. Detect drift by querying `AuthSession.SessionSecurityLevel` for privileged users on a schedule rather than trusting the Setup screen.

---

## Gotcha 5: API-only and integration users have no way to answer a challenge

**What happens:** Integration logins fail, or the integration user is permanently blocked from an operation, depending on whether the policy action is *raise* or *block*.

**When it occurs:** A session-level requirement is applied broadly — org-wide session settings, a profile shared with integrations, or a permission set that got into a permission set group everybody has. An API-only identity has no interactive channel on which to complete identity verification, so "raise the level" has no path to success.

**How to avoid:** Enumerate integration and API-only profiles before enabling anything, exclude them explicitly, and re-check after any permission set group recomposition. Control integration risk with the Connected App policies and IP posture covered by `security/connected-app-security-policies` instead.

