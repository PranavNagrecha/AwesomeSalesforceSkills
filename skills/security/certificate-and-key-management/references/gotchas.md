# Gotchas — Certificate and Key Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Private Key Is Permanently Non-Exportable After Import

**What happens:** When a CA-signed certificate is imported into Salesforce via a JKS keystore, Salesforce stores the private key internally but provides no mechanism to retrieve or export it. The Certificate and Key Management UI has no "Export" or "Download Private Key" button. The Metadata API only exports the public certificate, not the private key. There is no Apex API or REST endpoint to retrieve it.

**When it occurs:** Any time a CA-signed certificate is imported using the "Import from Keystore" function. This affects all orgs, all editions.

**How to avoid:** Always retain the original JKS, PKCS#12, and PEM source files in a secure external vault (e.g., a password manager, AWS Secrets Manager, or a hardware security module) before importing into Salesforce. Treat the Salesforce import as a one-way operation. If the JKS is lost after import, the certificate's private key is unrecoverable and a new certificate must be issued from the CA.

---

## Gotcha 2: Certificates Cannot Be Fully Deployed via Metadata API or SFDX

**What happens:** The `Certificate` metadata type exists in the Metadata API and `package.xml`, leading practitioners to assume certificates deploy like other metadata. In reality, a metadata deploy only carries the public certificate. For CA-signed certificates imported with a private key, the private key is not included in the retrieved metadata package — the deployed certificate in the target org is a public-key-only stub that cannot perform private key operations (signing, mTLS client auth). Integrations that depend on private key operations will fail silently or throw generic errors.

**When it occurs:** During any sandbox-to-production promotion or org-to-org migration using `sf project deploy start`, `sfdx force:source:deploy`, `ant migrate`, or Change Sets. Teams that automate all deployments through CI/CD and do not have an out-of-band step for certificates will see broken integrations after release.

**How to avoid:** Document certificates as an out-of-band deployment step in the release runbook. For each target org, manually import the JKS via Setup > Certificate and Key Management before running the metadata deploy that references the certificate. For self-signed certificates, create them independently in each org and update the connected app's public certificate reference in each org separately.

---

## Gotcha 3: Common Name Mismatch Causes Silent mTLS Handshake Failure

**What happens:** When Salesforce presents a client certificate during an outbound mTLS callout, the external API validates the certificate's Common Name (CN) or Subject Alternative Name (SAN) against its configured allowed-client list. If the CN in the certificate does not match what the external system expects, the TLS handshake is rejected at the TCP/TLS layer before any HTTP response is sent. In the Salesforce Apex debug log, this appears as a generic `System.CalloutException: Unable to connect to endpoint` or a timeout — not a meaningful certificate error. This makes CN mismatch extremely difficult to diagnose without coordination with the external system.

**When it occurs:** Whenever a CA-signed certificate is created or re-issued without verifying the exact CN/SAN value the external API expects. Common triggers: the external team changed their validation logic, a new certificate was issued with a slightly different CN format (e.g., `salesforce.api.example.com` vs `api.example.com`), or a wildcard cert is used where the external system expects an exact match.

**How to avoid:** Before importing a CA-signed certificate, confirm the exact CN and SAN values with the external system's integration team. Use `openssl x509 -in cert.crt -text -noout` to inspect the CN and SAN of the certificate before import. Document the expected CN/SAN in the integration runbook. When debugging mTLS failures, check with the external team's access logs rather than relying solely on Salesforce debug logs.

---

## Gotcha 4: Salesforce Sends No Certificate Expiry Notifications

**What happens:** Salesforce does not send any email alert, in-app notification, or platform event when a certificate is approaching or has passed its expiry date. The first indication that a certificate has expired is typically a broken integration, a failed OAuth token request, or a user reporting that a connected app login no longer works. By that point, the integration is already down.

**When it occurs:** Consistently, for all certificate types and all orgs. This is not a bug — it is a platform design gap. Certificates can expire silently during nights, weekends, or holidays.

**How to avoid:** After creating or rotating any certificate, immediately record the expiry date in your operations runbook and create a calendar reminder or monitoring alert at 60 days, 30 days, and 7 days before expiry. Consider a lightweight scheduled Apex job or an external monitoring tool that periodically checks integration health (e.g., a JWT token request) and alerts if it fails. Some teams use external certificate monitoring services pointed at the public certificate endpoint.

---

## Gotcha 5: Self-Signed Certificates Are Org-Bound and Cannot Be Migrated

**What happens:** Self-signed certificates generated in Salesforce have their private key generated and held exclusively in that org. There is no way to transfer the private key to another org (sandbox, production, or scratch org). When a team creates a connected app and certificate in a sandbox and tries to promote the integration to production, they discover that the sandbox certificate cannot be used in production — production needs its own self-signed certificate, which has a different public key, which must be re-uploaded to the connected app in production.

**When it occurs:** During all org-to-org promotions involving integrations that use self-signed certificates for JWT OAuth or SAML signing. Also occurs when restoring from a sandbox refresh — the refreshed sandbox gets a fresh org ID and any certificates generated in the pre-refresh sandbox are not carried over.

**How to avoid:** For each integration that uses a self-signed certificate, create the certificate independently in each org (sandbox, production, scratch org) and upload the org-specific public certificate to the relevant connected app in that org. Document this as a per-org setup step, not a deployable artifact. Consider switching to CA-signed certificates generated externally (Path 2) for integrations that must be portable, since the JKS file can be imported into any org.
