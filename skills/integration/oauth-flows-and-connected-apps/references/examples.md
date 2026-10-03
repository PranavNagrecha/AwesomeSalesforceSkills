# Examples - Oauth Flows And Connected Apps

## Example 1: Client Credentials For Middleware

**Context:** A middleware platform polls Salesforce for order changes every five minutes.

**Problem:** The team proposes a human admin account and password because it is quick.

**Solution:** Create an external client app with the client credentials flow enabled (files in `metadata-examples.md`), bind it to a dedicated execution user with only the required permission sets, and request tokens like this:

```http
POST /services/oauth2/token HTTP/1.1
Host: MyDomainName.my.salesforce.com
Authorization: Basic <base64(client_id:client_secret)>
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

A successful response, per the Identity guide:

```json
{
  "access_token": "*******************",
  "instance_url": "https://yourInstance.salesforce.com",
  "id": "https://login.salesforce.com/id/<orgId>/<userId>",
  "token_type": "Bearer",
  "scope": "id api",
  "issued_at": "1657741493799",
  "signature": "c2lnbmF0dXJl"
}
```

There is no `refresh_token` and there never will be: when the access token stops working, post the same request again. Do not add a `scope` parameter; Salesforce does not accept scopes on the token endpoint for this flow.

**Why it works:** There is no user context requirement, the secret is the only credential, and the token represents a least-privilege execution user that audit logs can attribute.

---

## Example 2: JWT Bearer For Certificate-Based Server Access

**Context:** A security team will not store long-lived shared secrets but already runs a PKI for server certificates.

**Problem:** Client credentials depends on a consumer secret, which the policy forbids.

**Solution:** Upload the integration server's X.509 certificate (4 KB maximum) to the app, pre-authorize the integration user through a permission set, and post a signed assertion:

```http
POST /services/oauth2/token HTTP/1.1
Host: login.salesforce.com
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer&assertion=<header.claims.signature>
```

The claims set carries `iss` (the consumer key), `sub` (the integration username), `aud` (`https://login.salesforce.com`, or `https://test.salesforce.com` for sandboxes), and `exp` (keep it short; Salesforce allows a 3-minute clock-skew buffer). Sign with RS256. A repeated `jti` claim is rejected as a replay.

**Why it works:** The private key never leaves the server, rotation is a certificate swap, and the token carries the pre-authorized user's identity.

---

## Example 3: Authorization Code For A User-Facing Portal Add-On

**Context:** A third-party application lets sales reps authorize access to their Salesforce records.

**Problem:** A server-to-server flow would lose per-user consent and authority.

**Solution:** Use the web server flow with PKCE and keep scopes limited to what the user-facing app truly needs. Set `isPkceRequired` on the app (or org-wide in `OauthOidcSettings`) so a client that skips PKCE is refused.

**Why it works:** The app acts with each user's context instead of a shared service principal, and PKCE protects the authorization code in transit.

---

## Anti-Pattern: Username-Password Flow As Default

**What practitioners do:** They choose the username-password flow because it seems easier to script.

**What goes wrong:** Orgs created Summer '23 or later block it by default, external client apps do not support it, and hardening the org breaks every script that relies on it. Password storage and rotation become an operational burden.

**Correct approach:** Use client credentials (Example 1) or JWT bearer (Example 2) for system access, and the web server flow with PKCE (Example 3) for user access.
