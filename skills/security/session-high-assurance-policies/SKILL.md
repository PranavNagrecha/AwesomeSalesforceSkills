---
name: session-high-assurance-policies
description: "Enforce step-up authentication for sensitive pages/objects using High Assurance session level and login flow policies. NOT for initial MFA enrollment UX — use admin/org-setup-and-configuration."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "step up auth for sensitive record"
  - "high assurance session salesforce"
  - "require mfa to view ssn field"
  - "session level policy"
tags:
  - session
  - mfa
  - high-assurance
inputs:
  - "Which objects/pages require step-up"
  - "current login policies"
outputs:
  - "Session Settings policy"
  - "profile/permission-set config"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-07-31
---

# Session High Assurance Policies

Every Salesforce session carries a security level. `AuthSession.SessionSecurityLevel` is documented as "Standard or High, depending upon the authentication method used." The level is decided by *how the session was created*, not by what the user is doing, so "require MFA to see this field" is never a single switch — it is a combination of a login-method mapping, a policy that names a protected operation, and (for anything Salesforce does not ship a policy for) Apex that reads and raises the level itself.

---

## Before Starting

- Confirm which login methods your population actually uses. The default level per method is set in Session Settings and decides whether anyone reaches High Assurance at all.
- Confirm whether the target is a **Setup operation** (Salesforce ships a policy), a **Connected App** (policy lives on the app), or a **record/field/page** (needs Apex or a login flow).
- Confirm there are no `@future`, Batch, or Scheduled jobs owned by the affected profiles — see the async-Apex interaction in `references/gotchas.md` before touching "Session Security Level Required at Login".
- Confirm the org's integration/API-only profiles are excluded from whatever you set.

---

## Core Concepts

### Login method → default session security level

Set in Setup → Session Settings → **Session Security Levels**, which sorts each login method into a Standard or High Assurance column.

| Login method | Documented default level |
|---|---|
| **Username and Password** | Standard |
| **Delegated Authentication** | Standard |
| **Activation** | Standard |
| **Lightning Login** | Standard |
| **Passwordless Login** | Standard |
| **Authentication Provider** (social / OpenID Connect) | Standard |
| **SAML** | Standard — the IdP can override per-assertion with the `SessionLevel` attribute |
| **Two-Factor Authentication** | High Assurance |

The practical consequence: in an org where everyone logs in with username + password and MFA is satisfied by a *post-login* verification, sessions can still be Standard. Moving **Two-Factor Authentication** out of the High Assurance column is the single change that silently disables every High Assurance policy in the org.

### The three places a High Assurance requirement can be set

| Where | Setup path | Scope | What it does when unmet |
|---|---|---|---|
| **Session security level policies** | Setup → Identity Verification → Session Security Level Policies | Named Setup operations, org-wide | Prompts the user to raise the session level, or blocks the operation outright |
| **Session Security Level Required at Login** | Profile or permission set, Session Settings section | Every session for the assigned users | Forces identity verification during login; the session starts High Assurance or not at all |
| **Connected App session policy** | App Manager → Connected App → Session Policies | One Connected App's tokens | Governed by `security/connected-app-security-policies` — read that skill, this one does not restate it |

### Operations Salesforce lets you gate declaratively

Session Security Level Policies covers a fixed list of Setup areas: Reports and Dashboards, Manage Encryption Keys, Manage Auth. Providers, Manage Certificates, Manage Connected Apps, Manage Data Export, Manage IP Addresses, Manage Login Access Policies, Manage Password Policies, Manage Permission Sets and Profiles, Manage Roles, Manage Sharing, Manage Two-Factor Authentication in API, Manage Two-Factor Authentication in User Interface, Unlock Users and Reset Passwords, View Event Log Files, View Health Check.

There is **no entry for an sObject, a field, or a Visualforce/LWC page**. Anything record-level is Apex work.

### The Apex API — `Auth.SessionManagement`

`UserInfo` has no session-security accessor. Its only session method is `getSessionId()`. The session-level API lives on `Auth.SessionManagement`:

| Member | Signature | Use |
|---|---|---|
| `getCurrentSession()` | `Map<String, String>` | Read `SessionSecurityLevel`, `SessionType`, `LoginType`, `LoginHistoryId`, `SourceIp`, `NumSecondsValid`, `UsersId`, `ParentId` |
| `setSessionLevel(Auth.SessionLevel)` | `void` | Raise/lower with `Auth.SessionLevel.HIGH_ASSURANCE` or `Auth.SessionLevel.STANDARD` |
| `generateVerificationUrl(Auth.VerificationPolicy, String, String)` | `String` | Build the identity-verification URL to redirect a Standard session to; policy value `Auth.VerificationPolicy.HIGH_ASSURANCE` |
| `getRequiredSessionLevelForProfile(String profileId)` | `Auth.SessionLevel` | Read the profile's configured login requirement |
| `validateTotpTokenForUser(String totpCode, String description)` | `Boolean` | Verify a TOTP code inside a custom step-up UI |
| `inOrgNetworkRange(String ipAddress)` / `isIpAllowedForProfile(String profileId, String ipAddress)` | `Boolean` | Combine network posture with session level |

The documented `getCurrentSession()` example returns `SessionSecurityLevel=STANDARD` — an upper-case token, not the `Standard` / `High` picklist form used by the `AuthSession` object. Do not reuse one comparison string for both surfaces.

---

## Common Patterns

### Pattern 1: Apex step-up gate in front of a sensitive controller

**When to use:** an LWC/Visualforce page or an Apex entry point exposes data that must never be read from a Standard session, and no Session Security Level Policy covers it.

```apex
// Returns null when the session is already elevated; otherwise the URL to redirect to.
public static String verificationUrlIfNeeded(String returnUrl) {
    String level = Auth.SessionManagement.getCurrentSession().get('SessionSecurityLevel');
    if (String.isNotBlank(level) && !'STANDARD'.equalsIgnoreCase(level)) {
        return null;
    }
    return Auth.SessionManagement.generateVerificationUrl(
        Auth.VerificationPolicy.HIGH_ASSURANCE, 'View compensation detail', returnUrl);
}
```

Full controller, including the `WITH USER_MODE` read and the failure path, is in `references/examples.md`.

**Why not a permission set with "Session Security Level Required at Login":** that raises the bar for *every* session those users open, including the ones that run their batch jobs. See `references/gotchas.md` Gotcha 1.

### Pattern 2: Declarative gate for a Setup operation

**When to use:** the requirement is one of the 17 named operations — most commonly Reports and Dashboards, Manage Data Export, or View Event Log Files.

1. Setup → Session Settings → Session Security Levels: confirm **Two-Factor Authentication** is in the High Assurance column.
2. Setup → Identity Verification → Session Security Level Policies: pick the operation.
3. Choose **raise the session security level to high assurance** when the user should be able to step up in place; choose **block** when there is no legitimate reason for that population to reach the operation at all.
4. Verify with a test user whose profile has no MFA-satisfying login method — confirm the block/prompt actually appears.

**Why not Apex here:** the platform already enforces it at the Setup entry point, including API paths an Apex guard would not see.

### Pattern 3: Elevate inside a login flow instead of at login

**When to use:** the session should be High Assurance for users who arrived by a specific route (a network range, a particular IdP) without a profile-wide login requirement.

Call `Auth.SessionManagement.setSessionLevel(Auth.SessionLevel.HIGH_ASSURANCE)` from the login-flow Apex once your own verification succeeds. `setSessionLevel` influences the level of sessions linked to the current one — including Visualforce and other UI entry points — so confirm the blast radius in a sandbox first. `inOrgNetworkRange(ipAddress)` and `isIpAllowedForProfile(profileId, ipAddress)` are the supported way to make that route decision in Apex.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Protect a named Setup area (reports, data export, event log files) | Session Security Level Policy | Enforced by the platform at every entry point, including API |
| Protect one field or one record page | Apex gate (Pattern 1) plus field-level security | No declarative policy covers record data; FLS is still the access control |
| Users own batch/scheduled/`@future` jobs | Never "Session Security Level Required at Login" | High Assurance login is documented as unsupported in asynchronous contexts |
| Requirement is "everyone must use MFA" | MFA permission / `security/mfa-enforcement-strategy` | High Assurance is a session attribute, not an enrollment control |
| Requirement is scoped to one Connected App | Connected App session policy | `security/connected-app-security-policies` owns the three-state policy |
| Integration / API-only profiles in scope | Explicitly exclude them | They have no interactive channel on which to satisfy a challenge |

---

## Recommended Workflow

1. Classify the requirement: named Setup operation, Connected App, or record/field/page. Only the first is declarative.
2. Verify the login-method mapping in Setup → Session Settings → Session Security Levels. If no method your users actually use lands in the High Assurance column, nothing downstream will ever be satisfied.
3. Apply the narrowest control that fits — a Session Security Level Policy for a named operation, an Apex gate built on `Auth.SessionManagement` for record data.
4. Enumerate the async-Apex owners and integration/API-only profiles in scope and exclude them before enabling anything.
5. Test with a real Standard-level session: confirm the prompt or block fires, and confirm that after stepping up the user is not re-prompted in the same session.
6. Instrument: query `AuthSession` for `SessionSecurityLevel` by user, and correlate with `LoginHistory` via `LoginHistoryId`.

---

## Review Checklist

- [ ] Session Settings → Session Security Levels confirmed; Two-Factor Authentication is in the High Assurance column
- [ ] The control is applied at the narrowest scope that satisfies the requirement
- [ ] No profile owning `@future`, Batch, or Scheduled Apex has "Session Security Level Required at Login" = High Assurance
- [ ] Integration and API-only profiles are explicitly out of scope
- [ ] Apex gates use `Auth.SessionManagement`, never a fabricated `UserInfo` accessor
- [ ] Field-level security and sharing are still correct independently of the session level
- [ ] A Standard-session negative test was executed, not assumed
- [ ] `AuthSession` monitoring exists so a silently-downgraded org is detectable

---

## Deep Dives

`references/examples.md` — Apex step-up gate, permission-set-scoped login requirement with the async carve-out, `AuthSession` audit query. `references/gotchas.md` — seven production failure modes. `references/llm-anti-patterns.md` — seven wrong/right code pairs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Session level policy matrix | Each protected operation → policy action (raise / block) → affected profiles |
| Login-method mapping snapshot | The Session Settings Standard/High Assurance column assignment, captured before and after the change |
| Async-Apex exclusion list | Profiles owning scheduled/batch/`@future` jobs that must not carry a login-level requirement |
| Step-up Apex gate | Controller-level guard built on `Auth.SessionManagement` with its negative test |

---

## Related Skills

- `security/connected-app-security-policies` — owns the Connected App High Assurance session policy and its three states; this skill defers all Connected App policy content to it.
- `security/session-management-and-timeout` — owns session timeout, concurrent sessions, and the rest of Session Settings.
- `security/mfa-enforcement-strategy` — owns MFA rollout, enrollment, and exception handling; High Assurance is downstream of it.
- `security/login-forensics` — owns `LoginHistory` / `AuthSession` investigation once you need to prove who authenticated how.
