# Well-Architected Notes — Encrypted Field Queries

## Relevant Pillars

- **Security** — at-rest encryption for sensitive data.
- **Performance** — deterministic schemes still index; probabilistic
  does not; queries without a plan become full-table scans.
- **Reliability** — silent filter mismatches after enabling encryption
  are a classic reliability trap.

## Architectural Tradeoffs

- **Probabilistic vs deterministic:** probabilistic is stronger against
  inference attacks but unusable for queries.
- **Case-sensitive vs case-insensitive deterministic:** case-insensitive
  is more useful for user-entered data; case-sensitive has marginally
  stronger cryptographic isolation of values.
- **Encrypting aggregatable numerics:** usually the wrong call — the
  operational cost is high.

## Scheme Discipline

- Decide per field, document reasons, store in a repo-checked decision
  log.
- Re-review when the query set changes (new report, new LWC filter).

## Official Sources Used

- Shield Platform Encryption Overview —
  https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm
- Deterministic Encryption —
  https://help.salesforce.com/s/articleView?id=sf.security_pe_deterministic_encryption.htm
