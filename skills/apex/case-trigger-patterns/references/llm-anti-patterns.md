# LLM Anti-Patterns — Case Trigger Patterns

Common mistakes AI coding assistants make when generating or advising on Case trigger logic.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `insert` Keyword Instead of `Database.insert()` with DmlOptions

**What the LLM generates:**

```apex
// In a handler or service — inserting cases without DmlOptions
insert caseList;
```

The LLM then adds a comment like "this will trigger the assignment rule" or says nothing about assignment rules at all, assuming the platform behavior matches what a UI save does.

**Why it happens:** Training data contains far more examples of the `insert` keyword than `Database.insert()` with options. The LLM does not distinguish between UI-triggered DML (which evaluates assignment rules) and programmatic DML (which does not).

**Correct pattern:**

```apex
Database.DmlOptions opts = new Database.DmlOptions();
opts.assignmentRuleHeader.useDefaultRule = true;
Database.insert(caseList, opts);
```

**Detection hint:** Search the generated code for `insert case` or `insert new Case` not preceded by `Database.`. Flag any code that inserts Case records and relies on assignment rules without using `Database.DmlOptions`.

---

## Anti-Pattern 2: Completing Milestones by Setting `IsCompleted = true`

**What the LLM generates:**

```apex
for (CaseMilestone cm : milestonesToComplete) {
    cm.IsCompleted = true;  // WRONG — IsCompleted is read-only
}
update milestonesToComplete;
```

The LLM treats `IsCompleted` as a writable field because it looks like a standard boolean flag.

**Why it happens:** The LLM infers the field name from context and assumes read/write parity. It does not know that `IsCompleted` on `CaseMilestone` is a computed, read-only field derived from `CompletionDate`.

**Correct pattern:**

```apex
Datetime now = Datetime.now();
for (CaseMilestone cm : milestonesToComplete) {
    cm.CompletionDate = now;  // Setting CompletionDate is the write path
}
update milestonesToComplete;
```

**Detection hint:** Search for `IsCompleted = true` on `CaseMilestone`. Any such assignment will cause a runtime or compile-time error — `IsCompleted` is not settable.

---

## Anti-Pattern 3: Assuming MasterRecordId Is Available in `Trigger.new` During a Delete

**What the LLM generates:**

```apex
trigger CaseTrigger on Case (before delete) {
    for (Case c : Trigger.new) {  // WRONG — Trigger.new is null in delete context
        if (c.MasterRecordId != null) { ... }
    }
}
```

**Why it happens:** The LLM reuses the `Trigger.new` pattern from insert/update contexts. It does not reliably know that `Trigger.new` (and `Trigger.newMap`) are null in delete trigger contexts.

**Correct pattern:**

```apex
trigger CaseTrigger on Case (after delete) {
    for (Case c : Trigger.old) {  // Use Trigger.old in delete context
        if (c.MasterRecordId != null) {
            // This is a merge — c is the losing record
        }
    }
}
```

**Detection hint:** Look for `Trigger.new` inside a `before delete` or `after delete` context. This will cause a `NullPointerException` at runtime.

---

## Anti-Pattern 3b: Checking `MasterRecordId` in `before delete`

**What the LLM generates:**

```apex
trigger CaseTrigger on Case (before delete) {
    for (Case c : Trigger.old) {
        if (c.MasterRecordId != null) {   // WRONG context — always null here
            archiveToMaster(c);           // never runs
        } else {
            purgeCase(c);                 // runs for merged cases too
        }
    }
}
```

**Why it happens:** Once the model has learned "use `Trigger.old` in delete context" it treats `before delete` and `after delete` as interchangeable for reading fields off the losing record. The code compiles, deploys, and passes a review — the defect is invisible without knowing the platform's write ordering.

**Correct pattern:** Put the merge branch in `after delete`. The Apex Developer Guide: "The MasterRecordId field is only set in after delete trigger events." The platform fires `before delete`, *then* deletes and sets `MasterRecordId`, *then* fires `after delete`.

```apex
trigger CaseTrigger on Case (after delete) {
    for (Case c : Trigger.old) {
        if (c.MasterRecordId != null) { archiveToMaster(c); }
        else { purgeCase(c); }
    }
}
```

**Detection hint:** Flag any `MasterRecordId` reference inside a `before delete` block or a handler method invoked from one. Unlike the `Trigger.new` mistake this throws no exception — it silently sends every merged record down the true-delete path.

---

## Anti-Pattern 3c: Merging Cases Through the SOAP `merge()` Call

**What the LLM generates:** A SOAP `merge()` envelope with `type="Case"`, or advice that an integration can dedupe cases the same way it dedupes leads and contacts.

**Why it happens:** `Case.MasterRecordId` exists, Lightning has a case merge action, and Apex genuinely does support case merge — "Only leads, contacts, cases, and accounts can be merged." The model generalizes that to every merge surface.

**Correct pattern:** The SOAP `merge()` call is narrower: "The supported object types are Lead, Contact, Account, Person Account, and Individual." Case is not among them. Merge cases from Apex or the Lightning UI, and have the integration call into Apex rather than issuing `merge()` directly.

**Detection hint:** Look for `merge()` request bodies or WSDL-typed merge calls naming Case, and for claims that Apex and SOAP merge support the same objects. They do not.

---

## Anti-Pattern 4: Querying SOQL Inside the Entitlement Association Loop

**What the LLM generates:**

```apex
for (Case c : Trigger.new) {
    if (c.EntitlementId == null && c.ContactId != null) {
        // Query inside loop — hits governor limits at 101 cases
        List<EntitlementContact> ecs = [
            SELECT EntitlementId FROM EntitlementContact
            WHERE ContactId = :c.ContactId LIMIT 1
        ];
        if (!ecs.isEmpty()) {
            c.EntitlementId = ecs[0].EntitlementId;
        }
    }
}
```

The LLM generates the correct intent but places the SOQL inside the loop, hitting the 100 SOQL queries per transaction limit at batch sizes above 100.

**Why it happens:** The LLM optimizes for correctness at a single-record level and does not account for bulk execution. Single-record SOQL patterns are common in training data.

**Correct pattern:**

```apex
// Collect all ContactIds first
Set<Id> contactIds = new Set<Id>();
for (Case c : Trigger.new) {
    if (c.EntitlementId == null && c.ContactId != null) {
        contactIds.add(c.ContactId);
    }
}
// Single SOQL outside loop
Map<Id, Id> contactToEntitlement = new Map<Id, Id>();
for (EntitlementContact ec : [
    SELECT ContactId, EntitlementId FROM EntitlementContact
    WHERE ContactId IN :contactIds AND Entitlement.Status = 'Active'
]) {
    if (!contactToEntitlement.containsKey(ec.ContactId)) {
        contactToEntitlement.put(ec.ContactId, ec.EntitlementId);
    }
}
// Apply results
for (Case c : Trigger.new) {
    if (c.EntitlementId == null && contactToEntitlement.containsKey(c.ContactId)) {
        c.EntitlementId = contactToEntitlement.get(c.ContactId);
    }
}
```

**Detection hint:** Look for `[SELECT` inside a `for (Case c :` loop body. Any SOQL inside a trigger loop is a bulkification violation.

---

## Anti-Pattern 5: Assuming Entitlement Auto-Association Works Without a Trigger When EntitlementContact Is Used

**What the LLM generates:** The LLM advises enabling "Auto-create Entitlement Contacts" in Setup and asserts that entitlements will be automatically associated to new cases. It omits the trigger entirely.

**Why it happens:** Salesforce does support account-level entitlement auto-association without a trigger. The LLM generalizes this to all entitlement configurations, not knowing that contact-specific coverage via `EntitlementContact` requires a trigger to resolve the correct entitlement.

**Correct pattern:** When `EntitlementContact` junction records are the coverage mechanism, a `Before Insert` trigger is required to query `EntitlementContact` and stamp `Case.EntitlementId`. Account-level auto-association does not cover contact-specific entitlements.

**Detection hint:** Look for advice like "enable auto-association in Setup and no Apex is needed" when the user has mentioned named contacts or `EntitlementContact` records. This advice is incomplete for contact-specific entitlement models.

---

## Anti-Pattern 6: Creating a Second `CaseTrigger` Instead of Extending the Existing One

**What the LLM generates:** The LLM scaffolds a new `trigger CaseTrigger2 on Case (after update)` (or a differently named trigger file) when the user asks to add case close milestone logic to an org that already has a `CaseTrigger`.

**Why it happens:** The LLM does not check for existing triggers before generating new ones. It generates the minimal code for the stated requirement without considering the org-level constraint that multiple triggers on the same object are allowed but anti-pattern.

**Correct pattern:** Check for existing triggers on Case before generating any new trigger. If one exists, add the new logic to the existing handler class and route to it from the existing trigger body. Multiple triggers on the same object have non-deterministic execution order and make debugging significantly harder.

**Detection hint:** If the response includes a `trigger` declaration on `Case` without first confirming there is no existing `CaseTrigger`, treat it as a potential duplicate.
