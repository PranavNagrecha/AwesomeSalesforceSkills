# Gotchas — Platform Encryption

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Probabilistic Encryption Removes Filtering — Find Every Filter First

**What happens:** Deterministic is the scheme that "lets customers filter on encrypted data" (api_meta 264 L127865-127866), so a filter on a probabilistically encrypted field stops working. Each probabilistic ciphertext is unique, so no two ever match. UNVERIFIED (2026-10-20): whether the query then returns zero rows or raises an error is not in the corpus; plan for either and test both in a sandbox.

**When it occurs:** Immediately after enabling probabilistic encryption on a field. Apex classes, Flows, integrations, list views, and reports that filter on that field all change behaviour. In integration middleware an empty result is often read as "no match found", which can trigger duplicate record creation.

**How to avoid:** Before enabling encryption on any field, list every query, report, Flow, and automation that filters on it. Update each to either remove the filter (if the field is display-only) or switch the field to a deterministic scheme (if equality filtering is required).

---

## Gotcha 2: Existing Data, History Duplicates and Archived History Are Three Different Cases

**What happens:** Teams assume one of two wrong things — that only new writes get encrypted, or that everything including history is covered. The corpus says a background encryption process "applies the customer's active key material" to encrypted data (api_meta 264 L127877-127882), and that after you turn on Platform Encryption Salesforce encrypts the existing field values and the previous updates in the History related list (secguide 262 L4899-4902). Two copies are left out: field-history and feed duplicates unless `PlatformEncryptionSettings.enableEncryptFieldHistory` is true (default false, L127877-127882), and history already archived in `FieldHistoryArchive`, which "remains stored without encryption" until you ask Salesforce to encrypt and re-archive it (secguide 262 L4903-4904).

**When it occurs:** Any org that enables encryption on a field that already holds data, and especially one with Field Audit Trail retention.

**How to avoid:** Decide `enableEncryptFieldHistory` explicitly, confirm the background process finished on each object before compliance sign-off, and raise the `FieldHistoryArchive` re-archive with Salesforce if archived history is in scope. UNVERIFIED (2026-10-20): how long background encryption takes on large volumes is Help-only.

---

## Gotcha 3: Encrypting the Name Field Changes the Lookup Experience

**What happens:** Enhanced lookups are "an updated lookup dialog interface that lets users filter, sort, and page through search results" (api_meta 264 L44309-44311). An earlier version of this gotcha said they search only recently accessed records; the corpus does not say that, so that claim was removed. UNVERIFIED (2026-10-20): that encrypting Name turns enhanced lookups on automatically, for which objects, and that it cannot be reversed are Help-only.

**When it occurs:** When encryption is enabled on a Name field.

**How to avoid:** Encrypt Name only when the mandate requires it, test lookup search with real users in a sandbox, and communicate the dialog change before rollout.

---

## Gotcha 4: Deterministic Encryption Is Equality-Only

**What happens:** Teams choose deterministic encryption to keep a field searchable, then find that only exact matches work. Fields encrypted with deterministic encryption "can be used in filters with equals and not equals operators" (api_meta 264 L33328-33329, Briefcase rule filters). Pick `CaseSensitiveDeterministicEncryption` or `CaseInsensitiveDeterministicEncryption` (L45625-45626) to match how values are compared. UNVERIFIED (2026-10-20): that LIKE, range operators, ORDER BY and SOSL stop working on deterministic fields is Help-only.

**When it occurs:** Any time a user-facing feature or integration depends on partial-text search, autocomplete, or sorted queries on an encrypted field.

**How to avoid:** Before choosing deterministic encryption, document every search behaviour tied to the field — exact match, partial match, global search, sorting — and test each one in a sandbox. Where partial-match search is a hard requirement, re-evaluate whether encryption or field-level security is the control the mandate actually asks for.

---

## Gotcha 5: Cache-Only Keys Put an External Key Service on the Read Path

**What happens:** With Cache-Only Keys, users "apply key material stored outside of Salesforce to data on demand" (api_meta 264 L118684-118687); the material is fetched through a named credential (`RemoteKeyServiceID`, obj 264 L283716-283717) and the feature needs the Cache-Only Key Service add-on (L134306). UNVERIFIED (2026-10-20): the exact user-facing failure during a key-service outage is not in the corpus.

**When it occurs:** During key-service downtime, a network partition, a misconfigured named credential — and after deliberate revocation, which is the point of the feature. Cache-Only Key Service customers can move a destroyed cache-only secret back to Active (obj 264 L283943-283944).

**How to avoid:** Choose Cache-Only Keys only when the mandate requires material held outside Salesforce. Turn on `enableReplayDetection` (api_meta 264 L118689-118692), monitor callouts with `RemoteKeyCalloutEvent`, which "captures events related to the success or failure of a callout that fetches encrypted key material" (platform_events 264 L15274), and write an outage runbook. For most compliance cases, customer-supplied (BYOK) material gives key control without the runtime dependency.

---

## Gotcha 6: Encryption at Rest Is Not an Access Decision — Test Who Sees Plaintext

**What happens:** A team encrypts SSN and tells the auditor that "only privileged users can see it" without changing field-level security. The corpus pulls two ways here. The Security Guide ties **View Encrypted Data** and masking to Classic Encryption (secguide 262 L2486, L2499-2503, note at L2548), and says Shield lets you "set encrypted data permissions to protect sensitive data from unauthorized users" (L305-306). UNVERIFIED (2026-10-20): the claim that Shield needs no decrypt permission at all (Help KB 000382508, "beginning Spring '17") and shows plaintext to everyone with FLS Read has no corpus line.

**When it occurs:** At the compliance review after go-live.

**How to avoid:** Treat encryption and access control as two workstreams. Run the FLS matrix for every encrypted field and remove Read where plaintext is not needed, then log in as each affected profile in a sandbox to see what is actually shown. Setting up Shield needs **Customize Application**, and key tasks need **Manage Encryption Keys** (api_meta 264 L127848-127849); those govern administration, not read access.
