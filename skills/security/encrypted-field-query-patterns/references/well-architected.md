# Well-Architected Notes — Encrypted Field Queries

## Relevant Pillars

- **Security** — at-rest encryption for sensitive data.
- **Performance** — deterministic schemes still index; probabilistic
  does not; queries without a plan become full-table scans.
  UNVERIFIED (2026-10-20): Shield index behaviour is not in the corpus.
- **Reliability** — silent filter mismatches after enabling encryption
  are a classic reliability trap.

## Architectural Tradeoffs

- **Probabilistic vs deterministic:** probabilistic is stronger against
  inference attacks but unusable for queries.
- **Case-sensitive vs case-insensitive deterministic:** case-insensitive
  is more useful for user-entered data; case-sensitive has marginally
  stronger cryptographic isolation of values. UNVERIFIED (2026-10-20): not in the corpus.
- **Encrypting aggregatable numerics:** usually the wrong call — the
  operational cost is high.

## Scheme Discipline

- Decide per field, document reasons, store in a repo-checked decision
  log.
- Re-review when the query set changes (new report, new LWC filter).

## Encryption Is Not Authorization

Shield Platform Encryption protects data **at rest**. It does not
decide who may read a value: decryption is transparent to any user with
field-level READ. Access-control decisions belong to FLS, page layouts,
and sharing. Encrypting a field and then assuming it is hidden from
internal users is the classic Security-pillar failure in this domain.

The "View Encrypted Data" permission is part of **Classic Encryption**
(legacy `Encrypted Text` fields), a different product (secguide 262 L2484-2486,
L2548); the `encryptionScheme` values "pertain to Shield Platform Encryption, not
Classic Encryption" (api_meta 264 L45629-45630).

## Official Sources Used

- Scheme values and Shield-not-Classic scope — api_meta 264 L45625-45630.
- Deterministic scheme "lets customers filter on encrypted data" — api_meta 264 L127865-127866.
- View Encrypted Data is the Classic Encryption permission — secguide 262 L2484-2486, L2548.
- Support adds custom indexes on request — apexdev 264 L9812.
- Tenant secret rotation frequency — obj 264 L283644.

- Shield Platform Encryption Overview —
  https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Deterministic Encryption —
  https://help.salesforce.com/s/articleView?id=sf.security_pe_deterministic_encryption.htm
- Use Field-Level, Event Bus, and Search Encryption (Trailhead) —
  "At runtime, encrypted data looks just like unencrypted data from the
  user's point of view"; "encryption doesn't take the place of
  field-level access controls" —
  https://trailhead.salesforce.com/content/learn/modules/spe_admins/spe_admins_deploy
- View Encrypted Data Permission Not Needed with Shield Platform
  Encryption Beginning Spring '17 —
  https://help.salesforce.com/s/articleView?id=000382508&type=1
- Classic Encryption for Custom Fields —
  https://help.salesforce.com/s/articleView?id=platform.fields_about_encrypted_fields.htm&type=5
