# Gotchas — SAML SSO Troubleshooting

Real-world surprises that bite SAML SSO implementations on
Salesforce.

---

## Gotcha 1: SAML SSO requires My Domain enabled and deployed

**What happens.** Customer enables SSO in Setup -> Single Sign-On
Settings, points the IdP at it, but logins fail with a generic
error. Root cause: My Domain is not enabled on the org.

**When it occurs.** Older orgs that have not yet enabled My Domain.

**How to avoid.** Confirm Setup -> My Domain shows the My Domain as
deployed before troubleshooting any SSO config.

---

## Gotcha 2: Sandbox refresh changes the My Domain URL

**What happens.** SSO works pre-refresh; post-refresh fails with
audience mismatch. The sandbox's My Domain hostname includes the
sandbox name; refreshing can change that name.

**When it occurs.** Any sandbox SSO config; especially after a
sandbox is renamed or refreshed from a different source.

**How to avoid.** Maintain a refresh checklist that updates the IdP-
side audience / ACS URL for the sandbox post-refresh.

---

## Gotcha 3: Federation Id matches are case-sensitive in some configurations

**What happens.** User logs in successfully via SSO sometimes but
not always; same NameID. Root cause: case-sensitivity mismatch
between the IdP NameID value and the Salesforce
`FederationIdentifier`.

**When it occurs.** IdP normalizes case; Salesforce stores raw.

**How to avoid.** Audit `FederationIdentifier` values on Salesforce
users for case consistency. Configure the IdP to send a normalized
form.

---

## Gotcha 4: SAML Assertion Validator does not validate signature against IdP metadata

**What happens.** SAML Assertion Validator returns "Signature
Successful" but real-world login fails. Root cause: the validator
uses the cert in SSO Settings; if you uploaded the wrong cert,
both the validator and the live login fail in the same way — but
that does not mean the live IdP cert is correct.

**When it occurs.** Diagnostic shortcut.

**How to avoid.** Treat the validator as "tests against my SSO
Settings configuration", not "tests against IdP truth". Always
cross-check that the cert in SSO Settings matches the IdP's
published metadata.

---

## Gotcha 5: NameID format must match SSO Settings exactly

**What happens.** IdP sends NameID with format
`urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified`. SSO
Settings expects `emailAddress`. Login fails despite the value being
a valid email.

**When it occurs.** IdP defaults that don't match the documented
Salesforce SSO Settings expectation.

**How to avoid.** Read the SSO Settings page carefully — the NameID
Format dropdown must match the IdP's exact format URI.

---

## Gotcha 6: RelayState is not preserved through some IdPs

**What happens.** SP-initiated flow: Salesforce sends a
`RelayState` carrying the user's intended landing page. Some IdPs
strip or alter `RelayState`; user lands on a default page after
login, not their intended deep link.

**When it occurs.** IdPs with strict RelayState handling, or
configurations that override it.

**How to avoid.** Test the deep-link flow specifically. If the IdP
strips RelayState, the deep-link feature is degraded; document the
limitation.

---

## Gotcha 7: Browser SAML tracer captures encrypted assertions as opaque blobs

**What happens.** SAML response is encrypted (AES). The browser
tracer captures it but the contents are not human-readable.

**When it occurs.** Encrypted assertions are configured (less
common; signature alone is more typical).

**How to avoid.** For diagnosis with encryption enabled, you need
the SP-side decryption key (Salesforce's). Disable encryption
temporarily in a dev / sandbox to capture readable assertions, or
use Salesforce-side debug logs.

---

## Gotcha 8: Login Flow / MFA can mask SSO success

**What happens.** SAML SSO succeeds. A Login Flow or MFA challenge
fails. Symptom appears to be "SSO failure" but Login History shows
"Success" for the SAML phase and a separate failure for the
post-SSO step.

**When it occurs.** Orgs with Login Flow or stepped MFA after SSO.

**How to avoid.** Read both the Login History row and the Login
Flow log separately. SAML success does not imply session
established.

---

## Gotcha 9: Just-in-Time Provisioning silently creates incomplete users

**What happens.** JIT enabled. IdP sends a SAML response that
matches a non-existent user. Salesforce auto-creates the user using
attributes in the assertion. If required fields are not in the
assertion, the user record is created with defaults; license
assignment may fail; user lands in an inconsistent state.

**When it occurs.** JIT misconfiguration where IdP attributes do
not cover Salesforce required fields.

**How to avoid.** Map every Salesforce required user field to an
IdP attribute. Test JIT specifically with a fresh user before
opening to production.
