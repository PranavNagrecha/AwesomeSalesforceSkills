# Examples — Named Credentials Setup

## Example 1: Org-Wide REST API Integration Using Client Credentials OAuth

**Context:** A Salesforce org needs to call a third-party REST API (e.g., a logistics provider) from Apex batch jobs. The external system uses OAuth 2.0 Client Credentials grant. All callouts should use one shared service account — no per-user delegation needed.

**Problem:** Without a Named Credential, the team hardcodes the token endpoint URL and client secret in a Custom Setting readable by any admin with SOQL access. Credential rotation requires a code or configuration change. The callout is also not covered by Salesforce's remote site whitelist enforcement.

**Solution:**

Step 1 — Create the External Credential (Setup > Named Credentials > External Credentials > New):

```
Label:              Logistics API Auth
Developer Name:     Logistics_API_Auth
Protocol:           OAuth 2.0
Flow Type:          Client Credentials
Client ID:          <client-id from external system>
Client Secret:      <client-secret from external system>
Token Endpoint URL: https://auth.logistics-provider.com/oauth/token
Scope:              api.read api.write
```

Add a Named Principal:

```
Principal Name:  OrgWide
Sequence Number: 1
```

Assign the Permission Set that integration users run under to this principal.

Step 2 — Create the Named Credential (Setup > Named Credentials > Named Credentials > New):

```
Label:               Logistics API
Developer Name:      Logistics_API
URL:                 https://api.logistics-provider.com/v2
External Credential: Logistics API Auth
```

Step 3 — Apex callout:

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Logistics_API/shipments');
req.setMethod('GET');
Http http = new Http();
HttpResponse res = http.send(req);
```

Salesforce automatically appends the Bearer token obtained via Client Credentials before sending the request. Token refresh is handled transparently.

**Why it works:** The External Credential's Named Principal holds one org-wide token. The Permission Set assignment controls which running user context can trigger the callout. Rotating the client secret requires only a Setup UI update — no code or metadata deployment.

---

## Example 2: Per-User OAuth 2.0 Integration (Authorization Code Flow)

**Context:** A sales team uses a CRM enrichment service where each salesperson has their own account. The enrichment API returns data scoped to the authenticated user's subscription tier. Salesforce must call the API as the individual Salesforce user, not as a shared service account.

**Problem:** Using a Named Principal (shared credential) would return data from the service account's subscription, not the individual user's. Data leakage risk: user A could see user B's enrichment data if the external service scopes by authenticated identity.

**Solution:**

Step 1 — Register Salesforce as an OAuth client in the external enrichment system. Set the redirect URI to:

```
https://<yourMyDomain>.my.salesforce.com/services/authcallback/Enrichment_Service_Auth
```

The developer name of the External Credential must match exactly (case-sensitive).

Step 2 — Create the External Credential:

```
Label:              Enrichment Service Auth
Developer Name:     Enrichment_Service_Auth
Protocol:           OAuth 2.0
Flow Type:          Authorization Code
Client ID:          <client-id>
Client Secret:      <client-secret>
Authorization Endpoint URL: https://auth.enrichment.com/authorize
Token Endpoint URL:         https://auth.enrichment.com/token
Scope:              openid profile enrichment:read offline_access
```

Add a Per User principal:

```
Principal Name:  PerUser
Sequence Number: 1
```

Assign the Permission Set that the sales team holds.

Step 3 — Each salesperson authorizes the connection:

```
User Settings > Authentication Settings for External Systems > New
External Credential: Enrichment Service Auth
```

Salesforce redirects them to the external IdP login. After consent, the token is stored against their user record.

Step 4 — Named Credential and Apex callout are identical in structure to Example 1. The token Salesforce injects is the per-user token for the currently running user context.

**Why it works:** The Per User principal stores a separate token per Salesforce user. `offline_access` scope ensures Salesforce obtains a refresh token so users do not have to re-authorize on every session. Users without a stored authorization receive a callout exception, which can be caught in Apex and surfaced as a user-friendly "Please authorize your account" message.

---

## Anti-Pattern: Embedding Credentials in Custom Settings or Custom Metadata

**What practitioners do:** Store API keys, client secrets, or bearer tokens in Custom Settings or Custom Metadata fields to avoid the Setup UI overhead of Named Credentials. Use Apex to read the value and pass it in an Authorization header manually.

**What goes wrong:**

- Custom Settings (Hierarchy type) are readable by all users with access to the object. A user with the "Customize Application" permission or even just Object permissions can query the value via SOQL or the Data Loader.
- Custom Metadata values are visible in metadata packages and version control, making secrets leak into source repositories.
- Token rotation requires a metadata deployment or a Setup record update that is itself auditable but not protected by the same vault encryption as Named Credentials.
- Remote Site Settings still require a separate entry; Named Credentials subsume the allowed-endpoint configuration in one record.

**Correct approach:** Use Named Credentials + External Credentials for all outbound auth. The Salesforce credential vault is encrypted at rest and inaccessible via SOQL or API. Rotation is a Setup UI operation with no deployment required.
