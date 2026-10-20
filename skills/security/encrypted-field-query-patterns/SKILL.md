---
name: encrypted-field-query-patterns
description: "Design SOQL, filters, reporting, and indexes against Shield Platform Encryption fields. Trigger keywords: Shield Platform Encryption, encrypted field query, probabilistic vs deterministic encryption, encrypted SOQL filter. NOT for Classic Encryption, field-level security policy, or tenant secret k — use security/platform-encryption."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Reliability
triggers:
  - "query encrypted field"
  - "shield platform encryption filter"
  - "deterministic encryption selection"
  - "encrypted field index"
  - "encrypted field soql limitations"
tags:
  - security
  - shield
  - encryption
  - soql
inputs:
  - List of fields requiring encryption
  - Query patterns over those fields (exact, range, like, aggregate)
  - Reporting requirements
outputs:
  - Encryption scheme choice per field (probabilistic / deterministic / case-sensitive deterministic)
  - SOQL pattern guidance per field
  - Index and reporting plan
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Encrypted Field Query Patterns

## The Core Constraint

Shield Platform Encryption changes SOQL semantics. Plan the queries
FIRST, then choose the encryption scheme. Reversing that order means
rebuilding schemas later.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which queries, reports and list views filter on this field today? | Gotcha 1: a probabilistic field that is filtered fails only at runtime (UNVERIFIED (2026-10-20)) | The query inventory that picks the scheme |
| Does any user search it by partial value (autocomplete, prefix)? | Gotcha 2: LIKE is not available on encrypted fields (UNVERIFIED (2026-10-20)) | A derived-hash field or a decision not to encrypt |
| Which existing tests cover each filter after the flip? | Gotcha 3: an old filter can return empty instead of erroring (UNVERIFIED (2026-10-20)) | A retest list per field |
| Is the field a selective filter on a large object? | Gotcha 4: a deterministic field gets no index by itself (UNVERIFIED (2026-10-20)); Support adds indexes on request (apexdev 264 L9812) | A Support index request in the plan |
| Do formula fields or External ID upserts depend on it? | Gotchas 5 and 6: both inherit the field's limits (UNVERIFIED (2026-10-20) for Shield) | Formulas and upsert keys to retest |
| Which integration users load or read it, and are they Shield or Classic? | Gotcha 7: Classic is gated by View Encrypted Data (secguide 262 L2484-2486); Shield by FLS (UNVERIFIED (2026-10-20)) | The right permission change for the right product |
| How large is the object and when is key rotation scheduled? | Gotcha 8: Data tenant secrets rotate at most every 24 h in production (obj 264 L283644); re-encryption of old data is UNVERIFIED (2026-10-20) | A rotation window and monitoring owner |

A proper configuration fixes the scheme per field from the query inventory, so nobody discovers a dead filter or report after the data is already encrypted.

## Scheme Matrix

| Scheme | Use Case | SOQL Support |
|---|---|---|
| **Probabilistic** | Max security, display-only | NO filter, NO sort, NO group by, NO index |
| **Deterministic (case-sensitive)** | Exact match required | `=`, `IN`, joins, unique indexes; NO range, NO LIKE |
| **Deterministic (case-insensitive)** | Exact match, case-agnostic | `=`, `IN`; NO range, NO LIKE |

No scheme supports `LIKE` on encrypted fields. No scheme supports range
(`>`, `<`, `BETWEEN`) operators. Grounded: the three scheme values
(api_meta 264 L45625-45628, "pertains to Shield Platform Encryption, not Classic
Encryption", L45629-45630) and that deterministic "lets customers filter on
encrypted data" (api_meta 264 L127865-127866; equals / not-equals in BriefcaseRule
filters, L33328-33329). UNVERIFIED (2026-10-20): the per-operator rows above (LIKE,
range, ORDER BY, GROUP BY, index, joins) — the Shield Platform Encryption guide is
not in the corpus; secguide 262 L303-306 is only the product overview.

## Decision By Query Pattern

| Query | Scheme |
|---|---|
| Display only (never filter) | Probabilistic |
| Lookup by exact value | Deterministic (case-sensitive if value is case-stable) |
| Customer search by name (case-agnostic) | Deterministic case-insensitive |
| Range query (date, amount) | **Do not encrypt** — use field-level security + masking |
| LIKE search | **Do not encrypt** — or store a derived hash/index field |
| Sort by field | Only if you rely on display order, not SOQL ORDER BY |

## Indexing

- Custom indexes on deterministic encrypted fields are supported for
  equality filters.
- Standard indexes (lookup, master-detail) are not automatically present
  on encrypted fields — request a custom index.
- Query selectivity degrades if the encrypted field has low cardinality
  post-encryption. UNVERIFIED (2026-10-20): the three Shield index claims above;
  the corpus only says "Salesforce Support can add custom indexes on request"
  (apexdev 264 L9812) and that no custom index can be built on the Classic
  `encrypted text` field type (apexdev 264 L9814).

## Aggregation And Reporting

- GROUP BY on encrypted field: supported only with deterministic.
- SUM / AVG on an encrypted number: generally not supported — leave
  aggregatable numerics unencrypted unless compliance requires.
- Reports with filters on encrypted fields: equality works for
  deterministic; others fail at runtime. UNVERIFIED (2026-10-20): the three
  aggregation and reporting claims above — not in the corpus.
- Criteria-based sharing rules: "you can't use lookup fields, encrypted
  fields, formula fields" as criteria (secguide 262 L3478).
- Field Audit Trail: after you turn on encryption, "previously archived data
  remains unencrypted"; to encrypt it, "contact Salesforce to encrypt and
  rearchive the stored field history data" (secguide 262 L4899-4904).

## Apex Patterns

Shield Platform Encryption decrypts **transparently**. Any user with
field-level READ access on the field receives plaintext — in Apex, in
SOQL results, in reports, and in the UI. There is no separate
"show me the plaintext" permission you can withhold. UNVERIFIED (2026-10-20):
transparent decryption on FLS read is Trailhead wording; the corpus overview says
only that you "can set encrypted data permissions to protect sensitive data from
unauthorized users" (secguide 262 L306) and names no masking permission.

> **Shield vs Classic — do not merge these.** The **"View Encrypted
> Data"** permission belongs to **Classic Encryption**, the legacy
> `Encrypted Text` custom field type, where a user without it sees a
> masked value (the `maskChar` values "pertain to Classic Encryption, not
> Shield Platform Encryption", api_meta 264 L45732-45737; "Only users with the View Encrypted Data permission can see
> data in encrypted custom text fields", secguide 262 L2484-2486; that page
> "is about Classic Encryption, not Shield Platform Encryption", L2548).
> Shield Platform Encryption has not used that permission since Spring '17,
> and removing "View Encrypted Data" does **not** mask a Shield-encrypted
> field — the user still sees plaintext if FLS grants read
> (UNVERIFIED (2026-10-20): the Spring '17 date and this behaviour are Help
> KB 000382508 only). Guidance that says otherwise tells a reader data is protected
> when it is not.

Plaintext visibility for Shield is restricted with **field-level
security** (profiles / permission sets), page layouts, and sharing.
Encryption is an at-rest control, not an authorization control. Plan for:

- Test users with FLS read granted and FLS read removed on each
  encrypted field.
- Avoid logging encrypted values in `System.debug` even when you do have
  read access — Event Monitoring / debug logs may persist.

## Recommended Workflow

1. Enumerate every query / report / list view / filter that touches
   each candidate field.
2. Classify each query: exact, range, LIKE, aggregate, display.
3. Apply the scheme matrix. Flag fields where encryption blocks a
   required query.
4. For blocked fields, decide: drop the requirement, skip encryption,
   or derive a hashed index field (one-way).
5. Request custom indexes on deterministic fields used as filters.
6. Test with a user who has FLS read on the field and one who does not
   — Shield gates plaintext on FLS, not on "View Encrypted Data"
   (UNVERIFIED (2026-10-20): Help/Trailhead only, see Apex Patterns).
7. Document the scheme per field in a schema decision log.

## Official Sources Used

- Shield Platform Encryption Overview —
  https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Deterministic Encryption —
  https://help.salesforce.com/s/articleView?id=sf.security_pe_deterministic_encryption.htm
- Encrypted Fields In SOQL —
  https://help.salesforce.com/s/articleView?id=sf.security_pe_apps_soql.htm
- Use Field-Level, Event Bus, and Search Encryption (Trailhead) —
  "encryption doesn't take the place of field-level access controls" —
  https://trailhead.salesforce.com/content/learn/modules/spe_admins/spe_admins_deploy
- View Encrypted Data Permission Not Needed with Shield Platform
  Encryption Beginning Spring '17 —
  https://help.salesforce.com/s/articleView?id=000382508&type=1
- Classic Encryption for Custom Fields (the feature that DOES use
  "View Encrypted Data") —
  https://help.salesforce.com/s/articleView?id=platform.fields_about_encrypted_fields.htm&type=5
