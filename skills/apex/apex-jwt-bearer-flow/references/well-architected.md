# Well-Architected Notes — Apex JWT Bearer Flow

## Relevant Pillars

- **Security** — JWT Bearer is the modern, password-free shape of
  server-to-server auth on Salesforce. The private key never leaves
  the platform (`Auth.JWS` signs in-process with a Setup-managed
  certificate), the assertion is short-lived (≤ 5 minutes), and
  pre-authorization on the Connected App scopes the integration
  user explicitly. Compared to the deprecated
  `grant_type=password` flow, there is no shared secret to rotate
  and no possibility of a leaked password.
- **Reliability** — Cached access tokens with expiry-aware
  refresh, plus differential error handling (`invalid_grant` vs
  `invalid_client_id` vs 5xx), keep the integration stable across
  certificate rotation, password resets in the source system, and
  user-deactivation events that would silently break a username-
  password integration.

## Architectural Tradeoffs

The main tradeoff is **declarative simplicity vs custom claims**.
Named Credentials with JWT Bearer auth give you the entire flow
(signing, exchange, caching, refresh) for free, but they only support
the standard OAuth 2.0 JWT Bearer profile. If the target IdP requires
custom claims (`scope` formatted as a space-separated array, an `act`
claim, a `cnf` thumbprint), you must hand-roll with `Auth.JWT` and
`Auth.JWS` and pay the maintenance cost.

Specifically:

- **Salesforce → Salesforce**: always Named Credential. The platform
  knows both sides of the contract.
- **Salesforce → standard SaaS supporting JWT Bearer**: Named
  Credential first; fall back to Apex only if a custom claim is
  required.
- **Salesforce → bespoke internal API**: Apex with `Auth.JWT` /
  `Auth.JWS` is justified.

## Anti-Patterns

1. **Hand-rolled JWT signing.** Concatenating base64url-encoded
   header + claims and calling `Crypto.signWithCertificate` is the
   largest source of `invalid_assertion` errors. `Auth.JWS` handles
   the canonical forms.
2. **Re-minting on every callout.** The token endpoint is rate-
   limited; cache the access token in `Cache.Org` and refresh near
   expiry only.
3. **`grant_type=password` fallback.** JWT Bearer's value
   proposition is the absence of a password. Falling back to
   password defeats the security model.

## Official Sources Used

- OAuth 2.0 JWT Bearer Token Flow — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm
- `Auth.JWT` Class (Apex Reference Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Auth_JWT.htm
- `Auth.JWS` Class (Apex Reference Guide) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Auth_JWS.htm
- Named Credentials with JWT Bearer (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Configure a Connected App for the JWT Bearer Flow — https://help.salesforce.com/s/articleView?id=sf.connected_app_create_api_integration.htm
- RFC 7523: JSON Web Token (JWT) Profile for OAuth 2.0 — https://datatracker.ietf.org/doc/html/rfc7523
