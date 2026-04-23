# Encryption Schema Plan

## Field Inventory

| Object.Field | Sensitivity | Query Patterns (exact/range/like/agg/display) | Chosen Scheme | Reason |
|---|---|---|---|---|

## Indexing

| Field | Custom Index Requested? | Selectivity Estimate |
|---|---|---|

## Test Plan

- [ ] User with "View Encrypted Data" sees plaintext.
- [ ] User without sees masked.
- [ ] All filters tested post-encryption flip.
- [ ] All reports tested post-encryption flip.

## Review Cadence

- [ ] Revisit when a new LWC / report filters this field.
- [ ] Revisit before key rotation.

## Sign-Off

- [ ] No probabilistic fields used in filters.
- [ ] No LIKE or range filters on encrypted fields.
- [ ] Custom indexes requested for hot deterministic filters.
- [ ] Debug logging of encrypted values is forbidden in standards.
