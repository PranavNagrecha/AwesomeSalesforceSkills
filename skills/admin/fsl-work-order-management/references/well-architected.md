# Well-Architected Notes — FSL Work Order Management

## Relevant Pillars

### Operational Excellence

FSL work order management is primarily an Operational Excellence concern. The WorkOrder → WOLI → ServiceAppointment → AssignedResource model exists to give field operations full visibility into job status, resource allocation, and scheduling. Key practices:

- Use WorkTypes to standardize job templates and reduce ad-hoc WO creation errors.
- Keep Work Order status and Service Appointment status in sync through explicit automation rather than assuming built-in behavior.
- Design Maintenance Plans with the 3x-daily batch cadence in mind; operational runbooks must account for this delay.
- Monitor WOLI counts per WO to stay within Gantt visibility limits (500 WOLIs) and record limits (10,000 child records).

### Reliability

Reliability applies through limit management and cascade automation:

- Exceeding 10,000 child records per WO will produce errors that break automations relying on WO record creation. Design data models that distribute work across parent-child WO hierarchies to prevent this.
- Status cascade automations (Flow on SA → WO) must be fault-tolerant. If a SA is deleted rather than completed, the cascade Flow must handle the edge case; otherwise WOs can get stuck open permanently.
- Maintenance Plan batch failures (e.g., validation rule preventing WO creation) will silently fail without alerting operations teams. Build monitoring (e.g., a scheduled report on Maintenance Plans with no recent generated WOs) to detect stalls.

### Security

Security applies to the FSL permission model:

- Field technicians use the FSL mobile app and require the **Field Service Standard** permission set to update SA status in the field. Without it, status updates fail silently on the mobile app.
- The **Field Service Admin** permission set is required for dispatchers managing the Dispatcher Console and creating/editing WorkTypes and Maintenance Plans. Scope this carefully — do not grant FSL Admin to field technicians.
- Work Order records inherit standard Salesforce sharing rules. If WOs are owned by a queue or a specific user, ensure field technicians have at least Read access to view job details on the mobile app.

### Performance

Performance concerns are minimal for standard implementations but relevant at scale:

- High-volume Maintenance Plan configurations (generating hundreds of WOs per day) can create governor limit pressure on downstream automations triggered by WO creation (Flows, Apex triggers). Profile trigger execution against WO batch creation volume.
- The Gantt performance degrades with large numbers of SAs in the unscheduled queue. Implement queue management practices (archive old unscheduled SAs) to keep the Dispatcher Console responsive.

---

## Architectural Tradeoffs

**AutoCreateSvcAppt vs. Flow-based SA Creation:**
AutoCreateSvcAppt is simple to configure but offers no control over SA field values at creation time. A Flow-based SA creation pattern provides full control (custom subject, initial status, specific time windows) at the cost of more implementation work. For enterprise implementations with complex routing or SLA requirements, prefer Flow over AutoCreateSvcAppt.

**Maintenance Plan vs. Scheduled Flow for WO Generation:**
Maintenance Plans are zero-code configuration but limited to ~3x daily cadence. Scheduled Flows can run on a precise hourly or minute-level schedule and create WOs via logic, but require development and are harder to maintain. For any SLA requiring WOs within a narrow time window of schedule, use Scheduled Flow.

**Single WO with Many WOLIs vs. Parent-Child WO Hierarchy:**
Flat WO models with many WOLIs are simpler to query and report on but hit Gantt visibility limits (500 WOLIs) and risk approaching the 10,000 child record limit. Parent-child WO hierarchies add query complexity but scale much better for large multi-day or multi-resource jobs.

---

## Anti-Patterns

1. **Treating WO and SA Status as a Single Lifecycle** — Designing status flows that assume WO status mirrors SA status leads to broken reporting and open records that never close. Always model and automate the two lifecycles independently, with explicit bridges only where the business requires it.

2. **Over-relying on AutoCreateSvcAppt for Complex Scheduling** — Using AutoCreateSvcAppt as the sole SA creation mechanism in orgs with advanced scheduling requirements (territory-specific time windows, skill-based routing) creates SAs with no scheduling constraints, forcing dispatchers to manually enrich every SA. Build a Flow or integration that sets SA fields at creation time in these scenarios.

3. **Building SLAs Around Maintenance Plan Timing** — Maintenance Plans are not an SLA-safe mechanism for time-sensitive WO generation. Promising customers or operations teams that WOs will be created at a specific time based on Maintenance Plans sets incorrect expectations and requires workarounds when the batch is delayed.

---

## Official Sources Used

- Guidelines for Creating Work Orders — https://help.salesforce.com/s/articleView?id=sf.fs_work_orders.htm
- Create Work Types — https://help.salesforce.com/s/articleView?id=sf.fs_create_work_types.htm
- WorkOrder Object Reference — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_class_FSL_ScheduleServiceUtil.htm
- Field Service Developer Guide (WorkOrder) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_dev_intro.htm
- Track Field Service Jobs (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-lightning-basics/track-field-service-jobs
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
