# Gotchas — Flow HTTP Callout Action

## Gotcha 1: NC version mismatch

**What happens:** Callout fails auth.

**When it occurs:** Legacy Named Credential.

**How to avoid:** External + Principal (Winter '23+).


---

## Gotcha 2: Complex JSON

**What happens:** Schema infer misses nested fields.

**When it occurs:** Deep response.

**How to avoid:** Apex wrapper or flatten sample.


---

## Gotcha 3: No fault path

**What happens:** Flow fails to user.

**When it occurs:** Default config.

**How to avoid:** Always fault connector → message screen.

