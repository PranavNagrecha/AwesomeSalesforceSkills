# Gotchas — Flow Migration From Trigger

## Gotcha 1: Order-of-execution changes between Apex and Flow

Before-Save Flows fire at a different point in the save order than Before-triggers. Migrating from Before-trigger to Before-Save Flow can shift field values visible to downstream automations. Reference: Salesforce "Trigger Order of Execution" doc.

---

## Gotcha 2: Recursion control disappears

Apex triggers often use `static Boolean alreadyRan` to prevent recursion. Flow has no equivalent for silent recursion prevention. Migration without a recursion guard can create infinite loops.

Fix: either keep Apex, or use entry conditions + custom permissions to gate flow re-entry.

---

## Gotcha 3: Custom exception wrapping is lost

Apex handlers often wrap exceptions in a custom hierarchy for downstream logging. Flow has no custom exception types. Migration loses the diagnostic context.

Fix: Flow fault paths log to Integration_Log__c with severity + source; reconstruct diagnostic context from log fields.

---

## Gotcha 4: Bulk behavior can regress

Apex handlers often do one SOQL with a large IN-clause. Flow's Get Records with Filter mapping can produce 1 SOQL per filter value unless designed carefully. Before migration, verify the Flow query plan.

---

## Gotcha 5: Test-class mocking breaks

Tests that mocked static Apex methods continue to run, but the new Flow code isn't mocked — hits the real logic. Tests may pass by coincidence (fixture matches flow output) or fail unexpectedly.

Fix: review every mocked call; audit that Flow-equivalent work is mocked at the Flow's inputs (SOQL results, Platform Event bus state) instead.

---

## Gotcha 6: Platform Event publish semantics shift

Apex-triggered `EventBus.publish()` is per-call. Flow's Create Records on an event object uses Publish After Commit by default (if supported). This can change whether downstream subscribers run on rolled-back saves.

---

## Gotcha 7: Sharing settings differ

Apex defaults to `without sharing` unless declared. Flow honors sharing by default. Migration changes who can see / modify what — may fix a security gap, may break expected behavior. Audit.
