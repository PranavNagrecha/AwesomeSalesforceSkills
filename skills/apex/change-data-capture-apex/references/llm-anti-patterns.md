# LLM Anti-Patterns — Change Data Capture Apex

Common mistakes AI coding assistants make when generating or advising on Change Data Capture Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `before insert` Instead of `after insert`

**What the LLM generates:** A CDC trigger with a `before insert` event declaration:

```apex
// WRONG
trigger AccountChangeEventTrigger on AccountChangeEvent (before insert) {
```

**Why it happens:** LLMs trained on general Apex patterns default to `before insert` for validation-style triggers. CDC triggers are always `after insert` — the event is published after the DML commits, so there is no "before" phase.

**Correct pattern:**

```apex
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
```

**Detection hint:** Any CDC trigger containing `before insert` is wrong. Grep for `on.*ChangeEvent.*before`.

---

## Anti-Pattern 2: Writing the Trigger on the Base sObject Instead of the Change Event Type

**What the LLM generates:** A trigger on the underlying sObject that attempts to behave like a CDC subscriber:

```apex
// WRONG — this is a standard DML trigger, not a CDC trigger
trigger AccountTrigger on Account (after update) {
    EventBus.ChangeEventHeader header = ...; // ChangeEventHeader does not exist on Account
```

**Why it happens:** LLMs conflate standard object triggers with CDC event triggers. CDC subscribes to `AccountChangeEvent` (the change event type), not `Account` (the sObject).

**Correct pattern:**

```apex
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    for (AccountChangeEvent event : Trigger.new) {
        EventBus.ChangeEventHeader header = event.ChangeEventHeader;
    }
}
```

**Detection hint:** Check that the trigger declaration references a type ending in `ChangeEvent` (standard) or `__ChangeEvent` (custom), not the bare sObject name.

---

## Anti-Pattern 3: Reading Field Values Directly from UPDATE Events Without Querying

**What the LLM generates:** Code that reads changed field values directly from the event body in an UPDATE handler, assuming the event body holds the current record state:

```apex
// WRONG — for UPDATE events, unchanged fields are null
for (AccountChangeEvent event : Trigger.new) {
    if (event.ChangeEventHeader.changeType == 'UPDATE') {
        String city = event.BillingCity; // null if BillingCity did not change
        syncToExternal(event.Id, city);  // sends null for unrelated updates
    }
}
```

**Why it happens:** LLMs assume the event body is a complete snapshot of the record. For CREATE events it is; for UPDATE events, only changed fields are populated. Unchanged fields are null.

**Correct pattern:**

```apex
Set<Id> updatedIds = new Set<Id>();
for (AccountChangeEvent event : Trigger.new) {
    if (event.ChangeEventHeader.changeType == 'UPDATE') {
        updatedIds.addAll((List<Id>) event.ChangeEventHeader.getRecordIds());
    }
}
if (!updatedIds.isEmpty()) {
    List<Account> accounts = [SELECT Id, BillingCity FROM Account WHERE Id IN :updatedIds];
    // use accounts for reliable current values
}
```

**Detection hint:** Look for direct field access on the change event variable (e.g., `event.BillingCity`, `event.Status`) in an UPDATE branch without a preceding SOQL query.

---

## Anti-Pattern 4: Missing GAP Event Handling

**What the LLM generates:** A CDC trigger that handles `CREATE`, `UPDATE`, `DELETE`, and `UNDELETE` but has no branch for `GAP_*` change types:

```apex
// INCOMPLETE — no GAP handling
if (header.changeType == 'CREATE') { ... }
else if (header.changeType == 'UPDATE') { ... }
else if (header.changeType == 'DELETE') { ... }
// GAP_CREATE, GAP_UPDATE, GAP_DELETE, GAP_UNDELETE silently dropped
```

**Why it happens:** LLMs are trained on simplified examples that enumerate only the "happy path" change types. Gap events are less commonly discussed, so the LLM omits them.

**Correct pattern:**

```apex
if (header.changeType == 'CREATE') { ... }
else if (header.changeType == 'UPDATE') { ... }
else if (header.changeType == 'DELETE') { ... }
else if (header.changeType == 'UNDELETE') { ... }
else if (header.changeType.startsWith('GAP_')) {
    // No field data available — queue re-fetch for all IDs
    gapIds.addAll((List<Id>) header.getRecordIds());
}
```

**Detection hint:** Search for CDC trigger code that does not contain `GAP_` or `.startsWith('GAP_')`. Any production CDC trigger without GAP handling is incomplete.

---

## Anti-Pattern 5: Performing Synchronous Callouts Inside the CDC Trigger Body

**What the LLM generates:** A CDC trigger that directly instantiates an `HttpRequest` or calls a service class that uses `Http.send()`:

```apex
// WRONG — synchronous callouts are not allowed from CDC trigger context
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    for (AccountChangeEvent event : Trigger.new) {
        ExternalApiClient.syncAccount(event.ChangeEventHeader.getRecordIds()); // throws CalloutException
    }
}
```

**Why it happens:** LLMs generate Apex callout patterns without accounting for the async execution context of CDC triggers. Synchronous callouts are prohibited in this context.

**Correct pattern:**

```apex
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
    Set<Id> updatedIds = new Set<Id>();
    for (AccountChangeEvent event : Trigger.new) {
        updatedIds.addAll((List<Id>) event.ChangeEventHeader.getRecordIds());
    }
    if (!updatedIds.isEmpty()) {
        // Dispatch callout to Queueable with Database.AllowsCallouts
        System.enqueueJob(new AccountSyncQueueable(updatedIds));
    }
}
```

**Detection hint:** Look for `Http`, `HttpRequest`, `HttpResponse`, or service class calls inside the trigger body without any `System.enqueueJob` or `@future` wrapping.

---

## Anti-Pattern 6: Issuing SOQL Inside the Event Loop

**What the LLM generates:** A CDC trigger that queries records inside the for-loop over `Trigger.new`, triggering a SOQL per event record:

```apex
// WRONG — SOQL inside event loop; blows governor limits at scale
for (AccountChangeEvent event : Trigger.new) {
    List<String> ids = event.ChangeEventHeader.getRecordIds();
    List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :ids]; // 1 SOQL per event
    processAccounts(accounts);
}
```

**Why it happens:** LLMs generate the per-record pattern commonly seen in simple trigger handlers. With up to 2,000 events per batch, this pattern exhausts the 100-SOQL governor limit at event 100 and throws an exception.

**Correct pattern:**

```apex
Set<Id> allIds = new Set<Id>();
for (AccountChangeEvent event : Trigger.new) {
    allIds.addAll((List<Id>) event.ChangeEventHeader.getRecordIds());
}
// Single bulk SOQL outside the loop
if (!allIds.isEmpty()) {
    List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :allIds];
    processAccounts(accounts);
}
```

**Detection hint:** Any SOQL or DML statement that appears inside a `for (... : Trigger.new)` loop in a CDC trigger is a governor limit risk.
