---
name: mutual-tls-callouts
description: "Configure mTLS for Apex callouts using Named Credentials with client certificate authentication. NOT for standard TLS or API key auth — use architect/integration-security-architecture."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "mtls salesforce callout"
  - "client certificate apex"
  - "mutual tls named credential"
  - "jks keystore apex"
  - "a partner API now requires a client certificate on our callouts"
  - "attach a CA-signed certificate to a named credential"
  - "renew the client certificate before it expires"
tags:
  - mtls
  - callout
  - named-credential
inputs:
  - "partner's required cert details"
  - "current Apex HttpClient"
outputs:
  - "Named Credential + uploaded certificate + callout snippet"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-10-19
---

# Mutual TLS Callouts

Mutual TLS (two-way SSL) means Salesforce presents a client certificate when it calls the partner, and the partner authenticates the request against its keystore. The certificate lives in Certificate and Key Management; the callout picks it up either from a Named Credential (`ClientCertificate` parameter) or from code (`HttpRequest.setClientCertificateName`). This skill sets up the certificate, binds it, proves the handshake, and monitors expiry.

---

## Before Starting

- Get the partner's requirements: CA-signed or self-signed acceptable, which CA, key size, renewal lead time.
- Confirm the endpoint, and whether other authentication (OAuth, API key) is also required — an External Credential handles that part.
- Find existing code that sets client certificates directly (`setClientCertificate`, `setClientCertificateName`, `clientCertName_x`).
- Decide who owns renewal and how far ahead the partner needs a new certificate.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does the partner require a CA-signed certificate, and from which CA? | A self-signed certificate must be added to the partner's keystore; a CA-signed one is created as a CSR, signed, then uploaded to the same record (gotcha 1). | The right certificate type and a signing timeline. |
| Must the private key stay non-exportable? | `privateKeyExportable` defaults to true when a certificate is created (gotcha 2). | A certificate created with export turned off, unless a documented need exists. |
| Which key size? | Self-signed certificates expire 1 year (2048-bit) or 2 years (4096-bit) after creation (gotcha 6). | An expiry date the renewal plan is built around. |
| Will the binding be a Named Credential or code? | The Named Credential `ClientCertificate` parameter keeps certificate names out of code and needs no Remote Site Setting; the legacy `certificate` field is deprecated (gotcha 3). | One binding point per partner. |
| Does the partner issue an intermediate chain? | A CA-signed certificate's `.crt` content is the certificate chain, which you update when the intermediate changes (gotcha 4). | A complete chain uploaded, and a plan when the CA rotates intermediates. |
| Is this outbound (we call them) or inbound (they call us with a certificate)? | Inbound client certificates are a different type (`InboundCertificate`, needs MutualAuthentication) (gotcha 5). | The right setup for the traffic direction. |
| Who is alerted, how far ahead of expiry? | Renewal is gated by the partner's signing turnaround, not the upload (gotcha 6). | A monitored expiry date and a probe callout. |

A properly configured mTLS callout adds a non-exportable, CA-signed key bound once through a Named Credential, with an expiry alert sized to the partner's turnaround, where "just uploading a certificate" leaves an exportable key, a broken chain, and an outage on the expiry date.

---

## Core Concepts

### Certificates in Salesforce

Certificates are created in Certificate and Key Management (or as `Certificate` metadata, suffix `.crt` in `certs/`). For self-signed certificates, Salesforce generates the key pair when you save. For CA-signed certificates, you download the CSR, have it signed, and upload the signed chain to the same certificate; `expirationDate` then updates to the signed certificate's date. The Metadata API doesn't import or export private keys. `privateKeyExportable` defaults to true, so turn it off at creation when the key must not leave the org.

### Binding the certificate to the callout

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- namedCredentials/BankACH.namedCredential-meta.xml (shape follows the Metadata API sample) -->
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>BankACH</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <namedCredentialParameters>
        <parameterName>DefaultEndpoint</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://ach.bank.example.com</parameterValue>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <parameterName>DefaultCert</parameterName>
        <parameterType>ClientCertificate</parameterType>
        <certificate>BankACH_Prod</certificate>
    </namedCredentialParameters>
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>false</allowMergeFieldsInHeader>
    <generateAuthorizationHeader>false</generateAuthorizationHeader>
</NamedCredential>
```

Code then calls `callout:BankACH/...`; a callout to a Named Credential needs no Remote Site Setting. If partner authentication also needs a token, add an `Authentication` parameter pointing at an External Credential. The code-level alternative is `req.setClientCertificateName('BankACH_Prod')`, which requires a Remote Site Setting for the endpoint; `setClientCertificate` (PKCS12 key store and password in code) is deprecated.

### Timeouts

`HttpRequest.setTimeout` accepts 1–120,000 ms; the default is 10 seconds.

---

## Recommended Workflow

1. Answer the Questions table; record partner, CA, key size, lead time, and owner in `templates/mutual-tls-callouts-template.md`.
2. Create the certificate (CA-signed: download CSR → partner/CA signs → upload the signed chain to the same record) with private-key export off; retrieve it so `certs/<Name>.crt-meta.xml` is in source.
3. Create the Named Credential with a `ClientCertificate` parameter (XML above) and, if needed, an `Authentication` parameter; replace any `setClientCertificate` code.
4. Run `python3 skills/integration/mutual-tls-callouts/scripts/check_mutual_tls_callouts.py --manifest-dir force-app` — it ERRORs on deprecated `setClientCertificate(` calls and on Named Credentials whose `ClientCertificate` points at a certificate missing from source, and WARNs on exportable keys, certificates expiring within 60 days, and the legacy `certificate` field.
5. Prove the handshake with the probe in `references/examples.md` against a side-effect-free endpoint, then schedule the probe and the expiry check.

---

## Decision Guidance

| Situation | Approach | Why |
|---|---|---|
| Partner requires mTLS on REST calls | Named Credential with `ClientCertificate` parameter | One binding, no Remote Site Setting, no certificate names in code |
| Partner also requires OAuth | Add an `Authentication` parameter with an External Credential | Certificate and token handled by the same credential |
| Generated SOAP stub (WSDL2Apex) | `stub.clientCertName_x = '<Unique Name>'` | The documented SOAP path |
| Partner calls *into* Salesforce with a certificate | `InboundCertificate` with MutualAuthentication enabled | Different direction, different type |
| Certificate renewal | New CSR on a new certificate, partner enrols it, switch the Named Credential parameter | Keeps the old one valid until the switch |

---

## Review Checklist

- [ ] Certificate is CA-signed (or the partner explicitly accepts self-signed) and the full chain is uploaded
- [ ] `privateKeyExportable` is false unless documented otherwise
- [ ] The Named Credential uses a `ClientCertificate` parameter, not the deprecated `certificate` field
- [ ] No `setClientCertificate(` (deprecated) in Apex
- [ ] A probe callout and an expiry alert run on a schedule
- [ ] Renewal lead time covers the partner's signing turnaround
- [ ] The checker exits 0

---

## Salesforce-Specific Gotchas

Full list in `references/gotchas.md`. The two that cause outages:

1. **Exportable by default** — `privateKeyExportable` is true unless you turn it off.
2. **Expiry is silent** — self-signed certificates last 1 or 2 years; CA-signed ones last as long as the CA says.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Certificate | CA-signed, non-exportable, full chain, in `certs/` |
| Named Credential | `ClientCertificate` parameter (+ `Authentication` if needed) |
| Probe + expiry monitor | Scheduled handshake check and expiry alert |
| Renewal runbook | CSR, partner enrolment, switch, retire |

---

## Reference Files

| File | Use it for |
|---|---|
| `references/examples.md` | Bank ACH mTLS mandate; expiry and handshake monitoring |
| `references/gotchas.md` | Seven certificate and binding behaviours |
| `references/llm-anti-patterns.md` | mTLS mistakes AI assistants make |
| `references/well-architected.md` | Pillar framing and the guide lines behind each claim |
| `references/renewal-runbook.md` | Certificate renewal without a gap, step by step |

---

## Related Skills

- `architect/integration-security-architecture` — standard TLS, API keys, and the wider integration security design
- `integration/api-governance-and-rate-limits` — governing inbound API consumption
- `devops/pipeline-secrets-management` — secrets in CI, including connected app certificates
