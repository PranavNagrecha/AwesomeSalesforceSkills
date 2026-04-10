# Gotchas — FSL Service Report Templates

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Conditional Sections Are Not Supported in Classic ServiceReportLayout

**What happens:** The Setup drag-and-drop Service Report Template builder (ServiceReportLayout) has no conditional visibility controls. Every section configured in the template always renders in the generated PDF, regardless of any record field values. There is no "show this section if Work Type = Electrical" logic available in the classic builder.

**When it occurs:** Any time a business requires different content in a report based on Work Type, custom fields, or job category. This is a very common requirement and the platform gap frequently surprises practitioners coming from CPQ quote template tooling where conditional sections are standard.

**How to avoid:** Evaluate requirements before committing to the classic builder. If conditional sections are needed, use Document Builder (Winter '25+) which supports conditional section visibility via Flow logic. Alternatively, configure multiple ServiceReportLayout templates (one per work category) and select the appropriate templateId programmatically in the Apex generation call based on Work Type.

---

## Gotcha 2: Offline PDF Renders Blank for Fields Not in Briefcase Builder

**What happens:** When a technician generates a service report while offline using the FSL mobile app, the PDF is rendered from locally cached data only. Any field referenced in the ServiceReportLayout template that was not included in the Briefcase Builder priming configuration will render as completely blank in the PDF. This is not a template configuration error — it is a data availability issue.

**When it occurs:** Any time the FSL mobile app is used offline or on a poor connection. Commonly discovered in post-deployment UAT when testers test in the field and find empty address blocks, contact names, or asset serial numbers that appear fine in the web UI.

**How to avoid:** After finalizing the ServiceReportLayout template, audit every field referenced in every section against the Briefcase Builder priming rules. Add any missing fields to the Briefcase record type and re-prime all devices. Maintain a documented mapping of "template fields → Briefcase priming rule" as a living artifact so future template changes trigger a Briefcase audit.

---

## Gotcha 3: Signature Must Be Synced Before Report Generation Fires

**What happens:** If report generation is triggered automatically on ServiceAppointment status change to `Completed`, the DigitalSignature record capturing the customer's signature may not yet be synced from the mobile device to the server at the moment the trigger fires. The report renders with a blank signature block.

**When it occurs:** When the technician completes the appointment on the mobile app while on a slow or intermittent connection. The status update event arrives at the server before the DigitalSignature sync completes — a race condition.

**How to avoid:** Do not auto-generate reports instantly on the status transition. Options include: (1) check for a `Captured` DigitalSignature record before calling `createServiceReport` and defer if absent, (2) trigger report generation from a separate user action ("Generate Report" button) after sync is confirmed, or (3) use a Platform Event published by the mobile app after signature sync to trigger generation.

---

## Gotcha 4: createServiceReport Requires FSL Managed Package and API v40.0+

**What happens:** `ConnectApi.FieldService.createServiceReport()` is not available in orgs without the Field Service managed package installed. Calling the method in a scratch org or developer org that has FSL licenses but not the managed package results in a compile error or runtime exception. Similarly, REST API calls to the `createServiceReport` action on v39 or earlier fail with an unsupported action error.

**When it occurs:** During early dev/sandbox setup, package installation order issues, or when building integrations that target FSL REST endpoints via external systems.

**How to avoid:** Confirm the FSL managed package is installed (check Setup > Installed Packages for "Field Service"). Confirm the connected app or API client is using API v40.0 or later. In Apex, guard the call with a try/catch and meaningful error messaging if the org context cannot be guaranteed.

---

## Gotcha 5: Multiple Reports Can Accumulate — No Auto-Deduplication

**What happens:** Each call to `createServiceReport` creates a new ContentDocument linked to the source record. If automation fires the call multiple times (e.g., a status toggles between Completed and other statuses, or a trigger fires on every save), multiple PDF versions accumulate on the record with no automatic deduplication or versioning linkage between them.

**When it occurs:** When trigger conditions are not carefully guarded (e.g., missing old-value check), or when a user manually re-triggers report generation without archiving the previous one. Over time, records accumulate dozens of reports.

**How to avoid:** Always guard `createServiceReport` calls with an old-value comparison (`Trigger.oldMap`) to ensure the call fires only on the first transition to Completed, not on every subsequent save. If re-generation is allowed, implement a pre-generation step that either deletes or archives the previous ContentDocument via `Database.delete` on the old ContentDocumentLink before generating the new one.
