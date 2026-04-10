# Well-Architected Notes — FSL Scheduling API

## Relevant Pillars

- **Performance** — FSL scheduling calls are synchronous HTTP callouts to an external optimization microservice. Response time varies with territory size, resource count, and scheduling policy complexity. Design Apex callers to be async (Queueable, Batch) rather than blocking user-facing transactions. Avoid calling schedule() in loops; batch with size 1 instead.
- **Reliability** — schedule() returns null without throwing when no resource is available. Bulk scheduling via Batch Apex with size 1 provides transaction isolation: one SA failure does not abort the others. OAAS Global optimization has a 2-hour hard server timeout; monitor job records for silent cancellations.
- **Security** — FSL scheduling API calls execute as the running user. Ensure the caller has Field Service Scheduling permissions (`FSL User` or `FSL Resource` permission set). Wrap callouts in permission checks rather than assuming caller is authorized.
- **Operational Excellence** — Log `ScheduleResult` nulls and exceptions to a custom error object rather than swallowing them. Expose a scheduling error dashboard so dispatchers can manually handle unscheduled SAs. Monitor OAAS job completion status in FSL optimization history records.

## Architectural Tradeoffs

**Sync vs. Async booking:** Calling schedule() synchronously in an @AuraEnabled method is simpler but blocks the UI thread for the duration of the callout and fails if called inside a larger DML transaction. Async Queueable is more resilient but requires the UI to poll for completion or use platform events for push notification.

**GetSlots + schedule() vs. schedule() alone:** GetSlots + GradeSlots + user selection gives dispatchers or customers control over the appointment window. Calling schedule() directly is fully automated but removes visibility into why a specific resource was chosen. Use the two-step flow for customer-facing booking; use direct schedule() for automated assignment during off-hours scheduling runs.

**ESO vs. legacy optimization:** ESO delivers better throughput and supports work chains, but adoption is irreversible per territory and removes the legacy engine fallback. Adopt ESO in stages, starting with low-criticality territories.

## Anti-Patterns

1. **Calling schedule() inside a trigger** — Apex triggers share the transaction with the DML that fired them. Any callout inside a trigger (including after-insert) throws `CalloutException: You have uncommitted work pending`. Always enqueue a Queueable from the trigger and make the callout there.
2. **Batch Apex with size > 1 for FSL scheduling** — FSL scheduling calls are callouts with a 100-per-transaction limit. Batch sizes > 1 breach this limit under load and create partial-failure data inconsistencies between Apex and the FSL microservice state.
3. **Assuming schedule() success from absence of exception** — schedule() returns null silently on no-resource. Treat a null return as a business logic failure, not a platform error, and handle it explicitly.

## Official Sources Used

- FSL AppointmentBookingService Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_namespace_FSL_AppointmentBookingService.htm
- FSL ScheduleService Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_namespace_FSL_ScheduleService.htm
- FSL GradeSlotsService Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_namespace_FSL_GradeSlotsService.htm
- FSL OAAS Class — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_namespace_FSL_OAAS.htm
- Limits for Enhanced Scheduling — https://help.salesforce.com/s/articleView?id=sf.fs_enhanced_scheduling_limits.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
