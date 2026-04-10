# Well-Architected Notes — FSL Apex Extensions

## Relevant Pillars

- **Reliability** — The FSL scheduling API's callout-DML transaction constraint is the dominant reliability risk. Implementations that do not respect the transaction boundary produce `CalloutException` failures that silently leave appointments unscheduled. Queueable and Batch patterns with explicit error handling and logging are the reliability baseline. Batch jobs must not re-throw exceptions from individual record failures — one bad appointment should not abort the entire run.
- **Performance** — Each `GetSlots()` or `schedule()` call invokes the FSL routing engine via HTTP. For bulk operations, the Batch pattern with batchSize=1 serializes these calls and can be slow for high volumes (e.g., 500 appointments × 1–3 seconds per callout = 8–25 minutes). Design bulk scheduling as background/overnight jobs rather than synchronous user-facing operations. Consider whether OAAS optimization is more appropriate than per-appointment scheduling for large territory re-optimization.
- **Security** — FSL API calls execute as the running user or the system context of the Queueable/Batch. Ensure the Apex class has `with sharing` or `without sharing` declared intentionally. Scheduling policy records and ServiceResource records may be restricted by object-level or record-level sharing; confirm the executing user (or System.runAs context in tests) has access to all referenced records. Avoid exposing SA IDs or policy IDs in URLs or client-side code that could be manipulated.
- **Scalability** — The batchSize=1 constraint is a hard architectural limit. At very high volumes (thousands of appointments daily), consider whether FSL's managed scheduling (Drip Feed or bulk optimizer via OAAS) is more appropriate than custom Apex scheduling. Each Queueable counts against the org's async job limits; monitor async job queue depth in high-volume orgs.
- **Operational Excellence** — Log scheduling outcomes (slot selected, resource assigned, any failures) to a custom object or Platform Event for dispatcher visibility. Track the FSL-returned slot grade so dispatchers can see why a specific resource was chosen. For OAAS, store the returned job ID for correlation with optimization outcome records created by the FSL package.

## Architectural Tradeoffs

**Queueable vs. Batch for scheduling:** Queueable is simpler for interactive, single-record scenarios and supports chaining for multi-step workflows. Batch with batchSize=1 is safer for bulk operations because each execution chunk is a fully isolated transaction with no shared state risk. The tradeoff is operational complexity: batch jobs are more visible in the Apex Jobs UI and easier to monitor, but they also serialize completely and cannot parallelize FSL calls.

**Per-appointment scheduling vs. OAAS optimization:** Per-appointment `ScheduleService.schedule()` places one appointment at a time against the best available slot. OAAS optimization considers the entire territory's schedule holistically and redistributes appointments for global efficiency. For high-volume re-optimization after disruption (sick call, emergency), OAAS is architecturally superior. For interactive booking of individual customer appointments, `GetSlots` + `schedule()` is the correct path.

**Synchronous user experience:** There is no synchronous path for FSL appointment booking from a UI action — the callout constraint forces async. Practitioners must design for eventual consistency: show the user a "booking in progress" state and update the UI when the async job completes (Platform Event, polling, or push notification from the Queueable finish handler).

## Anti-Patterns

1. **Synchronous FSL scheduling in the same DML transaction** — Inserting or updating a ServiceAppointment and then calling `GetSlots()` or `schedule()` in the same Apex method is architecturally broken. It will always fail due to the callout-after-uncommitted-DML restriction. This pattern appears in many code examples that were written without understanding the FSL routing callout behavior.

2. **Unguarded OAAS calls across environments** — Hardcoding `FSL.OAAS` calls without a license/feature check creates a deployment time bomb: it compiles in all environments but fails at runtime in any org without the Enhanced Scheduling and Optimization add-on. This is an operational excellence failure because it produces opaque runtime errors rather than clear, actionable failures.

3. **Batch with large chunk size for FSL** — Using the default or large batch size (200) for FSL scheduling batches is a latent bug. It appears to work in low-data-volume sandboxes (because there may be only 1–2 appointments) but fails in production at scale. Always enforce batchSize=1 as a documented, commented requirement in the batch class.

## Official Sources Used

- FSL Apex Namespace — Field Service Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_apex_namespace.htm
- AppointmentBookingService Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_apex_AppointmentBookingService.htm
- ScheduleService Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_apex_ScheduleService.htm
- OAAS Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_apex_OAAS.htm
- GradeSlotsService Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_apex_GradeSlotsService.htm
- Apex Developer Guide (Callouts) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
