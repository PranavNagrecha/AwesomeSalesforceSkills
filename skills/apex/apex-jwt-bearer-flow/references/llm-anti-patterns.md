# LLM Anti-Patterns — Apex JWT Bearer Flow

Common mistakes AI coding assistants make when generating Apex JWT Bearer Flow code.

---

## Anti-Pattern 1: Hand-rolled HMAC signing instead of `Auth.JWS`

**What the LLM generates.**

```apex
String header = '{"alg":"RS256","typ":"JWT"}';
Blob sig = Crypto.signWithCertificate('RSA-SHA256', toSign, 'AcmeJwtCert');
String jwt = b64u(header) + '.' + b64u(claims) + '.' + b64u(sig.toString());
```

**Correct pattern.** Use `Auth.JWT` and `Auth.JWS` — they handle
base64url encoding, JCS-style canonicalization, and the
`alg`/`typ`/`kid` header correctly. Hand-rolled signing is the
single largest source of `invalid_assertion` errors in production.

```apex
Auth.JWT jwt = new Auth.JWT();
jwt.setIss(...); jwt.setSub(...); jwt.setAud(...); jwt.setValidityLength(180);
String compact = new Auth.JWS(jwt, 'AcmeJwtCert').getCompactSerialization();
```

**Detection hint.** Any direct `Crypto.signWithCertificate` call
combined with `EncodingUtil.base64Encode` and `+ '.' +` string
concatenation is hand-rolling JWT.

---

## Anti-Pattern 2: Putting org My Domain in `aud`

**What the LLM generates.**

```apex
jwt.setAud('https://acme-dev.my.salesforce.com');
```

**Correct pattern.**

```apex
jwt.setAud('https://login.salesforce.com');     // production
jwt.setAud('https://test.salesforce.com');      // sandbox
```

The audience claim must match the *token endpoint server*, not the
caller's My Domain. This is the most common single-character
configuration error.

**Detection hint.** Any `setAud(...)` containing `.my.salesforce.com`
or anything other than `login.salesforce.com` /
`test.salesforce.com` for Salesforce-to-Salesforce JWT.

---

## Anti-Pattern 3: Re-minting on every callout (no caching)

**What the LLM generates.**

```apex
String token = JwtTokenExchanger.exchange(URL, mintAssertion(...)).accessToken;
HttpRequest req = new HttpRequest();
req.setHeader('Authorization', 'Bearer ' + token);
```

**Correct pattern.** Token endpoint is rate-limited per Connected
App. Cache the access token in `Cache.Org` (TTL ≤ token lifetime)
or transaction-scope static; only re-exchange on near-expiry or 401.

**Detection hint.** Any code path where `mintAssertion` /
`Auth.JWS` / a token endpoint POST appears in the same method as
the resource callout, with no surrounding cache check, is
re-minting.

---

## Anti-Pattern 4: Hardcoding the consumer key and username

**What the LLM generates.**

```apex
String iss = '3MVG9XXXXXXXXX_consumer_key_XXXXXXXXX';
String sub = 'integration@acme.com.dev';
```

**Correct pattern.** Read from Custom Metadata (`ConnectedAppConfig__mdt`)
or a Named Credential. Hardcoded values force a code change to
move the integration to a new Connected App or to rotate the
consumer key after a leak.

**Detection hint.** Any `setIss('3MVG...')` or `setSub('user@...')`
with a literal string in production code path.

---

## Anti-Pattern 5: Using `grant_type=password` "as a fallback"

**What the LLM generates.**

```apex
if (jwtFailed) {
    body = 'grant_type=password&username=' + u + '&password=' + p + secToken;
}
```

**Correct pattern.** There is no fallback. JWT Bearer's whole
point is removing the password. If JWT fails, fix the configuration
(certificate, pre-auth, aud, exp) — do not fall back to
`grant_type=password`. The username-password OAuth flow is
deprecated and disabled by default in new orgs.

**Detection hint.** Any code containing `grant_type=password`
alongside JWT logic is regressing the security posture.

---

## Anti-Pattern 6: Logging the full assertion at INFO

**What the LLM generates.**

```apex
System.debug(LoggingLevel.INFO, 'Sending JWT: ' + assertion);
```

**Correct pattern.** Log only the `iss`, `sub`, `aud`, and `exp`
claims — never the signature or the entire compact form, which is
a bearer credential for the next 3 minutes. If logging is needed
for diagnosis, redact the third segment (signature) before logging.

**Detection hint.** Any `System.debug` or `Logger.debug` whose
argument concatenates the result of `getCompactSerialization()`.

---

## Anti-Pattern 7: Treating any non-200 as a transient retry

**What the LLM generates.**

```apex
for (Integer i = 0; i < 5; i++) {
    res = http.send(req);
    if (res.getStatusCode() == 200) break;
}
```

**Correct pattern.** 4xx errors from the token endpoint are
configuration errors, not transient. Retrying `invalid_grant` 5
times wastes governor limits and obscures the real failure. Retry
only on 5xx and 429; surface 4xx immediately with `JwtErrorTranslator`.

**Detection hint.** Any retry loop around the token endpoint that
does not branch on the HTTP status code class.
