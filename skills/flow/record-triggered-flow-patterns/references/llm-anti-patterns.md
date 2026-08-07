# LLM Anti-Patterns — Record-Triggered Flow Patterns

Common mistakes AI coding assistants make when generating or advising on record-triggered flows.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using an after-save flow to update the triggering record

**What the LLM generates:**

```
Trigger: After a record is saved (After Save)
[Update Records: Update the triggering record's Status field]
```

**Why it happens:** LLMs default to after-save flows because they can perform DML. But updating the triggering record in an after-save flow causes a recursive save and a separate DML operation. Before-save is the correct choice for updating the triggering record.

**Correct pattern:**

```
Trigger: Before a record is saved (Before Save)
[Assignment: Set $Record.Status = 'Reviewed']
```

Before-save flows update the triggering record without additional DML, are faster, and do not trigger recursion.

**Detection hint:** After-save flow whose only DML is an Update Records element targeting the `$Record` or the same object with the triggering record's ID.

---

## Anti-Pattern 2: Not using $Record__Prior to check field changes

**What the LLM generates:**

```
Entry Conditions: Status__c equals "Closed"
// Fires every time the record is saved while Status is Closed, not just when it changes to Closed
```

**Why it happens:** LLMs set entry conditions on the current value without checking the prior value. This causes the flow to fire repeatedly on every save as long as the condition is met.

**Correct pattern:**

```
Entry Conditions:
  $Record.Status__c equals "Closed"
  AND $Record__Prior.Status__c does not equal "Closed"
```

Or use the built-in option: "Only when a record is updated to meet the condition" in the Start element configuration.

**Detection hint:** Entry conditions that check `$Record` field values without `$Record__Prior` comparison, especially for "changed to" scenarios.

---

## Anti-Pattern 3: Adding DML inside a Loop in a record-triggered flow

**What the LLM generates:**

```
[Get Records: Related Contacts]
[Loop: For each Contact]
    [Update Records: Set Contact.MailingCity = $Record.BillingCity]
```

**Why it happens:** LLMs process collections item-by-item. In a record-triggered flow that fires for 200 records, each loop iteration's DML multiplies, quickly hitting the 150 DML limit.

**Correct pattern:**

```
[Get Records: Related Contacts]
[Loop: For each Contact]
    [Assignment: Set Contact.MailingCity, add to updateCollection]
[Update Records: All records in updateCollection (one DML)]
```

**Detection hint:** Create/Update/Delete Records element inside a Loop in a record-triggered flow.

---

## Anti-Pattern 4: Not considering order of execution with Apex triggers

**What the LLM generates:**

```
"Create a before-save flow on Account to set the Rating field."
// Does not consider that an Apex before-trigger on Account may also set Rating
```

**Why it happens:** LLMs design flows in isolation. In the Salesforce order of execution, before-save flows (step 3) run before Apex before-triggers (step 4). If both modify the same field, the Apex trigger's value wins — deterministically, on every save.

**Correct pattern:**

Before creating a record-triggered flow:
1. Check for existing Apex triggers on the same object
2. Understand the order (Apex Developer Guide, *Triggers and Order of Execution*):

```text
step 3   before-save flow
step 4   before triggers
step 5   system validation + custom validation rules
step 7   save (not committed)
step 8   after triggers
step 11  workflow rules
step 14  after-save flow
step 19  commit
```

3. Document which fields are managed by which automation
4. Avoid having both a flow and a trigger modify the same field. If you cannot, put the guard in the **trigger** — it is the later writer, so a condition on the flow accomplishes nothing.

**Detection hint:** Record-triggered flow advice that does not mention checking for existing Apex triggers or order of execution. Also flag any ordering that places validation rules *before* before-triggers (they run at step 5, after step 4), or that describes the before-save-flow vs before-trigger sequence as unguaranteed or indeterminate — it is documented and fixed.

---

## Anti-Pattern 5: Setting "Run Asynchronously" without understanding the implications

**What the LLM generates:**

```
"Enable 'Run Asynchronously' on the after-save flow for better performance."
```

**Why it happens:** LLMs suggest async for performance. But asynchronous after-save flows run outside the original transaction, meaning they cannot roll back the triggering save on failure and may see stale data.

**Correct pattern:**

Use asynchronous paths only when:
- The flow's work does not need to roll back with the triggering save
- The flow can handle seeing the record in its committed state
- The flow is idempotent (safe to retry)
- The use case tolerates a slight delay (async is not immediate)

Keep the flow synchronous when the work must succeed or fail with the triggering save.

**Detection hint:** "Run Asynchronously" recommendation without discussing rollback implications, idempotency, or data consistency.

---

## Anti-Pattern 6: Creating multiple record-triggered flows on the same object instead of consolidating

**What the LLM generates:**

```
Flow 1: Account After Save - Update Contacts
Flow 2: Account After Save - Create Task
Flow 3: Account After Save - Send Notification
```

**Why it happens:** LLMs create one flow per requirement because it is modular. But multiple record-triggered flows on the same object and trigger type increase complexity and consume more governor limits, and their relative order is left to chance unless each one is given an explicit `triggerOrder` value (Metadata API 54.0+, surfaced as Flow Trigger Explorer) — which is one more thing to maintain.

**Correct pattern:**

Consolidate into a single flow with Decision elements:

```
Account After Save Flow:
  [Decision: Did Rating change?]
    Yes --> [Update Contacts]
  [Decision: Did Owner change?]
    Yes --> [Create Task]
  [Decision: Did Status change to Active?]
    Yes --> [Send Notification]
```

Use subflows to keep the consolidated flow maintainable.

**Detection hint:** Multiple active record-triggered flows on the same object with the same trigger type (e.g., after save on update).
