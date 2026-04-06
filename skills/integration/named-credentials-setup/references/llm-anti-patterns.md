# LLM Anti-Patterns — Named Credentials Setup

Common mistakes AI coding assistants make when generating or advising on Salesforce Named Credentials and External Credentials.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Legacy Named Credentials with Enhanced Named Credentials

**What the LLM generates:** Configuration steps that mix legacy Named Credential fields (Identity Type, Authentication Protocol in one screen) with enhanced Named Credential architecture (separate Named Credential + External Credential + Principal).

**Why it happens:** Salesforce introduced enhanced Named Credentials in Winter '23 as a replacement for the legacy model. Training data contains both patterns, and LLMs merge them into an incoherent hybrid.

**Correct pattern:**

```text
Legacy Named Credentials (pre-Winter '23):
- Single configuration object with endpoint URL + auth in one record
- Identity Type: Named Principal or Per User
- Authentication Protocol: Password, OAuth 2.0, JWT, etc.
- Configured in Setup > Named Credentials (legacy page)

Enhanced Named Credentials (Winter '23+):
- Three-part architecture:
  1. Named Credential: endpoint URL + reference to External Credential
  2. External Credential: authentication protocol + principal(s)
  3. Principal: Named Principal, Per User Principal, or Anonymous
- Configured in Setup > Named Credentials (new page) + External Credentials
- Supports multiple principals per External Credential
- Required for new development

Do NOT mix legacy and enhanced configurations. Choose one model.
New development should always use enhanced Named Credentials.
```

**Detection hint:** Flag Named Credential instructions that reference both "Identity Type" (legacy) and "External Credential" (enhanced) in the same setup. Check for legacy-style metadata (`NamedCredential` with `oauthScope` attribute) when enhanced is intended.

---

## Anti-Pattern 2: Hardcoding Endpoints in Apex Instead of Using Named Credentials

**What the LLM generates:** `HttpRequest req = new HttpRequest(); req.setEndpoint('https://api.example.com/v1/data');` with credentials managed in Custom Settings or hardcoded, bypassing Named Credentials entirely.

**Why it happens:** Direct HTTP endpoint configuration is simpler and more familiar from general programming. Named Credentials add indirection that LLMs skip for brevity.

**Correct pattern:**

```apex
// WRONG — hardcoded endpoint and manual auth:
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.example.com/v1/data');
req.setHeader('Authorization', 'Bearer ' + myToken);

// CORRECT — Named Credential handles endpoint and auth:
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:My_Named_Credential/v1/data');
req.setMethod('GET');
Http http = new Http();
HttpResponse res = http.send(req);

// Benefits:
// - Endpoint URL managed in Setup, not in code
// - Authentication injected automatically (OAuth, JWT, etc.)
// - Credentials encrypted at rest, not in Apex source
// - Environment-specific (different Named Credential per sandbox)
// - Deployable via metadata
```

**Detection hint:** Flag Apex HTTP callouts that use `setEndpoint()` with a full URL instead of `callout:` prefix. Regex: `setEndpoint\s*\(\s*['"]https?://`.

---

## Anti-Pattern 3: Using Named Principal When Per User Is Required

**What the LLM generates:** "Set up the Named Credential with Named Principal authentication" for scenarios where the external system requires per-user authorization (e.g., user-specific OAuth tokens for Microsoft Graph, Google APIs).

**Why it happens:** Named Principal is simpler (one set of credentials for all users) and appears more frequently in tutorials. LLMs default to it without evaluating whether the integration requires per-user identity.

**Correct pattern:**

```text
Principal type selection:

Named Principal:
- Single credential shared by all Apex callouts
- Best for: system-to-system integrations, backend services, APIs
  that accept a service account
- All requests appear as the same external user

Per User Principal:
- Each Salesforce user has their own credential to the external system
- Best for: integrations where the external system tracks per-user
  actions (Microsoft 365, Google Workspace, Slack)
- Requires each user to authorize via OAuth flow
- User must complete the authorization before callouts work

Anonymous:
- No authentication — for public APIs
- Best for: open endpoints, health checks

Choose Per User when the external system needs to know WHICH user is acting.
```

**Detection hint:** Flag Named Principal recommendations where the external system is described as user-specific (Microsoft Graph, Google APIs, Slack). Check for missing Per User evaluation.

---

## Anti-Pattern 4: Not Deploying Named Credential Secrets Between Environments

**What the LLM generates:** "Deploy the Named Credential metadata to production" without noting that credential secrets (OAuth tokens, passwords, API keys) are NOT included in metadata deployments and must be configured manually in each environment.

**Why it happens:** Named Credential metadata (endpoint URL, authentication type, protocol) is deployable. The actual secrets are environment-specific and stripped from metadata exports. LLMs treat the deployment as complete without the post-deploy credential configuration step.

**Correct pattern:**

```text
Named Credential deployment:

What IS deployed via metadata:
- Named Credential definition (endpoint URL, label)
- External Credential definition (authentication protocol, principal type)
- Reference bindings (which permission sets can use the credential)

What is NOT deployed (must be configured post-deploy):
- OAuth client ID and client secret
- JWT signing certificate or private key
- Username and password
- OAuth access/refresh tokens

Post-deployment steps:
1. Deploy metadata via change set, SFDX, or package
2. In target org: Setup > Named Credentials > Edit
3. Enter environment-specific credentials
4. For OAuth: re-authorize the connection in the target org
5. Test the callout to verify connectivity
```

**Detection hint:** Flag deployment instructions that imply Named Credential secrets transfer between environments. Look for missing post-deployment credential configuration steps.

---

## Anti-Pattern 5: Forgetting to Assign External Credential Principal Access

**What the LLM generates:** "Create the Named Credential and External Credential, then call it from Apex" without assigning the External Credential principal to a permission set, which causes "Named credential not found or not allowed" errors.

**Why it happens:** Enhanced Named Credentials require explicit permission set assignment to control which users/contexts can use the credential. This extra security step is not present in legacy Named Credentials and is often missed.

**Correct pattern:**

```text
Enhanced Named Credential access chain:

1. Create External Credential with principal(s)
2. Create Named Credential referencing the External Credential
3. CRITICAL: Assign the principal to a Permission Set:
   - Setup > Permission Sets > [Your PS] > External Credential Principal Access
   - Enable the principal for the permission set
4. Assign the Permission Set to the running user (or integration user)

Without step 3, Apex callouts using callout:My_Named_Credential will fail
with "Named credential not found or not allowed for this user."

For Named Principal: assign to the integration user's permission set
For Per User Principal: assign to each user's permission set
```

**Detection hint:** Flag Named Credential setup instructions that do not include "External Credential Principal Access" permission set configuration. Look for missing permission assignment between credential creation and usage.
