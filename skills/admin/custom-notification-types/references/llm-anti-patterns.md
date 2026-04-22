# LLM Anti-Patterns — Custom Notification Types

Common mistakes AI coding assistants make with custom notifications.

## Anti-Pattern 1: Hard-coding the Notification Type Id

**What the LLM generates:** `n.setNotificationTypeId('0ML...');`

**Why it happens:** Model copies an ID seen in training data.

**Correct pattern:**

```
Id typeId = [SELECT Id FROM CustomNotificationType
             WHERE DeveloperName = 'Opportunity_Won_Notif' LIMIT 1].Id;
n.setNotificationTypeId(typeId);

Or cache via Custom Metadata Type. IDs differ per org.
```

**Detection hint:** Apex literal starting with `0ML` passed to setNotificationTypeId.

---

## Anti-Pattern 2: Sending to >500 recipients in one call

**What the LLM generates:** `n.send(allUserIds)` where `allUserIds` has 2,000 entries.

**Why it happens:** Model doesn't know the 500-per-call cap.

**Correct pattern:**

```
Integer BATCH = 500;
List<Id> all = new List<Id>(userIds);
for (Integer i = 0; i < all.size(); i += BATCH) {
    Integer end = Math.min(i + BATCH, all.size());
    n.send(new Set<String>(all.subList(i, end)));
}
```

**Detection hint:** Apex passing a variable-length set directly to `n.send(...)` without chunking.

---

## Anti-Pattern 3: Setting title/body over character limits

**What the LLM generates:** A 300-char title; a 2,000-char body.

**Why it happens:** Model doesn't know the caps.

**Correct pattern:**

```
Title: up to 64 characters.
Body: up to 750 characters.

Truncate defensively:
n.setTitle(title.abbreviate(64));
n.setBody(body.abbreviate(750));
```

**Detection hint:** Apex `setTitle` / `setBody` with string literals longer than the caps, or concatenated strings with no length guard.

---

## Anti-Pattern 4: Expecting silent delivery failure to throw

**What the LLM generates:** A `try { n.send(...) } catch (Exception e) { ... }` expecting invalid IDs to throw.

**Why it happens:** Model applies general error-handling intuition.

**Correct pattern:**

```
Invalid recipient IDs cause silent drops — no exception thrown.
Log the send attempt explicitly and verify delivery out-of-band
(e.g., Platform Event marker, debug log correlation ID).
Don't rely on try/catch to detect delivery issues.
```

**Detection hint:** Apex expecting send() to throw on bad recipients.

---

## Anti-Pattern 5: Using CustomNotification for transactional email

**What the LLM generates:** Sends an "invoice ready" notification via CustomNotification only.

**Why it happens:** Model conflates notification channels.

**Correct pattern:**

```
CustomNotification is for push/desktop alerts — ephemeral. Persistent
transactional messages (invoices, receipts) belong in email via
Messaging.SingleEmailMessage. Combine: email for record, push for
attention nudge. Don't rely on a push alone for audit-worthy events.
```

**Detection hint:** Flow or Apex sending a CustomNotification for financial / compliance events with no email alert.
