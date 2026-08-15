---
name: api-only-user-hardening
description: "Provision and harden integration (API-only) users: no UI login, IP restrictions, minimum permission set, session lifetime, and monitoring. NOT for human admin account hardening — use admin/integration-user-management."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "integration user setup salesforce"
  - "api only user profile"
  - "harden service account salesforce"
  - "restrict integration user ip"
tags:
  - integration
  - service-account
  - api
inputs:
  - "Integration name"
  - "required objects/fields"
  - "caller IP range"
outputs:
  - "User record + Profile + Permission Set Group + Connected App config"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# API-Only User Hardening

An integration identity is the highest-value credential in most orgs. It is
long-lived, it usually carries broader object access than any human, and its secret
sits in a config store outside Salesforce's control. Hardening it is four decisions
plus a monitoring commitment:

| Decision | Hardened choice |
|---|---|
| Licence | Salesforce Integration user license |
| Profile | `Minimum Access - API Only Integrations` — not a clone of anything |
| Scope | One permission set, named objects, named operations, `viewAllRecords` over `ViewAllData` |
| Authentication | OAuth 2.0 client credentials or JWT bearer — no password anywhere |
| Ongoing | Named owner, exported login history, alerting, rotation cadence |

The permission that makes the rest coherent:

> "If a user has the API Only User permission, they can access Salesforce only via
> APIs, regardless of their other permissions."
> — Metadata API Developer Guide

"Regardless of their other permissions" makes this a mode switch, not a permission
among many.

---

## Before Starting

1. **Count the integrations against the org's licences.** "One or more Salesforce
   Integration user licenses are available by default in Enterprise, Unlimited,
   Performance, and Developer editions, with more add-on licenses available to
   purchase." A one-identity-per-integration design is a procurement item first.

2. **Enumerate the objects and operations this integration actually performs.** Not
   "needs access to Salesforce" — the object list and, per object, whether it reads,
   creates, edits, or deletes.

3. **Ask whether the caller has provisioned static egress**, in both IPv4 and IPv6.
   If not, IP restriction is unavailable and the posture must be carried elsewhere.

4. **Check whether anything renders UI as this identity** before enabling API Only
   User on an existing account — Visualforce, Lightning Out, Experience Cloud, a
   scheduled report. If something does, that is a second integration sharing the
   account.

---

## Core Concepts

### The licence carries a contractual boundary

> "The Salesforce Integration API permission set license extends and restricts
> specific user and object permissions for system-to-system integrations. It may not
> be used for human users to access Salesforce data or features through any user
> interface."

A human using an integration licence is a licence-compliance problem as well as a
security one. That boundary is a feature — it makes accidental reuse an event rather
than a convenience.

### The client credentials flow enforces API-only

```xml
<oauthConfig>
    <isClientCredentialEnabled>true</isClientCredentialEnabled>
    <oauthClientCredentialUser>etl.warehouse@example.com</oauthClientCredentialUser>
</oauthConfig>
```

> "`oauthClientCredentialUser` — The execution user for the OAuth 2.0 client
> credentials flow. Salesforce returns access tokens on behalf of this user. **This
> user must have the API Only permission.**"

The platform will not let you bind a machine flow to a UI-capable identity. Both
fields are API 56.0 and later.

### Scope with `viewAllRecords`, not `ViewAllData`

```xml
<objectPermissions>
    <object>Opportunity</object>
    <allowRead>true</allowRead>
    <viewAllRecords>true</viewAllRecords>
    <allowCreate>false</allowCreate>
    <allowEdit>false</allowEdit>
    <allowDelete>false</allowDelete>
    <modifyAllRecords>false</modifyAllRecords>
</objectPermissions>
```

Per-object, review-visible, and defensible line by line. **Modify All Data** grants
read, create, edit, and delete on every object and bypasses all sharing.

### The IP control is split across two screens

Profile `loginIpRanges` sets the restriction; the connected app's `ipRelaxation`
decides whether that app honours it. `ENFORCE` (default) honours it; `BYPASS`
"Allows a user to run this app without org IP restrictions." Audit both together or
you are auditing neither.

### Passwords bring three inherited problems

Expiry from a cloned profile (`ProfileSessionSetting.passwordExpiration` — `0`, `30`,
`60`, `90`, `180`, `365`, where `0` never expires), the MFA requirement that applies
to direct logins, and a copyable credential in a config store. Salesforce's own
guidance: "For security, we recommend blocking user-agent and username-password
flows."

### Login History is not your system of record

> "The Login History page shows up to 20,000 records of user logins for the past 6
> months."

For a frequent integration that is days. Export on a schedule or stream to a SIEM,
and decide this at provisioning — unretained data cannot be recovered.

---

## Common Patterns

### Pattern A — the hardened baseline

Salesforce Integration licence → `Minimum Access - API Only Integrations` → one
scoped permission set → connected app with client credentials, `ipRelaxation` set to
`ENFORCE`, and profile Login IP Ranges. Full metadata in
[`references/examples.md`](references/examples.md), Example 1.

### Pattern B — JWT bearer where no secret may cross the wire

The client signs an assertion with a private key; Salesforce validates against an
uploaded certificate. Rotation becomes a certificate swap. Choose this where the
client already has key management, or where the shared secret would otherwise live
in a shared config store.

### Pattern C — parallel-run migration off password auth

Stand up the hardened identity alongside the legacy one, cut traffic over behind a
flag, and *only then* remove the old credential. The completion criterion is thirty
days with no username-password subtype in Login History — not "the new flow works."

### Pattern D — the integration section of the access review

Integration identities have no manager and no role, so they fall out of
manager-based reviews entirely. Give them their own section with their own
questions: still live, permission set still minimal, IP range current, secret last
rotated, licence still needed.

---

## Decision Guidance

| Situation | Approach |
|---|---|
| New server-to-server integration | Salesforce Integration licence, `Minimum Access - API Only Integrations`, client credentials flow |
| Client already has key management, or secret would be shared | JWT bearer flow |
| Caller has provisioned static egress | Profile Login IP Ranges + `ipRelaxation` `ENFORCE` |
| Caller cannot provide static egress | No IP control — say so; carry posture with scope, short-lived tokens, and monitoring |
| Job must see all records on two objects | `viewAllRecords` on those two objects only |
| Job writes to one object | `modifyAllRecords` on that object only |
| Existing shared `integration@` account | Split per integration; prove the sharing with Login History first |
| Legacy password integration that cannot change this release | `passwordExpiration` `0` as a commented, owned, dated debt marker |
| Identity also renders a Visualforce page | Two integrations sharing one account — split before enabling API Only User |

---

## Recommended Workflow

1. **Scope the integration**: name the objects and, per object, the operations. Get
   the caller's egress addresses in both address families, with an owner and a
   renewal date.
2. **Provision the identity**: Salesforce Integration licence, the
   `Minimum Access - API Only Integrations` profile, one permission set granting
   exactly the scope from step 1 using per-object `viewAllRecords` /
   `modifyAllRecords` rather than org-wide permissions.
3. **Configure authentication with no password**: connected app with
   `isClientCredentialEnabled` and `oauthClientCredentialUser` (or JWT bearer),
   `isPkceRequired` where the flow supports it, and `ipRelaxation` set explicitly to
   `ENFORCE`.
4. **Apply Login IP Ranges to the integration profile**, one range per address per
   family, each with a `description` naming the owner and renewal date.
5. **Wire monitoring before go-live**: scheduled Login History export or SIEM
   stream, plus alerts on off-hours logins, unexpected source IPs, query-volume
   changes, and any username-password subtype.
6. **Record ownership**: a named human owner, a secret rotation cadence, and the
   identity's entry in the access review — somewhere queryable, not in a wiki.
7. **If migrating**: parallel-run, cut over, observe for thirty days with no legacy
   flow subtype in Login History, then remove the old credential and block the
   legacy flows org-wide.

---

## Review Checklist

- [ ] Uses the Salesforce Integration licence, not a full user licence
- [ ] Profile is `Minimum Access - API Only Integrations`, not a clone
- [ ] Permission set grants no `ViewAllData` and no `ModifyAllData`
- [ ] Every object permission is justified by a named operation the job performs
- [ ] No password in the authentication path
- [ ] `oauthClientCredentialUser` (if used) has the API Only permission
- [ ] `ipRelaxation` is explicitly `ENFORCE`, or the exception has a named approver
- [ ] Login IP Ranges cover both address families, with owner and renewal date
- [ ] One identity, one profile, one connected app, one owner — not shared
- [ ] Login History export or SIEM stream configured before go-live
- [ ] Alerting on off-hours logins, unexpected IPs, and legacy flow subtypes
- [ ] Secret rotation cadence recorded with the owner
- [ ] Identity appears in a dedicated section of the access review
- [ ] `apiOnlyUserHomePageURL` set so a confused admin lands somewhere explanatory

---

## Salesforce-Specific Gotchas

Full detail with quotes in [`references/gotchas.md`](references/gotchas.md).

1. **API Only User overrides every other permission** and replaces the login page.
2. **The client credentials flow refuses a user who can log in** — the execution
   user must hold the API Only permission.
3. **A cloned profile inherits a password expiry nobody chose**, and the job fails
   on that day with no human to warn.
4. **A connected app can cancel the profile's IP restriction** via `ipRelaxation`.
5. **The Salesforce Integration licence is not a free upgrade** — count before
   committing to one identity per integration.
6. **One shared identity destroys attribution and multiplies rotation cost.**
7. **Login History holds far less than you think** — 20,000 records, six months.
8. **Legacy auth flows keep working after you "migrate."**
9. **`Modify All Data` is almost never the permission you needed.**
10. **The integration user is invisible in most access reviews.**

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration identity record | Licence, profile, permission set, connected app, and the named human owner, all cross-referenced |
| Scope justification | Per object: which operations, why, and which part of the integration performs them |
| Authentication design | Flow chosen, why, where the secret lives, and the rotation cadence |
| Network control | IP ranges with owner and renewal date, plus the `ipRelaxation` value and its approver if not `ENFORCE` |
| Monitoring plan | Login History export or SIEM destination, alert conditions, and who receives them |
| Migration completion evidence | Thirty days of Login History showing no legacy flow subtype, before the old credential is removed |

---

## Related Skills

- `security/ip-relaxation-and-restriction` — the profile-vs-network-vs-connected-app
  IP model this skill applies to one identity
- `security/oauth-token-management` — token lifetime, refresh policy, and revocation
  for the credential this identity uses
- `security/mfa-enforcement-patterns` — why a password-based integration is a
  problem the MFA programme will surface
- `security/event-monitoring` — the data source that makes an integration identity's
  behaviour observable at all
