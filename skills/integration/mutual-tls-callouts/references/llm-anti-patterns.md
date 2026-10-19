# LLM Anti-Patterns — Mutual TLS Callouts

Scope: making an outbound Apex callout present a **client** certificate. Certificate
lifecycle and key management in general belong to
`security/certificate-and-key-management`; the wider trust-boundary design belongs to
`architect/integration-security-architecture`. This file covers only the mTLS wiring and
the failure strings it produces.

## Anti-Pattern 1: Building the TLS layer in Apex instead of declaring it

Given "call this partner with mTLS", assistants reach for keystore handling, because that
is what the pattern looks like in Java or Node: a base64 PKCS12 blob and a password in code.
Apex did have that method — `HttpRequest.setClientCertificate(clientCert, password)` — and it
is deprecated. The supported code-level method is `setClientCertificateName(certDevName)`,
which names a certificate already in Certificate and Key Management; the declarative and
preferred route is a Named Credential with a `ClientCertificate` parameter.

**Wrong** — key material and password in source, deprecated method:

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://partner.example.com/ach');
req.setClientCertificate(PKCS12_BASE64, KEYSTORE_PASSWORD);   // deprecated; secrets in code
req.setHeader('Content-Type', 'application/json');
HttpResponse res = new Http().send(req);
```

**Right** — the certificate is bound on the Named Credential; the code stays credential-free:

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:BankACH/v1/payments');   // Named Credential holds the cert
req.setMethod('POST');
req.setHeader('Content-Type', 'application/json');
req.setTimeout(120000);                            // documented maximum, in ms
req.setBody(JSON.serialize(payload));
HttpResponse res = new Http().send(req);
```

If a Named Credential genuinely can't be used, `req.setClientCertificateName('BankACH_Prod')`
with a raw endpoint works, and that endpoint then needs a Remote Site Setting — a callout to a
Named Credential does not.

Source: Apex Developer Guide, Summer '26 — Using Certificates with HTTP Requests; Apex Reference Guide — HttpRequest `setClientCertificate` (deprecated) and `setClientCertificateName`.

## Anti-Pattern 2: Generating the key pair outside Salesforce

The instinct is `openssl req -newkey`, then upload the key. That moves private key
material onto a laptop, into a ticket attachment and often into a chat thread. Salesforce
generates the key pair inside the platform and you send out only the certificate signing
request; the Metadata API doesn't import or export private keys.

❌ Generate key and CSR with `openssl`, upload the `.key` file.
✅ Setup → Certificate and Key Management → **Create CA-Signed Certificate**, download the
CSR, have the partner's CA sign it, then upload the signed certificate back onto the same
record. Create it with private-key export off — `privateKeyExportable` defaults to true.

## Anti-Pattern 3: Shipping a self-signed certificate to a partner

Self-signed certificates are the default choice in Setup and are fine for a sandbox where
you also control the far end. A partner that validates client certificates against a CA
will reject one, and the failure looks like a network fault rather than a trust fault.

❌ Create Self-Signed Certificate, send the `.crt` to the bank, wait for the outage.
✅ Self-signed for internal and sandbox testing; CA-signed for anything a third party
validates. Decide this before generating, because moving from self-signed to CA-signed
means a new certificate record and a Named Credential edit.

## Anti-Pattern 4: Reading the handshake failure as a firewall problem

mTLS failures surface as generic-looking `System.CalloutException` messages and teams spend
days on network tickets. The useful move is to map a failure to a *side* before escalating:

| Side | Typical cause | Fix |
|---|---|---|
| Partner rejected our certificate | Wrong certificate on the Named Credential, or the partner hasn't enrolled it | Check the `ClientCertificate` parameter and the partner's enrolment |
| We don't trust the partner's certificate | Their chain isn't trusted by the platform | Work with the partner on their chain |
| No certificate sent | The callout path never had one bound (no Named Credential parameter, no `setClientCertificateName`) | Bind the certificate |
| Endpoint not authorised | Raw host with no Remote Site Setting and no Named Credential | Use the Named Credential |

❌ Escalate to the network team on the first `CalloutException`.
✅ Run a sandbox probe once with the certificate deliberately unbound, record the exact message
your org returns for each case, and match on those recorded strings in the alerting code.

## Anti-Pattern 5: Uploading the leaf certificate without its chain

The partner's CA sends back the signed certificate and its intermediate chain; someone uploads
only the leaf. For a CA-signed certificate the `.crt` content is the certificate chain, and it
can be updated when the CA renews its intermediates.

❌ Upload the leaf, see "Success", assume done.
✅ Upload the full signed chain, and verify with a probe callout rather than by reading the
Setup page.

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
