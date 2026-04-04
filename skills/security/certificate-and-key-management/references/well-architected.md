# Well-Architected Notes — Certificate and Key Management

## Relevant Pillars

- **Security** — Certificate and key management is a foundational security control. Proper certificate lifecycle management (creation, rotation, expiry tracking, key protection) directly determines whether identity-based integrations remain trustworthy. mTLS provides mutual authentication that eliminates credential-sharing anti-patterns. Non-exportable private keys in Salesforce enforce a "keys never leave the platform" boundary for self-signed use cases, while CA-signed key management demands secure external key storage practices.
- **Reliability** — Certificate expiry is a leading cause of silent integration failures. A certificate that expires overnight can take down a batch job, an OAuth flow, or an mTLS connection with no warning. Reliability requires proactive expiry tracking, rotation runbooks, and validation procedures that are exercised before the certificate expires rather than after.
- **Operational Excellence** — Certificate management must be documented as an explicit out-of-band deployment step. Practitioners who assume certificates deploy automatically via Metadata API create brittle release processes. A mature operation treats certificate rotation as a first-class change event with its own runbook, rollback plan, and post-cutover monitoring window.

## Architectural Tradeoffs

**Self-signed vs CA-signed:** Self-signed certificates generated in Salesforce are simpler (no CA dependency, no key management overhead) but are org-bound and not trusted by external systems without explicit configuration. CA-signed certificates are portable (the JKS can be imported to any org) and trusted by external API gateways out of the box, but they introduce private key management responsibility — the JKS must be stored securely, backed up, and rotated on a schedule aligned with the CA's issuance period. For JWT-only OAuth flows where Salesforce holds the private key, self-signed is the recommended and simpler path. For mTLS with external enterprise systems, CA-signed is typically required.

**Key control vs operational simplicity:** Salesforce-managed self-signed certificate private keys never leave the platform — this is a security benefit. But it also means zero portability. Teams must weigh whether the integration is long-lived (favoring CA-signed with external key storage for portability) vs short-lived or test-only (favoring self-signed for simplicity).

**Certificate rotation cadence:** Shorter certificate lifetimes reduce exposure if a key is compromised but increase operational overhead for rotation. A 1-year default for self-signed certificates is a reasonable balance for most integrations, provided expiry tracking is implemented. For high-security environments, consider a 6-month or 90-day rotation schedule aligned with the Let's Encrypt or CA/Browser Forum recommendations.

## Anti-Patterns

1. **Assuming certificates deploy with the rest of the metadata package** — Teams that include `Certificate` in `package.xml` and assume the full certificate (including private key) will deploy to production will have broken integrations after release. Certificates must be manually re-imported in each target org. Document this as an explicit out-of-band release step.

2. **Deleting the old certificate immediately after creating the new one** — When rotating a certificate, deleting the old certificate before confirming the new one works in production risks a complete integration outage if the cutover has any issue. Always run both certificates in parallel (old still valid, new being tested) until end-to-end production validation is complete, then remove the old certificate.

3. **Not retaining the JKS source file before importing a CA-signed certificate** — Once a private key is imported into Salesforce, it cannot be retrieved. If the JKS is lost, the certificate is unrecoverable. Teams that import JKS files without archiving them first create an unrecoverable dependency on Salesforce's internal storage.

## Official Sources Used

- Salesforce Help: About Salesforce Certificates and Keys — https://help.salesforce.com/s/articleView?id=sf.security_keys_about.htm&type=5
- Salesforce Help: Generate a Certificate Signed by a Certificate Authority — https://help.salesforce.com/s/articleView?id=sf.security_keys_creating_ca.htm&type=5
- Salesforce Help: Import from a Keystore — https://help.salesforce.com/s/articleView?id=sf.security_keys_importing.htm&type=5
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide: Certificate Metadata Type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_certificate.htm
