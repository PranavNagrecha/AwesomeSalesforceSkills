---
name: fsl-service-report-templates
description: "Use this skill when designing, generating, or troubleshooting Field Service service report templates — covers the createServiceReport REST action (API v40.0+), ServiceReportLayout configuration, DigitalSignature capture, Document Builder (Winter '25+) with conditional logic via Flow, and PDF storage as ContentDocument/ContentVersion. NOT for quote templates, custom Visualforce pages, or Experience Cloud document generation."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I generate a service report PDF after a work order or service appointment is completed in Field Service?"
  - "Customer signature is not appearing on the service report or signature capture is not working on mobile"
  - "I need conditional sections on a service report template depending on work type or record values"
  - "Service report PDF shows blank fields when generated offline on the mobile app"
  - "How do I programmatically create a service report from Apex or a Flow?"
tags:
  - field-service
  - fsl
  - service-report
  - service-report-template
  - digital-signature
  - document-builder
  - connectapi
  - pdf-generation
inputs:
  - "Whether service reports are generated manually, via Apex, or via automation (Flow/Process)"
  - "Target record type: WorkOrder or ServiceAppointment"
  - "Whether offline mobile PDF generation is required"
  - "Whether conditional sections or dynamic content are required in the report"
  - "Whether customer signature capture (DigitalSignature) is needed"
  - "API version in use (v40.0+ required for createServiceReport)"
outputs:
  - "Apex code using ConnectApi.FieldService.createServiceReport() to programmatically generate reports"
  - "ServiceReportLayout configuration guidance for Setup UI drag-and-drop builder"
  - "DigitalSignature query pattern for retrieving linked signatures"
  - "Document Builder design guidance for conditional-section and LWC-embedded reports (Winter '25+)"
  - "ContentDocument/ContentVersion query pattern for retrieving generated PDFs"
  - "Briefcase Builder checklist for offline PDF field priming"
dependencies:
  - fsl-work-order-management
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Service Report Templates

This skill activates when building, generating, or troubleshooting Field Service service reports — including Apex-driven generation via the `ConnectApi.FieldService` namespace, ServiceReportLayout setup, customer signature capture via DigitalSignature, offline PDF gaps, and the newer Document Builder (Winter '25+) path for conditional report sections.

---

## Before Starting

Gather this context before working on anything in this domain:

- **FSL managed package installed?** The `ConnectApi.FieldService.createServiceReport()` method requires Field Service (the managed package) to be installed and configured in the org. Without it the method does not exist.
- **Most common wrong assumption:** Practitioners expect service reports to be built as custom Visualforce pages, like quote templates. They are not. Service report templates are configured in Setup via the ServiceReportLayout builder (drag-and-drop). Apex does not render HTML/VF — it invokes the platform REST action `createServiceReport` which produces a PDF from the configured layout.
- **API version constraint:** The `createServiceReport` REST action requires API v40.0 or later. Older connected apps or packages calling it on v39 or below will fail.
- **Offline limitation:** If a technician generates a service report on the FSL mobile app while offline, any field not included in the Briefcase Builder priming configuration will render blank in the PDF. This is a data availability issue, not a template defect.
- **Conditional sections:** The classic ServiceReportLayout Setup builder does NOT support conditional section visibility. If conditional logic is required, Document Builder (Winter '25+) is the only supported platform path.

---

## Core Concepts

### ServiceReportLayout — The Classic Template Builder

Service report templates are stored as `ServiceReportLayout` records and configured in Setup under **Field Service > Service Report Templates**. The builder provides a drag-and-drop canvas. Supported sections include:

- Header / footer with org logo and address
- Work order and service appointment field sections
- Product consumed, time sheet, and related list sections
- Signature placeholders for customer and technician

Templates are associated with Work Types or applied as defaults. A single org can have multiple layouts for different work categories (installation vs. maintenance vs. inspection).

**Limitation:** Conditional section visibility is not supported in the classic builder. All sections in a template always render. This is a known platform gap documented in the FSL Developer Guide.

### createServiceReport — Apex and REST Generation

Service reports are generated programmatically via:

```apex
ConnectApi.ServiceReport result =
    ConnectApi.FieldService.createServiceReport(serviceAppointmentId, serviceReportTemplateId);
```

Or equivalently via REST Composite/sObject API as a named action against a WorkOrder or ServiceAppointment record. Both paths require API v40.0+. The generated PDF is automatically stored as a `ContentDocument` / `ContentVersion` linked to the source record (WorkOrder or ServiceAppointment) via a `ContentDocumentLink`.

The `serviceReportTemplateId` is the `Id` of the `ServiceReportLayout` record to render. If omitted, the platform uses the default template associated with the related Work Type, falling back to the org-level default.

Apex invocation runs synchronously for records with modest field counts but can be slow (2–5 seconds) for data-heavy reports. Trigger contexts with tight CPU limits should invoke it asynchronously via a Queueable.

### DigitalSignature — Customer and Technician Signatures

Customer and technician signatures collected on the FSL mobile app are stored as `DigitalSignature` SObject records. Each `DigitalSignature` record is linked to the parent WorkOrder or ServiceAppointment via a lookup and stores:

- `SignatureType` — `Customer` or `Technician`
- `Status` — whether the signature was captured
- `CapturedImageDocument` — Id of the ContentDocument holding the signature image

The ServiceReportLayout signature placeholder reads from linked `DigitalSignature` records when rendering the PDF. If the signature was collected offline and not yet synced, the signature block renders blank. Signature capture must occur **before** `createServiceReport` is called to appear in the rendered output.

### Document Builder — Conditional and Dynamic Reports (Winter '25+)

Document Builder (Setup > Document Builder) is the newer platform feature for PDF generation across multiple objects. For FSL, it provides:

- **Conditional section visibility** controlled by Flow logic — the missing capability in classic ServiceReportLayout
- **LWC embedding** inside PDF sections for custom rendered components
- **Auto-generation triggers** on record status changes via Flow
- **Offline capture support** — works with mobile LWC embedding for richer offline forms

Document Builder templates are separate from `ServiceReportLayout` records. They are configured in Setup as Document Builder templates and linked to objects (WorkOrder, ServiceAppointment). Generated PDFs are stored as ContentDocument/ContentVersion, same as classic reports. For new implementations requiring conditional logic, Document Builder is the recommended path.

---

## Common Patterns

### Pattern 1: Apex-Driven Report Generation on Status Change

**When to use:** Automatically generate and attach a service report PDF when a ServiceAppointment status transitions to `Completed`.

**How it works:**

1. An Apex trigger (or Record-Triggered Flow calling an Apex action) fires on `ServiceAppointment` update.
2. It checks `Status == 'Completed'` and `Status_old != 'Completed'`.
3. It enqueues a Queueable to avoid CPU limit pressure from synchronous PDF rendering.
4. The Queueable calls `ConnectApi.FieldService.createServiceReport(saId, templateId)`.
5. The resulting ContentDocument is automatically linked to the ServiceAppointment.

```apex
public class ServiceReportQueueable implements Queueable {
    private Id serviceAppointmentId;
    private Id templateId;

    public ServiceReportQueueable(Id saId, Id tplId) {
        this.serviceAppointmentId = saId;
        this.templateId = tplId;
    }

    public void execute(QueueableContext ctx) {
        ConnectApi.FieldService.createServiceReport(
            serviceAppointmentId,
            templateId
        );
    }
}
```

**Why not synchronous trigger:** `createServiceReport` performs a REST callout internally and is slow (2–5 s). Calling it synchronously in a before/after trigger risks hitting governor limits for bulk operations and can cause lock contention on the ContentDocument table.

### Pattern 2: Document Builder with Flow-Driven Conditional Sections

**When to use:** Report template needs sections that appear only for certain work types or field values (e.g., show a safety checklist section only for electrical work orders).

**How it works:**

1. Create a Document Builder template in Setup, pointing at WorkOrder or ServiceAppointment.
2. Define conditional section visibility rules using Decision elements in a Flow embedded in the template.
3. Create a Record-Triggered Flow on the source record to auto-generate via the Document Builder Generate action.
4. The generated PDF is stored as ContentDocument linked to the record.

**Why not classic ServiceReportLayout:** Classic templates have no conditional rendering capability. Every configured section always appears in the output regardless of record data. Document Builder is the only supported path for conditional content.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Basic report with fixed sections, no conditional logic | Classic ServiceReportLayout + `createServiceReport` Apex | Simpler to configure, GA since API v40.0, well understood |
| Conditional section visibility required | Document Builder (Winter '25+) | Classic builder has no conditional section support |
| LWC-embedded custom UI in report | Document Builder | Classic layouts cannot embed LWC components |
| Customer signature capture on mobile | Classic ServiceReportLayout with DigitalSignature placeholder | Signatures in DigitalSignature object render natively in classic layout |
| Offline report generation on mobile app | Ensure Briefcase Builder primes all fields used in the template | Offline PDFs blank fields not in Briefcase priming config |
| Programmatic generation from Apex | `ConnectApi.FieldService.createServiceReport()` in a Queueable | Avoids CPU limits; runs async outside trigger context |
| Quote or proposal PDF | Use a separate CPQ or Proposal template tool | Service reports are NOT quote templates |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Clarify requirements** — Determine target record (WorkOrder vs. ServiceAppointment), whether signature capture is needed, whether conditional sections are required, and whether offline generation on mobile must be supported.
2. **Choose template approach** — If conditional sections or LWC embedding are required, use Document Builder (Winter '25+). Otherwise, configure a ServiceReportLayout in Setup under Field Service > Service Report Templates.
3. **Configure the template layout** — Drag and drop field sections, related lists (Products Consumed, Time Sheets), signature placeholders, and header/footer elements. Associate the template with the relevant Work Type or set it as the org default.
4. **Implement Apex or Flow generation** — For automated generation, implement a Queueable Apex class calling `ConnectApi.FieldService.createServiceReport(recordId, templateId)` triggered from a Record-Triggered Flow or trigger on status change to Completed. For Document Builder, configure a Record-Triggered Flow using the Document Builder Generate action.
5. **Configure signature capture** — If customer signatures are required, ensure the ServiceReportLayout includes a signature placeholder (or Document Builder section references DigitalSignature). Verify the DigitalSignature record is created and synced before the report generation action fires.
6. **Address offline requirements** — If mobile technicians generate reports offline, open Briefcase Builder and verify every field referenced in the report template is included in the priming rules. Missing fields render blank in offline PDFs.
7. **Validate and test** — Generate a test report on a WorkOrder/ServiceAppointment in a sandbox. Confirm ContentDocument is linked, PDF is not blank, signature image appears, and all expected sections render correctly.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] ServiceReportLayout is configured in Setup and associated with the correct Work Type or set as the org default
- [ ] `ConnectApi.FieldService.createServiceReport()` call is in a Queueable (not synchronous trigger) to avoid CPU limit failures
- [ ] DigitalSignature records are created and synced before report generation fires if signature capture is needed
- [ ] Briefcase Builder priming configuration includes all fields used in the report template for offline support
- [ ] Generated PDFs verified as ContentDocument linked to the source WorkOrder or ServiceAppointment via ContentDocumentLink
- [ ] If using Document Builder, conditional section logic tested with Flow in sandbox
- [ ] API version confirmed as v40.0+ for any connected apps or integrations invoking createServiceReport

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Conditional sections are not supported in classic ServiceReportLayout** — The Setup drag-and-drop builder has no conditional visibility controls. Every section in the template always renders regardless of record data. If you need conditional sections, migrate to Document Builder (Winter '25+). Attempting to work around this with empty sections or placeholder text causes cluttered reports with no clean solution in the classic builder.
2. **Offline PDF blanks fields not in Briefcase priming** — When a technician is offline and generates a service report via the FSL mobile app, the PDF is rendered from locally cached data only. Any field not included in the Briefcase Builder priming configuration will render as blank in the PDF. This is not a template defect — it is a data availability issue. Fix: audit the template fields against Briefcase Builder priming rules and add any missing field references.
3. **Signature must be captured before report generation** — The DigitalSignature record must exist and be synced to the server before `createServiceReport` is called. If the report is auto-generated immediately on status change (e.g., via a trigger on Completed), the signature may not yet be synced if the technician is on a slow connection. Solution: add a short delay (Scheduled Flow), check for signature existence before generating, or allow manual re-generation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `fsl-service-report-templates-template.md` | Work template for designing and implementing a service report template — captures requirements, layout decisions, and generation approach |
| `check_service_report.py` | Stdlib-only validator that checks Apex classes for common anti-patterns in service report generation (synchronous calls, missing Queueable pattern) |

---

## Related Skills

- `fsl-work-order-management` — Work Order and Service Appointment data model; report generation is linked to these records
- `apex-trigger-patterns` — Queueable and trigger patterns for async Apex; required for safe service report generation from triggers

---

## Official Sources Used

- Field Service Developer Guide — Create Service Report with Apex: https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_apex_sr_create.htm
- Field Service Developer Guide — ServiceReportLayout Object: https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_soap_srl.htm
- Field Service Developer Guide — DigitalSignature Object: https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_soap_digital_signature.htm
- Salesforce Help — Document Builder Overview: https://help.salesforce.com/s/articleView?id=sf.document_builder_overview.htm
- ConnectApi.FieldService Namespace — Apex Reference: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ConnectAPI_FieldService_static_methods.htm
