# Examples — Platform Encryption

## Example 1: Encrypting a Contact's SSN Custom Field (Display-Only, Probabilistic)

**Context:** A healthcare org stores a custom field `SSN__c` (Text, 9-char) on the Contact object to associate patients with their insurance records. The field is displayed to authorized users in a record page but is never used in SOQL filters, reports, or automation criteria.

**Problem:** With no encryption policy, SSN values are stored in plaintext in the Salesforce database tier. A database-level breach or a misconfigured data export could expose raw SSN values. The org must satisfy HIPAA data-at-rest requirements.

**Solution:**

1. In Setup, navigate to Platform Encryption > Encryption Policy.
2. Select the Contact object and locate `SSN__c`.
3. Choose **Probabilistic** as the encryption scheme.
4. Save the policy.
5. Verify the tenant secret is active under Platform Encryption > Key Management (generate one if not already present).
6. Navigate to Platform Encryption > Encryption Statistics to confirm new writes are being encrypted.
7. If existing Contact records already have SSN values, run the re-encryption job from Platform Encryption > Re-encrypt Data.

```text
Encryption Policy Setup Path:
  Setup > Platform Encryption > Encryption Policy
    Object: Contact
    Field:  SSN__c (Custom Text)
    Scheme: Probabilistic
```

**Why it works:** Probabilistic AES-256 encryption means every SSN value is stored as a unique ciphertext even if two patients have identical numbers. There is no way to recover the plaintext without the derived encryption key. Because `SSN__c` is never used in SOQL WHERE clauses, losing filter capability has no impact.

---

## Example 2: Encrypting Contact Email with Deterministic Encryption to Preserve Deduplication

**Context:** A financial services org encrypts the standard Contact `Email` field for PCI compliance. The marketing team runs SOQL queries to check for duplicate leads before campaign sends, and an integration flow uses `WHERE Email = :inboundEmail` to match inbound records.

**Problem:** If probabilistic encryption is applied to `Email`, the deduplication query `SELECT Id FROM Contact WHERE Email = 'user@example.com'` returns zero results even when a matching record exists, because each encrypted value is unique. Campaign sends generate duplicate contacts and the integration fails to match inbound records.

**Solution:**

1. In Setup, navigate to Platform Encryption > Encryption Policy.
2. Select the Contact object, locate the `Email` standard field.
3. Choose **Deterministic** as the encryption scheme.
4. Save the policy.
5. Update integration code and any Flows to use equality operators only — `=` and `!=` work; `LIKE` does not.

```apex
// This SOQL works correctly with deterministic encryption
List<Contact> matches = [
    SELECT Id, Name, Email
    FROM Contact
    WHERE Email = :inboundEmailValue
    LIMIT 1
];

// This SOQL will NOT work — LIKE is unsupported on encrypted fields
// List<Contact> bad = [SELECT Id FROM Contact WHERE Email LIKE '%@example.com%'];
```

**Why it works:** Deterministic encryption derives the initialization vector from the tenant secret and field metadata rather than a random nonce. The same plaintext email always produces the same ciphertext, so Salesforce can index and match the ciphertext directly. The query executes as an equality match on ciphertext at the database layer and returns the correct record.

---

## Example 3: BYOK Tenant Secret Upload

**Context:** A government contractor org must demonstrate that Salesforce cannot independently access encrypted data. The security team generates key material externally and uploads it to Salesforce as a customer-supplied tenant secret.

**Problem:** With Salesforce-managed tenant secrets, Salesforce staff with HSM access could theoretically derive the DEK. Regulatory requirements demand that key material originates outside Salesforce.

**Solution:**

1. Download the Salesforce RSA certificate from Setup > Platform Encryption > Key Management > Upload Customer-Supplied Key Material.
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
3. Paste the Base64-encoded wrapped key into the Salesforce upload form.
4. Salesforce verifies the wrapping and registers the customer-supplied key as the active tenant secret.
5. Store `key_material.bin` securely in your external KMS — Salesforce does not retain it.

**Why it works:** Salesforce uses the uploaded material as the tenant secret but never stores the unwrapped key material. The DEK derivation HMAC process runs inside the Salesforce HSM and derives a key that only works while the uploaded material is active. Destroying the tenant secret in Salesforce destroys all access to data encrypted under it.

---

## Anti-Pattern: Encrypting Fields Used in Sharing Rules or Automation Criteria

**What practitioners do:** An admin enables Shield encryption on a field used in criteria-based sharing rules (e.g., `Account.Industry__c` used to share accounts to industry-specific queues) without realizing the impact.

**What goes wrong:** Criteria-based sharing rules cannot evaluate encrypted field values. The sharing recalculation runs but no records are shared to the target group, silently breaking access. Users in the affected queue lose visibility into records without receiving any error.

**Correct approach:** Before enabling encryption on any field, audit all sharing rules, Flows, validation rules, and Process Builder criteria that reference that field. Remove the field from those criteria or redesign the sharing model to use non-encrypted fields as the sharing basis. Revisit any OWD or role hierarchy approach as an alternative if the field genuinely requires encryption.
