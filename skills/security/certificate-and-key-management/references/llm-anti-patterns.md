# LLM Anti-Patterns — Certificate and Key Management

Common mistakes AI coding assistants make when generating or advising on Salesforce Certificate and Key Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Directing Users to Named Credentials to Upload Certificates

**What the LLM generates:** "Go to Setup > Named Credentials and upload your certificate there to configure mTLS."

**Why it happens:** LLMs conflate certificate configuration with Named Credential configuration. Named Credentials reference certificates for authentication, but the certificate itself is managed separately under Certificate and Key Management. Training data from integration tutorials often skips the certificate setup step and jumps straight to Named Credentials.

**Correct pattern:**
```
Certificates are created and managed in Setup > Security > Certificate and Key Management.
Named Credentials reference these certificates in their authentication configuration.
For mTLS: first create or import the certificate in Certificate and Key Management,
then reference it in the Named Credential's "Client Certificate" field.
```

**Detection hint:** Look for instructions that say "upload certificate in Named Credentials" without mentioning "Certificate and Key Management." This is always wrong — Named Credentials do not have a certificate upload step; they have a certificate selection step.

---

## Anti-Pattern 2: Suggesting Metadata API or SFDX Deployment for Certificates

**What the LLM generates:** "Add `Certificate` to your `package.xml` and deploy with `sf project deploy start` to move the certificate from sandbox to production."

**Why it happens:** LLMs correctly know that Salesforce metadata deploys via `package.xml`, and the `Certificate` metadata type exists. They generalize that "deploy the metadata" handles certificates, not knowing that private keys are excluded from metadata retrieval and deployment.

**Correct pattern:**
```
Certificates with private keys (CA-signed imports) cannot be migrated via Metadata API.
Only the public certificate portion is retrievable. The private key is not exported.
For CA-signed certificates: manually import the original JKS file in each target org via
Setup > Certificate and Key Management > Import from Keystore.
For self-signed certificates: create a new certificate in each target org independently.
Document certificate migration as an out-of-band deployment step in your release runbook.
```

**Detection hint:** Any suggestion to include certificates in a standard CI/CD deploy pipeline without an explicit out-of-band manual step is suspect. Check for `<members>` entries under `<Certificate>` in `package.xml` recommendations combined with claims that this will fully migrate the integration.

---

## Anti-Pattern 3: Claiming the Private Key Can Be Exported or Retrieved Later

**What the LLM generates:** "You can export the private key later from Certificate and Key Management if you need to migrate it" or "Use the Download button to get the private key."

**Why it happens:** LLMs trained on general PKI and certificate management content learn that certificate stores (like Windows Certificate Store, macOS Keychain, or Java Keystores) typically allow key export. They incorrectly generalize this behavior to Salesforce.

**Correct pattern:**
```
Salesforce does not provide any mechanism to export a private key after import.
The "Download Certificate" button only downloads the public certificate (PEM format).
Private keys imported via JKS are stored internally and cannot be retrieved.
Always archive the original JKS, PKCS#12, and PEM files in a secure external vault
BEFORE importing into Salesforce. Treat the import as a one-way operation.
```

**Detection hint:** Any instruction that suggests the private key can be downloaded, exported, or retrieved from Salesforce after import is incorrect. Flag phrases like "you can always re-download the key" or "the keystore is accessible in Setup."

---

## Anti-Pattern 4: Telling Users to Upload PEM Files Directly for CA-Signed Certificates

**What the LLM generates:** "Upload your `.crt` and `.key` files directly in the Certificate and Key Management UI."

**Why it happens:** Many systems (nginx, Apache, AWS ACM) accept PEM files directly. LLMs trained on general TLS setup guides assume Salesforce's upload UI works similarly, without knowing that Salesforce requires JKS format for CA-signed imports that include a private key.

**Correct pattern:**
```
Salesforce's "Import from Keystore" UI requires JKS (Java KeyStore) format.
Raw PEM files (.crt, .key, .pem) cannot be uploaded directly for CA-signed imports.
Conversion steps:
1. Convert PEM cert + key to PKCS#12: openssl pkcs12 -export ...
2. Convert PKCS#12 to JKS: keytool -importkeystore -srcstoretype PKCS12 -deststoretype JKS ...
3. Upload the resulting .jks file via Setup > Certificate and Key Management > Import from Keystore.
Note: As of recent releases the UI may also accept PKCS#12 (.p12) directly — verify in your org.
```

**Detection hint:** Look for suggestions to upload `.pem`, `.crt`, or `.key` files through the Certificate and Key Management "Import from Keystore" dialog. These formats are not supported by the documented import path.

---

## Anti-Pattern 5: Treating Certificate Rotation as Instantaneous — Deleting Old Cert Immediately

**What the LLM generates:** "Create the new certificate, delete the old one, then update the connected app."

**Why it happens:** LLMs optimize for brevity and suggest the conceptually simplest sequence. They do not account for the sequencing risk: if the old certificate is deleted before the new one is confirmed working end-to-end in production, there is no rollback path and the integration is immediately broken.

**Correct pattern:**
```
Safe certificate rotation sequence:
1. Create the new certificate first (do not touch the old one yet).
2. Update all references (connected app, Named Credential, Apex code) to point to the new cert.
3. Coordinate with external systems if mTLS: they must trust the new cert before cutover.
4. Test end-to-end in sandbox, then production.
5. Monitor production for 24-48 hours after cutover.
6. Only then delete or archive the old certificate.
Never delete the old certificate before confirming the new one works in production.
```

**Detection hint:** Any rotation procedure that includes "delete the old certificate" as one of the first steps, or that does not include a production validation step before deletion, is following the unsafe pattern. The old certificate must remain in place until the new one is confirmed working.

---

## Anti-Pattern 6: Assuming Salesforce Notifies About Expiring Certificates

**What the LLM generates:** "Salesforce will send you an email notification before your certificate expires, so you'll have time to rotate it."

**Why it happens:** Many hosted services (AWS Certificate Manager, Let's Encrypt via Certbot, Google Cloud) send expiry notifications. LLMs assume Salesforce does the same, since this is the standard behavior in the broader cloud ecosystem.

**Correct pattern:**
```
Salesforce does NOT send certificate expiry notifications.
No email, in-app alert, or platform event is triggered as a certificate approaches expiry.
The first sign of an expired certificate is typically a broken integration.
Mitigation:
- Record expiry date in ops runbook immediately after certificate creation.
- Set calendar reminders at 60, 30, and 7 days before expiry.
- Consider a scheduled Apex job or external monitoring tool that tests integration health
  (e.g., a JWT token request) and alerts on failure.
```

**Detection hint:** Any response claiming Salesforce will proactively notify about certificate expiry is incorrect. Flag phrases like "you'll receive an alert," "Salesforce notifies you," or "there's a warning before it expires."

---

## Anti-Pattern: Claiming Salesforce Sends No Certificate Expiry Notifications

**What the LLM generates:** "Set a calendar reminder for the certificate's expiry date — Salesforce does not send expiry notifications for certificates." Variants: "there is no built-in alerting for certificate expiration, so build a scheduled Apex job / external monitor."

**Why it happens:** The advice pattern "the platform won't tell you, so track it yourself" is a genuine and very common shape in Salesforce guidance — it is true for many things — and the model applies it as a default when it does not recall a specific notification mechanism. The confident negative is more useful-sounding than "I'm not sure," so it wins.

**Why a false negative is worse than a false positive here:** it teaches a team to distrust a channel that is already working. Certificate-expiry emails then get treated as noise, filtered, or left pointed at a departed admin's address, and the manual calendar entry becomes the only control — one that survives exactly as long as the person who created it. The outage that follows is an integration-wide auth failure with no warning, caused by turning off an alarm that was ringing.

**Correct pattern:**
```
Salesforce DOES email certificate-expiration warnings, at:
    60 days before expiry
    30 days before expiry
    10 days before expiry
    the day of expiry

Configure the recipients: Setup > Certificate and Key Management >
"Set Expired Certificate Notification Permission".

The real work is not building an alerting mechanism — it is verifying the
existing one points at a monitored, role-based inbox rather than an individual,
and that someone owns the response. Add a calendar reminder on top if you like;
do not present it as a workaround for a missing feature.
```

**Detection hint:** any sentence asserting Salesforce does *not* notify on certificate expiry. Mechanically, a proposal to build scheduled Apex or an external cron purely to detect certificate expiry is the tell — the requirement is already met, and the review question should be "who receives the existing notification?" rather than "how do we build one?"

---

## Anti-Pattern: Inventing a Configurable Validity Period for Self-Signed Certificates

**What the LLM generates:** "Default validity is 1 year from creation. Custom validity (up to 10 years) can be set at creation time using the *Expiration* field." Variants: a `validityPeriod` or `expiryDate` parameter, "choose between 1, 2, 5 or 10 years."

**Why it happens:** Nearly every other tool that issues self-signed certificates — `openssl req -days`, `keytool -validity`, most cloud KMS UIs — takes an explicit validity argument, so the model assumes Salesforce's screen has one and supplies a plausible field name and ceiling. The "1 year default" half is right, which lends the invented half credibility.

**Why it matters:** rotation plans are built on this number. A team that believes it issued a 10-year certificate schedules no rotation and no successor, and the integration fails at the 1- or 2-year mark with the original engineer long gone.

**Correct pattern:**
```
Self-signed certificate validity is DERIVED FROM KEY SIZE and cannot be set:

    2048-bit  ->  1 year
    3072-bit  ->  1 year
    4096-bit  ->  2 years   (recommended for Shield Platform Encryption)

There is no "Expiration" field on the creation screen. Two years is the
maximum obtainable from a Salesforce self-signed certificate. If a longer
lifetime is genuinely required, use a CA-signed certificate — and check
current CA maximums, because industry certificate lifespans are shortening.
```

**Detection hint:** any self-signed-certificate validity longer than 2 years is wrong. So is any reference to an `Expiration` / `validityPeriod` / `expiryDate` input on the Salesforce creation screen. Positive tell of a correct answer: the validity is stated *as a consequence of* the key size rather than as an independent choice.
