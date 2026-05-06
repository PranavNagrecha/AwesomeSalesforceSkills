---
name: sso-saml-troubleshooting
description: "Diagnosing broken SAML SSO into Salesforce — IdP-initiated vs SP-initiated flows, signing-certificate validity / expiry, NameID format mismatches, RelayState handling, audience / entityId / issuer mismatches, clock skew, the SAML Assertion Validator in Setup, the Login History debug log, and the My Domain prerequisite for SSO. Covers the standard diagnostic loop: read the SAML response, identify which check failed, fix at the IdP or SP. NOT for OAuth / OpenID Connect SSO (see security/oauth-openid-troubleshooting), NOT for setting up SSO from scratch (see security/sso-saml-setup)."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "saml sso not working salesforce error login"
  - "saml assertion validator setup login history"
  - "nameid format mismatch idp salesforce"
  - "saml signing certificate expired entity id"
  - "idp initiated vs sp initiated saml relay state"
  - "saml clock skew not before not after"
  - "my domain saml sso prerequisite"
tags:
  - saml
  - sso
  - troubleshooting
  - idp
  - my-domain
inputs:
  - "Symptom (login error message, redirect loop, success-but-no-access)"
  - "Whether IdP-initiated or SP-initiated flow is in use"
  - "Sample SAML Response captured at the browser (encoded or decoded)"
outputs:
  - "Identified failing check (audience / signature / NameID / clock)"
  - "Specific configuration fix on the IdP or SP side"
  - "Validation steps using SAML Assertion Validator and Login History"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-05
---

# SAML SSO Troubleshooting

SAML SSO into Salesforce fails for a small number of well-known
reasons. The hard part is identifying *which* of the well-known
reasons applies to the specific failure. This skill walks the
diagnostic loop: capture the SAML response, validate it against
Salesforce's expectations, fix at the IdP or SP, retry.

## Required prerequisites

- **My Domain is enabled** and deployed for SSO use. Salesforce
  routes SAML through the My Domain hostname; without it, SSO
  cannot work.
- **Salesforce SAML SSO Settings exist** for the relevant IdP
  (Setup -> Single Sign-On Settings).
- **The IdP knows Salesforce as a Service Provider** with the
  Salesforce-side Entity Id (typically `https://saml.salesforce.com`
  for SP-initiated, or the My Domain URL).

## The diagnostic loop

```
Symptom -> Capture SAML Response -> Identify failing check -> Fix -> Retry
```

The SAML Assertion Validator (Setup -> Single Sign-On Settings ->
SAML Assertion Validator) accepts a base64-encoded SAML response and
runs Salesforce's exact checks against it, returning a per-check
pass / fail. This is the fastest way to narrow the problem.

The Login History (Setup -> Login History) records every login
attempt, including SAML failures, with a Status field that names
the failing check (e.g. "Signature Failure", "Audience Mismatch",
"Assertion Expired").

## The well-known failure modes

| Symptom / Error | Cause | Fix |
|---|---|---|
| "Signature Failure" | IdP's signing cert in Salesforce SSO Settings does not match the cert that signed the response | Re-upload the IdP's current public signing cert into the SSO Settings |
| "Audience Mismatch" | `<Audience>` element in the assertion does not match Salesforce's expected EntityId | Set IdP audience to `https://saml.salesforce.com` (or My Domain URL, depending on flow) |
| "Issuer Mismatch" | `Issuer` in the response does not match the Issuer configured in SSO Settings | Update SSO Settings Issuer to match the IdP's exact issuer string |
| "Assertion Expired" / "NotOnOrAfter in past" | Clock skew between IdP and Salesforce, or assertion expiry too short | Fix IdP clock; if drift is unavoidable, increase IdP's NotOnOrAfter window |
| "Assertion Not Yet Valid" / "NotBefore in future" | IdP clock ahead of Salesforce | Fix IdP clock |
| "User does not exist" | NameID does not match a Salesforce user (by Federation ID, Username, or Email — depending on SSO Settings) | Either provision the user in Salesforce or change SSO Settings to match the IdP's NameID format |
| "Federation Id is not unique" | Two users share the same Federation Id | Deduplicate Federation Ids on the user record |
| Login redirects but lands on user's home with a "session expired" feel | RelayState handling broken | Inspect the `RelayState` parameter; Salesforce uses it to redirect post-login |

## IdP-initiated vs SP-initiated

- **IdP-initiated.** User starts at the IdP (e.g. Okta dashboard),
  clicks the Salesforce app tile; the IdP POSTs a SAML response to
  Salesforce. Salesforce expects an `InResponseTo` of empty for this
  flow.
- **SP-initiated.** User starts at the Salesforce login page, gets
  redirected to the IdP via SAMLRequest, IdP responds. Salesforce
  expects `InResponseTo` matching the request it sent.

A common bug: misconfigured IdP-initiated when the user expects
SP-initiated, or vice versa. The error appears as `InResponseTo`
mismatch.

## Recommended Workflow

1. **Reproduce and capture.** Use a browser SAML tracer extension to capture the encoded SAML response from a failed login. Decode it (base64) for inspection.
2. **Run the SAML Assertion Validator.** Setup -> Single Sign-On Settings -> select the IdP -> SAML Assertion Validator. Paste the encoded response. The output names the failing check.
3. **Cross-check Login History.** Setup -> Login History. Find the failed attempt; the Status column names the failing check from the platform side (sometimes more specific than the validator).
4. **Identify the check.** Match the failing check to the well-known table above.
5. **Fix at the right end.** Most fixes are IdP-side (cert rotation, audience update, clock fix). Some are SP-side (Salesforce SSO Settings: Issuer, Identity Provider Login URL, NameID format, Federation Id mapping).
6. **Re-test with a fresh login.** Browser caches and IdP session caches can mask fixes; force a fresh login with cleared cookies or in an incognito window.
7. **Document the runbook.** Cert rotation will happen again. Capture the IdP cert refresh process, the Salesforce SSO Settings step, and a test plan in the runbook.

## What This Skill Does Not Cover

| Topic | See instead |
|---|---|
| Setting up SAML SSO from scratch | `security/sso-saml-setup` |
| OAuth / OpenID Connect SSO | `security/oauth-openid-troubleshooting` |
| MFA / multi-factor configuration | `security/mfa-configuration` |
| External Identity / Customer SSO | `security/customer-sso-experience-cloud` |
