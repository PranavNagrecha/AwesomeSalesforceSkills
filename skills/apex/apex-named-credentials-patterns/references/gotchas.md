# Gotchas — Apex Named Credentials Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Enhanced Model Separates External Credential From Named Credential — They Are Not the Same Record

**What happens:** Developers look for the auth configuration (OAuth client ID, client secret, principal type) on the Named Credential record and cannot find it. In the enhanced model (Spring '22+), the Named Credential only holds the endpoint URL; all auth configuration lives on the linked External Credential record.

**When it occurs:** Any time a developer or admin tries to inspect or modify OAuth settings for a Named Credential in an enhanced-model org. Also happens when Apex developers try to reference the External Credential API name directly in code — the correct reference is always the Named Credential API name with the `callout:` prefix, not the External Credential name.

**How to avoid:** In enhanced-model orgs, always navigate to **Setup > External Credentials** to view or modify auth configuration. The Named Credential record is only for endpoint URL and HTTP headers. The `callout:` syntax in Apex always references the Named Credential API name, never the External Credential name.

---

## Gotcha 2: Named Credentials Cannot Be Used With the Continuation Framework

**What happens:** A developer attempts to use Continuation (async Visualforce or Aura callout framework) with a Named Credential endpoint. The `callout:NCName` URL prefix is not supported by the Continuation framework. The callout either fails at setup time with an error or sends the literal string `callout:NCName/path` as the URL to the framework, which then fails to make the request.

**When it occurs:** When building Visualforce pages or Aura/LWC components that need async long-running callouts and the developer tries to use the Named Credential `callout:` prefix in the Continuation `endpoint` setter.

**How to avoid:** Use synchronous Named Credential callouts from a Queueable Apex job (which implements `Database.AllowsCallouts`) for async patterns. Alternatively, use a full HTTPS endpoint URL in the Continuation framework and handle authentication manually — but only if the Named Credential approach genuinely cannot be used for that integration. Document this limitation clearly in code comments.

---

## Gotcha 3: Remote Site Settings Exemption Does Not Apply to Managed Package Subscribers Automatically

**What happens:** A developer builds a managed package that includes Named Credentials. In their scratch org or dev org, callouts work perfectly because the Named Credential exempts the host from Remote Site Settings. After installation in a subscriber org, callouts fail with a "Unauthorized endpoint" error.

**When it occurs:** When the managed package's Apex code makes any callout using a full HTTPS URL (bypassing the `callout:` prefix), or when the Named Credential is not included in the package at all and the subscriber is expected to create it themselves.

**How to avoid:** Always use the `callout:` prefix consistently in package Apex code — never fall back to full URLs. If the Named Credential is subscriber-configurable (not shipped with the package), include documentation instructing the subscriber to create it with the correct API name. Consider providing a post-install script that validates Named Credential presence.

---

## Gotcha 4: Formula Tokens Only Resolve in Named Credential Custom Header Fields, Not in Request Body or URL Path

**What happens:** A developer places `{!$Credential.OAuthToken}` inside an Apex string used as a request body parameter or appended to the URL path. The external API receives the literal text `{!$Credential.OAuthToken}` and rejects the request, typically with an auth error. No runtime exception is thrown by the platform — the literal string is sent silently.

**When it occurs:** When the external API requires the token in the request body (e.g., a form-encoded `token=<value>` POST) or embedded in the URL as a query parameter, and the developer tries to use the formula syntax directly in Apex code.

**How to avoid:** Understand that `{!$Credential.*}` formula tokens are platform-side constructs evaluated only within Named Credential custom header field definitions in the Setup UI. They are never available to Apex code at runtime. If an API requires token injection in the body or URL, consider whether the integration can be redesigned to accept the header approach, or whether a Named Credential is the right tool for that specific endpoint.

---

## Gotcha 5: UserExternalCredential Record Existing Does Not Mean the Token Is Currently Valid

**What happens:** The `isUserAuthenticated()` check returns `true` because a `UserExternalCredential` record exists, but the subsequent callout still returns HTTP 401 because the OAuth access token has expired and the refresh token flow failed (or no refresh token was issued, as with Client Credentials flow).

**When it occurs:** In per-user OAuth flows where access tokens expire and refresh is not configured or fails. The `UserExternalCredential` record is created once when the user first authenticates and is not deleted when the token expires — its existence is a historical record of "the user has authenticated at some point," not "the user's token is currently valid."

**How to avoid:** Treat a 401 response from the external API as a signal to prompt the user to re-authenticate, regardless of the `UserExternalCredential` check result. The pre-callout `UserExternalCredential` check is a UX optimization (avoid unnecessary callouts for clearly unauthenticated users), not a guarantee of token validity. Always handle HTTP 401 responses gracefully in the callout code itself.
