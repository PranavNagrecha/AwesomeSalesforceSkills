# Well-Architected Notes — Sales Engagement API

## Relevant Pillars

- **Reliability** — Cadence enrollment is a business-critical operation for sales rep productivity. Silent enrollment failures (duplicate guard no-ops, invocable action errors not inspected) erode trust in the automation. Reliable enrollment requires explicit result inspection, error logging, and retry handling. CDC-based subscribers must set resume checkpoints so the event bus can replay missed events after Apex exceptions.
- **Security** — The `assignTargetToSalesCadence` action enforces license and permission checks internally, but the calling Apex code still runs in the context of the executing user. Use `with sharing` on service classes to respect record-level sharing. Ensure that user IDs passed as the assigned Sales Rep are validated as licensed Sales Engagement users before submission to avoid platform-level rejections at enrollment time.
- **Scalability** — Enrollment services must be bulkified from the start. List-based invocable action calls are the only governor-safe pattern at scale. CDC-based reactions must process events in batches (the Async Trigger receives a list of events, not one) and delegate heavy work to Queueable rather than executing inline.
- **Operational Excellence** — Enrollment errors are not surfaced to end users by default. Production systems need structured logging (custom object or Platform Event) that captures per-record enrollment outcomes, so support teams can diagnose missed enrollments without reading debug logs. CDC trigger checkpoint management should be tested under failure scenarios to confirm replay behavior.

## Architectural Tradeoffs

**Invocable action versus Flow for enrollment:** The `assignTargetToSalesCadence` action can be called from Apex (via `Invocable.Action`) or from Flow. Flow is simpler for simple use cases but offers less control over bulk behavior and error handling. Apex is preferred when the calling code is a batch job, trigger, or service layer that needs per-record result inspection and bulkification control.

**CDC versus scheduled polling for lifecycle reactions:** CDC delivers events as they happen and is the only platform-supported approach. Scheduled SOQL polling on `ActionCadenceTracker` will miss transitions between polls, consume SOQL queries in every execution, and scale poorly. Always prefer CDC. The tradeoff is that CDC requires a Setup configuration step (enabling the object in the CDC entity list) that must be done per environment.

**Synchronous service class versus asynchronous worker for post-enrollment logic:** If the enrollment service is called from a trigger context, any post-enrollment work that requires callouts or heavy DML must be delegated to Queueable. Keeping the enrollment service synchronous and thin allows it to be called from both synchronous and asynchronous contexts without mixed-DML or callout errors.

## Anti-Patterns

1. **Fire-and-forget invocable action calls** — Calling `assignTargetToSalesCadence` without inspecting results is an operational dead zone. Enrollment failures are invisible. Every action call site must iterate `List<Invocable.Action.Result>` and route failures to a logging layer or retry queue. Ignoring results is the most common source of "why wasn't this lead enrolled" support tickets.

2. **Building cadence content via Apex or Metadata API** — Attempts to script cadence structure creation produce deployment errors and delay projects. Cadence Builder UI is the only authoring surface. Architecture docs should state this explicitly so no sprint is lost discovering it during deployment.

3. **Standard Apex trigger on ActionCadence objects** — Writing a trigger on `ActionCadenceTracker` fails at deployment. Any design that relies on standard triggers here must be refactored to CDC before it can be released. Discovering this late in a project cycle is expensive.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Sales Engagement Actions — Apex Actions Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.salesforce_developer_guide.meta/salesforce_developer_guide/sfe_apex_action_assign_target.htm
- ActionCadenceTracker Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_actioncadencetracker.htm
- ActionCadence Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_actioncadence.htm
- Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
