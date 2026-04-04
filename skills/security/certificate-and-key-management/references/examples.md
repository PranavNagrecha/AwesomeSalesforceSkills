# Examples — Certificate and Key Management

## Example 1: Expiring Self-Signed Certificate Used in JWT OAuth Flow

**Context:** A middleware integration uses the Salesforce JWT Bearer OAuth flow (RFC 7523) to obtain access tokens without interactive user login. The self-signed certificate, created one year ago with the default 1-year validity, is now 14 days from expiry. The connected app is used by a nightly batch job that syncs data to an external ERP.

**Problem:** If the certificate expires before rotation, the JWT assertion Salesforce signs will be rejected by Salesforce's own token endpoint, because the connected app will no longer trust the expired certificate. The batch job will fail with a `invalid_client` error and no automatic retry.

**Solution:**

Step 1 — Create the replacement certificate in Setup > Security > Certificate and Key Management:
```
Label:         jwt_erp_sync_v2
Unique Name:   jwt_erp_sync_v2
Key Size:      2048
Expiration:    (set to 2 years from today, or the maximum allowed)
```
Click Save. Salesforce generates the new self-signed certificate and private key.

Step 2 — Download the new public certificate:
```
In Certificate and Key Management, click "Download Certificate" next to jwt_erp_sync_v2.
This downloads a .crt file containing the public certificate (PEM encoded).
```

Step 3 — Update the connected app in Setup > Apps > App Manager > [Your Connected App] > Edit:
```
Under "Use Digital Signatures":
  Upload the downloaded jwt_erp_sync_v2.crt file.
  This replaces the old certificate reference on the connected app.
```

Step 4 — If the integration builds JWT assertions via Apex using `Auth.JWT`, update the certificate name reference:
```apex
// Before:
jwt.setCertificateName('jwt_erp_sync');

// After:
jwt.setCertificateName('jwt_erp_sync_v2');
```

Step 5 — Test in sandbox: trigger the OAuth flow manually and confirm a valid access token is returned with a 200 response from the token endpoint.

Step 6 — Deploy the Apex change to production and run a manual test of the batch job to confirm end-to-end success.

Step 7 — After 48 hours of confirmed production success, delete the old `jwt_erp_sync` certificate from Certificate and Key Management.

**Why it works:** The connected app trusts whichever certificate is currently uploaded under "Use Digital Signatures." By uploading the new certificate before cutting over the code reference, there is a brief window where both the old and new certificates could work depending on which one the Apex code references — this minimizes downtime risk. Only after confirming the new certificate works is the old one removed.

---

## Example 2: Uploading a CA-Signed Certificate for mTLS Client Authentication

**Context:** A financial services org is integrating with an external payment gateway API. The payment gateway requires mTLS: Salesforce must present a client certificate signed by the gateway's approved CA (an internal enterprise CA, not a public CA). The security team generates key material externally using OpenSSL and provides the signed certificate chain and private key as PEM files.

**Problem:** Salesforce's Certificate and Key Management UI does not accept raw PEM files directly for CA-signed uploads. The private key and certificate must be packaged in a Java KeyStore (JKS) format. Additionally, once imported, the private key cannot be retrieved — so the JKS must be archived before import.

**Solution:**

Step 1 — Receive the following files from the security team:
```
salesforce_client.crt    # Signed leaf certificate (PEM)
salesforce_client.key    # Private key (PEM, unencrypted or password-protected)
enterprise_ca_chain.crt  # Intermediate and root CA certificates (PEM bundle)
```

Step 2 — Archive the original files in your secure vault (password manager or secrets manager) BEFORE any conversion or import.

Step 3 — Assemble a PKCS#12 keystore:
```bash
openssl pkcs12 -export \
  -in salesforce_client.crt \
  -inkey salesforce_client.key \
  -certfile enterprise_ca_chain.crt \
  -out salesforce_client.p12 \
  -name "sf-payment-gateway-mtls" \
  -passout pass:YourKeystorePassword123
```

Step 4 — Convert PKCS#12 to JKS using Java's keytool:
```bash
keytool -importkeystore \
  -srckeystore salesforce_client.p12 \
  -srcstoretype PKCS12 \
  -srcstorepass YourKeystorePassword123 \
  -destkeystore salesforce_client.jks \
  -deststoretype JKS \
  -deststorepass YourKeystorePassword123 \
  -destkeypass YourKeystorePassword123
```

Step 5 — Import the JKS into Salesforce:
```
Setup > Security > Certificate and Key Management > Import from Keystore
  Keystore File:      salesforce_client.jks
  Keystore Password:  YourKeystorePassword123
```
The certificate appears in the list with the alias "sf-payment-gateway-mtls."

Step 6 — Archive the `.p12` and `.jks` files in the secure vault alongside the original PEM files.

Step 7 — Reference this certificate in the Named Credential that points to the payment gateway API (see `named-credentials-setup` skill for the Named Credential configuration steps).

Step 8 — Coordinate with the payment gateway team: confirm they have added this certificate's CN to their allowed client list. Request a test call to verify mTLS handshake success.

**Why it works:** Packaging the full chain (leaf cert + CA intermediates) in the PKCS#12/JKS ensures Salesforce can present the complete chain during the TLS handshake, which strict API gateways require for chain-of-trust validation. Missing intermediates are the most common cause of mTLS failure in this pattern.

---

## Anti-Pattern: Assuming Certificates Deploy with SFDX or Metadata API

**What practitioners do:** A DevOps team adds certificates to their deployment pipeline assuming `sfdx force:source:deploy` or `sf project deploy start` will carry the certificates from sandbox to production as part of their release process.

**What goes wrong:** The Metadata API's `Certificate` type only deploys the public certificate file — it does not deploy the private key. For CA-signed certificates uploaded via JKS (which include the private key), the deployed certificate in production is incomplete and non-functional. For self-signed certificates, the private key is org-bound and cannot be moved at all. The integration breaks in production silently if the certificate reference exists but is non-functional, or the deploy fails with a metadata error about the certificate not existing in the target org.

**Correct approach:** Certificates are always migrated manually. For each target org:
1. For CA-signed certificates: re-import the original JKS file directly in that org's Setup > Certificate and Key Management.
2. For self-signed certificates: create a new self-signed certificate in each org separately, download each org's public certificate, and upload the correct public certificate to the respective connected app in that org.
Document this as an out-of-band deployment step in your release runbook so operators know to perform it before running the metadata deploy.
