---
name: integration-admin-connected-apps
description: "Use when managing Connected Apps for integration purposes — configuring OAuth policies, IP restrictions, refresh token expiry, and monitoring connected app usage. NOT for OAuth flows implementation (use oauth-flows-and-connected-apps)."
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
outputs:
  - "Connected app OAuth policy configuration (Permitted Users, IP Relaxation, Refresh Token)"
  - "Profile or permission set assignment for pre-authorized app access"
  - "EventLogFile query for connected app usage monitoring"
  - "Audit checklist for connected app security posture"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-12
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

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the authentication flow type** — Determine whether the integration uses OAuth user-agent flow (user consent required), JWT bearer flow (no user interaction), or username-password flow (legacy, avoid). This determines the Permitted Users setting and Refresh Token Policy.
2. **Configure Permitted Users** — For server-to-server integrations, set "Admin approved users are pre-authorized." For user-consent flows, set "All users may self-authorize."
3. **Assign connected app to profile or permission set (pre-authorized mode)** — If pre-authorized mode is selected, immediately assign the connected app to the integration user's Profile or a Permission Set. Navigate to Profile > Connected App Access or Permission Set > Assigned Apps. Verify the assignment is saved.
4. **Configure IP Relaxation** — If the integration server has a fixed, known IP range, set "Enforce login IP restrictions" and add those IPs to the integration user's profile trusted ranges. If IP ranges are dynamic, use "Relax IP restrictions" and compensate with certificate-based or MFA-based controls.
5. **Configure Refresh Token Policy** — Match the policy to the integration's session management. JWT bearer flow integrations do not use refresh tokens — set "Immediately expire." Standard OAuth refresh-token integrations should set an expiry that balances security with re-authentication overhead.
6. **Test authentication** — Authenticate as the integration user via the connected app. Confirm token issuance. If authentication fails, check: (a) profile/permission set assignment exists, (b) integration user's profile trusted IPs include the connecting IP, (c) connected app scopes include the required permissions.
7. **Monitor via EventLogFile** — For production integrations, schedule a periodic EventLogFile query for ConnectedApp and ConnectedAppOAuth events to audit usage, catch token revocations, and detect unauthorized access attempts.

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

## Related Skills

- integration-user-management — Setting up the dedicated integration user that will use this connected app
- remote-site-settings — Configuring server-side URL allowlist for Apex callouts (separate from connected app)
