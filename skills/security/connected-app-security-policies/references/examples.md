# Examples — Connected App Security Policies

## Example 1: Enforcing IP Restrictions on a Server-to-Server Integration

**Context:** A MuleSoft integration uses the JWT Bearer flow to query Salesforce from a fixed-IP data center. The Connected App was initially created with IP relaxation set to "Relax IP Restrictions" for testing and was never tightened before going to production.

**Problem:** A stolen access token can be replayed from any network because IP relaxation is disabled. A routine security audit flags the Connected App as high risk.

**Solution:**

```xml
<!-- ConnectedApp metadata XML — connectedApps/MuleSoftIntegration.connectedApp -->
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>MuleSoft Integration</label>
    <contactEmail>admin@example.com</contactEmail>
    <oauthConfig>
        <callbackUrl>https://login.salesforce.com/services/oauth2/success</callbackUrl>
        <consumerKey>3MVG9...</consumerKey>
        <scopes>Api</scopes>
        <scopes>RefreshToken</scopes>
    </oauthConfig>
    <oauthPolicy>
        <!-- Changed from relaxIpRanges to enforceIpRanges -->
        <ipRelaxation>enforceIpRanges</ipRelaxation>
        <refreshTokenPolicy>zero</refreshTokenPolicy>
    </oauthPolicy>
</ConnectedApp>
```

Then add the MuleSoft egress IP range to the integration user's profile under Login IP Ranges, or to the Connected App's IP ranges via Setup > App Manager > [App] > Edit > IP Ranges.

**Why it works:** `enforceIpRanges` causes Salesforce to validate every token request against the user's trusted IP ranges. A stolen token replayed from an unauthorized IP is rejected with `invalid_grant` before it can read any data.

---

## Example 2: Configuring PKCE for a Lightning Web Component Open Source SPA

**Context:** A developer builds a customer portal as a React SPA that authenticates end-users via Salesforce using the Authorization Code flow. The SPA runs in the browser and cannot safely store a client secret.

**Problem:** The developer enables "Require Secret for Web Server Flow" by default and also checks "Require PKCE." At runtime the token endpoint returns `invalid_client_credentials` and the PKCE `code_verifier` is silently ignored.

**Solution:**

In Setup > App Manager > [Your Connected App] > Edit > OAuth Settings:

1. Check "Enable Proof Key for Code Exchange (PKCE) Extension for Supported Authorization Flows."
2. **Uncheck** "Require Secret for Web Server Flow."
3. Save.

In the SPA authorization flow:

```javascript
// Generate PKCE pair (browser-side, no secrets stored)
async function generatePKCE() {
  const verifier = generateRandomString(96); // URL-safe base64, 43-128 chars
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  const challenge = base64UrlEncode(digest);
  return { verifier, challenge };
}

// Authorization URL — no client_secret included
const authUrl = `${SF_AUTH_URL}/services/oauth2/authorize?` +
  `response_type=code` +
  `&client_id=${CLIENT_ID}` +
  `&redirect_uri=${encodeURIComponent(REDIRECT_URI)}` +
  `&code_challenge=${challenge}` +
  `&code_challenge_method=S256`;

// Token exchange — submit verifier, not client_secret
const tokenResponse = await fetch(`${SF_AUTH_URL}/services/oauth2/token`, {
  method: 'POST',
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: authorizationCode,
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    code_verifier: verifier   // replaces client_secret
  })
});
```

**Why it works:** PKCE binds the authorization code to the session that requested it. Even if a code is intercepted via the redirect URI or browser history, it cannot be exchanged for a token without the `code_verifier` that was never transmitted in the authorization request.

---

## Anti-Pattern: Leaving IP Relaxation at "Relax IP Restrictions" After Testing

**What practitioners do:** Set IP relaxation to "Relax IP Restrictions" during development to avoid debugging IP-related errors, then deploy to production without reverting.

**What goes wrong:** Any compromised access token can be replayed from any network. This is especially damaging for long-lived refresh tokens used in server-to-server integrations: a leaked token grants unlimited API access until manually revoked.

**Correct approach:** Use "Relax IP Restrictions" only in developer sandboxes. Production Connected Apps should use `enforceIpRanges` for server-to-server flows and `relaxIpRangesWithSecondFactor` for human-facing flows. Add a deployment checklist item that verifies IP relaxation before promoting to production.
