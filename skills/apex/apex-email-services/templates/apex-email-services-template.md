# Apex Email Services — Work Template

Use this template when implementing or reviewing an inbound Apex Email Service.

---

## Scope

**Skill:** `apex-email-services`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before writing any code:

- **Org edition:** (Developer / Professional / Enterprise / Unlimited — affects daily limit)
- **Expected daily email volume:** (confirm it is within the 1,000/day default limit)
- **Sender identity:** (known internal system / external customer / unknown — drives Accept Email From policy)
- **Email body format:** (plain text / HTML / both — drives null-guard strategy)
- **Attachment types and sizes:** (none / small text CSV / large binary PDFs — drives sync vs async decision)
- **Target sObject:** (Case / custom / multiple — drives DML strategy)
- **Error handling preference:** (bounce back / silent discard — drives Error Action config)

---

## Handler Class

```apex
global class [YourHandlerName] implements Messaging.InboundEmailHandler {

    global Messaging.InboundEmailResult handleInboundEmail(
        Messaging.InboundEmail email,
        Messaging.InboundEnvelope envelope
    ) {
        Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();

        try {
            // --- 1. Validate sender (optional but recommended) ---
            // String sender = email.fromAddress;
            // if (!isAllowedSender(sender)) {
            //     result.success = false;
            //     result.message = 'Sender not authorized: ' + sender;
            //     return result;
            // }

            // --- 2. Parse body (guard both fields) ---
            String body = email.plainTextBody != null
                ? email.plainTextBody
                : (email.htmlBody != null ? email.htmlBody.stripHtmlTags() : '');

            // --- 3. Parse subject ---
            String subject = email.subject != null ? email.subject : '';

            // --- 4. Process text attachments ---
            if (email.textAttachments != null) {
                for (Messaging.InboundEmail.TextAttachment att : email.textAttachments) {
                    // TODO: handle att.fileName, att.body, att.mimeTypeSubType
                }
            }

            // --- 5. Process binary attachments ---
            if (email.binaryAttachments != null) {
                for (Messaging.InboundEmail.BinaryAttachment att : email.binaryAttachments) {
                    // TODO: persist att.body (Blob) to ContentVersion, then enqueue Queueable
                    // ContentVersion cv = new ContentVersion(
                    //     Title = att.fileName,
                    //     PathOnClient = att.fileName,
                    //     VersionData = att.body,
                    //     IsMajorVersion = true
                    // );
                    // insert cv;
                    // System.enqueueJob(new [YourQueueable](cv.Id));
                }
            }

            // --- 6. Create or update target record ---
            // [SObject__c] record = new [SObject__c](
            //     Subject__c = subject,
            //     Body__c    = body
            // );
            // insert record;

            result.success = true;

        } catch (Exception e) {
            // Log the error for visibility
            System.debug(LoggingLevel.ERROR, 'EmailHandler error: ' + e.getMessage());
            result.success = false;
            result.message = e.getMessage();
        }

        return result;
    }
}
```

---

## Email Service Configuration (Setup > Email Services)

| Setting | Value to Set |
|---|---|
| Name | [Descriptive name for this integration] |
| Apex Class | [YourHandlerName] |
| Active | **Checked** (critical — inactive = silent discard) |
| Accept Email From | [sender domain or specific address; blank = accept all] |
| Error Action | Bounce Message / Discard Message / Requeue Message |
| Over Email Rate Limit | Bounce Message / Discard Message / Requeue Message |

After saving, copy the generated Email Service Address and provide it to the sending system.

---

## Test Class Skeleton

```apex
@IsTest
private class [YourHandlerName]Test {

    @IsTest
    static void testSuccessfulProcessing() {
        // Arrange
        Messaging.InboundEmail email = new Messaging.InboundEmail();
        email.subject       = '[TEST-001] SAMPLE_SUBJECT';
        email.plainTextBody = 'Sample email body content.';
        email.fromAddress   = 'sender@example.com';

        Messaging.InboundEnvelope env = new Messaging.InboundEnvelope();
        env.toAddress   = 'handler@abc.salesforce.com';
        env.fromAddress = 'sender@example.com';

        // Act
        Test.startTest();
        [YourHandlerName] handler = new [YourHandlerName]();
        Messaging.InboundEmailResult result = handler.handleInboundEmail(email, env);
        Test.stopTest();

        // Assert
        System.assertEquals(true, result.success, 'Handler should succeed for valid email');
        // Add DML assertions here, e.g.:
        // System.assertEquals(1, [SELECT COUNT() FROM YourObject__c WHERE ...]);
    }

    @IsTest
    static void testNullPlainTextBody() {
        // Validates null guard — HTML-only email scenario
        Messaging.InboundEmail email = new Messaging.InboundEmail();
        email.subject       = 'Test subject';
        email.plainTextBody = null;
        email.htmlBody      = '<p>HTML only content</p>';
        email.fromAddress   = 'sender@example.com';

        Messaging.InboundEnvelope env = new Messaging.InboundEnvelope();

        Test.startTest();
        [YourHandlerName] handler = new [YourHandlerName]();
        Messaging.InboundEmailResult result = handler.handleInboundEmail(email, env);
        Test.stopTest();

        // Should not throw NullPointerException
        System.assertNotEquals(null, result, 'Result must never be null');
    }

    @IsTest
    static void testTextAttachmentProcessing() {
        Messaging.InboundEmail email = new Messaging.InboundEmail();
        email.subject       = 'Attachment test';
        email.plainTextBody = 'See attached.';
        email.fromAddress   = 'sender@example.com';

        Messaging.InboundEmail.TextAttachment att = new Messaging.InboundEmail.TextAttachment();
        att.fileName        = 'data.csv';
        att.body            = 'col1,col2\nval1,val2\n';
        att.mimeTypeSubType = 'plain';
        email.textAttachments = new List<Messaging.InboundEmail.TextAttachment>{ att };

        Messaging.InboundEnvelope env = new Messaging.InboundEnvelope();

        Test.startTest();
        [YourHandlerName] handler = new [YourHandlerName]();
        Messaging.InboundEmailResult result = handler.handleInboundEmail(email, env);
        Test.stopTest();

        System.assertEquals(true, result.success);
    }
}
```

---

## Checklist

Work through this before marking the implementation complete:

- [ ] Handler class is `global` and implements `Messaging.InboundEmailHandler`
- [ ] `handleInboundEmail` always returns a non-null `InboundEmailResult`
- [ ] `try/catch` block wraps all business logic; exception sets `result.success = false`
- [ ] `plainTextBody` and `htmlBody` null guards are in place
- [ ] `textAttachments` null guard is in place before iteration
- [ ] `binaryAttachments` null guard is in place before iteration
- [ ] Large attachments (> 1 MB) use Queueable pattern — not processed inline
- [ ] Email Service address is **Active** in Setup
- [ ] `Accept Email From` is configured — not left blank for public-facing addresses
- [ ] Error Action and Over Email Rate Limit settings are set intentionally
- [ ] Test class covers success path, null body path, and attachment path
- [ ] Daily volume estimate is within org edition limit

---

## Notes

Record any deviations from the standard pattern and the reason for the deviation:

- (example: "Binary attachment processing is synchronous because files are < 100 KB and volume is < 10/day")
