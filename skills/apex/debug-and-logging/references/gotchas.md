# Gotchas — Debug And Logging

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `System.debug` Is Not Retention Strategy

**What happens:** A critical incident occurs and the needed debug lines are gone or were never collected at the right level.

**When it occurs:** Teams assume the existence of a debug statement means production observability exists.

**How to avoid:** Use durable log storage for production-critical diagnostics.

---

## Sensitive Payload Logging Creates Security Debt

**What happens:** Tokens, bearer headers, or full request bodies end up in logs.

**When it occurs:** Teams log entire callout payloads or auth objects during troubleshooting.

**How to avoid:** Log identifiers and error classification, not secrets or unnecessary personal data.

---

## Async Failures Need More Than Stack Traces

**What happens:** Support knows a Queueable or Batch failed but cannot trace which business operation triggered it.

**When it occurs:** Logging ignores correlation IDs or async job IDs.

**How to avoid:** Capture the initiating record context and job ID together.

---

## Excessive Debug Noise Can Obscure Root Cause

**What happens:** The exact failure is present in the logs but buried under hundreds of low-value debug statements.

**When it occurs:** Teams use debug output as a permanent narrative of every method entry and variable value.

**How to avoid:** Use deliberate log levels and remove temporary debug statements after diagnosis.
