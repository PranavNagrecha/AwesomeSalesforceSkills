---
name: apex-jwt-bearer-flow
description: "OAuth 2.0 JWT Bearer Token Flow for server-to-server authentication from Apex — Connected App with certificate, Auth.JWT/Auth.JWS to mint signed assertions, token endpoint exchange, and the failure modes (clock skew, certificate not found, user not pre-authorized). NOT for user-context OAuth (use named-credentials-oauth-user-flow) or external client → Salesforce JWT (that is the inbound flow, configured in Connected App not Apex)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "apex jwt bearer flow server to server"
  - "salesforce to external system without user password"
  - "auth.jwt auth.jws sign assertion apex"
  - "connected app jwt certificate keystore"
  - "outbound oauth without storing password"
  - "named credential jwt bearer external service"
  - "user hasn't approved this consumer error"
tags:
  - oauth
  - jwt
  - authentication
  - connected-app
  - integration
inputs:
  - "Target system's token endpoint URL"
  - "Issuer (consumer key / client_id) and subject (username) the JWT must carry"
  - "Certificate / private key location: Salesforce certificate label OR external JWKS"
outputs:
  - "Apex helper class that mints a signed JWT and exchanges it for an access token"
  - "Connected App / Named Credential configuration checklist"
  - "Error-handling pattern for 400/401 responses from the token endpoint"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# Apex JWT Bearer Flow

The OAuth 2.0 JWT Bearer Token Flow lets server-side code obtain an
access token without a stored password and without an interactive
login. The client presents a short-lived JSON Web Token signed with
a private key; the authorization server (Salesforce, or an external
IdP) verifies the signature against a registered public key and
returns an access token.

In Salesforce Apex this comes up in two shapes. The outbound shape
is the one this skill covers: Apex calling a non-Salesforce system
(another Salesforce org, a Heroku service, an internal API, a
SaaS that supports JWT bearer) and needing an access token. The
two correct ways to implement it are (a) a Named Credential with
"JWT Bearer" auth — Salesforce manages the assertion and token
exchange for you — and (b) Apex that builds the assertion with
`Auth.JWT` and `Auth.JWS`, posts it to `/oauth2/token`, and parses
the response.

The inbound shape — an external system getting a token *into*
Salesforce via JWT — is configured entirely on the Connected App
("Use digital signatures" + uploaded certificate, "Pre-authorized"
profile/permset). No Apex is needed. That is out of scope for this
skill.

The mistakes are predictable. The JWT `exp` claim must be inside
the next ~5 minutes (Salesforce rejects assertions older than 5
minutes); `aud` must be the *server's* login URL (not your org's);
`sub` must be a username the Connected App has been pre-authorized
to issue tokens for; and the certificate used to sign must match
the public key uploaded to the Connected App. Any one of these
mismatches returns the same opaque `invalid_grant` error.

## Recommended Workflow

1. **Prefer Named Credentials over hand-rolled Apex.** Setup → Named
   Credentials → New, choose "JWT Bearer" identity type. Salesforce
   manages signing, refresh, and token caching. Reach for Apex
   `Auth.JWT` only when the target system requires a non-standard
   claim or a non-Salesforce IdP that Named Credentials does not
   support.
2. **Generate or import the certificate in Setup → Certificate and
   Key Management.** Use a self-signed certificate for sandboxes;
   in production use a CA-issued certificate if the target system
   requires it. Note the label — you reference it from `Auth.JWS`.
3. **Configure the Connected App on the target side.** Upload the
   public key (the .crt exported from Setup), enable "Use digital
   signatures", add the API scope you need, and pre-authorize the
   user(s) the `sub` claim will identify (Profiles → Manage Profiles
   or Permission Sets).
4. **Write the assertion builder.** Use `Auth.JWT` for the claims,
   `Auth.JWS` to sign with the certificate label. Set `iss`
   (consumer key), `sub` (username), `aud` (target login URL exactly
   — `https://login.salesforce.com` or `https://test.salesforce.com`
   for Salesforce-to-Salesforce), `exp` to now + 3 minutes.
5. **POST the assertion to the token endpoint.** Use form-encoded
   body with `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer`
   and `assertion=<jwt>`. Parse the response — `access_token` on
   success, `{error, error_description}` on failure.
6. **Handle the failure responses, not just `invalid_grant`.**
   `user hasn't approved this consumer` means pre-authorization is
   missing; `invalid_assertion` usually means clock skew or wrong
   `aud`; `invalid_client_id` means the `iss` doesn't match a
   Connected App.
7. **Cache the access token until ~30s before expiry.** The token
   endpoint is rate-limited (per-org, per-Connected-App). Re-exchange
   only on expiry or on a 401 from the resource server.

## When To Reach For This Skill

Use it when a backend Apex job (Schedulable, Queueable, callout
from a trigger) needs to call an external system as a fixed service
account, and the target supports JWT bearer. Use it for org-to-org
integration where one org calls the other unattended. Use it when
storing a password (even encrypted) in Custom Metadata is
unacceptable — JWT bearer has no password.

Do not use it for user-context callouts. If the calling user's
permissions matter at the destination, use Named Credentials with
"Per User" auth and the standard OAuth web-server flow. JWT bearer
is impersonation by a service principal; it bypasses the user's
interactive login.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Inbound JWT (external system → Salesforce) | `security/connected-app-jwt-inbound` (Connected App config; no Apex) |
| OAuth 2.0 user-agent / web-server flow | `apex/named-credentials-oauth-user-flow` |
| JWKS rotation and discovery endpoints | `integration/jwt-key-rotation` |
| MuleSoft / external orchestration of JWT | `integration/mulesoft-jwt-passthrough` |
