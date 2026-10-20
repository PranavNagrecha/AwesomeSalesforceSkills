# Gotchas — Flow HTTP Callout Action

## Gotcha 1: NC version mismatch

**What happens:** Callout fails auth.

**When it occurs:** Legacy Named Credential. UNVERIFIED (2026-10-20): that the action fails with a `Legacy` credential is not in the corpus.

**How to avoid:** `SecuredEndpoint` credential with an External Credential principal; the schema dates from Winter '23 (api_meta 264 L92875-92876, L92881-92882), and each user's permission set needs principal access (api_meta 264 L97688-97689).


---

## Gotcha 2: Complex JSON

**What happens:** Schema infer misses nested fields. UNVERIFIED (2026-10-20): schema inference is named only as the `SchemaInferred` source (api_meta 264 L66635); its nesting limits are not in the corpus.

**When it occurs:** Deep response.

**How to avoid:** Apex wrapper or flatten sample.


---

## Gotcha 3: No fault path

**What happens:** Flow fails to user. UNVERIFIED (2026-10-20): the unhandled-fault outcome for this action is not in the corpus.

**When it occurs:** Default config.

**How to avoid:** Always fault connector → message screen.

