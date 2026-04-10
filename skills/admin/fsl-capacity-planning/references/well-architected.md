# Well-Architected Notes — FSL Capacity Planning

## Relevant Pillars

- **Operational Excellence** — Capacity planning is fundamentally an operational discipline. Recording capacity constraints in platform objects (`WorkCapacityLimit`, `ServiceResourceCapacity`) rather than in dispatcher memory or spreadsheets is the key operational excellence move. Silent rejection behavior means that operational monitoring — reports, dashboards, alerts — must be built deliberately; the platform does not surface limit breaches automatically.

- **Reliability** — Date gaps in `ServiceResourceCapacity` records and misconfigured `WorkCapacityLimit` values cause silent scheduling failures that reduce appointment throughput without any alert. Reliable capacity configuration requires proactive gap auditing via SOQL and scheduled monitoring of territory appointment counts vs. limits. No-gap coverage of the scheduling horizon is a reliability requirement, not a nice-to-have.

- **Performance** — Capacity records constrain the scheduling candidate pool early in the optimization cycle. Well-scoped `WorkCapacityLimit` records (accurate `CapacityWindow` and `CapacityLimit` values) prevent the optimizer from evaluating overcrowded territories and improve schedule optimization runtime. Conversely, capacity records with zero or missing values can cause the optimizer to make many unsuccessful candidate evaluations before returning no result, degrading optimization performance.

- **Scalability** — There are no native bulk-update tools for `WorkCapacityLimit` or `ServiceResourceCapacity`. As the number of territories and resources grows, maintaining capacity records at scale requires automation (Data Loader runbooks, Apex batch, or integration pipelines). Planning for this automation before the record count grows is the scalable architecture decision.

- **Security** — `WorkCapacityLimit` and `ServiceResourceCapacity` are typically managed by FSL admins or territory managers, not dispatchers or field technicians. Object-level permissions should restrict Create/Edit/Delete on these objects to admin profiles. Incorrect capacity records (e.g., accidentally zeroed-out limits) cause operational impact that can be difficult to diagnose, so change-management controls around these records matter.

## Architectural Tradeoffs

**Resource-level vs. territory-level capacity:** Resource-level capacity (`ServiceResourceCapacity`) is more granular and provides precise per-resource control, but requires `IsCapacityBased = true` and creates more records to maintain as resource counts grow. Territory-level capacity (`WorkCapacityLimit`) is coarser but simpler to maintain — one record per territory/work type/window covers all resources in that territory. The tradeoff is precision vs. maintenance overhead. Most orgs benefit from using both: `WorkCapacityLimit` for demand-side throttling at territory intake, and `ServiceResourceCapacity` only for genuinely shared or pooled assets.

**Silent rejection vs. active notification:** FSL's `WorkCapacityLimit` design opts for silent rejection rather than active error display. This prevents dispatchers from receiving disruptive error messages mid-workflow, but it places the burden of capacity awareness entirely on operational reporting. The architectural implication is that any org using `WorkCapacityLimit` must invest in a monitoring layer (custom reports, CRM Analytics dashboards, or scheduled Apex notifications) to make the platform's silent enforcement visible to operations.

**Native reporting gap:** The absence of a standard report type aggregating `ServiceResourceCapacity` against `ServiceAppointment` durations means orgs must choose between a custom report type (no additional licensing, but limited analytics capability) and CRM Analytics (richer dashboards, requires licensing). This is an architectural decision that should be made early — retrofitting CRM Analytics into an org that has relied on custom reports for 2 years requires data model rework.

## Anti-Patterns

1. **Using resource deactivation to reduce capacity** — Setting `ServiceResource.IsActive = false` to limit a territory's throughput removes the resource from all scheduling and disrupts existing appointments. The correct approach is a bounded `ServiceResourceCapacity` record with a reduced `Capacity` value, or a `WorkCapacityLimit` record for territory-level throttling. Deactivation is an availability control, not a capacity control.

2. **Assuming capacity rejections will surface as errors** — Designing a dispatch workflow where operators assume they will be notified when capacity is reached leads to silent overbooking risk when `WorkCapacityLimit` records are configured. Any capacity-constrained FSL org must include operational monitoring as a first-class deliverable, not an afterthought.

3. **Creating ServiceResourceCapacity records without setting IsCapacityBased** — Inserting capacity records before enabling `IsCapacityBased = true` on the parent `ServiceResource` creates inert records that consume org storage and give admins false confidence that capacity is enforced. Always confirm the flag before creating capacity records.

## Official Sources Used

- Capacity Planning Overview — https://help.salesforce.com/s/articleView?id=sf.fs_capacity_planning.htm
- Define Capacity-Based Resources — https://help.salesforce.com/s/articleView?id=sf.fs_capacity_based_resources.htm
- Manage Work Capacity — https://help.salesforce.com/s/articleView?id=sf.fs_work_capacity.htm
- ServiceResourceCapacity Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_serviceresourcecapacity.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
