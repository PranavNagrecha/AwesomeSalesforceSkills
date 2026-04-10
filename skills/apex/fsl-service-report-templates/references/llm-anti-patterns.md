# LLM Anti-Patterns — FSL Service Report Templates

Common mistakes AI coding assistants make when generating or advising on FSL service report templates.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting a Custom Visualforce Page as the Service Report Template Mechanism

**What the LLM generates:** A custom Visualforce page that accepts a WorkOrder Id as a URL parameter, queries related fields, and renders them as a styled HTML report. The LLM presents this as how to "build a service report template" in Field Service.

**Why it happens:** The LLM conflates FSL service reports with CPQ quote templates and Salesforce document generation patterns where Visualforce is a standard approach. Training data contains many Visualforce-based document generation examples.

**Correct pattern:**

```
Service report templates in FSL are NOT Visualforce pages.
Templates are ServiceReportLayout records configured via Setup > Field Service > Service Report Templates.
PDFs are generated via:
  ConnectApi.FieldService.createServiceReport(serviceAppointmentId, templateId)
The platform renders the PDF from the ServiceReportLayout — Apex does not render HTML.
```

**Detection hint:** Look for `PageReference`, `<apex:page>`, or `renderAs="pdf"` in any code presented as a service report solution. These are the wrong mechanism.

---

## Anti-Pattern 2: Calling createServiceReport Synchronously in a Trigger

**What the LLM generates:**

```apex
trigger ServiceAppointmentTrigger on ServiceAppointment (after update) {
    for (ServiceAppointment sa : Trigger.new) {
        if (sa.Status == 'Completed') {
            ConnectApi.FieldService.createServiceReport(sa.Id, templateId);
        }
    }
}
```

**Why it happens:** The LLM generates simple, direct patterns. It does not model the governor limit implications of synchronous PDF generation within a DML trigger context, especially under bulk load.

**Correct pattern:**

```apex
// Enqueue asynchronously — createServiceReport is slow (2-5s) and CPU-intensive
trigger ServiceAppointmentTrigger on ServiceAppointment (after update) {
    for (ServiceAppointment sa : Trigger.new) {
        ServiceAppointment old = Trigger.oldMap.get(sa.Id);
        if (sa.Status == 'Completed' && old.Status != 'Completed') {
            System.enqueueJob(new ServiceReportGenerationQueueable(sa.Id, templateId));
        }
    }
}
```

**Detection hint:** Any `ConnectApi.FieldService.createServiceReport(` call that appears directly inside a trigger body (not inside a Queueable `execute` method) is the anti-pattern. Also check for missing old-value guard.

---

## Anti-Pattern 3: Assuming Conditional Sections Are Supported in Classic Templates

**What the LLM generates:** Instructions to use the ServiceReportLayout Setup builder to add conditional logic — e.g., "click the section visibility toggle and add your condition based on Work Type". Or code that tries to dynamically choose fields in a single template based on data values.

**Why it happens:** LLMs trained on general Salesforce documentation may generalize from CPQ, Quote Templates, or Document Builder features that do support conditional visibility — incorrectly applying that knowledge to the older ServiceReportLayout builder.

**Correct pattern:**

```
Classic ServiceReportLayout (Setup > Field Service > Service Report Templates)
does NOT support conditional section visibility.
All sections always render.

For conditional sections, options are:
  1. Document Builder (Winter '25+) — supports Flow-driven conditional sections
  2. Multiple ServiceReportLayout templates — one per work category, selected programmatically
     based on Work Type in the createServiceReport call
```

**Detection hint:** Any response that references "conditional" or "dynamic" section configuration within the classic Service Report Template Setup UI is incorrect.

---

## Anti-Pattern 4: Forgetting Offline Briefcase Builder Priming After Template Changes

**What the LLM generates:** Complete service report template setup instructions that omit any mention of Briefcase Builder priming for offline support. The LLM focuses on ServiceReportLayout configuration and Apex generation without noting the offline data dependency.

**Why it happens:** Briefcase Builder is a separate FSL configuration area. LLMs do not consistently model the cross-feature dependency between template field references and Briefcase priming rules, especially since offline failure (blank fields) is silent and not an error.

**Correct pattern:**

```
After finalizing ServiceReportLayout template fields, always:
1. Enumerate every field referenced in every template section
2. Open Setup > Briefcase Builder > [your record type priming rule]
3. Confirm each template field is included in the priming configuration
4. Re-prime all mobile devices after adding fields

Skipping this step causes offline PDFs to render blank fields silently.
```

**Detection hint:** Any service report template setup guidance that does not mention Briefcase Builder or offline field priming is incomplete for orgs with FSL mobile usage.

---

## Anti-Pattern 5: Querying ContentDocument Directly Without ContentDocumentLink

**What the LLM generates:**

```apex
// WRONG — this query has no filter on the linked record
List<ContentDocument> docs = [
    SELECT Id, Title FROM ContentDocument
    WHERE Title LIKE '%Service Report%'
    LIMIT 1
];
```

**Why it happens:** LLMs often generate direct ContentDocument queries without understanding the ContentDocumentLink junction object pattern required to filter documents by their linked record. This returns unrelated documents and is not scoped to the target WorkOrder or ServiceAppointment.

**Correct pattern:**

```apex
List<ContentDocumentLink> links = [
    SELECT ContentDocumentId, ContentDocument.Title, ContentDocument.CreatedDate
    FROM ContentDocumentLink
    WHERE LinkedEntityId = :serviceAppointmentId
      AND ContentDocument.FileType = 'PDF'
    ORDER BY ContentDocument.CreatedDate DESC
    LIMIT 1
];
```

**Detection hint:** Any `SELECT ... FROM ContentDocument WHERE Title LIKE ...` query without a `ContentDocumentLink` join or subquery when the goal is to find the report attached to a specific WorkOrder/ServiceAppointment record.

---

## Anti-Pattern 6: Treating DigitalSignature as Auto-Available at Report Generation Time

**What the LLM generates:** Code that calls `createServiceReport` immediately after a ServiceAppointment status update, with a comment like "the signature will be included automatically because it's linked to the record".

**Why it happens:** The LLM models DigitalSignature as a standard lookup that is always in sync, without accounting for the race condition between mobile device sync and server-side trigger execution.

**Correct pattern:**

```apex
// Check signature is synced before generating report
List<DigitalSignature> sigs = [
    SELECT Id FROM DigitalSignature
    WHERE ParentId = :serviceAppointmentId
      AND SignatureType = 'Customer'
      AND Status = 'Captured'
    LIMIT 1
];
if (!sigs.isEmpty()) {
    ConnectApi.FieldService.createServiceReport(serviceAppointmentId, templateId);
} else {
    // Defer — signature not yet synced
}
```

**Detection hint:** Any `createServiceReport` call triggered automatically on ServiceAppointment status change that does not include a DigitalSignature existence check before the call.
