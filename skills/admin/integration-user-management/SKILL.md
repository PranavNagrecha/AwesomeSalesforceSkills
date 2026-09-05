---
name: integration-user-management
description: "Use when setting up or auditing a dedicated Salesforce integration user — Salesforce Integration user license, API-only profile, permission set layering, MFA waiver, and login monitoring. NOT for creating human users, roles, or login hours — use admin/user-management. NOT for login IP ranges, session lifetime, or OAuth client-credential hardening — use security/api-only-user-hardening. Trigger keywords: service account, API-only user, run-as user, client credentials execution user, LoginHistory, REQUEST_LIMIT_EXCEEDED, integration login failure."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "How do I create a dedicated integration user that can only access the API and not the Salesforce UI?"
  - "Integration user is being blocked by MFA enforcement — how do I grant an exemption?"
  - "Should I use a System Administrator profile for an integration user to avoid permission issues?"
  - "How do I monitor which API calls are being made by the integration user?"
  - "What profile and license should I use for a MuleSoft integration user?"
  - "integration user login fails right after the MFA rollout"
  - "restrict a service account to API only so it cannot log into the UI"
  - "grant a least-privilege permission set to a middleware service account"
  - "query LoginHistory for an integration user's failed logins"
  - "client credentials flow needs an API-only run-as user"
  - "integration user blocked by profile login IP ranges or login hours"
  - "REQUEST_LIMIT_EXCEEDED — which integration user is burning the API allocation"
  - "audit which permission sets grant Modify All Data to service accounts"
tags:
  - integration-user
  - api-only
  - integration-user-management
  - mfa-waiver
  - permission-set
  - login-history
inputs:
  - "Integration system name and the Salesforce objects/fields it needs to access"
  - "Whether the org has MFA enforcement enabled"
  - "Current integration user license and profile configuration"
outputs:
  - "Integration user setup with Salesforce Integration license and API-only profile"
  - "Permission set configuration for least-privilege object and field access"
  - "Diagnosis of what is actually blocking the integration login: IP range, login hours, session level, or connected-app policy"
  - "Login History monitoring query for auditing integration activity"
  - "Deployable Profile, PermissionSet, ProfileSessionSetting and ConnectedApp XML for the service account"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Integration User Management

This skill activates when a practitioner needs to set up, configure, or audit a dedicated Salesforce integration user — the dedicated API-only user identity that middleware, ETL tools, or external systems use to authenticate to Salesforce. It covers the correct license/profile combination, least-privilege permission layering, the network and session gates that actually block API logins (and where MFA does and does not apply), and login monitoring.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Dedicated integration users are mandatory for production integrations**: Shared user accounts or admin-profile integration users violate Salesforce security best practices and create audit and compliance risks. Every integration should have its own dedicated integration user.
- **Most common wrong assumption**: Granting the System Administrator profile or a cloned admin profile to an integration user "for simplicity." This bypasses the API-only flag (grants interactive login capability), grants access to all org data, and violates least-privilege. The correct approach is the Minimum Access - API Only Integrations profile plus targeted permission sets.
- **MFA is the wrong first suspect for a blocked integration user**: org-wide MFA enforcement is scoped to direct UI logins (`api_meta.txt` L126248–126252), and an API-only user has no UI login to challenge, so an MFA waiver is not part of a working setup. Establish instead which of the four real gates the integration must pass — the profile's `loginIpRanges` and `loginHours`, the profile's `requiredSessionLevel`, and the connected app's session policy — and confirm the org's current values for each before creating the user.

---

## Questions to Ask Before Configuring

Ask these before creating the user; the answers decide the license, the profile, and the monitoring, and an assistant that skips them produces a service account that authenticates in the sandbox and fails in production.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which authentication flow will the middleware actually use — JWT bearer, client credentials, or username-password?" | Client credentials requires a named execution user that "must have the API Only permission" (`api_meta.txt` L35443–35448), and any flow without a user approval step is blocked outright by a High Assurance session level | The connected app shape, and whether `requiredSessionLevel` must stay `STANDARD` |
| "What is the middleware's egress IP range, and is it stable?" | `loginIpRanges` on the profile is the control that survives a stolen credential; `ipRelaxation` on the connected app decides whether it applies at all | The exact `startAddress`/`endAddress` pairs, or an explicit decision to skip the allowlist |
| "When does this integration run, including retries and backfills?" | Login hours are enforced per profile per weekday; a 03:00 retry against a window that closes at midnight fails as a *login* error, not a permission error | The seven-day `loginHours` block, or a documented decision to leave it open |
| "Which objects and fields does it read, and which does it write?" | The base profile grants nothing, so the permission set is the whole grant; write access to a field you did not name will simply fail at runtime | The `objectPermissions` and `fieldPermissions` list, and whether any `viewAllRecords` escape is genuinely needed |
| "Does another integration already exist in this org, and what is the current API consumption?" | The daily allocation is org-wide, not per user (`salesforce_app_limits_cheatsheet.txt` L616–618), so a new integration competes with every existing one | A go/no-go on headroom, and whether API Usage Notifications are configured |
| "Who owns this service account, and where does its mail go?" | `Username` must be unique across all orgs and the `Email` is where password and verification mail lands | A team alias rather than a leaver's inbox, and an org-suffixed username that survives a sandbox refresh |
| "What is the org's MFA and session-security posture right now?" | The org-wide MFA switch is scoped to direct UI logins; the thing that actually breaks headless flows is a High Assurance session requirement | The right diagnosis before anyone grants a waiver that changes nothing |

What a proper configuration adds over just creating a user: the credential is bounded in time, source IP and object scope, the authentication flow is one the session policy will not block, and `LoginHistory` can name this integration when the org's shared API allocation runs out.

---

## Core Concepts

### Salesforce Integration User License

The Salesforce Integration user license (also called the "Salesforce API Integration" license) is specifically designed for server-to-server integrations. Key characteristics:

- Cannot be used for interactive Salesforce UI login (no browser session capability).
- Requires the "Minimum Access - API Only Integrations" profile as the base profile.
- Consumes a dedicated user license, not a standard Salesforce license.
- Supports API access via username-password, OAuth client credentials, and JWT bearer flows.
- The license-profile combination enforces API-only access at the platform level — this is not configurable by admins.

### Minimum Access - API Only Integrations Profile

This profile is the mandatory base profile for Salesforce Integration user license accounts. It:
- Enforces API-only access (no Salesforce UI login).
- Grants no default object or field permissions (truly minimum access).
- Cannot be cloned or modified.
- All data access must be layered on via permission sets.

This profile-license combination ensures that even if the integration user's credentials are compromised, the attacker cannot access the Salesforce UI.

### Least-Privilege Permission Set Strategy

Because the base profile grants no object or field permissions, all access must be granted via permission sets following least-privilege:

1. Create a dedicated permission set for the integration (e.g., "MuleSoft Integration - Opportunity Access").
2. Grant only the specific object CRUD permissions the integration requires (no `Modify All Data`, no `View All Data` unless absolutely required).
3. Grant FLS access only to the specific fields the integration reads or writes.
4. Assign the permission set to the integration user.

For large integrations with many objects, multiple scoped permission sets (one per integration function) are preferred over a single broad permission set. This enables access to be revoked granularly if an integration function is decommissioned.

### What MFA Enforcement Actually Covers, and What Blocks an Integration User

Org-wide MFA enforcement is scoped to **direct UI logins**. The Metadata API guide defines the org switch as `SecuritySettings.enableMFADirectUILoginOptIn`: "Requires all users in your Salesforce org to provide an additional verification method when logging in directly to the UI with their username and password... The Waive Multi-Factor Authentication for Exempt Users user permission overrides this setting" (`api_meta.txt` L126248–126252). An API-only user has no direct-UI-login path for that setting to act on: a user carrying the API Only User permission "can access Salesforce only via APIs, regardless of their other permissions" (`api_meta.txt` L121360–121363).

So an integration user authenticating over OAuth, JWT bearer, or client credentials is not challenged by org-wide MFA enforcement, and **the waiver permission is not a prerequisite for making an integration work**. Grant "Waive Multi-Factor Authentication for Exempt Users" when a person or account is genuinely exempt from the org's MFA policy — not merely because the account is API-only. UNVERIFIED (2026-09-05): no separate MFA-for-API-logins control appears anywhere in the Metadata API guide, Object Reference, REST guide, or App Limits cheat sheet; if your org's Setup exposes one, it overrides this paragraph.

When an integration user really is blocked, the cause is almost always one of these four, and each produces a distinguishable `LoginHistory.Status`:

| Blocker | Where it lives | Fix |
|---|---|---|
| Source IP outside the allowlist | `Profile.loginIpRanges`; enforced for app traffic when the connected app's `ipRelaxation` is `ENFORCE` (`api_meta.txt` L35655–35661) | Add the middleware's egress range, including retry clusters |
| Login outside the permitted window | `Profile.loginHours`, per weekday (`api_meta.txt` L98071–98092) | Cover all seven days, or remove the restriction with an empty `<loginHours/>` |
| High Assurance session requirement | `ProfileSessionSetting.requiredSessionLevel`; "For flows without a user approval step, API logins with the High Assurance session security level are blocked" (`api_meta.txt` L35826–35836) | Keep the integration profile at `STANDARD` |
| Connected-app session policy | `ConnectedAppSessionPolicy.policyAction` = `RaiseSessionLevel` (`api_meta.txt` L35826–35836) | Leave the session policy off for headless apps |

Diagnose before you remediate: read the `Status` value on the failing login row first. Certificate-based JWT bearer and client-credentials flows carry a second advantage beyond MFA scope — they transmit no password at all, so there is no credential to rotate, expire, or leak.

### Login History Monitoring

Login History (Setup > Users > Login History) shows login attempts for all users including integration users:
- UI displays the most recent 20,000 records with a 6-month retention window.
- Full history is available via SOQL query on the `LoginHistory` object (API v21.0+).
- Key fields: `UserId`, `Status` (Success/Failed), `LoginType` (API, OAuth, etc.), `SourceIp`, `LoginTime`.

For detecting anomalous integration behavior:
- Monitor for failed login attempts (Status != "Success").
- Alert on login attempts from unexpected IP addresses (SourceIp not in known integration server range).
- Schedule periodic reports comparing actual login frequency against expected integration call patterns.

---

## Common Patterns

### Setting Up a New Integration User

**When to use:** A new integration system (MuleSoft, Informatica, custom middleware) needs a dedicated Salesforce identity.

**How it works:**
1. Purchase and provision a Salesforce Integration user license in Setup > Company Information.
2. Create a new user: Setup > Users > New User. Set License to "Salesforce Integration," Profile to "Minimum Access - API Only Integrations."
3. Create a permission set named after the integration system: `<IntegrationName>_Integration`.
4. In the permission set, grant object-level CRUD and FLS for only the specific fields the integration needs.
5. Assign the permission set to the user.
6. Confirm the network and session controls the integration must pass: the profile's `loginIpRanges` and `loginHours`, and a `requiredSessionLevel` of `STANDARD`. Do not reach for an MFA waiver — org-wide MFA enforcement does not apply to this user's API logins.
7. Configure the connected app with "Admin approved users are pre-authorized" and assign the connected app to the integration user's permission set or profile.
8. Test authentication and API access as the integration user.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New integration needs Salesforce API access | Salesforce Integration license + Minimum Access - API Only Integrations profile | Enforces API-only at the platform level, least-privilege base |
| Integration user "blocked by MFA" | Read `LoginHistory.Status` first, then fix the IP range, login hours, or session level | Org-wide MFA enforcement is scoped to direct UI logins (`api_meta.txt` L126248–126252), so it is not what is blocking an API-only user |
| A user genuinely exempt from the org's MFA policy | Grant "Waive Multi-Factor Authentication for Exempt Users" in a permission set | That permission is documented as overriding the org's direct-UI-login MFA setting (`api_meta.txt` L126248–126252) |
| Integration must not be affected by MFA or password policy at all | Certificate-based JWT bearer or client-credentials flow | No password is transmitted and no user approval step exists; the client-credentials execution user "must have the API Only permission" (`api_meta.txt` L35443–35448) |
| Integration needs access to specific objects | Targeted permission set for those objects only | Minimum Access profile grants no object permissions — all must be layered on |
| Quick fix: grant admin profile for integration | Never — violates least-privilege and security | Admin profile grants interactive login and all data access |
| Audit integration user activity | Query LoginHistory SOQL object | Setup UI shows 20K records; full history via API |
| Integration user needs to modify all records | Grant View All and Modify All only if technically required | Always justify in documentation; prefer object-level CRUD + sharing override |

---

## Recommended Workflow

1. **Answer the seven questions above, then pick the authentication flow.** The flow decides everything downstream: a client-credentials app needs an `oauthClientCredentialUser` that carries the API Only permission, and neither it nor a JWT bearer flow survives a High Assurance session requirement. Record the decision before writing any XML.
2. **Write the anchor Profile and its session/password policy from `references/metadata-examples.md` §1 and §3.** Set `userLicense`, write `<enabled>false</enabled>` explicitly for `ModifyAllData`, `ViewAllData`, `AuthorApex` and `ManageUsers`, add the middleware's `loginIpRanges`, and cover all seven days in `loginHours` — or none. Keep `requiredSessionLevel` at `STANDARD`.
3. **Write the per-integration Permission Set from §2** — one per integration system, named after it. Grant `ApiEnabled`, the exact `objectPermissions`, and the exact `fieldPermissions`. Use `license`, not the deprecated `userLicense`, and leave `hasActivationRequired` false.
4. **Run the checker before deploying.** From the repo root: `python3 skills/admin/integration-user-management/scripts/check_integration_user_management.py --manifest-dir force-app/main/default`. Name the profile and permission set in `integration-user-config.json`, and record any deliberate elevated grant in `allowedElevatedPermissions` so the exception is written down rather than argued about later.
5. **Deploy with `sf project deploy validate` first, then `deploy start`** (commands in §6), and create the User record over REST with the payload in §7 — never as packaged metadata.
6. **Verify with the three queries in §8**: profile and license on `User`, elevated permissions on `PermissionSetAssignment`, and the actual `LoginType`/`LoginSubType` on `LoginHistory`. A first successful call is not verification; the login row proving the intended flow is.
7. **Fill in `templates/integration-user-management-template.md` and schedule the review.** Read `references/gotchas.md` in full if any step fails — the eleven entries there cover the failure modes that look like permission errors and are not.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Salesforce Integration license assigned (not standard Salesforce license)
- [ ] Minimum Access - API Only Integrations profile assigned (no admin or cloned admin profile)
- [ ] Targeted permission set created with only required object/field access
- [ ] Permission set assigned to integration user
- [ ] Login failures diagnosed from `LoginHistory.Status` before any MFA waiver is considered; waiver granted only if the account is genuinely exempt from the org's MFA policy
- [ ] Connected app assigned to integration user (if pre-authorized mode is used)
- [ ] Authentication tested successfully — API calls succeed, UI login is blocked
- [ ] Login History monitoring configured
- [ ] `scripts/check_integration_user_management.py --manifest-dir <path>` exits 0, or every remaining finding is recorded in `integration-user-config.json`
- [ ] Profile carries `loginIpRanges`, and `loginHours` covers all seven days or is absent entirely
- [ ] `requiredSessionLevel` is `STANDARD` on the integration profile, and no High Assurance connected-app session policy applies
- [ ] `LoginHistory` shows the intended `LoginType` / `LoginSubType` for the flow you configured
- [ ] Monitoring queries filter only on `UserId` and `LoginTime`, and evaluate `Status` and `SourceIp` client-side

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Admin profile integration users bypass the API-only flag** — Granting System Administrator or any profile without the "API Only User" flag to an integration user enables interactive login capability. If the credentials are compromised, an attacker can log into the Salesforce UI with admin privileges. The Minimum Access - API Only Integrations profile enforces API-only at the platform level — this cannot be replicated by cloning and modifying another profile.
2. **An integration user that fails right after an MFA rollout was not stopped by MFA** — org-wide MFA enforcement covers direct UI logins (`api_meta.txt` L126248–126252), and an API Only User "can access Salesforce only via APIs" (`api_meta.txt` L121360–121363), so there is no UI login for the setting to challenge. The waiver permission is the documented override for accounts genuinely exempt from the org's MFA policy, not a prerequisite for an API-only account. The real blocker is an IP range, a login-hours window, a `HIGH_ASSURANCE` session level, or a connected-app session policy — read `LoginHistory.Status` on the failing row before changing anything. See `references/gotchas.md` § Gotcha 4.
3. **Login History UI shows only 20,000 records** — The Setup > Login History UI is limited to the most recent 20,000 records. For high-frequency integrations making thousands of API calls per day, this limit is reached quickly and older login records become invisible in the UI. For full audit history, query the `LoginHistory` SOQL object via the API — it retains up to 6 months of data regardless of the UI limit.
4. **A High Assurance session requirement, not MFA, is what stops a headless flow** — `requiredSessionLevel` set to `HIGH_ASSURANCE` on the integration user's profile, or a High Assurance connected-app session policy, blocks any API login on a flow with no user approval step. JWT bearer and client credentials are exactly those flows. See `references/gotchas.md` § Gotcha 7.
5. **`LoginHistory` refuses filters on `Status` and `SourceIp`** — the two fields every monitoring query wants to filter on are not in the object's filterable list, so the alert you write from the field table fails rather than returning nothing. See `references/gotchas.md` § Gotcha 5.
6. **The daily API allocation belongs to the org, not to the user** — there is no per-user throttle to raise, so one runaway integration exhausts the allocation for every other client in the org. See `references/gotchas.md` § Gotcha 9.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Integration user configuration | License, profile, username, and service account email setup |
| Permission set definition | Object CRUD and FLS grants for the specific integration scope |
| Login-blocker diagnosis | Which of IP range, login hours, session level, or connected-app policy is blocking the user, read from `LoginHistory.Status` |
| LoginHistory monitoring query | SOQL query for auditing integration login activity |
| Deployable metadata set | Profile, PermissionSet, ProfileSessionSetting, ProfilePasswordPolicy, ConnectedApp XML plus package.xml (`references/metadata-examples.md`) |
| Checker run | `scripts/check_integration_user_management.py --manifest-dir <path>` output and any recorded exceptions in `integration-user-config.json` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing the deployable Profile, PermissionSet, session/password policy, ConnectedApp XML, the User REST payload, or the verification queries |
| `references/gotchas.md` | An integration authenticates in one org and not another, or a monitoring query returns nothing it should |
| `references/examples.md` | Triaging a live failure — an MFA-shaped login block, or unexplained API activity from a service account |
| `references/llm-anti-patterns.md` | Reviewing an assistant's integration-user recommendation before acting on it |
| `references/well-architected.md` | Justifying the one-user-per-system and JWT-over-password tradeoffs, and citing the official sources behind them |

---

## Related Skills

- `admin/integration-admin-connected-apps` — Configure the connected app the integration user will authenticate through
- `admin/remote-site-settings` — Configure the server-side callout allowlist for the integration's external endpoints
- `security/api-only-user-hardening` — Login IP ranges, session lifetime, and OAuth client-credential hardening for the same user
- `admin/permission-set-architecture` — Structuring the permission sets that carry the integration's object and field grants
- `admin/user-management` — Creating and governing human users, roles, and login hours
- `integration/oauth-flows-and-connected-apps` — Choosing between JWT bearer, client credentials, and web server flows
