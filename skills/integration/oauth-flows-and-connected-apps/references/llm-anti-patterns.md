# LLM Anti-Patterns — OAuth Flows and Connected Apps

Common mistakes AI coding assistants make when generating or advising on Salesforce OAuth flows and Connected App configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Username-Password Flow for Production Integrations

**What the LLM generates:** "Use the username-password OAuth flow for server-to-server integration" including hardcoded username, password, and security token in the integration code.

**Why it happens:** Username-password flow is the simplest OAuth flow with the most training examples. LLMs default to it because it requires the fewest setup steps. However, the Identity guide recommends avoiding it because it passes credentials back and forth, orgs created Summer '23 or later block it by default, and external client apps do not support it.

**Correct pattern:**

```text
OAuth flow selection for server-to-server integrations:

RECOMMENDED:
1. Client Credentials Flow:
   - Simplest secure option for system-to-system
   - Token represents the configured execution user (API Only permission)
   - Enable it on the app (isClientCredentialsFlowEnabled) and set the execution user
   - No refresh token; request a new access token when it expires

2. JWT Bearer Flow:
   - Certificate-based: X.509 certificate registered on the app
   - Requires prior approval (admin pre-authorization or an earlier user approval)
   - No refresh token; no scope parameter on the token call

NOT RECOMMENDED:
3. Username-Password Flow:
   - Stored password is a security risk and breaks on password changes
   - Blocked by default in orgs created Summer '23 or later
   - Not supported by external client apps
```

UNVERIFIED (2026-10-03): an earlier version of this file dated the client credentials flow to Spring '23 and said the username-password flow has "no MFA support"; neither statement appears in the Identity guide read for this revision.

**Detection hint:** Flag `grant_type=password` in OAuth token requests. Look for username/password/security_token in integration configuration.

---

## Anti-Pattern 2: Using Overly Broad OAuth Scopes

**What the LLM generates:** `scope=full` or `scope=api refresh_token web` in Connected App configurations without evaluating the minimum required scope.

**Why it happens:** Broad scopes ensure the integration "just works." LLMs optimize for functionality over security, using the most permissive scope.

**Correct pattern:**

```text
OAuth scope selection (principle of least privilege):

api:           REST/SOAP API access (most common need)
refresh_token: offline access (long-lived token)
chatter_api:   Chatter REST API only
custom_permissions: custom permission-based access
content:       Content API access
id:            OpenID Connect identity
profile:       user profile information
web:           web-based access (redirects)
full:          ALL of the above (avoid for most integrations)

Guidelines:
- Start with the minimum scope required
- Add scopes only when specific functionality is needed
- Avoid "full" unless the integration genuinely needs all capabilities
- Document why each scope was selected
```

**Detection hint:** Flag Connected App configurations with `scope=full` without justification. Check for refresh_token scope on integrations that do not need offline access.

---

## Anti-Pattern 3: Not Setting Token Expiration Policies

**What the LLM generates:** Connected App configuration with refresh token set to "Until Revoked" without noting the security risk of indefinitely-lived tokens.

**Why it happens:** "Until Revoked" is the simplest configuration and avoids token expiration errors. LLMs choose the path of least friction.

**Correct pattern:**

```text
Token lifecycle policies:

Access token expiration:
- Default: governed by session timeout settings (UNVERIFIED 2026-10-03: the "typically 2 hours" figure from an earlier version is not in the fetched Identity guide)
- Configurable via session policies on the Connected App

Refresh token expiration (Connected App > OAuth Policies):
- "Immediately expire": no refresh tokens issued (metadata value Zero)
- "Expire after N hours/days/months": SpecificLifetime or SpecificInactivity
- "Until Revoked": Infinite; use ONLY when justified (long-running batch, offline mobile)

Recommendations:
- Server-to-server: use Client Credentials or JWT (no refresh token needed)
- Interactive: set refresh token to expire after 7-30 days
- Mobile: "Until Revoked" may be acceptable but document the risk
- Always implement token revocation on user deprovisioning
```

**Detection hint:** Flag "Until Revoked" refresh token policies without documented justification. Check for missing token expiration configuration in Connected App setup.

---

## Anti-Pattern 4: Confusing Connected App Callback URL with the Integration Endpoint

**What the LLM generates:** Setting the callback URL to the Salesforce API endpoint or the external system's API endpoint instead of the OAuth redirect URI where the authorization code is delivered.

**Why it happens:** The term "callback URL" is ambiguous. LLMs sometimes confuse the OAuth redirect URI (where the browser redirects after authorization) with API callback endpoints.

**Correct pattern:**

```text
Connected App Callback URL:

Purpose: the URL where Salesforce redirects the browser after the user
authorizes the Connected App (authorization code flow only).

For web applications:
  https://myapp.example.com/oauth/callback

For local development:
  https://localhost:8443/oauth/callback

For CLI/SFDX:
  http://localhost:1717/OauthRedirect

For server-to-server flows (JWT, Client Credentials):
  Callback URL is still required but is not used during the flow.
  Set to a valid URL owned by your organization.
  Example: https://login.salesforce.com/services/oauth2/callback

The callback URL is NOT:
- The Salesforce REST API endpoint
- The external system's API endpoint
- The Salesforce org's My Domain URL (unless building a Canvas app)
```

**Detection hint:** Flag callback URLs pointing to Salesforce API endpoints (`/services/data/`) or to external system APIs. The callback should be an application-owned redirect handler.

---

## Anti-Pattern 5: Not Restricting Connected App Access with IP and Profile Policies

**What the LLM generates:** A Connected App with "All users may self-authorize" and no IP restrictions, allowing any authenticated user from any location to obtain tokens.

**Why it happens:** Permissive defaults are easier to set up. LLMs skip the access restriction steps because they add complexity without being required for functionality.

**Correct pattern:**

```text
Connected App security hardening:

1. Permitted Users:
   - "Admin approved users are pre-authorized" (recommended for server-to-server)
   - Then assign the Connected App to specific profiles or permission sets
   - Avoids: any user being able to self-authorize

2. IP Relaxation:
   - "Enforce IP restrictions" — respects the user's profile IP range
   - "Relax IP restrictions" — only when mobile/remote access is required
   - For server-to-server: enforce IP restrictions and allowlist the integration server

3. Session Policies:
   - Set session timeout appropriate for the use case
   - Enable "Require Proof Key for Code Exchange (PKCE)" for public clients

4. OAuth Policies:
   - Set refresh token expiration (not "Until Revoked")
   - Set "Require Secret for Web Server Flow" to true
```

**Detection hint:** Flag Connected Apps with "All users may self-authorize" in production. Check for missing IP restrictions on server-to-server Connected Apps.

---

## Anti-Pattern 6: Sending a scope parameter on client credentials or JWT token calls

**What the LLM generates:** `grant_type=client_credentials&scope=api%20refresh_token`, with the assumption that the token will include a refresh token.

**Why it happens:** Generic OAuth 2.0 examples pass `scope` on the token endpoint.

**Correct pattern:** Configure scopes on the app. The Identity guide says Salesforce does not support scopes on the token endpoint for client credentials, and that JWT bearer scopes come from the Permitted Users policy or API Access Control. Neither flow issues refresh tokens.

**Detection hint:** `scope=` in a token request body whose `grant_type` is `client_credentials` or `urn:ietf:params:oauth:grant-type:jwt-bearer`.

---

## Anti-Pattern 7: Committing external client app global OAuth settings

**What the LLM generates:** A retrieve-and-commit script that adds every file under `force-app`, including `extlClntAppGlobalOauthSets/*.ecaGlblOauth-meta.xml` with `consumerKey` and `consumerSecret`.

**Why it happens:** The model treats all metadata as safe for source control.

**Correct pattern:** Exclude the global OAuth settings folder in `.forceignore` and `.gitignore`. The Metadata API guide says this type "can't be packaged and must not be added to source control." Keep the secret in a vault.

**Detection hint:** A tracked file under `extlClntAppGlobalOauthSets/`, or a `consumerSecret` element in any committed XML.

---

## Anti-Pattern 8: Defaulting to a new connected app for new integrations

**What the LLM generates:** Step-by-step "App Manager > New Connected App" instructions for a new integration, with no mention of external client apps.

**Why it happens:** Connected apps dominate older training material.

**Correct pattern:** The Identity guide recommends external client apps "in all situations" and migrating local connected apps, unless a connected-app-only feature is needed (for example SAML, canvas, user provisioning, or dynamic client registration). Note that local external client apps are not copied to refreshed sandboxes, so deploy their metadata after each refresh.

**Detection hint:** New-integration guidance that creates a connected app without checking whether an external client app fits.

