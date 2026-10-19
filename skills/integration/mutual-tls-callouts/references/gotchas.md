# Gotchas — Mutual TLS Callouts

## Gotcha 1: Key pair generated outside Salesforce

**What happens:** IT generates a key pair on a workstation, gets it signed, and tries to "upload the key". The key file now exists outside the org, on disks and in tickets.

**When it occurs:** Teams follow a generic TLS recipe. In Salesforce, a CA-signed certificate is created in Certificate and Key Management, its CSR is downloaded and signed, and the signed chain is uploaded back to the same certificate; the Metadata API doesn't import or export private keys. Importing a key pair from a keystore is possible (the Apex Developer Guide lists it for SOAP two-way SSL), but by then the key already exists outside the org.

**How to avoid:** Create the certificate in Salesforce, send out only the CSR, and upload the signed chain to that same record — a new record has a different key pair and won't match.

---

## Gotcha 2: Private keys are exportable by default

**What happens:** An admin later exports the certificate with its private key to a keystore "for testing", and the key leaves the org.

**When it occurs:** `privateKeyExportable` defaults to true when a certificate is created without specifying it.

**How to avoid:** Create mTLS certificates with export turned off; the checker WARNs on any `certs/*.crt-meta.xml` with `privateKeyExportable` true or absent.

---

## Gotcha 3: Binding through deprecated paths

**What happens:** A Named Credential migrated from an old org still uses the `certificate` field, or Apex embeds a PKCS12 key store with `setClientCertificate`, and the setup breaks or can't be maintained.

**When it occurs:** The NamedCredential `certificate` field is valid only for the `Legacy` type and is deprecated in API 56.0; the current schema uses a `namedCredentialParameters` entry of type `ClientCertificate`. `HttpRequest.setClientCertificate(clientCert, password)` is deprecated in favour of `setClientCertificateName`.

**How to avoid:** Bind through a `ClientCertificate` parameter on the Named Credential; use `setClientCertificateName` only where a Named Credential can't be used, and add the Remote Site Setting it then needs.

---

## Gotcha 4: Incomplete certificate chain

**What happens:** The partner rejects the handshake even though the leaf certificate is correct.

**When it occurs:** The partner expects the issuing intermediate chain, but only the leaf was uploaded, or the CA rotated its intermediate. For a CA-signed certificate, the `.crt` content is the certificate chain, which can be updated when the intermediate chain is renewed.

**How to avoid:** Upload the full signed chain the CA returns, and re-upload the chain when the CA announces an intermediate change.

---

## Gotcha 5: Inbound and outbound certificates are different things

**What happens:** A team configures `InboundCertificate` to satisfy a partner that wants Salesforce to present a client certificate, and nothing changes on outbound calls.

**When it occurs:** `InboundCertificate` represents a mutual authentication certificate imported so that clients calling *into* Salesforce can be authenticated, and it needs the MutualAuthentication permission. Outbound mTLS uses a certificate from Certificate and Key Management bound to the callout.

**How to avoid:** Decide the traffic direction first; outbound uses the Named Credential `ClientCertificate` parameter.

---

## Gotcha 6: Expiry arrives on the certificate's schedule

**What happens:** The callout fails on the expiry date and the partner notices before you do.

**When it occurs:** Self-signed certificates expire 1 year (2048-bit keys) or 2 years (4096-bit keys) after creation; CA-signed certificates take the signed certificate's expiration date. Renewal is slow because the partner or CA must sign and enrol the new certificate.

**How to avoid:** Keep `certs/*.crt-meta.xml` in source and alert from its `expirationDate` (the checker warns inside 60 days), plus a scheduled probe callout.

---

## Gotcha 7: The callout timeout governs connection set-up

**What happens:** Connections to a slow partner fail at the default timeout and get misread as certificate failures.

**When it occurs:** `HttpRequest.setTimeout` (1–120,000 ms) is the maximum time to wait for establishing the HTTP connection and for the request to start; once the request is executing, the connection is kept alive until it finishes. The default is 10 seconds.

**How to avoid:** Set an explicit timeout sized to the partner's documented latency, and classify failures by message before assuming a certificate problem.
