---
name: platform-encryption
description: "Use this skill when deciding which Salesforce fields to encrypt at rest, choosing between deterministic and probabilistic schemes, managing tenant secrets and keys (including BYOK and Cache-Only Keys), and satisfying compliance mandates for data-at-rest encryption. NOT for TLS/transport encryption, Classic Encrypted Text fields, or field masking without Shield. Trigger keywords: Shield Platform Encryption, data at rest, AES-256, tenant secret, BYOK, key rotation, encrypted search."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "we need to encrypt sensitive PII fields like SSN or credit card numbers at rest in Salesforce"
  - "our compliance team requires data-at-rest encryption for HIPAA or PCI — what do we enable in Salesforce"
  - "encrypted field can't be searched or filtered in SOQL — how do we fix this without removing encryption"
  - "how do I rotate tenant secrets or bring our own encryption key to Salesforce Shield"
  - "what fields cannot be encrypted with Shield Platform Encryption and why"
tags:
  - shield
  - encryption
  - security
  - compliance
  - key-management
  - data-at-rest
inputs:
  - List of fields (standard or custom) that must be encrypted and their data types
  - Compliance mandate (HIPAA, PCI-DSS, GDPR, etc.) driving the encryption requirement
  - Whether the fields need to be searchable or filterable after encryption
  - Shield Platform Encryption license status for the org
  - "Key management preference: Salesforce-managed, BYOK, or Cache-Only Keys"
outputs:
  - Field encryption scheme recommendation (probabilistic vs deterministic per field)
  - Key management strategy and rotation plan
  - List of fields that cannot be encrypted with rationale
  - Search/filter impact assessment and mitigation approach
  - Review checklist for Shield rollout
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Platform Encryption

This skill activates when an org needs to encrypt Salesforce field data at rest using Shield Platform Encryption. It covers encryption scheme selection, field eligibility, key management (including BYOK and Cache-Only Keys), the impact on search and reporting, and rollout considerations. It does NOT address TLS/transport security, Classic Encrypted Text fields, or Salesforce org-wide field masking.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has a Shield Platform Encryption license (add-on to Enterprise, Performance, or Unlimited Edition). Developer Edition orgs get it at no cost for testing.
- Identify which specific fields need encryption and whether any must remain searchable or filterable after encryption — this is the single biggest architectural decision.
- Determine the key management model: Salesforce-managed tenant secrets (default), Bring Your Own Key (BYOK), or Cache-Only Keys (key never persisted in Salesforce storage).
- Understand that enabling encryption on a field is applied immediately to new data written, but existing data must be re-encrypted separately using the re-encryption process.

---

## Core Concepts

### Encryption Schemes: Probabilistic vs Deterministic

Shield Platform Encryption offers two schemes:

**Probabilistic encryption** (default): Uses AES-256 with a random initialization vector per value. Every encrypted value is unique, even if the underlying plaintext is identical. This provides the strongest confidentiality guarantee but makes SOQL filtering, WHERE clauses, ORDER BY, GROUP BY, and full-text search (SOSL) impossible on encrypted values. Reports that filter on probabilistically encrypted fields will not return correct results.

**Deterministic encryption**: Uses AES-256 with a fixed, field-specific initialization vector derived from the tenant secret. The same plaintext always produces the same ciphertext, which means Salesforce can support equality-based SOQL filters (`=`, `!=`, `IN`, `NOT IN`) and case-insensitive matching. LIKE/wildcard searches and range comparisons are still not supported. Deterministic encryption is slightly weaker than probabilistic because identical values produce identical ciphertext (leaking that two records share the same value), but it is the correct choice for any field that must remain filterable.

Choose probabilistic for fields that are never searched or filtered (e.g., a stored SSN that is only displayed). Choose deterministic for fields used in lookup matching, deduplication, or any SOQL filter.

### Tenant Secrets and Key Derivation

Salesforce does not store the raw AES-256 data encryption key (DEK). Instead, it derives the DEK from an org-specific **tenant secret** combined with a Salesforce master secret using HMAC-SHA256 in an HSM. The derived DEK is used to encrypt field values and is never persisted to disk.

Key management options:
- **Salesforce-managed tenant secrets** (default): Salesforce generates and manages the tenant secret material. You can rotate tenant secrets from Setup > Platform Encryption > Key Management.
- **Bring Your Own Key (BYOK)**: You generate a 256-bit AES key material value outside Salesforce, wrap it with a Salesforce-provided RSA public certificate, and upload it. Salesforce uses your key material as the tenant secret. You retain control of the underlying key.
- **Cache-Only Keys**: The key material is hosted by an external key service (e.g., AWS KMS, Azure Key Vault). Salesforce fetches the key at runtime via a callout and never persists it. If the external key service is unavailable, encrypted data cannot be decrypted — this is a critical availability tradeoff.

### Key Rotation and Re-Encryption

Rotating a tenant secret generates a new secret but does **not** automatically re-encrypt existing data. Previously encrypted data can still be decrypted because Salesforce retains the archived tenant secret. To re-encrypt existing data with the new secret, you must explicitly initiate a re-encryption process. Re-encryption is an asynchronous background job and can affect platform performance during execution.

Destroying a tenant secret permanently destroys access to all data encrypted with it. This is irreversible. Only use key destruction for deliberate data-destruction workflows (e.g., right-to-be-forgotten GDPR requests).

### Field Eligibility

**Fields that CAN be encrypted:**
- Custom fields of type: Text, Long Text Area, Text Area, Phone, URL, Email, Date, Date/Time, Number (limited), Checkbox
- Selected standard fields: Contact and Lead Email, Phone, Mobile, Home Phone, Fax; Account Phone, Fax; Case Subject, Description; and others listed in the official Standard Fields reference

**Fields that CANNOT be encrypted:**
- Formula fields (calculated at read time — encryption cannot be applied)
- Lookup relationship fields and external lookup fields
- Auto-Number fields, Roll-Up Summary fields
- Fields used in unique validation or duplicate-matching rules (in some configurations)
- Fields encrypted with Classic Encrypted Text (separate feature — not Shield)
- Required fields on certain objects where platform-internal processes depend on the plaintext value
- Fields used in criteria-based sharing rules

Enabling encryption on the Name field of an object automatically switches lookups to enhanced lookups, which only searches recently accessed records rather than all records. This is a one-way, irreversible change.

---

## Common Patterns

### Pattern 1: Encrypting PII Fields for HIPAA Compliance

**When to use:** An org stores Protected Health Information (PHI) such as patient names, dates of service, or social security numbers in custom or standard fields and must satisfy HIPAA data-at-rest requirements.

**How it works:**
1. Audit all fields containing PHI. Classify each as "needs search" vs "display-only."
2. For display-only fields (SSN, full date of birth): assign probabilistic encryption. These will no longer be filterable in SOQL — update any integration queries to fetch by record ID instead.
3. For fields used in patient matching or lookup (e.g., Email, Phone): assign deterministic encryption so equality SOQL filters still work.
4. Generate or upload a tenant secret in Setup > Platform Encryption > Key Management.
5. Enable encryption for each field in Setup > Platform Encryption > Encryption Policy.
6. Verify all integration users and connected apps have the View Encrypted Data permission or a field-level decrypt permission granted.
7. Run the re-encryption job if existing data must be encrypted retroactively.

**Why not probabilistic for all fields:** Audit logs, deduplication workflows, and many integrations depend on being able to query by Email or Phone. Using probabilistic on those fields would require full table scans or application-side decryption, neither of which is scalable.

### Pattern 2: Bring Your Own Key for Regulatory Key Control

**When to use:** A financial services or government org must demonstrate that Salesforce cannot independently access encrypted data without the customer's involvement, for regulatory reasons such as FedRAMP or internal security policy.

**How it works:**
1. In your external key management system (e.g., AWS KMS or an HSM), generate a 256-bit AES key material value.
2. Download the Salesforce-provided RSA certificate from Setup > Platform Encryption > Key Management.
3. Wrap (encrypt) your key material with the RSA certificate and upload the wrapped value to Salesforce as a customer-supplied key material tenant secret.
4. Salesforce uses your uploaded material as the tenant secret. The DEK derivation uses this material — without it, Salesforce cannot decrypt data.
5. Rotate the customer-supplied material on your defined schedule (quarterly or annually). Upload the new wrapped material as a new tenant secret version.
6. Initiate re-encryption to apply the new key to existing records.

**Why not Cache-Only Keys for all scenarios:** Cache-Only Keys provide the strongest key separation guarantee but introduce an availability dependency. If your external key service has an outage, users cannot read encrypted records. BYOK retains key control without introducing a real-time availability dependency.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Field must be filterable in SOQL (Email, Phone used in lookup) | Deterministic encryption | Equality SOQL filters work; slight confidentiality tradeoff is acceptable |
| Field is display-only, never filtered (SSN, full account number) | Probabilistic encryption | Maximum confidentiality; no search capability needed |
| Must prove Salesforce cannot independently decrypt data | BYOK or Cache-Only Keys | Customer controls key material |
| Need instant key revocation with no availability risk | BYOK with manual destruction | Key destruction in Salesforce is immediate; no runtime callout dependency |
| Need real-time key revocation with zero Salesforce key persistence | Cache-Only Keys | Key never stored in Salesforce; revoking external key immediately stops decryption |
| Name field on a custom object needs encryption | Probabilistic or deterministic, but plan for enhanced lookups | Enabling encryption on Name field triggers irreversible switch to enhanced lookups |
| Formula field value needs to be confidential | Do not encrypt; use a non-formula field or restrict access via FLS | Formula fields cannot be encrypted |
| Existing data must be encrypted | Run re-encryption job after enabling policy | New writes are encrypted immediately; old data requires explicit re-encryption |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking encryption rollout complete:

- [ ] Shield Platform Encryption license is provisioned and active in the target org
- [ ] All fields requiring encryption are classified as probabilistic (display-only) or deterministic (filterable)
- [ ] Formula fields, lookup fields, and roll-up summaries are excluded from the encryption policy
- [ ] Tenant secret has been generated or customer key material has been uploaded and verified
- [ ] View Encrypted Data permission is granted to all users and integration profiles that need plaintext access
- [ ] All SOQL queries filtering on newly encrypted fields are tested — probabilistic fields must be removed from WHERE clauses
- [ ] Report and dashboard filters on encrypted fields are reviewed and updated
- [ ] Flows and Process Builder criteria that reference encrypted fields are audited (automation cannot filter on encrypted values)
- [ ] Re-encryption job has been run and completed for existing data if required
- [ ] Key rotation schedule and re-encryption runbook are documented
- [ ] Test in a sandbox or Developer Edition org before enabling in production

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Probabilistic encryption silently breaks SOQL filters** — Queries with WHERE conditions on probabilistically encrypted fields return zero results rather than an error. This can silently corrupt reports, list views, and integration queries without throwing an exception. Audit all SOQL usages before enabling encryption.

2. **Re-encryption is required for existing data but is not automatic** — Enabling an encryption policy encrypts only new writes going forward. Records written before the policy was enabled remain unencrypted until an explicit re-encryption job completes. Many teams assume enabling the policy retroactively encrypts all data.

3. **Encrypting the Name field triggers irreversible enhanced lookups** — If you encrypt the Name field on a standard or custom object, Salesforce automatically enables enhanced lookups, which only searches recently accessed records. This cannot be undone and may confuse users who expect full-table name search.

4. **Cache-Only Key outages make encrypted data completely unreadable** — If the external key service is unreachable at read time, Salesforce cannot decrypt values and users receive errors. Ensure the external key service has an SLA equal to or stronger than your Salesforce SLA before choosing Cache-Only Keys.

5. **Deterministic encryption still blocks LIKE, range, and SOSL** — Deterministic encryption enables equality SOQL operators only. Wildcard searches (`LIKE '%smith%'`), range filters (`> date`), and SOSL full-text search do not work on deterministically encrypted fields. Teams that need partial-match search on encrypted fields have no good option short of application-layer decryption.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Field encryption scheme matrix | Table mapping each target field to its encryption scheme (probabilistic/deterministic) with justification |
| Key management decision record | Documents chosen key model (Salesforce-managed, BYOK, Cache-Only), rotation schedule, and responsible owner |
| SOQL impact assessment | List of queries, reports, and automations affected by encryption with required changes |
| Re-encryption runbook | Step-by-step procedure for running the background re-encryption job and verifying completion |

---

## Related Skills

- data-quality-and-governance — overlaps when Shield encryption affects deduplication workflows or SOQL-based data quality checks
- custom-field-creation — Classic Encrypted Text vs Shield Platform Encryption field type selection decision
