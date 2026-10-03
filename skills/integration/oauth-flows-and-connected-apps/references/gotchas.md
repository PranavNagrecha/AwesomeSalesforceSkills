# Gotchas - Oauth Flows And Connected Apps

Non-obvious behaviors that cause real production problems. "Identity guide" means Identify Your Users and Manage Access, Spring '26 (identity.pdf), chapters External Client Apps and Connected Apps and Authorize Apps with OAuth. "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: The Correct Flow Can Still Be Overpowered

**What happens:** The architecture uses client credentials or JWT bearer correctly, but the token can read far more than the integration needs.

**When it occurs:** Teams treat OAuth scopes as the whole authorization model. Client credentials returns an access token "on behalf of the integration user you assigned", and the JWT bearer token represents the user named in `sub`, so object, field, and record access come from that user's permissions.

**How to avoid:** Give the execution user only the permission sets the integration needs. The Metadata API guide says the client credentials execution user "must have the API Only permission". Review the user, the app's permitted-user policy, and the scopes together.

**Source:** Identity guide, OAuth 2.0 Client Credentials Flow for Server-to-Server Integration; OAuth 2.0 JWT Bearer Flow for Server-to-Server Integration; Metadata API, ExtlClntAppOauthConfigurablePolicies (`clientCredentialsFlowUser`).

---

## Gotcha 2: JWT Bearer and Client Credentials Never Return a Refresh Token

**What happens:** An integration built around refresh tokens stops working when its first access token expires, because no refresh token was ever issued.

**When it occurs:** For JWT bearer, "This flow never issues a refresh token." For client credentials, "This flow doesn't support refresh tokens", and Salesforce "automatically filters out" the `full`, `web`, and `refresh_token`/`offline_access` scopes from the response.

**How to avoid:** When the access token expires (a 401 from the API), run the flow again to get a new access token. Do not add `refresh_token` to these apps expecting it to help.

**Source:** Identity guide, JWT Bearer Flow (Note) and Client Credentials Flow (Note; Salesforce Grants an Access Token, scope parameter).

---

## Gotcha 3: Scopes Cannot Be Requested on the Token Call

**What happens:** The client sends `scope=api` with a client credentials or JWT request and still receives a different set, or the team cannot work out where scopes come from.

**When it occurs:** "Because Salesforce doesn't support scopes on the token endpoint, you can't include scopes in the request" (client credentials). For JWT bearer, "You can't specify scopes in a JWT bearer token flow. Scopes are issued according to the connected app's Permitted Users policy or your org's API Access Control settings." With self-authorization, the scopes come from prior approvals; with admin pre-authorization, from the scopes assigned to the app.

**How to avoid:** Configure scopes on the app, set permitted users to admin-approved, and assign the app to a permission set. If an allowlisted app does not return the expected scopes, the guide's fix is to block and then unblock it under Connected Apps OAuth Usage.

**Source:** Identity guide, Client Credentials Flow (Request an Access Token note); JWT Bearer Flow (Scope Parameter table).

---

## Gotcha 4: JWT Bearer Needs Prior Approval and a Tight Clock

**What happens:** A correctly signed JWT returns an unauthorized error, or works for some users and not others.

**When it occurs:** The flow "does require prior approval of the client app": either admin pre-authorization through profiles or permission sets, or an earlier user approval that included a refresh token. "If Salesforce doesn't find previous approvals that included a refresh token or any available approved scopes, the request fails as unauthorized." The JWT must be signed with RS256 using an uploaded X.509 certificate (no larger than 4 KB), `aud` must be `https://login.salesforce.com`, `https://test.salesforce.com`, or the Experience Cloud site URL, and Salesforce allows only a 3-minute clock-skew buffer on `exp`. A repeated `jti` is rejected to prevent replay.

**How to avoid:** Pre-authorize the integration user through a permission set on the app, keep server clocks synced, set short `exp` values, and use the sandbox audience for sandboxes.

**Source:** Identity guide, OAuth 2.0 JWT Bearer Flow for Server-to-Server Integration (Create a JWT; Salesforce Grants Access Token).

---

## Gotcha 5: A Leaked Client Credentials Secret Is a Working Login

**What happens:** A consumer key and secret committed to a repository let anyone mint tokens as the integration user.

**When it occurs:** "With this flow enabled, any person or app that has access to your connected app's consumer key and consumer secret can get an access token."

**How to avoid:** Store the secret in a vault, send it in the POST body or a Basic authorization header (never a GET query string), rotate it on a schedule, and rotate immediately on suspicion of compromise. Keep the execution user least-privilege so a leak is contained.

**Source:** Identity guide, Client Credentials Flow (Warning; Request an Access Token Important note).

---

## Gotcha 6: Username-Password Flow Is Blocked by Default in Newer Orgs

**What happens:** A script that worked in an older sandbox fails in a new org, or stops working after someone hardens OAuth settings.

**When it occurs:** "If your org is created in Summer '23 or later, the username-password flow is blocked by default." Admins can block the user-agent and username-password flows in OAuth and OpenID Connect Settings (metadata `OauthOidcSettings`: `blockOAuthUnPwFlow`, `blockOAuthUsrAgtFlow`). "After a flow is blocked ... existing integrations that use the blocked flow no longer work," and blocking the user-agent flow also blocks the hybrid app token flow. External client apps do not support the username-password flow at all.

**How to avoid:** Replace username-password integrations with client credentials or OpenID Connect dynamic client registration, as the guide recommends, before blocking. Test the block in a sandbox first.

**Source:** Identity guide, Block Authorization Flows to Improve Security; Connected App to External Client App Migration (Important note); Metadata API, OauthOidcSettings.

---

## Gotcha 7: Local External Client Apps Do Not Follow Sandbox Refreshes

**What happens:** After a sandbox refresh, the integration's external client app is missing in the sandbox while the connected apps came across.

**When it occurs:** "Local external client apps aren't copied to a new sandbox when you clone or refresh a sandbox. Only packaged external client apps are copied to the sandbox."

**How to avoid:** Keep the app's metadata (header, OAuth settings, policies) in source control and deploy it after each refresh, or package it. Plan new consumer credentials for each sandbox.

**Source:** Identity guide, Comparison of Connected Apps and External Client Apps Features (note 5).

---

## Gotcha 8: Global OAuth Settings Carry Secrets and Must Stay Out of Source Control

**What happens:** A developer retrieves the external client app and commits `ExtlClntAppGlobalOauthSettings` with the consumer key and secret.

**When it occurs:** The Metadata API guide describes that type as holding "private and sensitive OAuth consumer information that can't be packaged and must not be added to source control." Retrieving it also needs the Allow Access to OAuth Consumer Secrets via Metadata API org permission and, for developers, the View External Client Apps Consumer Secrets in Metadata user permission.

**How to avoid:** Exclude the global settings folder from version control (for example in `.forceignore` and `.gitignore`), keep consumer secrets in a vault, and set the flow switches in the configurable policies file instead. If rotation through deploy is needed, `shouldRotateConsumerSecret` requires the deploy to ignore warnings.

**Source:** Metadata API, ExtlClntAppGlobalOauthSettings (description, Special Access Rules, `shouldRotateConsumerSecret`).

---

## Gotcha 9: The Metadata Guide's Own Samples Do Not Parse

**What happens:** A team copies the sample `OauthOidcSettings` or `ExtlClntAppOauthConfigurablePolicies` XML from the guide and the deploy fails with an XML parse error.

**When it occurs:** The `OauthOidcSettings` sample uses typographic quotes (`“` and `”`) in the XML declaration and namespace. The `ExtlClntAppOauthConfigurablePolicies` sample closes `<namedUserJwtTimeout>` with `</namedUserJwtSessionTimeout>`.

**How to avoid:** Start from the corrected files in `references/metadata-examples.md`, and run an XML parser over any file before deploying.

**Source:** Metadata API, OauthOidcSettings (Declarative Metadata Sample Definition); ExtlClntAppOauthConfigurablePolicies (Declarative Metadata Sample Definition).

---

## Gotcha 10: Each User Gets Five Authorizations per App by Default

**What happens:** A user who signs in to the same app from a sixth device silently invalidates the oldest token.

**When it occurs:** "The default is five authorizations per connected app per user. If a user tries to grant access to a connected app after reaching the org's limit, the access token that has been unused for the longest period of time is revoked."

**How to avoid:** For shared integration users, do not run many parallel authorizations of the same app with user-delegated flows; use client credentials or JWT bearer for system access.

**Source:** Identity guide, OAuth Authorization Flows and Connected Apps (Note).

---

## Gotcha 11: Connected Apps Outlive Their Owners

**What happens:** An app remains active but nobody knows who owns or audits it.

**When it occurs:** Setup work is treated as one-time implementation instead of governed access.

**How to avoid:** Record an owner, a purpose, and a revocation runbook for every app, and review OAuth usage periodically. This is governance practice rather than a documented platform behavior.

**Source:** Practice guidance; no platform claim.
