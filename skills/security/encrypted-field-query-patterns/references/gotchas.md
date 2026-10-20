# Encrypted Field Query — Gotchas

## 1. Probabilistic Breaks Filters Silently Until Runtime

Setup does not block probabilistic on a field you filter on. The query
fails at runtime. Inventory filters BEFORE encrypting. UNVERIFIED (2026-10-20):
the corpus does not describe Setup's behaviour here.

## 2. LIKE Is Blocked For All Schemes

No partial-match search works on encrypted fields. This hits
autocomplete, prefix search, and many reports. Plan a derived hash or
skip encryption. UNVERIFIED (2026-10-20): the Shield SOQL operator list is not in
the corpus; only deterministic filtering is (api_meta 264 L127865-127866).

## 3. Existing Filters Continue To "Work" After Encryption

The query may not error — it may return wrong or empty results. Test
every query after flipping a field to encrypted. UNVERIFIED (2026-10-20): not in the corpus.

## 4. Custom Index Must Be Requested

Creating a deterministic field does not create an index. For selective
queries, request a custom index via Support — "Salesforce Support can add
custom indexes on request" (apexdev 264 L9812). UNVERIFIED (2026-10-20): that a
deterministic field gets no index of its own, and any self-service index setting.

## 5. Formula Fields Over Encrypted Fields

Formula fields referencing encrypted fields inherit limitations and may
not be filterable even if they look scalar. UNVERIFIED (2026-10-20) for Shield;
the corpus holds the Classic rule only — Classic encrypted text fields "Aren't
available for ... formula fields" (secguide 262 L2526).

## 6. External IDs On Encrypted Fields

You can set a deterministic encrypted field as External ID for
upsert-by-external-id, but the upsert path has specific requirements.
Test thoroughly. UNVERIFIED (2026-10-20) for Shield; a Classic encrypted text
field "Can't be unique, have an external ID" (secguide 262 L2520).

## 7. Data Import Tools Need FLS, Not "View Encrypted Data"

Data Loader / ETL users loading to a Shield-encrypted field need
field-level **Read** (to verify) and **Edit** (to write) on that field.
Shield decryption is transparent to anyone with FLS read.

"View Encrypted Data" is a **Classic Encryption** permission (secguide 262
L2484-2486, L2548) and has no effect on Shield-encrypted fields
(UNVERIFIED (2026-10-20): the "no effect on Shield" half and the
transparent-decryption sentence above are Help/Trailhead only). If an
integration user is seeing a masked value, the field is a Classic (the mask
characters `asterisk` / `X` "pertain to Classic Encryption, not Shield
Platform Encryption", api_meta 264 L45732-45737)
`Encrypted Text` field, not a Shield field — check which product is in
play before changing permissions.

## 8. Key Rotation Rebuilds Encryption

Key rotation re-encrypts data. For huge objects this takes time and
produces background jobs. Plan and monitor. UNVERIFIED (2026-10-20): whether
rotation re-encrypts existing data is not in the corpus. Grounded: Data-type
tenant secrets rotate at most "once every four hours in a sandbox org or every 24
hours in production orgs" (obj 264 L283644).
