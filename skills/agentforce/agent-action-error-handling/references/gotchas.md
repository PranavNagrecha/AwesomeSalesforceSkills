# Gotchas — Agent Action Error Handling

## Gotcha 1: Throwing AuraHandledException from an Invocable

**What happens:** The agent receives an opaque framework message and loops.

**When it occurs:** Copy-pasted from an LWC controller.

**How to avoid:** Invocables must *return* a response, never throw. AuraHandledException is LWC-only.


---

## Gotcha 2: Governor-limit exceptions pre-empt your catch

**What happens:** LimitException (uncatchable) kills the transaction — agent sees raw Flow failure.

**When it occurs:** Bulk input of 1000+ records into an Invocable that does DML per-record.

**How to avoid:** Bulkify DML before the per-row loop and guard with `Limits.getLimitDMLRows()` checks; keep @InvocableMethod bulk-safe.


---

## Gotcha 3: Empty list returned when input list is empty

**What happens:** Agent receives an empty array and hallucinates a success message.

**When it occurs:** A filter upstream removed all items.

**How to avoid:** Always return one Response per Request; never return fewer entries than you received.

