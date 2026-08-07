# Gotchas — Platform Encryption

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Probabilistic Encryption Silently Returns Zero Results in SOQL Filters

**What happens:** When a field is encrypted with probabilistic encryption, any SOQL WHERE clause that filters on that field returns zero rows — not an error. Because each encrypted value uses a random initialization vector, no two ciphertexts ever match, even when the underlying plaintext values are identical. Salesforce does not throw an exception; the query simply returns an empty result set.

**When it occurs:** Immediately after enabling probabilistic encryption on a field. Existing queries in Apex classes, Flows, integrations, list views, and reports that use that field in a filter condition will silently stop returning data. This is particularly dangerous in integration middleware where an empty result set is treated as "no match found," potentially triggering duplicate record creation.

**How to avoid:** Before enabling encryption on any field, use the Platform Encryption Analyzer (Setup > Platform Encryption Analyzer) to identify which SOQL queries, reports, Flows, and automations reference the field in a filter. Update each to either remove the filter (if the field is display-only) or switch to deterministic encryption (if equality filtering is required). Never enable probabilistic encryption on a field used in a WHERE clause without first resolving all query dependencies.

---

## Gotcha 2: Re-Encryption Does Not Happen Automatically — Existing Data Stays Unencrypted Until You Run the Job

**What happens:** Enabling a Shield encryption policy encrypts only data written after the policy is activated. Records that already existed in the org remain stored in plaintext. Many teams enable the policy, perform a compliance audit, and declare success — but historical data is still unencrypted at the database tier.

**When it occurs:** Any time an org retroactively enables encryption on a field that already contains data. This is the common case for production orgs adding Shield after go-live. The gap between "policy enabled" and "all data encrypted" can last days or weeks if the re-encryption job is not explicitly triggered.

**How to avoid:** After enabling the encryption policy, navigate to Setup > Platform Encryption > Re-encrypt Data and initiate the re-encryption job for each affected object. Monitor the job status under Encryption Statistics. Be aware that re-encryption is an asynchronous background process and may take significant time on large data volumes (millions of records). Schedule re-encryption during off-peak hours. Include re-encryption completion verification as a mandatory step in any Shield rollout checklist.

---

## Gotcha 3: Encrypting the Name Field Irreversibly Enables Enhanced Lookups

**What happens:** When Shield encryption is enabled on the Name field of any object (standard or custom), Salesforce automatically and permanently enables enhanced lookups for that object. Enhanced lookups restrict the lookup search to recently accessed records rather than all records in the org. Users who previously used the lookup dialog to search the full record set will now only see recently accessed records, making it difficult to look up records they haven't accessed before.

**When it occurs:** At the moment encryption is enabled on a Name field. The switch is triggered by the platform when it detects the field being encrypted. It cannot be reversed, even if encryption is later removed from the field.

**How to avoid:** Carefully evaluate whether encrypting the Name field is truly necessary. In most compliance frameworks, the Name field is lower-risk than fields like SSN, Email, or financial identifiers. If Name encryption is mandatory, communicate the enhanced lookup change to users before rollout and provide alternative search pathways (e.g., global search, custom search components) for records that are not recently accessed.

---

## Gotcha 4: Deterministic Encryption Does Not Support LIKE, Range Queries, or SOSL

**What happens:** Teams choose deterministic encryption specifically because they need to keep a field searchable, then discover that only exact equality operators work. SOQL LIKE patterns (e.g., `WHERE LastName LIKE '%son%'`), range operators (`>`, `<`, `>=`, `<=`), ORDER BY, and all SOSL full-text search remain non-functional on deterministically encrypted fields. The field is "searchable" only in the narrow sense of exact-match equality.

**When it occurs:** Any time a user-facing feature or integration depends on partial-text search, autocomplete, or sorted queries on an encrypted field. A common example: an org encrypts Contact.Email with deterministic encryption to preserve integration matching, then discovers that the org-wide search bar no longer surfaces contacts by email, and the autocomplete in the email field on the New Email record page stops working.

**How to avoid:** Before choosing deterministic encryption, document all search behaviors associated with the field: exact match, partial match, global search, list view sorting, report sorting. Accept that only exact-match SOQL (= and IN) will work. For fields where partial-match search is a hard requirement, re-evaluate whether encryption is truly necessary or whether field-level security (FLS) combined with org-level access controls satisfies the compliance requirement.

---

## Gotcha 5: Cache-Only Keys Create a Hard Runtime Dependency on External Key Service Availability

**What happens:** Cache-Only Keys give the strongest key separation guarantee — the key material never persists in Salesforce storage. However, every decryption operation requires a live callout to the external key service. If that service experiences an outage, returns an error, or is intentionally shut down, every read of an encrypted field fails with a decryption error. Users see error messages on record pages; Apex triggers that read encrypted fields throw exceptions; integrations fail.

**When it occurs:** During any external key service downtime, network partition, or misconfigured key service URL. Also occurs after deliberate key revocation — which is a feature, not a bug, for right-to-be-forgotten workflows.

**How to avoid:** Only use Cache-Only Keys when the org has a contractual requirement for immediate key revocation capability or when the external key service has an SLA and availability guarantee that equals or exceeds the Salesforce org's SLA. Implement robust monitoring and alerting on the external key service. Document the operational runbook for key service outages, including who can restore service and how long users can expect degraded access. For most compliance use cases, BYOK provides sufficient key control without the runtime availability dependency.

---

## Gotcha 6: Shield Encryption Grants No Access Control At All — Everyone With FLS Still Sees Plaintext

**What happens:** A team encrypts SSN, then tells the auditor that "only privileged users can see it." Nobody's visibility changed. Shield Platform Encryption is transparent above the storage layer: any user who could read the field before encryption reads exactly the same plaintext after it. There is no masked (`*******`) rendering and no separate decrypt permission — Salesforce removed the need for a "View Encrypted Data" permission with Shield beginning Spring '17 (KB 000382508). That permission belongs to legacy Classic Encryption (the *Encrypted Text* custom field type), which is a different feature.

**When it occurs:** At the compliance review after go-live, or worse, at the breach. The rollout "succeeded" — the Encryption Statistics page shows every record encrypted — so nothing signals that the intended need-to-know restriction was never implemented.

**How to avoid:** Treat encryption and access control as two separate workstreams. Shield protects data at rest (a stolen database file, a physical media disposal path); field-level security protects it from users. Before go-live, run the FLS matrix for every encrypted field and remove Read from every profile and permission set that does not need plaintext — that is the only lever that changes who sees the value. If a design document says "grant View Encrypted Data to X," it was written against Classic Encryption and the access model in it does not apply. Setting *up* Shield needs **Customize Application** plus **Manage Encryption Keys**; those govern administration, not read access.
