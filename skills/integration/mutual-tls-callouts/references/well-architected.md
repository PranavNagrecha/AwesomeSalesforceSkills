# Well-Architected Notes — Mutual TLS Callouts

**Security:** the key pair is generated inside the platform, and the Metadata API doesn't import or export private keys — but `privateKeyExportable` defaults to true, so the strongest control is procedural: create the certificate in Setup with export off and send out only the CSR. Any workflow that produces a key file on someone's machine, or a PKCS12 blob in Apex, has already lost the property that makes this design safe. Binding the certificate on a Named Credential keeps certificate names and secrets out of code.

**Reliability:** an mTLS callout gives no gradual degradation signal; it works until it does not. That requires two independent monitors — a long-lead expiry check sized to the partner's signing turnaround (read from the certificate's `expirationDate` in source), and a probe callout that catches revocation, chain changes, and configuration edits, none of which move the expiry date. Scheduled Apex can't make synchronous callouts, so the probe runs in a Queueable that allows callouts.

## Official Sources Used

Corpus: Summer '26 (API 67.0) PDFs; line numbers are `grep -n` positions in the `pdftotext -layout` text.

- Apex Developer Guide (`salesforce_apex_developer_guide.txt`) L35767–35784 — two-way SSL with a Salesforce-generated or CA-signed certificate; share a self-signed certificate with the partner's keystore; Remote Site Setting unless the endpoint is a Named Credential (SKILL.md Core Concepts, anti-pattern 1).
- Apex Developer Guide L35790–35791 — a key pair can also be imported from a keystore (gotcha 1).
- Apex Developer Guide L35795–35837 — generating certificates, SOAP `clientCertName_x`, HTTP `setClientCertificateName('DocSampleCert')` (Decision Guidance).
- Apex Reference Guide (`salesforce_apex_reference_guide.txt`) L216559–216587 — `setClientCertificate(clientCert, password)` deprecated; `setClientCertificateName(certDevName)` (gotcha 3, checker).
- Apex Reference Guide L216720–216722 and Apex Developer Guide L35854 — `setTimeout` 1–120,000 ms, connection set-up semantics, 10-second default (gotcha 7).
- Apex Developer Guide L16975 — synchronous callouts aren't supported from scheduled Apex; use Queueable (examples.md Example 2).
- Metadata API Developer Guide (`api_meta.txt`) L32818–32900 — `Certificate`: `.crt` in `certs/`, `expirationDate` (1 / 2 years for 2048 / 4096-bit self-signed; CA-signed from the uploaded chain), `privateKeyExportable` default true, no private-key import/export via the API, chain update (gotchas 1, 2, 4, 6, checker).
- Metadata API Developer Guide L90011–90015 and L90255–90410 — legacy `certificate` field deprecated in API 56.0; `NamedCredentialParameter` `ClientCertificate` type and the sample definition (SKILL.md XML fence, gotcha 3).
- Metadata API Developer Guide L80783–80849 — `InboundCertificate` for inbound mutual authentication, MutualAuthentication permission (gotcha 5).
