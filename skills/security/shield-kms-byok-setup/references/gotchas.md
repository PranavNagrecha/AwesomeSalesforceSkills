# Gotchas — Shield Platform Encryption — BYOK / KMS Setup

## Gotcha 1: Destroy-key not tested

**What happens:** On a real incident nobody can prove revocation works.

**When it occurs:** Production-first rollout.

**How to avoid:** Sandbox rehearsal of destroy-then-recover every quarter.


---

## Gotcha 2: KMS outage = decrypt failure

**What happens:** User pages go blank; agents cannot read records.

**When it occurs:** Cache-Only flavor.

**How to avoid:** Define KMS SLO ≥99.99%, multi-region KMS, and an incident runbook.


---

## Gotcha 3: Mix of deterministic and probabilistic

**What happens:** SOQL filter on a field silently fails to return results.

**When it occurs:** Field migrated from deterministic to probabilistic.

**How to avoid:** Document the encryption mode per field and the query impact.

