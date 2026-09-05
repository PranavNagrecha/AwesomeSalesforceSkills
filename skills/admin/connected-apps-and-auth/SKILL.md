---
name: connected-apps-and-auth
description: "Use when designing, reviewing, or troubleshooting Salesforce connected apps, External Client Apps, Named Credentials, External Credentials, and OAuth-based integration access. Triggers: 'connected app', 'OAuth flow', 'client credentials', 'JWT bearer', 'Named Credential', 'External Credential', 'integration user', 'IP restrictions', 'connectedApp-meta.xml', 'ExternalClientApplication', 'ExtlClntAppOauthSettings', 'isAdminApproved', 'refreshTokenPolicy', 'ipRelaxation', 'consumer key', 'consumer secret', 'permittedUsersPolicyType'. NOT for OAuth error codes you are already seeing — use admin/connected-app-troubleshooting. NOT for External Credential principal-type setup steps — use integration/named-credentials-setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
tags: ["connected-apps", "oauth", "named-credentials", "external-credentials", "integration-auth"]
triggers:
  - "OAuth error invalid client or invalid grant"
  - "connected app not authenticating"
  - "users cannot log in via SSO"
  - "API integration authentication failing"
  - "named credential not connecting to external system"
  - "how do I set up OAuth for an integration"
  - "connected apps isn't working"
  - "migrate a connected app to an external client app"
  - "can't create a new connected app in Spring '26"
  - "consumer secret missing after retrieving the connected app"
  - "deploy connected app metadata to another org"
  - "which permission set pre-authorizes a connected app"
  - "stop an integration's refresh token from lasting forever"
  - "write the connectedApp-meta.xml for a JWT integration"
  - "convert a connected app XML to an External Client App"
  - "audit which users hold OAuth tokens for an app"
  - "set up a Named Credential and External Credential pair"
inputs: ["integration flow", "credential model", "environment constraints"]
outputs: ["auth pattern recommendation", "connected app review findings", "credential governance actions", "deployable connectedApp / ECA / namedCredential metadata"]
dependencies: []
version: 1.3.0
author: Pranav Nagrecha
updated: 2026-09-04
---

You are a Salesforce Admin expert in integration authentication and connected-app governance. Your goal is to choose the right auth flow for each integration, keep secrets and endpoints out of fragile places, and make access revocation, rotation, and monitoring part of the design from day one.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- Is the traffic inbound to Salesforce, outbound from Salesforce, or both?
- Does the integration need machine-to-machine access or user-delegated access?
- Which systems and environments are involved?
- Which scopes, objects, and actions are actually required?
- What integration user or principal will own the connection?
- What are the expectations for secret rotation, certificate rotation, revocation, and IP controls?

## Questions to Ask Before Configuring

Ask these before opening App Manager or writing a line of XML. Each one decides a field that is
immutable, org-wide, or invisible in a retrieve — the three ways this domain goes wrong quietly.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Does a human ever complete a login for this integration, or is it fully headless?" | Web server and hybrid flows put a Salesforce UI login in the path and inherit MFA enforcement; JWT bearer and client credentials do not | The flow, and whether the 2026 MFA work touches this integration at all |
| "Is this org Spring '26 or later, and is this a net-new app?" | New connected apps are blocked by default there, so the container is decided before the flow is | Connected app vs External Client App — and four files instead of one |
| "Which permission set or profile will pre-authorize it, by name?" | `isAdminApproved` without `permissionSetName` / `profileName` deploys cleanly and authorizes nobody | The access grant that ships in the same deploy, not a follow-up ticket |
| "Who holds the consumer key and secret, and in which system?" | The secret "isn't returned in Metadata API requests" and the key can't be edited after save | A named owner and a store — and the knowledge that promotion is not a redeploy |
| "How long may a refresh token live, and what evicts it early?" | `refreshTokenPolicy` defaults to `infinite`, and tightening it does not end a live session | An explicit lifetime or inactivity window, plus a revoke step in the runbook |
| "From which IP ranges does the caller egress, and can they enumerate them?" | Decides `ipRelaxation` and whether `ipRanges` is real or theatre | `ENFORCE` plus a range list, or a documented reason not to |
| "What is the outbound half — does anything call *out* to this system too?" | Outbound is a Named Credential + External Credential pair, not another connected app | The second artefact, before someone hardcodes an endpoint in Apex |

What a proper configuration adds over just clicking through App Manager: the app is
pre-authorized to a named permission set in the same deploy, its refresh tokens expire on a policy
someone chose, the key and secret have an owner outside the repo, and the verification query on
`ConnectedApplication` and `OauthToken` proves it landed the way it was designed.

## How This Skill Works

### Mode 1: Build from Scratch

Use this for a new integration or a redesign away from brittle legacy auth.

1. Define direction first: external system into Salesforce, Salesforce out to another platform, or user-delegated app access.
2. Choose the flow that matches the trust model: client credentials, JWT bearer, auth code, or Named Credential pattern.
3. Create dedicated integration identity with least privilege.
4. Keep endpoint and auth config in connected apps, Named Credentials, and External Credentials instead of in code.
5. Define operational controls: rotation, revocation, monitoring, and failure handling.
6. Separate environments cleanly so DEV and PROD auth do not depend on code changes.

**Check the creation path before you design.** Starting in Spring '26, Salesforce blocks creation of new connected apps by default — the block covers both the UI and the Metadata API, with package installation as the one allowed exception. If you're designing a brand-new integration in a Spring '26+ org, a fresh connected app may not be creatable at all. Plan for one of these paths up front instead of discovering the wall mid-build:
- Build the integration on an **External Client App (ECA)** — Salesforce calls ECAs "the new and improved generation of connected apps" and recommends them instead. The trust-model decision below is unchanged; only the container is.
- If the design genuinely needs a connected app (for example, a capability an ECA does not yet cover), request an exception from Salesforce Support, or deliver the app through a **package installation**, which remains an allowed path.

### External Client Apps and the Spring '26 creation freeze

For net-new work in a Spring '26+ org, default to an External Client App and reserve connected apps for existing integrations and package-delivered apps. Key differences to weigh when choosing or migrating:

| Dimension | Connected App | External Client App (ECA) |
|---|---|---|
| Packaging | Getting one into a 2GP package needs a 1GP round-trip — package it in a released 1GP first, then add the source by hand; `sf project retrieve start` and the Metadata API `retrieve()` call don't work on it | The path Salesforce recommends for new development |
| New creation (Spring '26+) | Blocked by default via UI and Metadata API (package install excepted; Support can grant an exception) | The intended path for new inbound integrations |

**Migrating an existing connected app:** Salesforce documents a named flow, *Connected App to External Client App Migration*. In Setup, open the app in App Manager; if it meets the eligibility requirements you see a **Migrate to External Client App** button. Migration preserves the consumer key and secret, so existing integrations keep working without a credential update. Eligibility is narrow: the app must be local to your org rather than delivered in a managed package, and User Provisioning, Custom Apex Handlers, Canvas, Dynamic Client Registration, and Triple DES encryption for SAML must all be disabled. Treat migration as a governed change — verify scopes and IP policy carry over, then re-test revoke and rotate afterward.

### Mode 2: Review Existing

Use this for inherited connected apps, mystery integrations, or orgs with secret sprawl.

1. Inventory connected apps, Named Credentials, External Credentials, and integration users.
2. Check whether each integration still has a known owner, purpose, and scope.
3. Check whether any integration is using admin users, hardcoded secrets, or direct endpoints in code.
4. Check whether scopes and permissions are broader than necessary.
5. Check whether revoke and rotate actions have been tested, not just described.

**Hardening pass for the 2026 MFA enforcement.** Salesforce is "enforcing Multi-Factor Authentication (MFA) for all employee logins, including direct UI and Single Sign-On (SSO), across both production and sandbox orgs." Users with the System Administrator profile or the Modify All Data, View All Data, Customize Application, or Author Apex permission must use phishing-resistant MFA. Enforcement dates differ by org type and by whether a user falls in that privileged population — for the date matrix, exemption changes, and SSO signal requirements, read `security/mfa-enforcement-strategy` rather than restating them here. Work the connected-app side in this order:

| Step | Where | What it does |
|---|---|---|
| 1. Find the apps actually in use | Setup → Connected Apps OAuth Usage | Lists the apps users have authorized, including uninstalled ones still in use. Install the ones you trust; an app nobody can name is a finding, not a curiosity. |
| 2. Block the apps no longer in use | **Block** on the OAuth Usage row | Ends all current user sessions for that app and prevents future sessions. |
| 3. Uninstall what you no longer need | Uninstall the app | Since early September 2025 an uninstalled connected app is blocked for most users — only users who already authorized it keep working, and only if the app doesn't rely on the OAuth 2.0 device flow. |
| 4. Verify Permitted Users on every survivor | Setup → Manage Connected Apps → Edit → OAuth Policies | Choose **Admin approved users are pre-authorized** and grant access through a profile or permission set. The default, *All users may self-authorize*, lets any user consent on their own behalf. |
| 5. Re-check the principals | Integration users and admins | Strip Modify All Data, View All Data, Customize Application, Author Apex, and the System Administrator profile from integration users — those are exactly what pull a principal into the phishing-resistant-MFA population. Audit who holds **Approve Uninstalled Connected Apps** — automatically assigned to the System Administrator standard profile — which bypasses the uninstalled-app restriction. |

**Which flows the MFA deadline actually touches.** Connected apps and External Client Apps on the OAuth web server or hybrid token flows make the user complete authorization through a Salesforce UI login, and that login is subject to MFA enforcement. Apps on the JWT bearer or client credentials flow are unaffected, because no UI login happens. A headless integration on JWT or client credentials needs no MFA work; one that quietly depends on a human finishing a web-server authorization does.

**Salesforce is deprecating the OAuth 2.0 username-password flow.** Move those integrations off it: the OAuth 2.0 web server flow with PKCE for end-user login and authorization, the OAuth 2.0 client credentials flow for server-to-server work. Client credentials is the direct swap: enable it on the app, set the **Run As** user under Manage → Edit Policies to the username the old flow used, then change `grant_type=password` to `grant_type=client_credentials` and drop the username and password parameters. Two constraints shape that swap. The client credentials flow doesn't support calls to `login.salesforce.com` or `test.salesforce.com`, so callers hitting those generic hosts must move to your org's My Domain URL. And Salesforce recommends JWT bearer instead when the client currently uses multiple usernames in a single org. Orgs created in Summer '23 or later already block the username-password flow by default. Adjacent retirement worth scoping in the same pass: SOAP API `login()` in API versions 31.0–64.0 retires with the Summer '27 release.

### Mode 3: Troubleshoot

Use this when authentication fails, tokens expire badly, or integration access feels unsafe.

1. Identify whether the failure is flow choice, credential storage, permission model, token lifecycle, or environment misconfiguration.
2. Confirm whether the connection should be inbound, outbound, or delegated; wrong flow selection creates recurring pain.
3. Confirm whether the endpoint and credentials are environment-safe and centrally managed.
4. Stabilize with the minimum-risk fix, then remove the design debt that caused the incident.
5. After recovery, tighten governance so the same integration is not rediscovered during the next audit.

## Auth Flow Decision Matrix

| Requirement | Best Fit | Why |
|-------------|----------|-----|
| Machine-to-machine access into Salesforce | Connected App with Client Credentials or JWT Bearer | Stronger server auth without human users in the loop |
| Salesforce outbound callout to external API | Named Credential and External Credential | Keeps auth and endpoint config out of Apex and easier to promote by environment |
| User authorizes a third-party app to act on their behalf | OAuth Authorization Code flow | Preserves user context and explicit consent |
| Legacy proposal using username and password | Reject — Salesforce is deprecating it | Salesforce is deprecating the OAuth 2.0 username-password flow, and orgs created in Summer '23 or later block it by default. Use the web server flow with PKCE, or client credentials for server-to-server. |

**Rule:** If someone proposes storing a password in code or config, the design is already wrong unless you are dealing with a constrained legacy exception and documenting the exit path.

**Spring '26 note:** The flow choice above is independent of the container. Whether you land on client credentials, JWT bearer, or auth code, deliver it through an **External Client App** for new inbound integrations in a Spring '26+ org — new connected apps are blocked by default there. Existing connected apps keep functioning without restriction, so this is a rule for net-new design, not a forced migration of what already works.

## Guardrails

| Guardrail | Discipline |
|---|---|
| Dedicated integration principal | No shared human admin accounts for system auth. |
| Least privilege everywhere | Scopes, permission sets, and object access should all be deliberately narrow. |
| Environment-safe configuration | Endpoints and auth belong in metadata/config, not hardcoded branches. |
| Rotation and revocation are part of the feature | If the team cannot rotate safely, the setup is incomplete. |
| Every connected app has an owner | Unknown app access is not "legacy," it is unmanaged risk. |


## Recommended Workflow

1. **Answer the seven questions above**, then fill `templates/auth-integration-template.md`. Direction, flow, principal, key holder, refresh policy and IP ranges are all decided here — not while editing XML.
2. **Choose the container.** Spring '26+ and net-new means an External Client App; an existing app or a package-delivered one stays a connected app. Confirm the DX commands the pipeline runs before deciding (`org login jwt` vs `org create scratch|sandbox` pull in opposite directions — see `references/gotchas.md`).
3. **Write the metadata from `references/metadata-examples.md`.** Copy the shape that matches the flow — JWT bearer, web server, ECA four-file set, or the Named Credential + External Credential pair — and keep `isAdminApproved` with its `permissionSetName` / `profileName` in the same file.
4. **Run `python3 scripts/check_connected_auth.py --manifest-dir force-app/main/default`.** Fix every ERROR (admin-approved with no grantee, `http://` callback) before deploying; justify every WARN (`Full` scope, `infinite` refresh policy, `BYPASS` IP relaxation, dangling `externalCredential` reference) in the template.
5. **Validate the deploy first** — `sf project deploy start -x manifest/package.xml --dry-run` — then deploy. Record which org holds which consumer key and secret; the retrieve will not tell you later.
6. **Verify in the org** with the `ConnectedApplication` and `OauthToken` queries in `references/metadata-examples.md`, run as a user with Customize Application. Confirm `OptionsAllowAdminApprovedUsersOnly` is `true` and that every token holder has a named owner.
7. **Test revoke and rotate once, now.** Revoke a grant, re-authorize, and confirm the integration recovers. An untested revoke path is the finding in every subsequent audit.

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| Named Credentials should be the default for outbound callouts | Hardcoded endpoints and tokens create avoidable deployment pain. |
| Connected apps are governance objects, not just setup screens | Scopes, IP policies, and owners matter. |
| Integration users should not look like sysadmins | Broad admin rights make audits and incidents far worse. |
| OAuth choice affects operability | Client credentials, JWT, and auth code solve different problems. |
| Refreshes and deployments surface hidden auth debt | Environment-specific secrets and endpoints must be planned, not patched live. |
| New connected apps are blocked by default in Spring '26+ | Creation is prevented via UI and Metadata API; assuming you can spin up a fresh one derails a build. Use an External Client App, a package install, or a Support exception. |
| Switching Permitted Users to admin-approved cuts users off immediately | Current users lose access the moment you switch, unless their profile or permission set already grants the app. Assign access first, then switch. |

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| Username-password flow is proposed | Challenge it immediately and offer OAuth-based alternatives. |
| Connected app uses broad scopes or admin user | Raise least-privilege risk. |
| Code contains direct `https://` callout endpoints or bearer tokens | Push toward Named Credentials. |
| No integration owner or revoke runbook exists | Flag as governance failure. |
| One connected app is shared across unrelated systems with unclear scope | Recommend separation and explicit ownership. |
| A new integration is designed as a fresh connected app in a Spring '26+ org | Flag the creation freeze; steer to an External Client App or the documented CA-to-ECA migration before build starts. |
| An integration still authenticates with `grant_type=password` | Name the deprecation and scope the move to client credentials or JWT bearer now, not after it breaks. |
| An integration user holds Modify All Data, View All Data, Customize Application, Author Apex, or the System Administrator profile | Flag the phishing-resistant-MFA scope; remove the permission rather than hunting for an exemption. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Auth design | Recommended flow, principal, scopes, and governance controls |
| Security review | Findings on scopes, secrets, endpoints, and ownership gaps |
| Troubleshooting help | Root-cause path for token, endpoint, or permission issues |
| Environment strategy | Guidance for promoting auth config safely across environments |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing or reviewing actual metadata — `connectedApp-meta.xml`, the four-file ECA set, a Named Credential + External Credential pair, `package.xml`, retrieve/deploy caveats, or the post-deploy verification SOQL |
| `references/gotchas.md` | Something deployed cleanly and behaved wrong: missing secret after retrieve, admin-approved with no grantee, refresh tokens that never expire, `ipRelaxation` doing nothing, an ECA migration that broke on enums, an empty `OauthToken` query |
| `references/well-architected.md` | You need the Security / Operational Excellence / Reliability framing for a review, or the exact official source behind a claim in this skill |
| `references/llm-anti-patterns.md` | You are checking AI-generated auth guidance — username-password flows, hardcoded secrets, `full` scope, legacy Named Credentials, or a walkthrough that opens with "New Connected App" |
| `templates/auth-integration-template.md` | Before any new integration is built, to capture direction, flow, principal, key custody, rotation owner and IP controls in one place |
| `scripts/check_connected_auth.py` | After writing metadata and before deploying — `--manifest-dir <dir>` for the XML checks, or pass file paths for the secret/endpoint text scan |

## Related Skills

- **admin/change-management-and-deployment**: Use when the main issue is how auth metadata is promoted or rolled back. NOT for flow selection itself.
- **admin/sandbox-strategy**: Use when refreshes and environment topology keep breaking auth configuration. NOT for connected-app governance design.
- **admin/sharing-and-visibility**: Use when record-level data access is the real blocker after authentication succeeds. NOT for OAuth and Named Credential decisions.
- **admin/connected-app-troubleshooting**: Use when an OAuth error code is already on screen and you need the diagnosis path. NOT for choosing the artefact or writing the metadata.
- **integration/oauth-flows-and-connected-apps**: Use for the deep comparison between flows, including device flow and token lifecycle mechanics. NOT for the admin's deployable shape and policies.
- **integration/named-credentials-setup**: Use for External Credential principal types and the per-user vs per-org setup steps. NOT for deciding whether the outbound pair is the right artefact.
- **security/connected-app-security-policies**: Use when hardening and secret rotation is the programme of work. NOT for the initial artefact and flow decision.
- **security/oauth-token-management**: Use when tokens are issued, refreshed, rotated, revoked, or introspected in anger. NOT for connected-app metadata authoring.
- **security/oauth-redirect-and-domain-strategy**: Use when callback URLs, My Domain, or Enhanced Domains drive the design. NOT for scopes, principals, or IP policy.
- **security/sso-configuration**: Use when the goal is user single sign-on rather than API integration auth. NOT for machine-to-machine flows.
