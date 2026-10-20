# Encryption Schema Plan

## Field Inventory

| Object.Field | Sensitivity | Query Patterns (exact/range/like/agg/display) | Chosen Scheme | Reason |
|---|---|---|---|---|

## Indexing

| Field | Custom Index Requested? | Selectivity Estimate |
|---|---|---|

## Test Plan

- [ ] User with FLS Read on the field sees plaintext (Shield decrypts
      transparently for anyone with field read — UNVERIFIED (2026-10-20):
      Trailhead wording, not in the corpus).
- [ ] User with FLS Read removed cannot retrieve the field at all.
- [ ] Plan does NOT rely on "View Encrypted Data" — that is a Classic
      Encryption permission (secguide 262 L2548) and does not mask Shield
      fields (UNVERIFIED (2026-10-20): Help only).
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
