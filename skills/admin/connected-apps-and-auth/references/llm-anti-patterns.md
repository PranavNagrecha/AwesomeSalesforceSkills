# LLM Anti-Patterns — Connected Apps and Auth

Common mistakes AI coding assistants make when generating or advising on Salesforce Connected Apps, OAuth flows, and Named/External Credentials.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Username-Password OAuth flow for production integrations

**What the LLM generates:** "Use the Username-Password OAuth flow to authenticate your integration. Pass the username, password, and security token in the request body."

**Why it happens:** The Username-Password flow is the simplest to demonstrate and appears frequently in tutorials. LLMs default to it because it requires the fewest steps. However, this flow exposes credentials in the request body, does not support MFA, and Salesforce has deprecated it for new connected apps in recent releases.

**Correct pattern:**

```
For server-to-server (machine-to-machine) integrations:
- Use the OAuth 2.0 Client Credentials flow (Spring '23+).
- Or use the JWT Bearer Token flow with a certificate.

For user-delegated access:
- Use the OAuth 2.0 Authorization Code flow (with PKCE for public clients).

The Username-Password flow is deprecated for new connected apps.
Existing implementations should be migrated.
```

**Detection hint:** If the output includes `grant_type=password` or mentions passing a username and password in the OAuth token request body, the deprecated flow is being recommended. Search for `grant_type=password` or `Username-Password flow`.

---

## Anti-Pattern 2: Hardcoding client secrets and tokens in source code

**What the LLM generates:** "Store the consumer key and consumer secret in your configuration file: `clientId = '3MVG9...'` and `clientSecret = 'ABC123...'`."

**Why it happens:** LLMs generate working examples that embed secrets directly. In production, secrets should be stored in Named Credentials, External Credentials, or a secure vault -- never in code, config files, or custom settings.

**Correct pattern:**

```
Never hardcode OAuth secrets. Use Salesforce-native secure storage:
1. Named Credential: stores the endpoint URL and auth config.
   Apex callouts reference the Named Credential by name, not raw URLs.
2. External Credential: stores the authentication principal and secrets.
   Paired with a Named Credential for the endpoint.
3. For external systems calling Salesforce: the connected app's
   consumer secret should be managed in the external system's vault,
   not in Salesforce custom settings or code.
```

**Detection hint:** If the output shows `clientSecret`, `consumer_secret`, `security_token`, or `password` as string literals in code or config, secrets are being hardcoded. Regex: `(clientSecret|consumer_secret|security_token)\s*=\s*['"]`.

---

## Anti-Pattern 3: Ignoring scope restrictions on connected apps

**What the LLM generates:** "Create a connected app and grant it full access so the integration can do everything it needs."

**Why it happens:** LLMs skip scope design for simplicity. Granting `full` or `api` scope without restrictions violates least privilege. Connected apps should request only the OAuth scopes the integration actually needs.

**Correct pattern:**

```
Configure scopes based on actual integration needs:
- api: Access to REST/SOAP APIs (most integrations need this).
- refresh_token: Long-lived access via refresh tokens.
- chatter_api: Only if the integration posts to Chatter.
- custom_permissions: Only if checking custom permissions.
- Do NOT grant "full" scope unless every API surface is required.

Also configure Connected App policies:
- Admin pre-authorized users: assign via Permission Set, not "All users."
- IP Relaxation: "Enforce IP restrictions" for production.
- Refresh token policy: set expiration (e.g., 90 days, not "unlimited").
```

**Detection hint:** If the output mentions `full access` or omits scope configuration entirely, the connected app is over-permissioned. Search for `full` scope or absence of `OAuth Scopes` configuration.

---

## Anti-Pattern 4: Confusing Named Credentials (legacy) with External Credentials (new model)

**What the LLM generates:** "Create a Named Credential and enter the username and password for the external system."

**Why it happens:** LLMs reference the legacy Named Credential model (pre-Spring '23) where auth config was directly on the Named Credential. The new model separates the endpoint (Named Credential) from the authentication principal (External Credential), giving better governance and reuse.

**Correct pattern:**

```
New Named Credential model (Spring '23+):
1. External Credential: defines the auth protocol (OAuth, Basic Auth, etc.)
   and holds the authentication principal (client ID, secret, certificate).
2. Named Credential: references the External Credential and defines
   the endpoint URL. Multiple Named Credentials can share one External Credential.
3. Permission Set Mapping: controls which users/integrations can use
   which External Credential principal.

Legacy Named Credentials (pre-Spring '23):
- Auth config is directly on the Named Credential.
- Still functional but not recommended for new implementations.
```

**Detection hint:** If the output describes entering a username/password directly on a Named Credential without mentioning External Credentials, it is using the legacy model. Search for `External Credential` in the output.

---

## Anti-Pattern 5: Omitting IP restrictions and token expiration on connected apps

**What the LLM generates:** "Create the connected app and enable OAuth. The integration is ready."

**Why it happens:** LLMs focus on getting the integration working and skip hardening. A connected app without IP restrictions accepts tokens from any network. A connected app with no refresh token expiration allows indefinite access even if credentials are compromised.

**Correct pattern:**

```
Connected app hardening checklist:
1. IP Relaxation: set to "Enforce IP restrictions" for production.
   (Relaxing IP restrictions is acceptable in sandboxes for testing.)
2. Refresh Token Policy: set a finite expiration (e.g., "Expire after 90 days"
   or "Expire if not used for 7 days").
3. Session Policy: set timeout values appropriate for the integration.
4. Permitted Users: "Admin approved users are pre-authorized" →
   assign access via a Permission Set, not "All users may self-authorize."
5. Certificate rotation: if using JWT Bearer, document the certificate
   expiration date and rotation process.
```

**Detection hint:** If the output creates a connected app without configuring IP restrictions, token expiration, or permitted user policies, the app is unhardened. Search for `IP Relaxation`, `Refresh Token`, or `Permitted Users`.
