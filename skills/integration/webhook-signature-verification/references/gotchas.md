# Gotchas — Webhook Signature Verification

## Gotcha 1: Non-constant-time compare

**What happens:** Timing attack leaks signature.

**When it occurs:** Using `==` on Blob.

**How to avoid:** Byte-by-byte loop that always reads full length.


---

## Gotcha 2: Secret in plain CMDT

**What happens:** Any reader sees it.

**When it occurs:** Forgot Protected flag.

**How to avoid:** Protected Custom Metadata only.


---

## Gotcha 3: Missing replay defense

**What happens:** Replayed events processed twice.

**When it occurs:** Idempotency + freshness skipped.

**How to avoid:** Timestamp check + idempotency key.

