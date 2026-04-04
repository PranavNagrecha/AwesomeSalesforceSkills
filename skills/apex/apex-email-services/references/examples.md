# Examples — Apex Email Services

## Example 1: Support Ticket Auto-Creation from Vendor Alerts

**Context:** A logistics company receives automated alert emails from a third-party warehouse management system. Each email subject contains a warehouse code and alert type. The team wants these to create Cases in Salesforce automatically, assigned to the correct support queue based on warehouse region — without switching to Email-to-Case (which the org already uses for customer email on a different address).

**Problem:** Email-to-Case is already in use and cannot be repurposed. The alert emails have structured subjects (`[WH-EAST-042] HIGH_TEMP_ALERT`) that must be parsed. Declarative tools cannot extract the warehouse code and look up the correct queue in a single step without complex Flow logic.

**Solution:**

```apex
global class WarehouseAlertEmailHandler implements Messaging.InboundEmailHandler {

    global Messaging.InboundEmailResult handleInboundEmail(
        Messaging.InboundEmail email,
        Messaging.InboundEnvelope envelope
    ) {
        Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();

        try {
            // Parse warehouse code from subject: [WH-EAST-042] HIGH_TEMP_ALERT
            Pattern p = Pattern.compile('\\[([A-Z0-9\\-]+)\\]\\s+([A-Z_]+)');
            Matcher m = p.matcher(email.subject != null ? email.subject : '');

            if (!m.find()) {
                result.success = false;
                result.message = 'Subject did not match expected format: ' + email.subject;
                return result;
            }

            String warehouseCode = m.group(1);   // e.g. WH-EAST-042
            String alertType     = m.group(2);   // e.g. HIGH_TEMP_ALERT

            // Look up queue ID from Custom Metadata (avoids hardcoded IDs)
            List<Warehouse_Queue_Mapping__mdt> mappings = [
                SELECT Queue_Id__c FROM Warehouse_Queue_Mapping__mdt
                WHERE Warehouse_Code__c = :warehouseCode
                LIMIT 1
            ];

            Id queueId = mappings.isEmpty() ? null : mappings[0].Queue_Id__c;

            Case c = new Case(
                Subject      = email.subject,
                Description  = email.plainTextBody != null
                                   ? email.plainTextBody
                                   : email.htmlBody,
                Origin       = 'Email',
                Status       = 'New',
                Priority     = alertType.contains('HIGH') ? 'High' : 'Medium',
                OwnerId      = queueId
            );
            insert c;

            result.success = true;

        } catch (Exception e) {
            result.success = false;
            result.message = 'Handler error: ' + e.getMessage();
        }

        return result;
    }
}
```

**Why it works:** Pattern matching extracts structured data from the subject reliably. Custom Metadata drives queue routing without hardcoding IDs, making the handler environment-safe (no ID differences between sandbox and production). The handler always returns a result — success or failure — so Email Services can apply the configured Error Action if anything goes wrong.

---

## Example 2: CSV Attachment Import via Async Queueable

**Context:** A finance team receives a daily CSV export from their ERP system, emailed to a Salesforce address. Each CSV has up to 500 rows of invoice data. The team wants these rows automatically inserted as `Invoice__c` records.

**Problem:** Parsing 500 rows of CSV inline inside `handleInboundEmail` risks hitting CPU time limits (10,000 ms for synchronous Apex) and heap limits (12 MB). A naive synchronous approach fails under production load.

**Solution:**

```apex
// Step 1: Handler — accept the email, store attachment, enqueue work
global class InvoiceCsvEmailHandler implements Messaging.InboundEmailHandler {

    global Messaging.InboundEmailResult handleInboundEmail(
        Messaging.InboundEmail email,
        Messaging.InboundEnvelope envelope
    ) {
        Messaging.InboundEmailResult result = new Messaging.InboundEmailResult();

        try {
            if (email.textAttachments == null || email.textAttachments.isEmpty()) {
                result.success = false;
                result.message = 'No text attachments found.';
                return result;
            }

            // Store the raw CSV as a ContentVersion to preserve it
            Messaging.InboundEmail.TextAttachment csv = email.textAttachments[0];
            ContentVersion cv = new ContentVersion(
                Title           = csv.fileName,
                PathOnClient    = csv.fileName,
                VersionData     = Blob.valueOf(csv.body),
                IsMajorVersion  = true
            );
            insert cv;

            // Enqueue async processing — handler returns immediately
            System.enqueueJob(new InvoiceCsvQueueable(cv.Id));
            result.success = true;

        } catch (Exception e) {
            result.success = false;
            result.message = e.getMessage();
        }

        return result;
    }
}

// Step 2: Queueable — does the heavy parsing in a separate transaction
public class InvoiceCsvQueueable implements Queueable {

    private Id contentVersionId;

    public InvoiceCsvQueueable(Id cvId) {
        this.contentVersionId = cvId;
    }

    public void execute(QueueableContext ctx) {
        ContentVersion cv = [
            SELECT VersionData FROM ContentVersion WHERE Id = :contentVersionId LIMIT 1
        ];
        String csvBody = cv.VersionData.toString();
        List<Invoice__c> toInsert = new List<Invoice__c>();

        for (String line : csvBody.split('\n')) {
            if (String.isBlank(line)) continue;
            List<String> cols = line.split(',');
            if (cols.size() < 3) continue;
            toInsert.add(new Invoice__c(
                InvoiceNumber__c = cols[0].trim(),
                Amount__c        = Decimal.valueOf(cols[1].trim()),
                DueDate__c       = Date.valueOf(cols[2].trim())
            ));
        }

        if (!toInsert.isEmpty()) {
            insert toInsert;
        }
    }
}
```

**Why it works:** The handler's only job is to accept the email and persist the attachment — both are fast, low-limit operations. All parsing and DML happens inside `InvoiceCsvQueueable`, which runs in its own governor limit budget (separate heap, CPU, and SOQL allocations). The ContentVersion record acts as a durable handoff point between the two transactions.

---

## Anti-Pattern: Parsing Both Body Fields Without Null Guards

**What practitioners do:** Implement the handler assuming `email.plainTextBody` is always populated, then use `.split()` or `.contains()` on it directly.

```apex
// WRONG — crashes on HTML-only emails
String body = email.plainTextBody;
if (body.contains('ORDER-')) {
    // NullPointerException when body is null
}
```

**What goes wrong:** HTML-only emails (sent by many email clients by default) leave `plainTextBody` as `null`. Calling any method on null in Apex throws a `NullPointerException`. The handler sets `success = false`, triggering whatever Error Action is configured — often a bounce back to the sender, which looks like a platform failure.

**Correct approach:** Always guard both body fields and coalesce:

```apex
String body = email.plainTextBody != null
    ? email.plainTextBody
    : (email.htmlBody != null ? email.htmlBody.stripHtmlTags() : '');

if (body.contains('ORDER-')) {
    // Safe — body is never null
}
```
