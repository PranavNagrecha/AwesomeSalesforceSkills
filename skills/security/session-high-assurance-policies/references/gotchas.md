# Gotchas — Session High Assurance Policies

## Gotcha 1: A High Assurance login requirement is reported to break asynchronous Apex

**What happens:** `@future`, Batch, and Scheduled Apex owned by the affected user stop working. There is no login error to correlate against — the job simply fails.

**When it occurs:** The user's profile has **Session Security Level Required at Login** set to **High Assurance** (`ProfileSessionSetting.requiredSessionLevel`, api_meta 264 L101471). UNVERIFIED (2026-10-20): the async conflict, and the permission-set form of the setting, come from Help KB 000392426, not the corpus — reproduce it in a sandbox before relying on it.

**How to avoid:** Set **Session Security Level Required at Login** to **None** for anyone who owns asynchronous Apex, and enforce the second factor with the **Multi-Factor Authentication for User Interface Logins** permission instead (it triggers identity verification at login, platform_events 264 L20413-20415). If you need the login-level requirement across the whole team, re-own the scheduled jobs to a dedicated automation user first.

---

## Gotcha 2: The session-level value has different literal forms — and a LOW level

**What happens:** A comparison that works in a Visualforce controller returns the wrong answer when the same logic is ported to a report or an audit query, so the gate quietly passes.

**When it occurs:** Apex `Auth.SessionManagement.getCurrentSession()` documents its returned value as `SessionSecurityLevel=STANDARD` (apexref 262 L11487) — an upper-case token. The `AuthSession` object documents its `SessionSecurityLevel` picklist as "Standard or High" (obj 264 L47595). The Apex value when elevated is not spelled out; the enum value is `HIGH_ASSURANCE` (apexref 262 L11911). A third level, `LOW`, exists at the API level (L11901-11906; api_meta 264 L101518-101520).

**How to avoid:** Write the gate as "elevated only if the value equals `HIGH_ASSURANCE`, ignoring case". An earlier version of this gotcha recommended "not blank and not `STANDARD`" — that passes a `LOW` session, so it fails open. With an exact match, any unexpected value, including a different elevated spelling, fails closed and shows up in the Standard-session test as a redirect loop rather than as exposure. Test both branches with real sessions.

---

## Gotcha 3: High Assurance is a session attribute, not a per-action authorization

**What happens:** Once a user steps up, the whole session is elevated. Every subsequent page, report, and API call in that session inherits the level until they log out. Reviewers who read "requires MFA to view SSN" assume a per-view challenge; there is not one.

**When it occurs:** Any time the design treats step-up as if it re-prompts per record. `setSessionLevel` "affects the session level of all sessions associated with the current session, such as Visualforce or UI access" (apexref 262 L11711), which widens the blast radius further.

**How to avoid:** Keep field-level security, sharing, and (where warranted) Shield Platform Encryption as the actual access controls. Use the session level to raise the bar on *reaching* the surface, and say so explicitly in the design doc so nobody removes an FLS control believing the session gate replaced it.

---

## Gotcha 4: The whole scheme can be silently disabled from Session Settings

**What happens:** Every High Assurance policy in the org stops enforcing. No error, no notification, no failed login — sensitive Setup areas simply become reachable again. UNVERIFIED (2026-10-20): this silent-disable consequence is Help-only, and the corpus says a successful identity verification raises the session to high assurance whatever the login method (apexref 262 L11411-11413) — confirm the effect in a sandbox before relying on it.

**When it occurs:** Someone moves **Two-Factor Authentication** out of the High Assurance column in Setup → Session Settings → Session Security Levels, or an IdP stops sending the SAML `SessionLevel` attribute that was upgrading SAML sessions. UNVERIFIED (2026-10-20): the per-method defaults (only Two-Factor Authentication at High Assurance) and the SAML `SessionLevel` attribute are Help-only; the corpus says only that username and password require standard and MFA requires HIGH_ASSURANCE (api_meta 264 L101497-101499).

**How to avoid:** Treat the Session Security Levels mapping as a controlled configuration item: capture it in the change record, and monitor it. Detect drift by querying `AuthSession.SessionSecurityLevel` for privileged users on a schedule rather than trusting the Setup screen.

---

## Gotcha 5: API-only and integration users have no way to answer a challenge

**What happens:** Integration logins fail, or the integration user is permanently blocked from an operation, depending on whether the policy action is *raise* or *block*.

**When it occurs:** A session-level requirement is applied broadly — org-wide session settings or a profile shared with integrations. An API-only identity has no interactive channel on which to complete identity verification; for connected apps, flows without a user approval step such as JWT bearer have their High Assurance API logins blocked (api_meta 264 L37961-37966).

**How to avoid:** Enumerate integration and API-only profiles before enabling anything, exclude them explicitly, and re-check after any permission set group recomposition. Control integration risk with the Connected App policies and IP posture covered by `security/connected-app-security-policies` instead.

