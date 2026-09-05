# Examples: Connected Apps and Auth

---

## Example: External System Calling Salesforce

**Scenario:** Middleware needs server-to-server API access to create and update Cases in Salesforce.

**Recommended pattern:**
- Connected App
- Client Credentials or JWT Bearer flow
- dedicated integration user
- minimal permission set for the Case operations required

**Why:** This keeps machine access separate from human credentials and supports controlled token lifecycle.

---

## Example: Salesforce Calling an External API

**Scenario:** A Flow-triggered Apex callout sends invoice data to a billing platform.

**Recommended pattern:**
- Named Credential
- External Credential / OAuth config
- `callout:` endpoint in Apex
- environment-specific credential records

**Why:** Endpoint and auth stay out of code, making promotion and rotation safer.

**What the Apex actually looks like.** The class names the credential, never the host. The
Apex Developer Guide: "A named credential URL contains the scheme `callout:`, the name of the
named credential, and an optional path."

```apex
public with sharing class BillingInvoicePublisher {
    // No endpoint, no token, no environment branch. The Named Credential 'Billing_API'
    // resolves to a different host in DEV, UAT and PROD; this class is deployed unchanged.
    public static Integer publish(String invoicePayload) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Billing_API/invoices');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(invoicePayload);

        HttpResponse res = new Http().send(req);
        return res.getStatusCode();
    }
}
```

Note what is absent: no `Authorization` header. The Named Credential's
`generateAuthorizationHeader` is `true` by default, so Salesforce "generates an authorization
header and applies it to each callout that references the named credential." Setting a bearer
token by hand here is the anti-pattern, not the pattern.

The paired promotion trick is the reason this holds across environments: "If you have multiple
orgs, you can create a named credential with the same name but with a different endpoint URL in
each org. You can then package and deploy — on all the orgs — one callout definition that
references the shared name of those named credentials."

For the `NamedCredential` and `ExternalCredential` XML behind `Billing_API`, see
`references/metadata-examples.md`. For principal-type setup steps, see
`integration/named-credentials-setup`.

---

## Example: User-Delegated Third-Party App

**Scenario:** A productivity tool needs a salesperson to connect their own Salesforce account so actions respect that user's access.

**Recommended pattern:** OAuth Authorization Code flow with controlled scopes.

**Why:** User-delegated access is different from machine-to-machine integration and should preserve explicit user consent and user-level permissions.

---

## Example: Choosing the Artefact When All Three Look Plausible

**Scenario:** A vendor asks for "API access to Salesforce." That sentence maps to three different
artefacts depending on answers the vendor has not given you yet.

| What the vendor actually needs | Artefact | Tell |
|---|---|---|
| Their servers read and write records on a schedule, no person involved | Connected app / ECA on JWT bearer (they hold the private key) or client credentials (you nominate a Run As user) | They ask for a certificate upload, or for a username to run as |
| Each of *your* users links their own Salesforce account inside the vendor's product | Connected app / ECA on the web server flow with PKCE | They ask for a redirect URI |
| Salesforce pushes data to *them* when something happens here | Named Credential + External Credential — no connected app at all | They give you an API base URL and their own credentials |

The failure mode is answering the first sentence with a connected app when the third is what was
meant, then discovering at build time that nothing in Salesforce points outward.

**Quick disambiguation, before any Setup work:**

```text
Who initiates the HTTP request?
├─ The vendor's system → into Salesforce → connected app or External Client App
│   └─ Does a human ever click "Allow"?
│       ├─ Yes → web server flow + PKCE (isPkceRequired = true)
│       └─ No  → JWT bearer (certificate) or client credentials (oauthClientCredentialUser,
│                 which the guide requires to hold the API Only permission)
└─ Salesforce → out to the vendor → NamedCredential (endpoint)
                                    + ExternalCredential (principal)
```

**Why it matters:** the two directions share vocabulary ("OAuth", "client ID", "scopes") and share
almost no metadata. Deciding direction first is what stops a team from building the wrong half.
