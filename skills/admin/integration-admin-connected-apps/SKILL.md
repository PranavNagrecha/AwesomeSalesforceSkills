---
name: integration-admin-connected-apps
description: "Use when managing Connected Apps for integration purposes — configuring OAuth policies, IP restrictions, refresh token expiry, pre-authorization assignment via profile or permission set, and monitoring connected app usage via EventLogFile. Also covers the running-integration operations: revoking a grant, rotating the consumer key or secret, pairing the app to an integration user's permission set, and the periodic review. Trigger keywords: 'revoke OAuth token', 'DeleteToken', 'OauthToken query returns nothing', 'ipRelaxation ENFORCE', 'permissionSetName', 'PermissionSetAssignment ExpirationDate', 'LoginHistory Application', 'connected app quarterly review', 'rotate consumer secret'. NOT for choosing which OAuth grant flow to implement — use integration/oauth-flows-and-connected-apps. NOT for decoding a specific OAuth error such as invalid_grant — use admin/connected-app-troubleshooting. NOT for authoring the full connectedApp / External Client App / Named Credential file or choosing the auth artefact — use admin/connected-apps-and-auth."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "Connected App authentication is failing after I set Admin approved users are pre-authorized"
  - "How do I restrict which IP addresses a connected app can authenticate from?"
  - "Integration stopped working after the refresh token expired — what setting controls this?"
  - "How do I monitor which users are using a connected app for integration?"
  - "Uninstalled connected app is blocking users from authenticating"
  - "revoke an OAuth token for one integration user without breaking everyone else"
  - "OauthToken query returns fewer rows than the org actually has"
  - "rotate the consumer secret on a connected app that is already live"
  - "which permission set pre-authorizes this integration's connected app"
  - "audit connected app usage quarterly and prove the policy has not drifted"
  - "why did the integration stop working when nobody changed the connected app"
tags:
  - connected-app
  - oauth
  - integration-admin-connected-apps
  - oauth-policies
  - ip-relaxation
  - refresh-token
  - event-monitoring
inputs:
  - "Connected app name and current OAuth policy configuration"
  - "Integration user profile and permission set assignments"
  - "IP ranges used by the integration system"
  - "Required refresh token expiry window for the integration"
  - "Named owner for each connected app in the org, for the periodic review"
outputs:
  - "Connected app OAuth policy configuration (Permitted Users, IP Relaxation, Refresh Token)"
  - "Profile or permission set assignment for pre-authorized app access"
  - "EventLogFile query for connected app usage monitoring"
  - "Audit checklist for connected app security posture"
  - "Revocation and key/secret rotation runbook for a live integration"
  - "Quarterly connected-app review checklist (YAML the skill checker lints)"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Integration Admin: Connected Apps

This skill activates when an admin needs to configure or troubleshoot Connected App OAuth policies for integration use cases — setting Permitted Users mode, IP Relaxation policy, Refresh Token Policy, and monitoring usage via EventLogFile. It covers the critical post-configuration step that admins most commonly miss: assigning the connected app to a profile or permission set when using pre-authorization mode.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Three independent policy controls**: Connected App OAuth configuration has three separate policy controls that each gate different aspects of authentication. Configuring one does not automatically configure the others. All three must be reviewed for each integration.
- **Most common wrong assumption**: Setting "Admin approved users are pre-authorized" without assigning the connected app to a Profile or Permission Set leaves no users actually able to authenticate. Pre-authorization mode requires an explicit assignment before any user can authenticate — it does not default to any users.
- **Monitoring requires Event Monitoring add-on**: The primary data source for connected app usage is EventLogFile (ConnectedApp and ConnectedAppOAuth event types). These are NOT visible in the standard Setup UI audit trail and require the Event Monitoring add-on license to access.

---

## Questions to Ask Before Configuring

Ask these before opening the app's Manage page. Each answer decides a policy value or an operational
step that no error message will later name for you — the app authenticates or it does not, and the
platform does not explain which control said no.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which permission set pre-authorizes this app, and is that assignment dated?" | `isAdminApproved` with no `permissionSetName` / `profileName` authorizes nobody, and `PermissionSetAssignment.ExpirationDate` un-authorizes the integration user on a day nobody diarised | A named permission set plus a check that the integration user's assignment has no expiry |
| "Can the caller enumerate its egress IPs, and who owns the org's trusted-IP list?" | `ENFORCE` is only as strict as that list, and redeploying `NetworkAccess` replaces the whole list rather than merging into it | `ENFORCE` plus a real range list, or a written reason for a looser value |
| "How does this integration get cut off in an incident — what is the exact step?" | `OauthToken` supports only `describeSObjects()` and `query()`; there is no DML delete, so the revoke path is the `DeleteToken` value against the revoke endpoint | A runbook line someone has actually executed once, not "revoke the token" |
| "Who holds the consumer key and secret, and what does rotation cost?" | `consumerKey` can be set only at creation and can't be edited afterwards; only an External Client App has `shouldRotateConsumerKey` / `shouldRotateConsumerSecret`, and those need the ignore-warnings deploy attribute | A rotation plan that is either an ECA deploy or a replacement app plus a caller cutover |
| "Does anyone hold Customize Application to run the token inventory?" | Without it, `OauthToken` returns only the caller's own tokens, so a least-privileged reviewer reports "nobody uses this app" about an app in daily use | A named reviewer who can actually see org-wide tokens |
| "Which named user owns this app, and when was it last reviewed?" | `SetupAuditTrail` keeps Setup changes for "at least the last 180 days" — a policy change made two quarters ago has no evidence left | An owner and a review cadence short enough that the audit trail still covers the gap |
| "Is the org's `enableAdminApprovedAppsOnly` switch on?" | It changes whether *any* unapproved connected app can call the API org-wide, and turning it on requires a Salesforce Customer Support request to enable API Access Control | The blast radius of every per-app policy decision below it |

What a proper configuration adds over just setting the three OAuth policies: the app is pre-authorized
to a named permission set whose assignment does not expire, the revoke and rotate steps have been run
once against a sandbox, the token inventory runs as someone who can see all tokens, and each quarter's
review is written down while `SetupAuditTrail` can still corroborate it.

---

## Core Concepts

### Three OAuth Policy Controls

Connected App OAuth policies have three independent controls accessible in Setup > App Manager > [App] > Manage:

1. **Permitted Users**: Controls who can authorize the connected app.
   - "All users may self-authorize" — any user can grant access to the app via OAuth consent.
   - "Admin approved users are pre-authorized" — only users whose Profile or Permission Set has the connected app explicitly assigned can authenticate. No consent screen is shown — authentication is immediate if the user is assigned.

2. **IP Relaxation**: Controls how the org's login IP restrictions interact with connected app sessions.
   - "Enforce login IP restrictions" — IP restrictions from the user's profile apply to API calls via this connected app.
   - "Relax IP restrictions" — API calls via this connected app bypass the user's profile IP restrictions entirely.
   - "Relax IP restrictions, with second factor for non-login IPs" — Relaxes IP for authenticated sessions but requires MFA for logins from outside the profile's IP range.

3. **Refresh Token Policy**: Controls how long a refresh token remains valid.
   - "Immediately expire refresh token" — Tokens expire immediately, requiring re-authentication every API call. Suitable for server-to-server flows that do not use refresh tokens.
   - "Expire refresh token if not used for N days" — Inactivity-based expiry.
   - "Expire refresh token after N days" — Absolute time-based expiry.
   - "Immediately expire refresh token if IP address changes" — Security control for sensitive contexts.

### Pre-Authorization Mode Assignment

When "Admin approved users are pre-authorized" is selected, the connected app must be assigned to one or more Profiles or Permission Sets. This assignment is done via:
- Profile settings: Profile > Connected App Access > toggle on the app
- Permission set: Permission Set > Manage Assignments > Assigned Apps (or via API `PermissionSetAssignment`)

Without this assignment, the "pre-authorized" setting effectively blocks all users.

### Connected App Usage Monitoring (EventLogFile)

Two EventLogFile event types capture connected app activity:
- **ConnectedApp** event: Logs each connected app authorization event (when a user authorizes or revokes a connected app).
- **ConnectedAppOAuth** event: Logs each OAuth token grant, refresh, and revocation.

Both require the Event Monitoring add-on. Access via REST API:
```
GET /services/data/vXX.0/query?q=SELECT+Id+FROM+EventLogFile+WHERE+EventType='ConnectedApp'+AND+LogDate=TODAY
```

The standard Setup UI Login History shows connected app sessions but does not capture OAuth token-level events.

### Monitoring Without the Add-On: Four Standard Objects

Every org has these three, add-on or not. They answer different questions and each carries a
constraint that silently corrupts the answer if you don't know it.

| Object | Answers | Constraint the Object Reference states |
|---|---|---|
| `ConnectedApplication` | What policy actually landed on each app | "all fields are read-only"; supports `describeSObjects()`, `query()`, `retrieve()` |
| `OauthToken` | Who currently holds a grant, and when they last used it | "Users with the Customize Application permission see all tokens for all users in the org. Otherwise, you see only your own tokens." `query()` returns 500 rows, `queryMore()` up to 2,500 total, and "No more records are returned after 2,500" |
| `LoginHistory` | Which sessions the app produced, from where | Only twelve fields are filterable — `Application`, `SourceIp` and `Status` are **not** among them |
| `SetupAuditTrail` | Who changed a policy, and when | Holds Setup changes "for at least the last 180 days"; `SELECT count()` works but `SELECT count(Id)` fails |

`LoginType` is filterable, and the values that mean *connected app* are `Application`,
`Oauth, Remote Access Client` and `Oauth2, Remote Access 2.0` — two of the three contain a comma
inside the picklist value itself.

**What the app is consuming.** A connected app's traffic lands in the org's shared 24-hour inbound
API allocation, which the Salesforce Developer Limits and Allocations Quick Reference sets as 15,000
calls for Developer Edition and, for Enterprise and Professional with API access, "100,000 + (number
of licenses x calls per license type) + purchased API Call Add-Ons" — 1,000 per Salesforce or
Salesforce Platform licence, rising to 5,000 each on Unlimited and Performance Edition. A Full
Sandbox not created from a template gets 5,000,000. Adding an integration adds load to that one
bucket, so the review should record call volume alongside token count. The same reference caps stored
credentials: "Salesforce stores third-party access and refresh tokens of up to 10,000 characters in
length."

### Revocation, Rotation, and the Periodic Review

These three are the operations that keep an app safe *after* it exists. None of them is a Setup
checkbox, and each has a shape the platform does not advertise.

| Operation | The actual mechanism | Where it bites |
|---|---|---|
| Revoke one grant | `OauthToken.DeleteToken` posted to the revoke endpoint: `https://MyDomainName.my.salesforce.com/services/oauth2/revoke?token=(the Delete Token)` | `OauthToken` supports only `describeSObjects()` and `query()` — there is no DML delete to write a Flow or Apex around |
| Kill an app entirely | **Block** on the Connected Apps OAuth Usage page, or `sessionPolicy/policyAction` = `Block`, which "ends all current user sessions with the connected app and prevents all new sessions" | Blocking is org-wide and immediate; it is not a per-user action |
| Rotate the key or secret | On an External Client App, `shouldRotateConsumerKey` / `shouldRotateConsumerSecret` — "if this field is set to `true`, you must include the ignore warnings attribute in the deploy command" | A `ConnectedApp` has no such field: `consumerKey` "can be set only during creation" and after save "it can't be edited" |
| Periodic review | A written per-app row: owner, last-reviewed date, and the date the token-count query was actually run | `SetupAuditTrail` only reaches back 180 days, so a review cadence longer than two quarters cannot be corroborated |

The deployable file that carries these policies — the full `connectedApp-meta.xml`, the External
Client App four-file set, and the Named Credential pair — belongs to `admin/connected-apps-and-auth`.
This skill shows only the policy excerpts you edit during operations; see
`references/metadata-examples.md`.

---

## Common Patterns

### Configuring a Server-to-Server Integration App

**When to use:** Setting up a connected app for a server-to-server integration (middleware, ETL, MuleSoft) where no user consent flow is needed.

**How it works:**
1. Create the connected app in Setup > App Manager > New Connected App.
2. Enable OAuth, add required scopes (api, refresh_token, offline_access).
3. Set Permitted Users to "Admin approved users are pre-authorized."
4. Assign the connected app to the integration user's Profile: Profile > Connected App Access > enable the app.
5. Set Refresh Token Policy based on the integration's session management: for JWT bearer flow (no refresh tokens), set "Immediately expire refresh token."
6. Set IP Relaxation to "Enforce login IP restrictions" — the integration server's IP should be added to the integration user's profile trusted IP ranges.

**Why this matters:** Without step 4, no user can authenticate against the connected app, even the admin. The most common support issue after creating a pre-authorized connected app.

### Monitoring Connected App Usage After an Incident

**When to use:** An integration is failing and you need to determine which users are authenticating, from what IPs, and when token refreshes are occurring.

**How it works:**
1. Query EventLogFile for the ConnectedAppOAuth event type for the relevant date range.
2. Parse the CSV log file (EventLogFile stores log data as a downloadable CSV).
3. Filter by the connected app's client_id and the integration user's username.
4. Review the GrantType, IP address, and TokenType columns to identify anomalies.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Server-to-server integration (no user consent) | Admin approved users are pre-authorized + profile assignment | Pre-authorization prevents consent screens; profile assignment restricts to integration user |
| Users need to authorize app themselves (OAuth) | All users may self-authorize | Allows individual user consent flow |
| Connected app blocking all authentication after "pre-authorized" set | Check profile or permission set assignment | Missing assignment is the most common cause |
| Integration failures after IP changes at integration server | Review IP Relaxation setting | Enforce login IP blocks new IPs; Relax if integration server IPs change frequently |
| Refresh token expired causing integration failure | Adjust Refresh Token Policy | Increase expiry window or use JWT bearer flow (no refresh tokens) |
| Monitor which users are hitting a connected app | EventLogFile ConnectedApp and ConnectedAppOAuth event types | Standard UI does not show OAuth token-level detail |
| Uninstalled app blocking users | Audit Connected Apps OAuth Usage in Setup, re-permit the app | September 2025 policy: uninstalled apps blocked by default |

---

## Recommended Workflow

1. **Answer the seven questions above and fill the template.** `templates/integration-admin-connected-apps-template.md` captures the app name, integration user, the three policy values, the pre-authorizing permission set, and the IP ranges. If the app does not exist yet, stop here and go to `admin/connected-apps-and-auth` — this skill starts once there is an app to operate.
2. **Write the policy excerpt from `references/metadata-examples.md`.** Copy the hardened `oauthPolicy` block (`ipRelaxation` `ENFORCE`, an explicit `refreshTokenPolicy`, `isAdminApproved` plus `permissionSetName`) into the existing `connectedApp-meta.xml`. Do not author the whole file here; the sibling owns it.
3. **Pair the permission set to the integration user.** Deploy the pre-authorization permission set fragment, then create the `PermissionSetAssignment` with `ExpirationDate` left null. Confirm with the pairing SOQL in `references/metadata-examples.md`.
4. **Run `python3 scripts/check_integration_admin_connected_apps.py --manifest-dir force-app/main/default`.** Fix every ERROR — `ipRelaxation` `BYPASS`, `isAdminApproved` with no grantee — before deploying. Justify each WARN (`infinite` refresh policy on an admin-approved app, `Full` scope, a client-credentials user) in the template's Notes section.
5. **Deploy, then verify in the org.** `sf project deploy start -x manifest/package.xml --dry-run`, then without the flag. Run the `ConnectedApplication` and `OauthToken` verification queries from `references/metadata-examples.md` **as a user holding Customize Application** — a least-privileged reviewer sees only their own tokens and will report a false clean.
6. **Rehearse revoke and rotate once, in a sandbox.** Revoke one grant via `DeleteToken` against the revoke endpoint, re-authorize, and confirm the integration recovers. For rotation, decide now whether the path is an ECA deploy with the ignore-warnings attribute or a replacement app plus a caller cutover — the connected app's `consumerKey` cannot be edited after save.
7. **Commit the review checklist and schedule it.** Fill `templates/connected-app-review-checklist.yaml` with one row per app (owner, `last-reviewed`, `token-count-query-run`) and re-run the checker with `--manifest-dir` pointed at the folder holding it; the checker lints those three fields. Set the cadence inside 180 days so `SetupAuditTrail` still corroborates the previous review.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Permitted Users setting matches the authentication flow type
- [ ] Connected app assigned to integration user's Profile or Permission Set (if pre-authorized)
- [ ] IP Relaxation configured consistently with the integration server's network characteristics
- [ ] Refresh Token Policy matches the integration's session management approach
- [ ] Authentication tested successfully as the integration user
- [ ] EventLogFile monitoring configured or scheduled for production use
- [ ] Uninstalled connected apps audit completed (September 2025 default blocking policy)
- [ ] Integration user's `PermissionSetAssignment.ExpirationDate` is null (or the expiry date is diarised)
- [ ] Token inventory was run by a user holding Customize Application, and the row count is under 2,500
- [ ] Revoke path rehearsed once — `DeleteToken` against `/services/oauth2/revoke` — and the integration recovered
- [ ] Rotation path decided and written down (ECA deploy with ignore-warnings, or replacement app + caller cutover)
- [ ] `templates/connected-app-review-checklist.yaml` has an owner, `last-reviewed`, and `token-count-query-run` for every app
- [ ] `python3 scripts/check_integration_admin_connected_apps.py --manifest-dir <dir>` exits 0

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Pre-authorized mode requires explicit profile/permission set assignment** — Setting "Admin approved users are pre-authorized" without assigning the connected app to any Profile or Permission Set blocks ALL users from authenticating, including the admin who created the app. The authentication attempt returns a generic OAuth error. The fix is straightforward — assign the app to the relevant profile or permission set — but the error message does not indicate the missing assignment.
2. **Uninstalled connected apps are blocked by default (September 2025)** — As of September 2025, Salesforce changed the default behavior so that uninstalled connected apps are blocked for most users. Any app that was uninstalled but whose tokens are still in use by integrations will fail silently. Admins must audit connected app usage in Setup > Apps > Connected Apps > OAuth Usage and explicitly permit any still-active apps.
3. **ConnectedApp EventLogFile events require Event Monitoring add-on** — ConnectedApp and ConnectedAppOAuth event types are NOT available in the standard Login History or audit trail UI. They require the Event Monitoring add-on and must be queried via the REST API on the EventLogFile object. Admins without this add-on have no visibility into OAuth token-level activity.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OAuth policy configuration | Permitted Users, IP Relaxation, Refresh Token settings for the connected app |
| Profile/permission set assignment | Step-by-step for assigning connected app to integration user's access |
| EventLogFile query | REST API query template for monitoring connected app usage |
| Connected app security checklist | Audit template for connected app security posture review |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are editing the policy block on a live app, writing the pre-authorization permission set, or need the monitoring SOQL, the revoke procedure, the rotation deploy, or the review-checklist YAML shape |
| `references/gotchas.md` | Something changed and the integration broke, or a monitoring query returned an answer you don't trust — truncated `OauthToken` results, an unfilterable `LoginHistory` field, an assignment that expired, a rotation deploy that was rejected |
| `references/examples.md` | You want the worked end-to-end narratives: pre-authorized mode blocking everyone, and an incident traced through token-level events |
| `references/well-architected.md` | You need the Security / Operational Excellence framing for a review, or the exact official source behind a claim in this skill |
| `references/llm-anti-patterns.md` | You are checking AI-generated connected-app operations guidance before acting on it |
| `templates/integration-admin-connected-apps-template.md` | Before configuring or auditing one app, to capture the policy values, integration user, IP ranges and monitoring plan in one place |
| `templates/connected-app-review-checklist.yaml` | At each periodic review — one row per app, linted by the skill checker |
| `scripts/check_integration_admin_connected_apps.py` | After editing policy XML and before deploying, and again after updating the review checklist |

---

## Related Skills

- **admin/connected-apps-and-auth**: Use to choose the auth artefact and author the full `connectedApp-meta.xml`, External Client App four-file set, or Named Credential pair. NOT for operating an app that already exists.
- **admin/connected-app-troubleshooting**: Use when a specific OAuth error code is already on screen. NOT for hardening or the periodic review.
- **admin/integration-user-management**: Use to set up and govern the dedicated integration user this app pre-authorizes. NOT for the app's own policy values.
- **admin/permission-set-expiration**: Use when the pre-authorizing assignment carries an `ExpirationDate` and you need the expiry model. NOT for which permission set to grant.
- **admin/remote-site-settings**: Use for the outbound URL allowlist for Apex callouts, which is a separate control from anything on the connected app.
- **admin/org-setup-and-configuration**: Use before changing the org trusted-IP list that `ipRelaxation` `ENFORCE` depends on — deploying `NetworkAccess` replaces the whole list.
- **security/connected-app-security-policies**: Use when hardening and secret rotation is the programme of work rather than a single app's operations.
- **security/oauth-token-management**: Use for token issue, refresh, rotation and introspection mechanics in depth. NOT for the admin-side revoke runbook.
- **security/api-only-user-hardening**: Use when the integration principal itself is the risk — API Only, licence choice, and permission scope.
- **security/event-monitoring**: Use when you need the EventLogFile pipeline itself rather than the two connected-app event types.
- **integration/oauth-flows-and-connected-apps**: Use for the deep comparison between OAuth flows. NOT for the admin's policy and monitoring surface.
