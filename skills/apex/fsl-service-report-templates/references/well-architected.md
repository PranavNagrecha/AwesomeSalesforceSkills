# Well-Architected Notes — FSL Service Report Templates

## Relevant Pillars

- **Security** — Service report PDFs may contain sensitive customer information (site addresses, asset serial numbers, signature images). ContentDocument access is controlled by ContentDocumentLink sharing and org-level sharing settings. Reports should not be shared via public URLs without expiry controls. DigitalSignature records inherit field-level security and must be reviewed to ensure customer signature data is not exposed to unauthorized profiles.
- **Reliability** — The `createServiceReport` call is synchronous and slow (2–5 seconds). Invoking it in bulk DML contexts (trigger on 200 records) causes CPU limit failures and partial transaction rollbacks. Async execution via Queueable is mandatory for reliability at scale. Race conditions between DigitalSignature sync and report generation must be handled with retry logic.
- **Operational Excellence** — ServiceReportLayout templates and Briefcase Builder priming rules must be co-managed. A change to the template (adding a new field section) without a corresponding Briefcase update produces blank offline reports — a silent failure that is hard to detect in production. Treat template changes as change events requiring a Briefcase audit step.
- **Performance** — PDF generation is computationally expensive on the platform. It should always be performed asynchronously (Queueable or scheduled) and never in synchronous Apex paths called from user interactions. For high-volume orgs (hundreds of completions per hour), monitor Queueable job queue depth and consider batch generation windows.
- **Scalability** — Multiple ServiceReportLayout templates can be maintained (one per Work Type or job category) to support different business units without conditional-section workarounds. The Document Builder approach scales better for orgs with complex conditional requirements because it externalizes logic to Flow rather than requiring multiple static templates.

## Architectural Tradeoffs

**Classic ServiceReportLayout vs. Document Builder:**
- Classic is simpler to configure, has more community documentation, and has been GA since API v40.0. It integrates natively with DigitalSignature and Briefcase Builder offline priming.
- Document Builder (Winter '25+) supports conditional sections and LWC embedding but is newer and has less community experience. It requires Flow expertise and may have feature gaps with older FSL mobile clients.
- Choose Classic unless conditional sections or LWC embedding are hard requirements.

**Trigger-based vs. Flow-based generation:**
- Apex triggers give more control over conditions and error handling but require code maintenance.
- Record-Triggered Flows calling Apex Actions are lower-code but offer less fine-grained error handling for async failures.
- For teams with limited Apex resources, a Flow-triggered Apex Action calling the Queueable is a reasonable hybrid.

**Single template vs. multiple templates:**
- A single template with all possible sections (some always blank for irrelevant work types) is simpler to maintain but produces cluttered reports.
- Multiple templates with programmatic selection (based on Work Type at generation time) produces clean reports per job category but increases template maintenance surface.

## Anti-Patterns

1. **Synchronous createServiceReport in DML trigger context** — Calling `ConnectApi.FieldService.createServiceReport()` directly in an Apex trigger's execute method (not via Queueable) fails under bulk loads due to CPU limit exhaustion. The method performs a REST-like internal hop to render the PDF, which consumes significant CPU. All production implementations must use Queueable or equivalent async pattern.

2. **Custom Visualforce as a service report replacement** — Building a custom VF page styled as a service report bypasses all FSL integrations: DigitalSignature, offline Briefcase priming, mobile app Service Reports tab, and ContentDocument versioning. The output is not a platform-recognized service report. This pattern creates a maintenance burden and is functionally inferior to the native mechanism.

3. **Ignoring Briefcase Builder priming after template changes** — Updating a ServiceReportLayout template to add new field sections without auditing Briefcase Builder results in offline PDFs that silently render blank for new fields. This is invisible in web-based testing and only surfaces in field testing on poor connectivity.

## Official Sources Used

- Field Service Developer Guide — Create Service Report with Apex: https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_apex_sr_create.htm
- Field Service Developer Guide — ServiceReportLayout Object: https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_soap_srl.htm
- Field Service Developer Guide — DigitalSignature Object: https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_soap_digital_signature.htm
- Salesforce Help — Document Builder Overview: https://help.salesforce.com/s/articleView?id=sf.document_builder_overview.htm
- ConnectApi.FieldService Apex Reference: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ConnectAPI_FieldService_static_methods.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
