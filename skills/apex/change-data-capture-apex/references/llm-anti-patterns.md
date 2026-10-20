# LLM Anti-Patterns — Change Data Capture Apex

Common mistakes AI coding assistants make when generating or advising on Change Data Capture Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `before insert` Instead of `after insert`

**What the LLM generates:** A CDC trigger with a `before insert` event declaration (declaration-line excerpt):

```apex
// WRONG
trigger AccountChangeEventTrigger on AccountChangeEvent (before insert) {
```

**Why it happens:** LLMs trained on general Apex patterns default to `before insert` for validation-style triggers. CDC triggers are always `after insert` — the event is published after the DML commits, so there is no "before" phase.

**Correct pattern** (declaration-line excerpt):

```apex
trigger AccountChangeEventTrigger on AccountChangeEvent (after insert) {
```

**Detection hint:** Any CDC trigger containing `before insert` is wrong. Grep for `on.*ChangeEvent.*before`.

---

## Anti-Pattern 2: Writing the Trigger on the Base sObject Instead of the Change Event Type

**What the LLM generates:** A trigger on the underlying sObject that attempts to behave like a CDC subscriber (excerpt):

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

---

## Anti-Pattern 7: Budgeting a CDC Trigger Against Asynchronous, Stale, or Invented Heap

**What the LLM generates:**

```apex
trigger AccountChangeTrigger on AccountChangeEvent (after insert) {
    // "CDC runs async, so we have 25 MB heap — safe to hydrate all 2,000 parents."
    Set<Id> ids = new Set<Id>();
    for (AccountChangeEvent e : Trigger.new) {
        ids.addAll((List<Id>) e.ChangeEventHeader.getRecordIds());
    }
    List<Account> parents = [SELECT FIELDS(STANDARD) FROM Account WHERE Id IN :ids];
    // heap blows at ~10 MB, long before the SOQL row limit
}
```

…and prose of the form "CDC triggers consume Apex synchronous limits (100 SOQL, 150 DML, **25 MB heap**)" — a sentence that contradicts itself, since 25 MB is the asynchronous figure — or the stale "**6 MB heap**", which was the figure through Summer '26 and survives in Winter '27 only on a nonproduction org that opted back to the lower limits (`api_meta` 264 L113855–113862) — or a figure such as "**8 MB**" or "**20 MB**" that matches neither release.

**Why it happens:** The Change Data Capture docs correctly and repeatedly describe change event triggers as running **asynchronously**, after the transaction that produced the change. The model reads "asynchronous" and applies the asynchronous heap allocation, which is the natural inference and is wrong — Salesforce documents change event triggers as running under *synchronous* governor limits despite the asynchronous delivery. The 6 MB variant is a separate failure: the Summer '26 figure (262 L19577) carried forward from training data after Winter '27 raised it to 10 MB (`apexdev` 264 L19780). The third variant is invention: a round number that belongs to neither release. Since Winter '27, 10 MB is a real figure — the synchronous one — so the test is no longer "is it 10 MB?" but "is it 10/25 MB (Winter '27) or 6/12 MB (Summer '26), in the column this context uses?"; any other heap figure has no source. All three survive review because the accompanying advice (bulkify, query outside the loop) is correct on its own terms.

**Correct pattern:** Change event triggers run under **synchronous** limits: 100 SOQL, 150 DML, **10 MB heap** (Winter '27; 6 MB before), 10,000 ms CPU (`apexdev` 264 L19747, L19757, L19780, L19782) — with up to 2,000 events per trigger invocation (`apexdev` 264 L20065). UNVERIFIED (2026-09-05): the 2,000 batch size and the 10/25 MB heap split are both grounded in the Apex Developer Guide, but the classification of a *change event trigger* into the synchronous column is a Change Data Capture Developer Guide claim and cannot be read in the Apex guides. Do not infer the limit profile from the word "asynchronous"; delivery timing and limit context are independent here. Size hydration against 10 MB: select only the fields you consume, and if 2,000 events × parent records will not fit, chunk into a Queueable (which *does* get 25 MB) rather than assuming you already have it.

**Detection hint:** in any file matching `ChangeEvent|change event trigger`, flag a sentence that attaches `(12|25)\s?MB` to the trigger's own heap (the Queueable's 25 MB is legitimate), any `6\s?MB\s+heap` without a Summer '26 qualifier, any heap figure other than 6, 10, 12 or 25 MB, and any sentence containing both `asynchron` and `heap` within a CDC file: the pairing is almost always the wrong inference. Conversely, correct CDC guidance states `10 MB` (Winter '27+) and `synchronous` together.
