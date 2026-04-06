# LLM Anti-Patterns — Apex Email Services

Common mistakes AI coding assistants make when generating or advising on inbound Apex email services.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Returning SUCCESS even when processing fails

**What the LLM generates:**

```apex
public Messaging.InboundEmailResult handleInboundEmail(
    Messaging.InboundEmail email, Messaging.InboundEnvelope envelope
) {
    Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();
    try {
        insert new Case(Subject = email.subject);
    } catch (Exception e) {
        System.debug('Error: ' + e.getMessage());
    }
    result.success = true; // Always returns true
    return result;
}
```

**Why it happens:** LLMs default to swallowing exceptions and returning success. When `result.success` is always `true`, the sender never gets a bounce notification, and failures are silently lost.

**Correct pattern:**

```apex
public Messaging.InboundEmailResult handleInboundEmail(
    Messaging.InboundEmail email, Messaging.InboundEnvelope envelope
) {
    Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();
    try {
        insert new Case(Subject = email.subject);
        result.success = true;
    } catch (Exception e) {
        result.success = false;
        result.message = 'Failed to process email: ' + e.getMessage();
        LogService.logError('InboundEmailHandler', e);
    }
    return result;
}
```

**Detection hint:** `result\.success\s*=\s*true` appearing outside a `try` block, or no `result.success = false` branch anywhere in the method.

---

## Anti-Pattern 2: Ignoring the difference between TextAttachments and BinaryAttachments

**What the LLM generates:**

```apex
if (email.binaryAttachments != null) {
    for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
        insert new ContentVersion(
            Title = att.fileName, VersionData = att.body, PathOnClient = att.fileName
        );
    }
}
// textAttachments completely ignored
```

**Why it happens:** LLMs only generate the `binaryAttachments` loop and forget that plain text attachments (`.csv`, `.txt`, `.ics`) arrive in `textAttachments` with a `String body` instead of a `Blob body`. Those attachments are silently dropped.

**Correct pattern:**

```apex
List<ContentVersion> versions = new List<ContentVersion>();
if (email.binaryAttachments != null) {
    for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
        versions.add(new ContentVersion(
            Title = att.fileName, VersionData = att.body, PathOnClient = att.fileName
        ));
    }
}
if (email.textAttachments != null) {
    for (Messaging.InboundEmail.TextAttachment att : email.textAttachments) {
        versions.add(new ContentVersion(
            Title = att.fileName, VersionData = Blob.valueOf(att.body), PathOnClient = att.fileName
        ));
    }
}
if (!versions.isEmpty()) {
    insert versions;
}
```

**Detection hint:** `binaryAttachments` present but no reference to `textAttachments` in the same handler class.

---

## Anti-Pattern 3: Performing DML per-attachment inside a loop

**What the LLM generates:**

```apex
for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
    insert new ContentVersion(Title = att.fileName, VersionData = att.body, PathOnClient = att.fileName);
}
```

**Why it happens:** LLMs generate single-record patterns by default. An email with many attachments hits the DML statement limit when combined with other transaction work.

**Correct pattern:**

```apex
List<ContentVersion> versions = new List<ContentVersion>();
for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
    versions.add(new ContentVersion(
        Title = att.fileName, VersionData = att.body, PathOnClient = att.fileName
    ));
}
if (!versions.isEmpty()) {
    insert versions;
}
```

**Detection hint:** `insert ` appearing inside a `for.*Attachment` loop.

---

## Anti-Pattern 4: Not null-checking the email body before parsing

**What the LLM generates:**

```apex
String body = email.plainTextBody;
List<String> lines = body.split('\n'); // NullPointerException if body is null
```

**Why it happens:** LLMs assume `plainTextBody` always exists. Some emails are HTML-only or have no body at all, making `plainTextBody` null.

**Correct pattern:**

```apex
String body = email.plainTextBody;
if (String.isBlank(body)) {
    body = email.htmlBody != null ? email.htmlBody.stripHtmlTags() : '';
}
if (String.isBlank(body)) {
    result.success = false;
    result.message = 'Email had no parseable body content.';
    return result;
}
List<String> lines = body.split('\n');
```

**Detection hint:** `email\.plainTextBody` used without a preceding null or `isBlank` check.

---

## Anti-Pattern 5: Running the handler without validating the sender

**What the LLM generates:**

```apex
public Messaging.InboundEmailResult handleInboundEmail(
    Messaging.InboundEmail email, Messaging.InboundEnvelope envelope
) {
    // Immediately create a record from whoever sent the email
    insert new Case(Subject = email.subject, SuppliedEmail = email.fromAddress);
    // ...
}
```

**Why it happens:** LLMs do not consider that email services run in system context and any external sender can email the service address. Without sender validation, anyone can create records in the org.

**Correct pattern:**

```apex
List<Contact> senders = [
    SELECT Id, AccountId FROM Contact WHERE Email = :email.fromAddress LIMIT 1
];
if (senders.isEmpty()) {
    result.success = false;
    result.message = 'Sender not recognized: ' + email.fromAddress;
    return result;
}
insert new Case(Subject = email.subject, ContactId = senders[0].Id, AccountId = senders[0].AccountId);
result.success = true;
```

**Detection hint:** `handleInboundEmail` method with no reference to `fromAddress` validation or sender lookup before DML.

---

## Anti-Pattern 6: Writing tests that pass null for the InboundEnvelope

**What the LLM generates:**

```apex
@IsTest
static void testHandler() {
    Messaging.InboundEmail email = new Messaging.InboundEmail();
    email.subject = 'Test';
    MyHandler handler = new MyHandler();
    handler.handleInboundEmail(email, null); // null envelope
}
```

**Why it happens:** LLMs generate minimal test setup. Passing a `null` envelope or skipping required fields like `fromAddress` does not exercise real code paths and may NPE on envelope access in production.

**Correct pattern:**

```apex
@IsTest
static void testHandler() {
    Messaging.InboundEmail email = new Messaging.InboundEmail();
    email.subject = 'Test Case Creation';
    email.fromAddress = 'test@example.com';
    email.plainTextBody = 'Body content.';

    Messaging.InboundEnvelope envelope = new Messaging.InboundEnvelope();
    envelope.fromAddress = 'test@example.com';
    envelope.toAddress = 'service@org.salesforce.com';

    insert new Contact(LastName = 'Test', Email = 'test@example.com');

    Test.startTest();
    Messaging.InboundEmailResult result = new MyHandler().handleInboundEmail(email, envelope);
    Test.stopTest();

    System.assert(result.success, 'Handler should succeed for known sender');
    System.assertEquals(1, [SELECT COUNT() FROM Case WHERE Subject = 'Test Case Creation']);
}
```

**Detection hint:** `handleInboundEmail\(.*,\s*null\)` in test classes.
