---
name: certificate-and-key-management
description: "Use this skill when creating, uploading, or rotating certificates in Salesforce, configuring mutual TLS (mTLS) client authentication, managing the Java KeyStore for CA-signed certificates, diagnosing certificate expiry in JWT OAuth flows, or understanding which certificate types Salesforce supports and how to migrate them between orgs. NOT for Named Credential configuration (use named-credentials-setup skill), NOT for Shield Platform Encryption key management. Trigger keywords: Certificate and Key Management, self-signed certificate, CA-signed certificate, mutual TLS, mTLS, keystore, JKS, PKCS12, certificate rotation, certificate expiry, JWT certificate."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "how to configure mutual TLS for external callouts from Salesforce using a client certificate"
  - "certificate is expiring and needs rotation without breaking the JWT OAuth flow"
  - "upload a CA-signed certificate to Salesforce for mTLS client authentication"
  - "self-signed certificate expired in connected app — how do I create and apply a new one"
  - "how do I export or migrate a Salesforce certificate to another org or sandbox"
tags:
  - certificate
  - mutual-tls
  - mTLS
  - keystore
  - JKS
  - jwt
  - certificate-rotation
  - security
  - connected-app
inputs:
  - Certificate type needed (self-signed generated in Salesforce vs CA-signed uploaded from external PKI)
  - Use case for the certificate (JWT-based OAuth, mTLS client auth, SAML assertion signing)
  - Whether the certificate is already expiring or this is a fresh setup
  - "For CA-signed certificates: the keystore file format (JKS, PKCS#12/PFX, or PEM) and whether private key export is available"
  - The connected app or external system that will consume the certificate
outputs:
  - Step-by-step certificate creation or upload procedure
  - Certificate rotation runbook with zero-downtime sequencing
  - Decision table for self-signed vs CA-signed based on use case
  - Warnings about non-exportable private keys and metadata API limitations
  - Review checklist for certificate setup completeness
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Certificate and Key Management

This skill activates when an org needs to create, upload, rotate, or diagnose certificates in Salesforce's Certificate and Key Management UI (Setup > Security > Certificate and Key Management). It covers self-signed and CA-signed certificates, mutual TLS client authentication, Java KeyStore management, and safe certificate rotation procedures. It does NOT cover Named Credential configuration (use the `named-credentials-setup` skill), and it does NOT address Shield Platform Encryption tenant secret management (use the `platform-encryption` skill).

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the certificate's purpose: JWT-based OAuth (server-to-server auth), mTLS client authentication for outbound callouts, SAML signing, or general message signing.
- Confirm whether the org already has an existing certificate assigned to the relevant connected app, Named Credential, or remote site — changes must be sequenced to avoid breaking live integrations.
- Understand the hard limit: Salesforce supports **up to 50 certificates per org**. Orgs with many integrations can hit this limit and must archive or delete unused certificates before adding new ones.
- Know that once a CA-signed certificate's private key is imported into Salesforce, it **cannot be exported**. If the keystore file is lost or the private key is not backed up externally before import, it is permanently inaccessible from Salesforce. Always retain the original keystore outside Salesforce in a secure vault.
- Confirm the certificate format available for upload. Salesforce accepts Java KeyStore (JKS) format for CA-signed certificate imports. PEM/CRT + private key files must be converted to JKS or PKCS#12 before upload. Salesforce does not accept raw PEM bundles directly through the UI.

---

## Core Concepts

### Self-Signed Certificates

Self-signed certificates are generated directly in Salesforce Setup under Certificate and Key Management. Salesforce creates the certificate and private key internally; the private key never leaves Salesforce storage.

Key facts:
- Default validity: **1 year** from creation date. Custom validity (up to 10 years) can be set at creation time using the "Expiration" field.
- Key size: 2048-bit RSA (Salesforce-managed).
- Common use cases: JWT-based OAuth flows (the certificate's public key is uploaded to the connected app and the corresponding private key — held by Salesforce — signs the JWT assertion), SAML assertion signing for identity provider setups, and any scenario where a third party needs to verify a Salesforce-generated signature using the public certificate.
- Self-signed certificates are not trusted by external systems by default for mTLS server validation. For mTLS, a CA-signed certificate is typically required unless the external system is configured to trust the specific self-signed certificate explicitly.
- These certificates do not appear in Salesforce-managed backups or metadata deploys. If you delete a self-signed certificate that is actively in use, the integration it supports will fail immediately.

### CA-Signed Certificates

CA-signed certificates are signed by a trusted Certificate Authority (e.g., DigiCert, Entrust, Let's Encrypt, or an internal enterprise CA). The process in Salesforce has two paths:

**Path 1 — Salesforce generates the CSR:**
1. In Setup > Certificate and Key Management, create a new certificate and choose "CA-Signed Certificate."
2. Salesforce generates a Certificate Signing Request (CSR) and holds the private key internally.
3. Submit the CSR to your CA. The CA returns a signed certificate file.
4. Upload the signed certificate back into the same Salesforce record to activate it.

**Path 2 — Upload an externally generated certificate and key pair:**
1. Your security team generates the key pair and CSR externally (e.g., using OpenSSL).
2. The CA signs the CSR and returns a certificate chain.
3. Assemble the certificate, private key, and any intermediate CA certificates into a Java KeyStore (JKS) file or PKCS#12 file.
4. Convert to JKS if needed (see Keystore Management section below).
5. Upload via Setup > Certificate and Key Management > "Import from Keystore."

CA-signed certificates are required for any mTLS flow where the external system validates the client certificate against a known CA trust store, which is the standard for enterprise and government API gateways.

### Mutual TLS (mTLS) Client Authentication

In standard TLS, only the server presents a certificate. In mTLS, both client and server present certificates to authenticate each other. In the Salesforce context:

- **Salesforce as the mTLS client** (outbound callout): Salesforce presents a certificate to the external API. The certificate must be configured in the Named Credential or directly in the connected app. See the `named-credentials-setup` skill for the Named Credential side of this configuration. The certificate itself (self-signed or CA-signed) is managed under Certificate and Key Management.
- **External system as the mTLS client** (inbound): Salesforce acts as the mTLS server. The external system presents its client certificate; Salesforce validates it. This is configured in Setup > Connected Apps > the specific app > "Client Certificate" — you upload the external system's public certificate here so Salesforce knows to trust it.
- The certificate used for mTLS client auth must have the correct **Common Name (CN)** or **Subject Alternative Name (SAN)** that the external system expects. A CN mismatch will cause the TLS handshake to fail even if the certificate is otherwise valid.

### Certificate Rotation

Certificates expire. Rotating them without downtime requires:

1. **Create the new certificate first** — before touching anything in production. Generate or upload the replacement certificate in Salesforce and confirm it is valid.
2. **Update all references** — find every connected app, Named Credential, Apex callout configuration, or external system that uses the old certificate. Update them to point to the new certificate. For JWT flows: update the connected app's consumer key/secret and upload the new public certificate to the connected app.
3. **Coordinate with the external system** — if the external system trusts your certificate explicitly (common with mTLS), they must add trust for the new certificate before you switch. Request this in advance with enough lead time.
4. **Deactivate the old certificate** — after confirming the new certificate is working in production, delete or archive the old certificate. Do not delete it immediately after cutover; wait at least 24–48 hours to catch any missed references.
5. **Set a calendar reminder** for the new certificate's expiry date. Salesforce does not send expiry notifications for certificates.

---

## Common Patterns

### Pattern 1: JWT OAuth Flow — Self-Signed Certificate Rotation

**When to use:** A server-to-server integration using the JWT Bearer OAuth flow has a self-signed certificate approaching expiry, or the certificate has already expired and the integration is failing with authentication errors.

**How it works:**
1. In Setup > Certificate and Key Management, create a new self-signed certificate with an appropriate expiry. Give it a distinct name (e.g., `jwt_auth_v2`).
2. In Setup > Apps > Connected Apps, open the connected app used by the integration.
3. Under "Use Digital Signatures," upload the **public certificate** of the new self-signed certificate (download it from Certificate and Key Management using the "Download Certificate" button).
4. If the integration server generates the JWT locally using the Salesforce-held private key (via Apex `Auth.JWT`), update the Apex code or Named Credential to reference the new certificate name.
5. Test the JWT flow end-to-end in a sandbox before cutting over in production.
6. After confirming production success, delete the old certificate or let it expire naturally.

**Why not just re-use the old certificate name:** Salesforce certificates have immutable validity periods. You cannot extend an existing certificate's expiry. A new certificate must be created.

### Pattern 2: CA-Signed Certificate Upload for mTLS Client Authentication

**When to use:** An external API gateway requires Salesforce to present a CA-signed client certificate during mTLS handshake, and the security team manages the PKI externally.

**How it works:**
1. Obtain the signed certificate chain (leaf cert + any intermediate CA certs) and the private key from your PKI team.
2. Assemble the JKS keystore:
   ```bash
   # Convert PEM cert + key to PKCS#12 first
   openssl pkcs12 -export \
     -in salesforce_client.crt \
     -inkey salesforce_client.key \
     -certfile intermediate_ca.crt \
     -out salesforce_client.p12 \
     -name "salesforce-mtls"

   # Convert PKCS#12 to JKS
   keytool -importkeystore \
     -srckeystore salesforce_client.p12 \
     -srcstoretype PKCS12 \
     -destkeystore salesforce_client.jks \
     -deststoretype JKS
   ```
3. In Salesforce: Setup > Certificate and Key Management > Import from Keystore. Upload the JKS file and provide the keystore password.
4. The certificate now appears in Certificate and Key Management with the alias you assigned.
5. Reference this certificate in the Named Credential's "Client Certificate" field (see `named-credentials-setup` skill) or in the connected app's mTLS configuration.
6. Retain the original `.p12` and `.jks` files in your secure vault. Once imported, the private key cannot be retrieved from Salesforce.

---

## Keystore Management

Java KeyStore (JKS) is the format Salesforce's UI uses for CA-signed certificate import. Key operational notes:

- **Format conversion chain:** PEM/CRT → PKCS#12 (`.p12`/`.pfx`) → JKS. OpenSSL handles the first conversion; the Java `keytool` utility handles the second.
- **Alias:** When importing to JKS with `keytool`, the alias you specify becomes the identifier Salesforce uses internally. Choose a meaningful alias.
- **Keystore password and key password:** During JKS creation, you set a keystore-level password and a per-entry key password. Salesforce requires these during import. Use the same password for both to avoid confusion.
- **Certificate chain:** Include intermediate CA certificates in the PKCS#12 file (`-certfile` flag in the openssl command) so Salesforce can present the full chain during TLS handshake. Missing intermediates cause handshake failures against strict validators.
- **PKCS#12 direct import:** As of recent Salesforce releases, the UI may also accept `.p12`/`.pfx` directly in addition to JKS. Verify in your org's Setup UI. JKS remains the documented and most broadly supported format.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| JWT-based server-to-server OAuth, private key managed by Salesforce | Self-signed certificate generated in Setup | Salesforce holds the private key; CSR process not needed; simpler to create |
| mTLS client auth where external system validates against a CA trust store | CA-signed certificate uploaded via JKS import | External API gateways reject self-signed certs unless explicitly trusted |
| mTLS where external system will explicitly trust any cert you provide | Self-signed certificate is acceptable | Simpler; eliminates CA dependency; external team adds your public cert to their trust store |
| SAML assertion signing for SSO | Self-signed certificate (Salesforce-generated) or CA-signed | Salesforce-generated is standard; CA-signed required if your IdP enforces CA validation |
| Certificate needs to be migrated to another org or sandbox | CA-signed (Path 2 with external key): migrate the JKS file. Self-signed: impossible — private key cannot be exported | Self-signed certs are org-bound; CA-signed certs with external key generation are portable |
| Integration failing with auth errors and certificate is older than 1 year | Rotate: create new self-signed cert, update connected app, test, cut over | Default self-signed expiry is 1 year; expired certs cause immediate auth failures |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on certificate management:

1. **Identify the certificate's role** — determine whether the cert is used for JWT OAuth, mTLS outbound client auth, mTLS inbound (connected app trust), or SAML. The role dictates the certificate type and where it must be configured.
2. **Inventory existing certificates** — navigate to Setup > Security > Certificate and Key Management and list all certificates, their expiry dates, and any certificates that appear in connected apps or Named Credentials. Check the 50-certificate org limit.
3. **Create or obtain the certificate** — for self-signed: generate directly in Setup. For CA-signed: either generate a CSR in Setup and get it signed, or assemble the JKS from an externally generated key pair using the openssl and keytool commands in the Keystore Management section.
4. **Update all references before deactivating the old certificate** — for JWT flows: update the connected app's digital signature. For mTLS: update Named Credentials and coordinate with the external system to trust the new cert. Never delete the old cert before confirming the new one works.
5. **Test end-to-end in a lower environment** — for JWT: trigger the OAuth flow and confirm a valid access token is returned. For mTLS: make an authenticated callout through the Named Credential and confirm a 200 response from the external system.
6. **Cut over production and monitor** — update production references, monitor integration logs for authentication errors for 24–48 hours, then deactivate the old certificate.
7. **Record expiry dates and set calendar reminders** — Salesforce sends no automatic expiry alerts. Track expiry dates in your operations runbook or monitoring tool.

---

## Review Checklist

Run through these before marking certificate setup or rotation complete:

- [ ] Certificate type matches the use case (self-signed for Salesforce-held JWT key; CA-signed for external PKI or strict mTLS)
- [ ] For CA-signed imports: original JKS/PKCS#12 file is backed up in a secure vault before import
- [ ] Certificate CN/SAN matches what the external system expects (checked with the external team)
- [ ] All connected apps, Named Credentials, and Apex references using the old certificate have been updated
- [ ] External system has been coordinated for mTLS trust update if required
- [ ] Integration tested end-to-end in sandbox before production cutover
- [ ] Old certificate is NOT deleted until new certificate is confirmed working in production
- [ ] Certificate expiry date recorded in ops runbook or monitoring system
- [ ] Org is within the 50-certificate limit (old unused certificates cleaned up)
- [ ] Confirmed that certificate is NOT referenced in any metadata deployment pipeline (metadata API does not deploy certificates — deployments will not carry it)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Private key is permanently non-exportable after import** — When you import a JKS containing a private key into Salesforce, the private key cannot be retrieved from Salesforce under any circumstances. There is no export function in the UI or API. If the source keystore is lost, the certificate's private key is gone. Always retain the JKS file externally before importing.

2. **Certificates cannot be deployed via Metadata API or SFDX** — The `Certificate` metadata type exists in the Metadata API, but it only deploys the public certificate, not the private key. Full certificate migration between orgs (e.g., sandbox to production) requires manual re-import of the JKS in each target org. Automated deployment pipelines cannot carry certificates. Teams that assume certificates deploy automatically are surprised when integrations fail post-deployment.

3. **Salesforce sends no certificate expiry notifications** — Unlike some certificate management systems, Salesforce does not send email alerts or platform notifications as a certificate approaches its expiry date. The first sign of an expired certificate is often a broken integration or failed OAuth flow. Expiry tracking must be implemented externally (calendar reminder, monitoring script, or a third-party tool).

4. **CN mismatch causes mTLS handshake failure with no clear error message** — When Salesforce presents a client certificate during mTLS, the external API validates the CN/SAN against its expected value. If there is a mismatch, the TLS handshake fails before any HTTP response is sent. The Salesforce debug log shows a generic callout exception, not a CN mismatch error. Always verify the CN with the external system's API team before uploading.

5. **Self-signed certificates are org-bound and cannot be migrated** — Salesforce generates the private key for self-signed certificates and never exposes it. This means a self-signed certificate created in a sandbox cannot be migrated to production. Each org needs its own self-signed certificate. For JWT flows, the connected app in production must have the production org's certificate public key uploaded, not the sandbox certificate.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Certificate rotation runbook | Step-by-step procedure for rotating a specific certificate with zero-downtime sequencing, pre/post-validation steps, and rollback guidance (see templates/) |
| Certificate inventory | Table of all org certificates with expiry dates, assigned integrations, and renewal owner |
| JKS assembly commands | OpenSSL and keytool commands customized for the specific certificate chain being imported |
| mTLS coordination checklist | List of items to align with the external API team (CN/SAN, CA trust, testing schedule) |

---

## Related Skills

- named-credentials-setup — use alongside this skill when configuring Named Credentials that reference the certificates managed here; Named Credential mTLS settings are out of scope for this skill
- oauth-flows-and-connected-apps — JWT Bearer flow setup references self-signed certificates managed under this skill
- platform-encryption — separate skill for Shield Platform Encryption tenant secret and key management; not related to transport or identity certificates
- network-security-and-trusted-ips — covers TLS version enforcement and network-layer security; complements this skill's certificate configuration guidance
