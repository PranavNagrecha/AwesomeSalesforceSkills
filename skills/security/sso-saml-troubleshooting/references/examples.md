# Examples — SAML SSO Troubleshooting

## Example 1 — Signature failure after IdP cert rotation

**Symptom.** All SSO logins start failing on a Tuesday morning.
Login History shows "Signature Failure".

**Diagnosis.** The IdP's signing certificate rotated. Salesforce
still has the previous cert configured in Single Sign-On Settings.
The signature on the new IdP responses does not validate against
the old cert.

**Fix.**

1. Setup -> Single Sign-On Settings -> select the IdP entry.
2. Replace `Identity Provider Certificate` with the new cert from
   the IdP (download as PEM / CER from the IdP's metadata).
3. Save. Re-test login.

**Prevention.** Subscribe to the IdP's cert-rotation notifications;
schedule the Salesforce-side replacement before the IdP cuts over.
Some IdPs publish two valid certs during a rotation window — load
both and remove the old one after migration.

---

## Example 2 — Audience Mismatch on a sandbox after refresh

**Symptom.** SSO works in production. Sandbox refresh produces a
new sandbox; SSO into the sandbox fails with "Audience Mismatch".

**Diagnosis.** The sandbox's My Domain URL changed (it includes the
sandbox name). The IdP's Salesforce app is configured with the
production audience or the previous sandbox audience.

**Fix.** On the IdP side, configure the Salesforce app's audience
to the sandbox-specific URL (typically
`https://<orgname>--<sandboxname>.my.salesforce.com` for SP-
initiated, or `https://saml.salesforce.com` for IdP-initiated). Or
maintain a separate IdP app per sandbox with its own audience.

**Note.** Sandbox SSO is fragile around refresh because URLs shift.
Document the post-refresh SSO checklist explicitly.

---

## Example 3 — User Does Not Exist with Federation Id mapping

**Symptom.** New user in the IdP. Login fails with "User does not
exist".

**Diagnosis.** Salesforce SSO Settings is configured to match users
by `Federation Id`. The new IdP user's NameID is their email; the
matching Salesforce user's `FederationIdentifier` field is empty.

**Fix.** Populate `FederationIdentifier` on the Salesforce user
record with the value the IdP sends as NameID. Either bulk-load all
users via Data Loader or wire up SCIM provisioning.

**Alternative.** If the IdP cannot send a Federation Id, change
Salesforce SSO Settings to match by `Username` (Salesforce
username = IdP NameID). This is simpler but requires that
Salesforce usernames match the IdP NameID format.

---

## Example 4 — Decoded SAML Response walkthrough

**Context.** You have a captured base64 SAML response. Decode for
inspection.

```bash
echo '<base64>' | base64 -d | xmllint --format -
```

Key elements to inspect:

```xml
<saml:Issuer>https://idp.example.com</saml:Issuer>
<!-- Must match SSO Settings Issuer -->

<ds:Signature>...</ds:Signature>
<!-- Validated against IdP cert in SSO Settings -->

<saml:Conditions NotBefore="2026-05-05T10:00:00Z"
                 NotOnOrAfter="2026-05-05T10:05:00Z">
    <saml:AudienceRestriction>
        <saml:Audience>https://saml.salesforce.com</saml:Audience>
        <!-- Must match Salesforce-expected audience -->
    </saml:AudienceRestriction>
</saml:Conditions>

<saml:Subject>
    <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
        user@example.com
    </saml:NameID>
    <!-- Format must match SSO Settings; value matched by FederationId / Username / Email -->
</saml:Subject>

<saml:AttributeStatement>
    <saml:Attribute Name="...">...</saml:Attribute>
    <!-- Optional; used by Just-in-Time Provisioning if enabled -->
</saml:AttributeStatement>
```

A failed check usually maps directly to one of these elements being
wrong: cert doesn't match Signature, audience string mismatch,
NameID format / value mismatch, NotBefore / NotOnOrAfter outside
window.

---

## Example 5 — Clock skew producing "Assertion Expired"

**Symptom.** Intermittent SSO failures, especially during peak
hours. Login History sometimes shows "Assertion Expired".

**Diagnosis.** Tight `NotOnOrAfter` window (e.g. 30 seconds) plus
clock drift between IdP host and Salesforce. SAML uses UTC; an IdP
clock 90 seconds behind UTC produces assertions that look already-
expired to Salesforce.

**Fix.**

1. Confirm IdP host clock is synchronized to a reliable NTP source.
2. Increase IdP's NotOnOrAfter window (typical: 5 minutes, 300
   seconds).
3. Reduce reliance on tight assertion lifetimes — they don't add
   security if the IdP is otherwise trusted.

---

## Example 6 — IdP-initiated vs SP-initiated InResponseTo

**Symptom.** IdP-initiated login from Okta dashboard fails with an
`InResponseTo` mismatch error.

**Diagnosis.** The IdP is sending a SAML response with
`InResponseTo` populated (as if responding to a SAMLRequest), but
in IdP-initiated flow Salesforce did not send a request. The mismatch
is the empty-vs-populated mismatch.

**Fix.** On the IdP side, configure the Salesforce app for IdP-
initiated flow specifically — the IdP should not include
`InResponseTo` for IdP-initiated assertions.

**Alternative.** Switch users to SP-initiated (start at Salesforce
login URL, get redirected) so the IdP's `InResponseTo` is correct.
