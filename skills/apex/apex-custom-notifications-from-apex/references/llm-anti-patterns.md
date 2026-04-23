# LLM Anti-Patterns — Apex Custom Notifications From Apex

## Anti-Pattern 1: Hardcoding Notification Type Id

**What the LLM generates:**

```apex
n.setNotificationTypeId('0MLxx0000004DfK');
```

**Why it happens:** LLMs see sample Ids in documentation and reproduce them literally. They don't know Ids are org-specific.

**Correct pattern:**

```apex
Id typeId = [SELECT Id FROM CustomNotificationType
             WHERE DeveloperName = 'Case_Escalation' LIMIT 1].Id;
n.setNotificationTypeId(typeId);
```

**Detection hint:** A string literal Id passed to `setNotificationTypeId`. DeveloperName-based resolution is always correct.

---

## Anti-Pattern 2: Sync Send From A Trigger Without Try/Catch

**What the LLM generates:**

```apex
trigger CaseTrigger on Case (after update) {
    for (Case c : Trigger.new) {
        Messaging.CustomNotification n = new Messaging.CustomNotification();
        // ... configure ...
        n.send(new Set<String>{ c.OwnerId });
    }
}
```

**Why it happens:** LLMs default to "do the thing inline" and don't know platform failures in `send()` abort the DML.

**Correct pattern:** Collect record Ids, enqueue a Queueable, and do the sends there with try/catch.

**Detection hint:** `.send(` called inside a trigger body.

---

## Anti-Pattern 3: Passing Contact Or Account Ids As Recipients

**What the LLM generates:**

```apex
n.send(new Set<String>{ caseRecord.ContactId });
```

**Why it happens:** LLMs treat any record Id as a valid "who" value. Only Users, Groups, and Queues are valid.

**Correct pattern:** Resolve the user via `[SELECT User__c FROM Contact WHERE Id = :contactId]` or a platform relationship, then pass the User Id.

**Detection hint:** `.send(Set<String>{ ... })` with a variable whose name suggests Contact, Account, or a custom object.

---

## Anti-Pattern 4: Not Validating Recipient Id Prefix

**What the LLM generates:**

```apex
Set<String> ids = new Set<String>(userProvidedIds);
n.send(ids);
```

**Why it happens:** LLMs accept the caller's input at face value.

**Correct pattern:**

```apex
Set<String> valid = new Set<String>();
for (String s : userProvidedIds) {
    Id id = (Id) s;
    if (id.getSobjectType() == User.SObjectType ||
        id.getSobjectType() == Group.SObjectType) {
        valid.add(s);
    }
}
n.send(valid);
```

**Detection hint:** Recipient set passed directly from untrusted input to `send` without a type filter.

---

## Anti-Pattern 5: Not Setting `setTargetId`

**What the LLM generates:**

```apex
n.setNotificationTypeId(typeId);
n.setTitle('Case escalated');
n.setBody(body);
n.send(recipients);
```

**Why it happens:** LLMs see the method as optional because many Apex setters are. Omitting `setTargetId` produces a non-clickable notification.

**Correct pattern:** Always call `setTargetId(recordId)` with the record the user should open.

**Detection hint:** A `Messaging.CustomNotification` configured without any `setTargetId` call.

---

## Anti-Pattern 6: Sending The Full Raw Body With HTML

**What the LLM generates:**

```apex
n.setBody(myOpp.LongDescription__c);  // rich text field with HTML
```

**Why it happens:** LLMs don't know mobile push renders plain text and truncates at ~200 chars.

**Correct pattern:** Strip HTML, normalize whitespace, truncate: `n.setBody(TruncationUtil.short(myOpp.LongDescription__c, 190))`.

**Detection hint:** `setBody` argument from a rich-text or long-text field without any truncation or `.stripHtmlTags()`.

---

## Anti-Pattern 7: Querying The Notification Type Inside A Bulk Loop

**What the LLM generates:**

```apex
for (Case c : cases) {
    Id typeId = [SELECT Id FROM CustomNotificationType WHERE DeveloperName = 'X' LIMIT 1].Id;
    // ... send ...
}
```

**Why it happens:** LLMs don't hoist invariants.

**Correct pattern:** Query once before the loop or cache at class scope.

**Detection hint:** SOQL on `CustomNotificationType` inside a `for` or `while` block.

---

## Anti-Pattern 8: Assuming `send` Has A Return Value

**What the LLM generates:**

```apex
Boolean ok = n.send(recipients);
if (!ok) { /* retry */ }
```

**Why it happens:** LLMs invent method signatures. `send()` returns `void` and throws on failure.

**Correct pattern:** `try { n.send(recipients); } catch (Messaging.CustomNotificationException e) { ... }`.

**Detection hint:** Any code that treats the result of `send(...)` as a Boolean or object.
