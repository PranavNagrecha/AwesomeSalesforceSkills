# Gotchas — Apex JWT Bearer Flow

Non-obvious Salesforce platform behaviors that cause real production problems with JWT Bearer.

---

## Gotcha 1: `aud` is the *server's* login URL, not the org's My Domain

The audience claim must be the literal token endpoint host:
`https://login.salesforce.com` (production) or
`https://test.salesforce.com` (sandbox). It is *not* your org's My
Domain URL, even though `My Domain` is where you log in
interactively. Putting `https://acme.my.salesforce.com` in `aud`
yields `invalid_grant` with `audience invalid`.

---

## Gotcha 2: `exp` must be ≤ 5 minutes in the future

Salesforce rejects assertions whose `exp` is more than ~5 minutes
ahead of the server clock, and rejects already-expired assertions.
`Auth.JWT.setValidityLength(seconds)` defaults to a safe value but
lets callers exceed 300; staying around 180 seconds (3 minutes) is
the recommended practice and survives normal clock skew.

---

## Gotcha 3: Pre-authorization is per-Connected-App, not per-user

A user with the same username in two orgs will not authenticate
unless the Connected App in the *target* org has been profile-
or permset-pre-authorized for that user. The error
`user hasn't approved this consumer` always means missing
pre-authorization (Connected App → Manage → Profiles / Permission
Sets), not a missing user.

---

## Gotcha 4: Self-signed certs work for sandboxes; some IdPs require CA-signed

Salesforce's own token endpoint accepts self-signed certificates
generated in Setup. External IdPs (Okta, Azure AD, Auth0)
sometimes require a CA-issued certificate or a JWKS-discoverable
public key. Check the target's docs before generating.

---

## Gotcha 5: `Auth.JWS` requires the certificate label, not the `Id`

```apex
new Auth.JWS(jwt, 'AcmeJwtCert');         // label — correct
new Auth.JWS(jwt, '0XX5g00000xxxxxxxxx'); // Id — runtime error
```

The label is the human-readable name from Setup → Certificate and
Key Management. It is also what users select when configuring a
Connected App for digital signatures.

---

## Gotcha 6: Token endpoint is rate-limited per Connected App

Repeatedly minting and exchanging on every callout (no caching) can
hit the per-Connected-App rate limit and produce intermittent 503s
or `rate_limit_exceeded` errors. Always cache the access token in
`Cache.Org` and only re-exchange near expiry or after a 401.

---

## Gotcha 7: `error_description` is intentionally opaque

The Salesforce token endpoint folds many distinct failures into the
generic `invalid_grant` with vague descriptions. The differential
diagnosis (clock, aud, sub, iss, certificate, pre-authorization)
must be done from the call site. Logging the *full* response body
(redacted assertion) at WARN is the only practical debugging aid.

---

## Gotcha 8: `Cache.Org` keys cannot include the consumer key directly

Platform Cache keys must match `[A-Za-z0-9]{1,50}`. Consumer keys
have characters that are not allowed. Hash or base64-encode the key
fragment before using it as a cache key.

---

## Gotcha 9: Inactive integration user breaks JWT silently

If the user named in `sub` is deactivated, the token endpoint
returns `invalid_grant` with no specific indication that the user
is inactive. Frequent silent failures of a previously-working
integration are usually a deactivated integration user.
