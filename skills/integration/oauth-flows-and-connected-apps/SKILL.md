---
name: oauth-flows-and-connected-apps
description: "Use when choosing or reviewing Salesforce OAuth flows and connected-app policy for integrations, including client credentials, JWT bearer, authorization code, device flow, scopes, and token lifecycle controls. Triggers: 'OAuth flow', 'connected app', 'client credentials', 'JWT bearer', 'refresh token', 'integration user'. NOT for creating and configuring the connected app or External Client App itself in Setup — use admin/connected-apps-and-auth. NOT for wiring the Named Credential and External Credential that carry the chosen flow — use integration/named-credentials-setup. NOT for a live token failure such as invalid_grant after refresh, or token rotation and revocation — use security/oauth-token-management."
category: integration
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - oauth
  - connected-apps
  - client-credentials
  - jwt-bearer
  - auth-code
triggers:
  - "which OAuth flow should this Salesforce integration use"
  - "connected app scope and policy review"
  - "client credentials versus JWT bearer in Salesforce"
  - "refresh token or invalid grant troubleshooting"
  - "username password flow should we use it"
  - "set up client credentials flow for a middleware integration"
  - "decide between a connected app and an external client app"
inputs:
  - "traffic direction such as system to Salesforce, Salesforce to external system, or user delegated access"
  - "whether user context is required"
  - "scope, token lifetime, IP policy, and integration-user constraints"
outputs:
  - "OAuth flow recommendation"
  - "connected-app review findings"
  - "token lifecycle and governance checklist"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Oauth Flows And Connected Apps

Use this skill when the success or failure of an integration depends on picking the right trust model up front. OAuth flow choice is not protocol trivia. It determines whether the integration respects user context, how secrets rotate, how outages behave when tokens expire, and whether security review becomes easy or painful.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the traffic inbound to Salesforce, outbound from Salesforce, or user delegated?
- Does the use case require a human user's authority, or is it machine-to-machine with a dedicated integration principal?
- What scopes, token lifetime, revoke process, and IP/session controls are required by policy?

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Does a human user authorize the access, or is this system-to-system?" | Delegated access needs the web server flow (with PKCE); system access uses client credentials or JWT bearer | The flow family | Tokens that carry the right identity, so audit logs show who acted |
| "If system-to-system, which Salesforce user should the integration act as, and what is that user allowed to do?" | Client credentials returns tokens for one execution user; JWT bearer issues them for the user in `sub` after prior approval | A dedicated integration user and its permission sets | Least privilege that survives scope mistakes |
| "Who manages certificates and secret rotation, and how often?" | JWT bearer needs an X.509 certificate on the app; client credentials depends on a consumer secret anyone holding it can use | A rotation owner and schedule | A planned rotation instead of an outage or a leaked secret that keeps working |
| "Will this app be packaged, promoted across sandboxes, or kept in source control?" | External client apps are metadata-compliant and support 2GP; local ones are not copied to new sandboxes; global OAuth settings hold secrets that must stay out of source control | Connected app vs external client app, and a promotion plan | Repeatable deployments without secrets in git |
| "Which org-wide flows must be blocked?" | Orgs created Summer '23 or later block username-password by default; blocking a flow breaks every existing integration that uses it | The `OauthOidcSettings` target state, tested in a sandbox | A hardened org that does not surprise the integrations already running |
| "What scopes does the consumer really need?" | Scopes cannot be requested on the token call for client credentials or JWT; they come from the app configuration | The minimal scope list on the app | Tokens that cannot reach data the integration never needed |

What a proper configuration adds over "just creating a connected app": the flow matches the actor, the principal behind the token is least-privilege, secrets and certificates have an owner and a rotation date, and insecure flows are blocked org-wide without breaking anything that still depends on them.

---

## Core Concepts

### Flow Choice Starts With Identity

Use Authorization Code when a user must grant access and their permissions matter. Use Client Credentials or JWT bearer when the workload is system-to-system. Device flow is for constrained-user-input experiences, not a shortcut around better integration design.

| Flow | Grant / token endpoint call | Refresh token | Who the token represents | Key constraint (Identity guide) |
|---|---|---|---|---|
| **Web server** | `authorization_code`, recommended with PKCE | Yes, per app policy | The authorizing user | The web server must protect the client secret |
| **JWT bearer** | `urn:ietf:params:oauth:grant-type:jwt-bearer` with a signed assertion | Never issued | The user in `sub` | RS256 with an uploaded certificate (4 KB max); requires prior approval; scopes cannot be passed; 3-minute clock-skew buffer on `exp` |
| **Client credentials** | `client_credentials` with consumer key and secret (body or Basic header) | Not supported | The configured execution (integration) user | Scopes cannot be passed on the token call; `full`, `web`, and `refresh_token` are filtered out |
| **Device** | Device authorization, user approves on a second device | Per policy | The approving user | For limited-input devices and command-line apps |
| **Token exchange** | Exchange an external IdP token for a Salesforce token | Per policy | The mapped user | For architectures with a central identity provider |
| **User-agent** | Implicit grant | Not recommended | The user | Salesforce recommends blocking it; blocking also blocks the hybrid app token flow |
| **Username-password** | `password` | Not recommended | The user whose password is stored | Blocked by default in orgs created Summer '23 or later; not supported by external client apps |

### Connected Apps and External Client Apps

The Identity guide recommends external client apps "in all situations" and migrating local connected apps to local external client apps, while noting some features remain connected-app only.

| Concern | Connected app | External client app |
|---|---|---|
| Packaging | 1GP; 2GP only by reference | 2GP, with distribution states |
| Metadata API | Subset through `ConnectedApp` | Full: `ExternalClientApplication` plus OAuth settings and policy types |
| Sandbox clone or refresh | Copied | Local apps are not copied; only packaged ones are |
| Username-password flow | Supported (if not blocked) | Not supported |
| Dynamic client registration | Supported | Still in development |
| Secrets in metadata | `consumerKey` / `consumerSecret` on `ConnectedAppOauthConfig` | Only in `ExtlClntAppGlobalOauthSettings`, which "can't be packaged and must not be added to source control" |

### Connected App Policy Is Part Of The Architecture

A connected app is not just a client ID. Scopes, token settings, IP rules, and ownership determine how the integration behaves operationally and under incident response.

### Integration Principals Need Least Privilege

Even a perfect OAuth flow is unsafe if the integration user has broad object access or sysadmin-level power. The flow and the permission model must line up.

### Token Lifecycle Is An Operations Problem

Rotation, revocation, monitoring repeated auth failures, and handling `invalid_grant` should be decided before production, not during the first outage.

---

## Common Patterns

### Client Credentials For Server-To-Server Access

**When to use:** A system needs Salesforce API access and no end-user context is required.

**How it works:** Use an external client app (or a connected app) with the client credentials flow enabled, an execution user dedicated to the integration, and narrow scopes and permission sets.

**Why not the alternative:** Username-password flow is weaker operationally and worse for security review.

### JWT Bearer For Certificate-Managed Server Auth

**When to use:** The organization has mature certificate management and wants server authentication without interactive consent.

**How it works:** The external system signs the assertion and exchanges it for access under a controlled principal.

### Authorization Code For Delegated Access

**When to use:** A user must explicitly authorize the app and user-level access should be preserved.

**How it works:** The app obtains consent, receives an authorization code, and manages the token lifecycle according to policy.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Machine-to-machine integration into Salesforce | Client Credentials or JWT bearer | No end-user context required |
| Enterprise-grade server auth with certificate operations already in place | JWT bearer | Strong fit for managed key posture |
| User authorizes an app to act on their behalf | Authorization Code | Preserves user context and consent |
| Legacy proposal uses username and password | Usually reject | Poor security and operability compared with OAuth-based patterns |

---


## Recommended Workflow

1. Classify the actor (human-delegated or system) and the direction of traffic, then pick the flow from the Core Concepts table.
2. Decide connected app or external client app using the comparison table; default to an external client app unless a connected-app-only feature is required.
3. Create the integration principal: a dedicated user with only the permission sets the integration needs (the client credentials execution user must have the API Only permission per the Metadata API guide).
4. Configure the app: minimal OAuth scopes, permitted users set to admin-approved with a permission set, refresh token policy, IP policy, PKCE for authorization code flows, certificate or secret ownership. Use [`references/metadata-examples.md`](references/metadata-examples.md) for deployable files.
5. Harden the org: set `OauthOidcSettings` to block username-password and user-agent flows after confirming in a sandbox that no integration still uses them.
6. Run `python3 skills/integration/oauth-flows-and-connected-apps/scripts/check_oauth_flows_and_connected_apps.py --manifest-dir <project>` and resolve every finding.
7. Rehearse rotation and revocation: rotate the consumer secret or certificate in a sandbox and confirm the integration recovers.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The chosen flow matches the actor and trust model.
- [ ] Connected app scopes and policies are intentionally narrow.
- [ ] A dedicated integration principal exists with least privilege.
- [ ] Secret or certificate rotation is documented and testable.
- [ ] Refresh token and revoke behavior are understood before go-live.
- [ ] Weak legacy patterns such as username-password flow are challenged.

---

## Salesforce-Specific Gotchas

One-line summaries; the full entries are in [`references/gotchas.md`](references/gotchas.md).

| Gotcha | Short form |
|---|---|
| Scopes are not the permission model | The principal behind the token decides what data is reachable |
| No refresh tokens for JWT bearer or client credentials | Request a new access token when it expires |
| Scopes cannot be requested on those token calls | They come from the app and its permitted-user policy |
| Username-password flow | Blocked by default for orgs created Summer '23 or later, and unsupported by external client apps |
| Local external client apps | Not copied to new or refreshed sandboxes |
| Client credentials secret | Anyone holding the key and secret gets a token; rotate it |
| Connected apps without owners | No accountable revoke and rotation path during incidents |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| OAuth decision table | Recommended flow, principal, and policy model |
| Connected-app review | Findings on scopes, secrets, policies, and weak legacy choices |
| Token operations checklist | Rotation, revocation, and outage-handling actions |

---

## Related Skills

- `admin/connected-apps-and-auth` - use when the org-wide auth inventory and setup governance are the main concern, not just integration flow selection.
- `integration/graphql-api-patterns` - use when API shape is the design issue after authentication is settled.
- `apex/callouts-and-http-integrations` - use when outbound callout handling in Apex is the real implementation problem.
