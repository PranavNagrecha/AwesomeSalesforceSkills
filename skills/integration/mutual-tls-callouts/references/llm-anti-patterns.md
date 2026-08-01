# LLM Anti-Patterns — Mutual TLS Callouts

Scope: making an outbound Apex callout present a **client** certificate. Certificate
lifecycle and key management in general belong to
`security/certificate-and-key-management`; the wider trust-boundary design belongs to
`architect/integration-security-architecture`. This file covers only the mTLS wiring and
the failure strings it produces.

## Anti-Pattern 1: Building the TLS layer in Apex instead of declaring it

Given "call this partner with mTLS", assistants reach for keystore handling, because that
is what the pattern looks like in Java or Node. Apex has no such API surface. There is no
supported way to load a keystore, and there is no per-request method for attaching a
client certificate to an `HttpRequest`. The certificate is selected declaratively by the
Named Credential; the Apex simply calls `callout:`.

**Wrong** — invented API, will not compile:

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://partner.example.com/ach');
req.setClientCertificateName('BankACH');   // no such method for a Named-Credential flow
req.setHeader('Content-Type', 'application/json');
Http h = new Http();
HttpResponse res = h.send(req);
```

**Right** — the certificate is bound in Setup; the code stays credential-free:

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:BankACH/v1/payments');   // Named Credential holds the cert
req.setMethod('POST');
req.setHeader('Content-Type', 'application/json');
req.setTimeout(120000);                            // documented maximum, in ms
req.setBody(JSON.serialize(payload));
HttpResponse res = new Http().send(req);
```

The endpoint must also be reachable: an endpoint reached through `callout:` is authorised
by the Named Credential, but a raw host still needs a Remote Site Setting.

Source: Apex Callouts and Named Credentials as callout endpoints —
https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm

## Anti-Pattern 2: Generating the key pair outside Salesforce

The instinct is `openssl req -newkey`, then upload the key. That moves private key
material onto a laptop, into a ticket attachment and often into a chat thread. Salesforce
generates the key pair inside the platform and exports only the certificate signing
request, so the private key never leaves.

❌ Generate key and CSR with `openssl`, upload the `.key` file.
✅ Setup → Certificate and Key Management → **Create CA-Signed Certificate**, download the
CSR, have the partner's CA sign it, then upload the signed certificate back onto the same
record. The private key is never exportable, which is the point.

## Anti-Pattern 3: Shipping a self-signed certificate to a partner

Self-signed certificates are the default choice in Setup and are fine for a sandbox where
you also control the far end. A partner that validates client certificates against a CA
will reject one, and the failure looks like a network fault rather than a trust fault.

❌ Create Self-Signed Certificate, send the `.crt` to the bank, wait for the outage.
✅ Self-signed for internal and sandbox testing; CA-signed for anything a third party
validates. Decide this before generating, because moving from self-signed to CA-signed
means a new certificate record and a Named Credential edit.

## Anti-Pattern 4: Reading the handshake failure as a firewall problem

mTLS failures surface as generic-looking exceptions and teams spend days on network
tickets. The strings are diagnostic if you know how to read them:

- `System.CalloutException: IO Exception: Received fatal alert: bad_certificate` — the
  server rejected the client certificate you presented. Wrong certificate selected on the
  Named Credential, or the partner has not enrolled your certificate.
- `System.CalloutException: IO Exception: Received fatal alert: handshake_failure` — the
  two sides could not agree, commonly because no client certificate was presented at all:
  the Named Credential has no certificate bound, so the code path never had one to send.
- `System.CalloutException: IO Exception: Unable to tunnel through proxy` or
  `sun.security.validator.ValidatorException: PKIX path building failed` — your side does
  not trust *their* certificate. This is the mirror-image problem and is fixed by
  uploading their CA chain, not yours.
- `System.CalloutException: Unauthorized endpoint` — nothing to do with TLS; the endpoint
  is not registered as a Remote Site or Named Credential.

❌ Escalate to the network team on `bad_certificate`.
✅ Map the alert to a side first. `bad_certificate` and `handshake_failure` are almost
always your client certificate; `PKIX path building failed` is almost always their chain.

## Anti-Pattern 5: Uploading the leaf certificate without its chain

The partner sends back one `.crt`, it imports cleanly, and the handshake still fails
because the intermediate CA is missing. Import success is not validation success — the
platform will accept a certificate whose issuer it cannot complete a path to.

❌ Import the leaf, see "Success", assume done.
✅ Import the full chain, and verify with a probe callout rather than by reading the
Setup page. A `PKIX path building failed` after a clean import is the signature of a
missing intermediate.

## Anti-Pattern 6: No expiry monitor, so the outage arrives on the certificate's schedule

Certificates expire on a date chosen months earlier by someone who has left. Because the
callout works right up until it does not, there is no gradual signal.

❌ Diarise the renewal and hope.
✅ Query the certificate metadata on a schedule and alert with enough lead time to run a
partner re-enrolment, which is the slow part — the signing round trip, not the upload.
Alert at 60 and 30 days, and page on a probe-callout failure so a revoked certificate is
caught even when the expiry date is still in the future.

## Anti-Pattern 7: One Named Credential reused for every partner

Assistants consolidate because it looks tidy. A Named Credential binds one certificate,
so sharing it across partners means either every partner sees the same client identity or
one partner's rotation breaks the others.

❌ `callout:PartnerAPI` for three partners.
✅ One Named Credential per partner per environment, each with its own certificate, so
rotation and revocation have a blast radius of one integration.
