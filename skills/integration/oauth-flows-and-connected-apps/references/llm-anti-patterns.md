# LLM Anti-Patterns — OAuth Flows and Connected Apps

Common mistakes AI coding assistants make when generating or advising on Salesforce OAuth flows and Connected App configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Username-Password Flow for Production Integrations

**What the LLM generates:** "Use the username-password OAuth flow for server-to-server integration" including hardcoded username, password, and security token in the integration code.

**Why it happens:** Username-password flow is the simplest OAuth flow with the most training examples. LLMs default to it because it requires the fewest setup steps. However, it is insecure and Salesforce is actively deprecating it.

**Correct pattern:**

```text
OAuth flow selection for server-to-server integrations:

RECOMMENDED:
1. Client Credentials Flow (Spring '23+):
   - Simplest secure option for system-to-system
   - No user context — runs as the Connected App's execution user
   - Requires "Enable Client Credentials Flow" on the Connected App

2. JWT Bearer Flow:
   - Service account with certificate-based authentication
   - X.509 certificate registered on the Connected App
   - Pre-authorized — no interactive login required

NOT RECOMMENDED:
3. Username-Password Flow:
   - Password in configuration is a security risk
   - Breaks when password expires or security token changes
   - No MFA support — blocked when MFA is enforced
   - Salesforce is phasing out this flow
```

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
- Default: session timeout settings (typically 2 hours)
- Configurable via session policies on the Connected App

Refresh token expiration (Connected App > OAuth Policies):
- "Immediately expire" — no refresh tokens issued
- "Expire after N hours/days" — recommended for most integrations
- "Until Revoked" — use ONLY when justified (long-running batch, offline mobile)

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
