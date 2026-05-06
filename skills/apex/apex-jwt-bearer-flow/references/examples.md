# Examples — Apex JWT Bearer Flow

## Example 1: JWT Bearer via Named Credential (preferred)

When the target supports the standard JWT Bearer profile and
Salesforce can manage signing, this is one declarative step. No
Apex callout boilerplate — `callout:` does the work.

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Acme_API/v1/orders');
req.setMethod('GET');
HttpResponse res = new Http().send(req);
```

The Named Credential (Setup → Named Credentials, External Credential
type "JWT Bearer") holds the consumer key, certificate label, scope,
and `aud`. Token caching, refresh on 401, and assertion lifecycle
are platform-managed.

---

## Example 2: Hand-rolled assertion with `Auth.JWT` and `Auth.JWS`

When you need a non-standard claim or the target IdP isn't a Named
Credential identity provider:

```apex
public class JwtBearerClient {
    private static final Integer EXP_SECONDS = 180; // 3 minutes

    public static String mintAssertion(
        String issuer, String subject, String audience, String certLabel
    ) {
        Auth.JWT jwt = new Auth.JWT();
        jwt.setIss(issuer);          // Connected App consumer key
        jwt.setSub(subject);         // pre-authorized username
        jwt.setAud(audience);        // e.g. https://login.salesforce.com
        jwt.setValidityLength(EXP_SECONDS);

        Auth.JWS jws = new Auth.JWS(jwt, certLabel);
        return jws.getCompactSerialization();
    }
}
```

`certLabel` is the label from Setup → Certificate and Key Management
(the same .crt whose public half is uploaded to the Connected App).
`Auth.JWS` signs with the private key inside Salesforce — the key
material never leaves the platform.

---

## Example 3: Token exchange POST

```apex
public class JwtTokenExchanger {
    public class TokenResult {
        public String accessToken;
        public String instanceUrl;
        public String error;
        public String errorDescription;
    }

    public static TokenResult exchange(String tokenUrl, String assertion) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint(tokenUrl);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/x-www-form-urlencoded');
        req.setBody(
            'grant_type=' + EncodingUtil.urlEncode(
                'urn:ietf:params:oauth:grant-type:jwt-bearer', 'UTF-8'
            ) +
            '&assertion=' + EncodingUtil.urlEncode(assertion, 'UTF-8')
        );

        HttpResponse res = new Http().send(req);
        Map<String, Object> parsed =
            (Map<String, Object>) JSON.deserializeUntyped(res.getBody());

        TokenResult r = new TokenResult();
        if (res.getStatusCode() == 200) {
            r.accessToken = (String) parsed.get('access_token');
            r.instanceUrl = (String) parsed.get('instance_url');
        } else {
            r.error = (String) parsed.get('error');
            r.errorDescription = (String) parsed.get('error_description');
        }
        return r;
    }
}
```

Note the URL-encoded `grant_type` — the colons in the URN matter.

---

## Example 4: Cached token with expiry-aware refresh

The token endpoint is rate-limited per Connected App. Cache.

```apex
public class CachedJwtToken {
    private static String cachedToken;
    private static Long cachedExpiryEpochMs;

    public static String getAccessToken() {
        Long nowMs = DateTime.now().getTime();
        if (cachedToken != null && cachedExpiryEpochMs - nowMs > 30_000) {
            return cachedToken;
        }
        String assertion = JwtBearerClient.mintAssertion(
            ConnectedAppConfig__mdt.getInstance('AcmeOrg').ConsumerKey__c,
            ConnectedAppConfig__mdt.getInstance('AcmeOrg').IntegrationUser__c,
            'https://login.salesforce.com',
            'AcmeJwtCert'
        );
        JwtTokenExchanger.TokenResult r = JwtTokenExchanger.exchange(
            'https://login.salesforce.com/services/oauth2/token', assertion
        );
        if (r.error != null) {
            throw new CalloutException(
                'JWT exchange failed: ' + r.error + ' — ' + r.errorDescription
            );
        }
        cachedToken = r.accessToken;
        cachedExpiryEpochMs = nowMs + (2 * 60 * 60 * 1000);
        return cachedToken;
    }
}
```

Static variables are scoped to the transaction in Apex; for
cross-transaction caching, use `Cache.Org` (Platform Cache) with a
TTL ≤ token lifetime.

---

## Example 5: Mapping `error` strings to actionable messages

```apex
public class JwtErrorTranslator {
    public static String explain(String error, String description) {
        if (error == 'invalid_grant') {
            if (String.isNotBlank(description) &&
                description.containsIgnoreCase('user hasn')) {
                return 'Pre-authorize the integration user on the ' +
                       'Connected App (Profiles or Permission Sets).';
            }
            if (String.isNotBlank(description) &&
                description.containsIgnoreCase('audience')) {
                return 'aud claim does not match the token endpoint host.';
            }
            return 'Check exp (must be < 5 min in future), iss (consumer ' +
                   'key), sub (username), and certificate match.';
        }
        if (error == 'invalid_client_id') {
            return 'iss does not resolve to a Connected App. Check ' +
                   'consumer key and that the app is installed.';
        }
        return 'Unmapped error: ' + error + ' — ' + description;
    }
}
```

The platform's `error_description` is opaque on purpose; this
translation table is what saves a 2-hour debug session.
