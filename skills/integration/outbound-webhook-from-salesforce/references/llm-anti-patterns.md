# LLM Anti-Patterns — Outbound Webhook

## Anti-Pattern 1: Callout In Trigger

**What the LLM generates:** `Http.send()` inside an after-insert trigger.

**Why it happens:** "fire and forget."

**Correct pattern:** enqueue a Queueable from the trigger; the Queueable
does the callout.

## Anti-Pattern 2: Outbound Message For New Integration

**What the LLM generates:** recommend Outbound Message.

**Why it happens:** declarative, no code.

**Correct pattern:** Outbound Message lacks retry, HMAC, OAuth. Use Apex
Queueable or Flow HTTP Callout with Delivery object.

## Anti-Pattern 3: Retry Any Status Code

**What the LLM generates:** retry on all non-2xx.

**Why it happens:** naive retry logic.

**Correct pattern:** retry 5xx, 408, 429 only. 4xx is permanent.

## Anti-Pattern 4: Secret In Custom Metadata

**What the LLM generates:** store the HMAC secret in a CMDT field.

**Why it happens:** CMDT is the de-facto config store.

**Correct pattern:** External Credential inside the Named Credential;
encrypted storage.

## Anti-Pattern 5: No Idempotency Key

**What the LLM generates:** POST payload with no `X-Event-Id`.

**Why it happens:** webhook looks like a one-shot.

**Correct pattern:** always include an idempotency id so retries don't
double-apply.
