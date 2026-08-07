---
name: encrypted-field-query-patterns
description: "Design SOQL, filters, reporting, and indexes against Shield Platform Encryption fields. Trigger keywords: Shield Platform Encryption, encrypted field query, probabilistic vs deterministic encryption, encrypted SOQL filter, encrypted field index. Does NOT cover: Classic Encryption (deprecated), field-level security policy, or tenant secret key rotation."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Encrypted Field Query Patterns

## The Core Constraint

Shield Platform Encryption changes SOQL semantics. Plan the queries
FIRST, then choose the encryption scheme. Reversing that order means
rebuilding schemas later.

## Scheme Matrix

| Scheme | Use Case | SOQL Support |
|---|---|---|
| **Probabilistic** | Max security, display-only | NO filter, NO sort, NO group by, NO index |
| **Deterministic (case-sensitive)** | Exact match required | `=`, `IN`, joins, unique indexes; NO range, NO LIKE |
| **Deterministic (case-insensitive)** | Exact match, case-agnostic | `=`, `IN`; NO range, NO LIKE |

No scheme supports `LIKE` on encrypted fields. No scheme supports range
(`>`, `<`, `BETWEEN`) operators.

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
  post-encryption.

## Aggregation And Reporting

- GROUP BY on encrypted field: supported only with deterministic.
- SUM / AVG on an encrypted number: generally not supported — leave
  aggregatable numerics unencrypted unless compliance requires.
- Reports with filters on encrypted fields: equality works for
  deterministic; others fail at runtime.

## Apex Patterns

Shield Platform Encryption decrypts **transparently**. Any user with
field-level READ access on the field receives plaintext — in Apex, in
SOQL results, in reports, and in the UI. There is no separate
"show me the plaintext" permission you can withhold.

> **Shield vs Classic — do not merge these.** The **"View Encrypted
> Data"** permission belongs to **Classic Encryption**, the legacy
> `Encrypted Text` custom field type, where a user without it sees
> `*********`. Shield Platform Encryption has not used that permission
> since Spring '17. Removing "View Encrypted Data" does **not** mask a
> Shield-encrypted field — the user still sees plaintext if FLS grants
> read. Guidance that says otherwise tells a reader data is protected
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
   — Shield gates plaintext on FLS, not on "View Encrypted Data".
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
