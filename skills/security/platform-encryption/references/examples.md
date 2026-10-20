# Examples — Platform Encryption

UNVERIFIED (2026-10-20): the Setup menu paths in these examples other than the Key Management and Encryption Policy pages (platform_events 264 L5732-5733), and the `openssl` commands in Example 3, are not in the corpus — confirm them against current Help before use.

## Example 1: Encrypting a Contact's SSN Custom Field (Display-Only, Probabilistic)

**Context:** A healthcare org stores a custom field `SSN__c` (Text, 9-char) on the Contact object to associate patients with their insurance records. The field is displayed to authorized users in a record page but is never used in SOQL filters, reports, or automation criteria.

**Problem:** With no encryption policy, SSN values are stored in plaintext in the Salesforce database tier. A database-level breach or a misconfigured data export could expose raw SSN values. The org must satisfy HIPAA data-at-rest requirements.

**Solution:**

1. In Setup, navigate to Platform Encryption > Encryption Policy.
2. Select the Contact object and locate `SSN__c`.
3. Choose **Probabilistic** as the encryption scheme.
4. Save the policy.
5. Verify a tenant secret is `Active` on the Key Management page (generate one if not already present; obj 264 L283777-283778).
6. Confirm the background encryption process has covered the existing `SSN__c` values (api_meta 264 L127877-127882; secguide 262 L4899-4902).
7. If `SSN__c` is history-tracked, decide `enableEncryptFieldHistory` and whether archived `FieldHistoryArchive` rows need Salesforce to re-archive them (secguide 262 L4903-4904).

```text
Encryption Policy Setup Path:
  Setup > Platform Encryption > Encryption Policy
    Object: Contact
    Field:  SSN__c (Custom Text)
    Scheme: Probabilistic
```

**Why it works:** Probabilistic encryption stores every SSN value as a unique ciphertext even if two patients have identical numbers (UNVERIFIED (2026-10-20): the cipher, AES-256, is Help-only). Because `SSN__c` is never used in SOQL WHERE clauses, losing filter capability has no impact.

---

## Example 2: Encrypting Contact Email with Deterministic Encryption to Preserve Deduplication

**Context:** A financial services org encrypts the standard Contact `Email` field for PCI compliance. The marketing team runs SOQL queries to check for duplicate leads before campaign sends, and an integration flow uses `WHERE Email = :inboundEmail` to match inbound records.

**Problem:** If probabilistic encryption is applied to `Email`, the deduplication query `SELECT Id FROM Contact WHERE Email = 'user@example.com'` returns zero results even when a matching record exists, because each encrypted value is unique. Campaign sends generate duplicate contacts and the integration fails to match inbound records.

**Solution:**

1. In Setup, navigate to Platform Encryption > Encryption Policy.
2. Select the Contact object, locate the `Email` standard field.
3. Choose case-insensitive **Deterministic** as the scheme (`CaseInsensitiveDeterministicEncryption`, api_meta 264 L45625), since email addresses are compared without regard to case.
4. Save the policy.
5. Update integration code and any Flows to use equality operators only — equals and not equals are the documented operators (api_meta 264 L33328-33329); UNVERIFIED (2026-10-20): that `LIKE` fails is Help-only.

```apex
// This SOQL works correctly with deterministic encryption
List<Contact> matches = [
    SELECT Id, Name, Email
    FROM Contact
    WHERE Email = :inboundEmailValue
    LIMIT 1
];

// Expect this SOQL to fail — LIKE is not a documented operator on encrypted fields (UNVERIFIED (2026-10-20): Help-only; test it)
// List<Contact> bad = [SELECT Id FROM Contact WHERE Email LIKE '%@example.com%'];
```

**Why it works:** Deterministic encryption always produces the same ciphertext for the same plaintext, and it is the scheme that "lets customers filter on encrypted data" (api_meta 264 L127865-127866), so the equality match returns the record. UNVERIFIED (2026-10-20): the IV derivation from the tenant secret and field metadata is Help-only.

---

## Example 3: BYOK Tenant Secret Upload

**Context:** A government contractor org must demonstrate that Salesforce cannot independently access encrypted data. The security team generates key material externally and uploads it to Salesforce as a customer-supplied tenant secret.

**Problem:** Regulatory requirements demand that key material originates outside Salesforce (`Source = Uploaded`, obj 264 L283762-283763) rather than being Salesforce-generated (`HSM`, L283749-283750).

**Solution:**

1. Create a BYOK-compatible certificate in Salesforce and export its public part (obj 264 L283874-283875).
2. In your external KMS (e.g., AWS KMS CLI):
   ```bash
   # Generate 256-bit AES key material
   openssl rand -out key_material.bin 32

   # Wrap with Salesforce RSA certificate
   openssl rsautl -encrypt -oaep -pubin \
     -inkey salesforce_cert.pem \
     -in key_material.bin \
     -out wrapped_key.bin

   # Base64-encode for upload
   base64 wrapped_key.bin > wrapped_key_b64.txt
   ```
3. Upload the wrapped key with its hash and the certificate's unique name — `SecretValue`, `SecretValueHash`, `SecretValueCertificate` (obj 264 L283876-283888).
4. Confirm the new secret is `Active`; the previous one becomes `Archived` and still decrypts old data (L283777-283781).
5. Keep `key_material.bin` in your external KMS — it is what you re-import if the secret is ever destroyed (L283928-283929).

**Why it works:** The uploaded material becomes the tenant secret, and `KeyDerivationMode` decides whether the data encryption key is derived from it (`PBKDF2`) or is the material itself (`NONE`) (obj 264 L283676-283682). Setting it to `Destroyed` stops all decryption (L283782-283785) — unless you exported the key earlier and import it back (L283928-283929). UNVERIFIED (2026-10-20): "Salesforce never stores the unwrapped material" and an HSM-resident HMAC derivation are Help-only.

---

## Anti-Pattern: Encrypting Fields Used in Sharing Rules or Automation Criteria

**What practitioners do:** An admin enables Shield encryption on a field used in criteria-based sharing rules (e.g., `Account.Industry__c` used to share accounts to industry-specific queues) without realizing the impact.

**What goes wrong:** "In criteria-based sharing rules, you can't use lookup fields, encrypted fields, formula fields" (secguide 262 L3478-3479), so the rule's criterion no longer works once the field is encrypted. UNVERIFIED (2026-10-20): whether an existing rule is blocked at enablement or silently stops sharing is not in the corpus.

**Correct approach:** Before enabling encryption on any field, audit all sharing rules, Flows, validation rules, and Process Builder criteria that reference that field. Remove the field from those criteria or redesign the sharing model to use non-encrypted fields as the sharing basis. Revisit any OWD or role hierarchy approach as an alternative if the field genuinely requires encryption.
