# Gotchas — Exception Handling

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Trigger Exceptions Roll Back More Than You Expect

**What happens:** A developer catches one exception in a trigger helper, logs it, then rethrows a different generic exception. The entire save fails, including records that were otherwise valid in the same transaction.

**When it occurs:** Trigger logic throws unexpectedly during insert, update, delete, undelete, or cross-object DML from the same transaction.

**How to avoid:** Use `addError` for expected business validation on specific records. Let unexpected faults surface with enough context to debug, but do not confuse that with record-level validation behavior.

---

## `Database.*(..., false)` Moves Failures Into `SaveResult[]`

**What happens:** The code switches from `update records;` to `Database.update(records, false)` for bulk resilience, but still assumes an exception will be thrown when a row fails.

**When it occurs:** Partial success DML is used and the code never loops through `Database.SaveResult[]`.

**How to avoid:** Always inspect every `SaveResult`, record the failed IDs and messages, and make the return type or log structure explicit about partial success.

---

## `AuraHandledException` Can Hide The Real Root Cause

**What happens:** A deep service layer throws `AuraHandledException` directly. The message reaches the UI, but the platform stack trace and operational context are lost.

**When it occurs:** Teams use UI-specific exception types in reusable services shared by LWC, Batch, Flow-invocable methods, and REST resources.

**How to avoid:** Keep `AuraHandledException` at the controller boundary. Throw custom domain exceptions in lower layers, then translate them at the last user-facing hop.

---

## `System.debug` Is Not Production Error Handling

**What happens:** A catch block looks active because it prints the exception, but production troubleshooting has no durable record and the transaction continues in a bad state.

**When it occurs:** Teams rely on developer-console debugging habits in deployed Apex.

**How to avoid:** Log through a real mechanism such as a custom log object, platform event, or observability integration, and decide explicitly whether the exception should be rethrown.
