# Encrypted Field Query — Gotchas

## 1. Probabilistic Breaks Filters Silently Until Runtime

Setup does not block probabilistic on a field you filter on. The query
fails at runtime. Inventory filters BEFORE encrypting.

## 2. LIKE Is Blocked For All Schemes

No partial-match search works on encrypted fields. This hits
autocomplete, prefix search, and many reports. Plan a derived hash or
skip encryption.

## 3. Existing Filters Continue To "Work" After Encryption

The query may not error — it may return wrong or empty results. Test
every query after flipping a field to encrypted.

## 4. Custom Index Must Be Requested

Creating a deterministic field does not create an index. For selective
queries, request a custom index via Support (or set it up per feature
setting).

## 5. Formula Fields Over Encrypted Fields

Formula fields referencing encrypted fields inherit limitations and may
not be filterable even if they look scalar.

## 6. External IDs On Encrypted Fields

You can set a deterministic encrypted field as External ID for
upsert-by-external-id, but the upsert path has specific requirements.
Test thoroughly.

## 7. Data Import Tools Need Permission

Data Loader / ETL users loading to encrypted fields need "View
Encrypted Data" to verify. Otherwise they see masked values in
confirmations.

## 8. Key Rotation Rebuilds Encryption

Key rotation re-encrypts data. For huge objects this takes time and
produces background jobs. Plan and monitor.
