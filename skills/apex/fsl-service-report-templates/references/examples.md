# Examples — FSL Service Report Templates

## Example 1: Async Service Report Generation on ServiceAppointment Completion

**Context:** A Field Service org wants to automatically generate and attach a service report PDF whenever a ServiceAppointment transitions to `Completed` status.

**Problem:** Calling `ConnectApi.FieldService.createServiceReport()` synchronously inside an Apex trigger causes CPU limit failures for bulk status updates (e.g., dispatcher completing 20 appointments at once via list view). The synchronous call also risks lock contention on ContentDocument inserts.

**Solution:**

Define a Queueable to handle the generation asynchronously:

```apex
public class ServiceReportGenerationQueueable implements Queueable {
    private final Id serviceAppointmentId;
    private final Id templateId;

    public ServiceReportGenerationQueueable(Id saId, Id tplId) {
        this.serviceAppointmentId = saId;
        this.templateId = tplId;
    }

    public void execute(QueueableContext ctx) {
        try {
            ConnectApi.ServiceReport report =
                ConnectApi.FieldService.createServiceReport(
                    serviceAppointmentId,
                    templateId
                );
            // report.id is the ContentDocument Id — log or store if needed
        } catch (ConnectApi.ConnectApiException e) {
            // Log to a custom error object; do not re-throw in Queueable
            System.debug('Service report generation failed: ' + e.getMessage());
        }
    }
}
```

Trigger the Queueable from a Record-Triggered Flow (Apex Action) or a lightweight trigger:

```apex
// Trigger fragment — fires on ServiceAppointment after update
for (ServiceAppointment sa : Trigger.new) {
    ServiceAppointment old = Trigger.oldMap.get(sa.Id);
    if (sa.Status == 'Completed' && old.Status != 'Completed') {
        // Query the Work Type default template Id
        Id tplId = getDefaultTemplateId(sa.WorkTypeId);
        System.enqueueJob(new ServiceReportGenerationQueueable(sa.Id, tplId));
    }
}
```

**Why it works:** Running in a Queueable gives a fresh governor limit context (CPU, callout budget) separate from the trigger transaction. The platform's `createServiceReport` action internally performs a REST hop to render the PDF, which cannot be done reliably inside bulk trigger execution.

---

## Example 2: Querying the Generated PDF ContentDocument

**Context:** After a service report is generated, a downstream process needs to retrieve the ContentDocument Id (e.g., to email it to the customer or send it via a third-party API).

**Problem:** Practitioners often query `ContentDocument` directly without knowing the `ContentDocumentLink` junction object pattern required to find documents linked to a specific record.

**Solution:**

```apex
public static Id getLatestServiceReportDocumentId(Id serviceAppointmentId) {
    List<ContentDocumentLink> links = [
        SELECT ContentDocumentId, ContentDocument.Title,
               ContentDocument.CreatedDate, ContentDocument.FileType
        FROM ContentDocumentLink
        WHERE LinkedEntityId = :serviceAppointmentId
          AND ContentDocument.FileType = 'PDF'
        ORDER BY ContentDocument.CreatedDate DESC
        LIMIT 1
    ];

    if (links.isEmpty()) {
        return null;
    }
    return links[0].ContentDocumentId;
}
```

To also get the download URL for use in an email or REST response:

```apex
String baseUrl = URL.getSalesforceBaseUrl().toExternalForm();
String downloadUrl = baseUrl + '/sfc/servlet.shepherd/document/download/' + documentId;
```

**Why it works:** Service reports are stored as `ContentDocument` records linked to the source WorkOrder or ServiceAppointment via `ContentDocumentLink`. Filtering by `FileType = 'PDF'` and ordering by `CreatedDate DESC` ensures retrieval of the most recently generated report when multiple reports exist on a single record.

---

## Example 3: Verifying DigitalSignature Before Generating Report

**Context:** A client requires the customer signature to always appear in the service report. The report is auto-generated on completion but signatures are sometimes missing because the technician's mobile device hasn't synced yet.

**Problem:** Without a signature-existence check, the platform generates the PDF immediately and the signature block renders blank. Regenerating later is cumbersome and confusing for customers.

**Solution:**

Add a check in the Queueable before calling `createServiceReport`:

```apex
public void execute(QueueableContext ctx) {
    List<DigitalSignature> sigs = [
        SELECT Id, Status, SignatureType
        FROM DigitalSignature
        WHERE ParentId = :serviceAppointmentId
          AND SignatureType = 'Customer'
          AND Status = 'Captured'
        LIMIT 1
    ];

    if (sigs.isEmpty()) {
        // Re-enqueue after a short delay using a Schedulable pattern
        // or record the pending state to a custom object for retry
        System.debug('Customer signature not yet available — deferring report generation');
        return;
    }

    ConnectApi.FieldService.createServiceReport(serviceAppointmentId, templateId);
}
```

**Why it works:** `DigitalSignature` records are synced from the mobile device before the parent ServiceAppointment status update propagates, in most connectivity conditions. Checking for a `Captured` Customer signature before rendering guarantees it will appear in the PDF. For persistent sync delays, a retry mechanism (Schedulable or Platform Event) provides resilience.

---

## Anti-Pattern: Building Service Report Templates as Custom Visualforce Pages

**What practitioners do:** Create a Visualforce page styled like a service report, add it to a custom button on Work Order, and call it a "service report template". They pass the WorkOrder Id as a URL parameter and render fields inline.

**What goes wrong:**
- The generated output is an HTML page, not a formal PDF with the platform's content versioning, ContentDocument linkage, or offline availability.
- DigitalSignature records do not integrate with custom VF pages.
- Offline mobile support is impossible.
- FSL mobile app "Service Reports" tab does not surface custom VF pages.
- Signature capture on mobile relies on the `DigitalSignature` object, which only integrates with `ServiceReportLayout`-based or Document Builder templates.

**Correct approach:** Use `ServiceReportLayout` configured in Setup and generate via `ConnectApi.FieldService.createServiceReport()`. For conditional sections, use Document Builder (Winter '25+). Custom Visualforce is not the service report mechanism in FSL.
