# Gotchas — FSL SLA Configuration Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Salesforce Never Auto-Marks Work Order Milestones as Completed

**What happens:** `WorkOrderMilestone.CompletionDate` is never populated by the platform when a Work Order is closed or completed. The milestone records remain in an open/incomplete state indefinitely. Success actions (which fire when the milestone is completed before its TargetDate) never execute. SLA performance reports show all milestones as open regardless of actual work order status.

**When it occurs:** On every Work Order entitlement process deployment that does not include a custom automation layer. This is not a bug — it is documented platform behavior. It affects all versions of FSL and all org types.

**How to avoid:** Build a Record-Triggered Flow on the `WorkOrder` object that fires when `Status` changes to a completion value (e.g., "Completed", "Cannot Complete"). The Flow must query related `WorkOrderMilestone` records with `CompletionDate = null` and update each one with `CompletionDate = {!$Flow.CurrentDateTime}`. Test in sandbox with a 1-minute milestone time limit before go-live.

---

## Gotcha 2: Work Order and Case Entitlement Processes Are Completely Separate — Cannot Span Both

**What happens:** An entitlement process configured with type "Case" applies only to Case records. Associating that same entitlement (via `EntitlementId`) to a Work Order produces no milestone tracking on the Work Order. The platform does not raise an error — no `WorkOrderMilestone` records are created, no timers run, and no actions fire. The Work Order appears to have an entitlement but has no active SLA enforcement.

**When it occurs:** When teams migrate from Service Cloud SLA configuration to FSL and reuse existing entitlement records without creating a new Work Order-type process. Also occurs when a practitioner incorrectly assumes that one entitlement process can serve both objects.

**How to avoid:** Create a new entitlement process and select type "Work Order" in the wizard. This type selection is permanent — a process type cannot be changed after the process is saved. Maintain separate Case processes and Work Order processes. Document the distinction explicitly in org runbooks.

---

## Gotcha 3: Milestone Countdowns Pause Outside Business Hours — And This Is Independent of FSL Operating Hours

**What happens:** The Business Hours object assigned to an entitlement process controls when the milestone clock ticks. When the current time falls outside Business Hours, the clock pauses. However, the FSL Operating Hours object (assigned to Service Territories) is a completely separate configuration that controls technician scheduling availability — these two objects are not synchronized. A Work Order dispatched to a territory with 24/7 Operating Hours can have its milestone clock paused at 5pm if the entitlement process uses a Business Hours object with M–F 8am–5pm hours.

**When it occurs:** When Business Hours on the entitlement process are not aligned with the Operating Hours of the Service Territory. This is common when the entitlement process is configured by the Service Cloud team without coordinating with the FSL configuration team.

**How to avoid:** For each Service Territory, confirm the Business Hours object on the entitlement process matches the coverage window defined in the territory's Operating Hours. For 24/7 territories, use a 24/7 Business Hours record. For business-hours-only territories, use a matching M–F Business Hours record. Document the mapping explicitly. For geographic SLA differentiation, create separate entitlement processes with separate Business Hours records aligned to each territory's Operating Hours.

---

## Gotcha 4: Work Order Milestone Related List Shows Fewer Fields by Default Than Case Milestones

**What happens:** When the WorkOrderMilestone related list is added to the Work Order page layout, it does not display `TargetDate`, `CompletionDate`, or `IsViolated` in the default column set. Dispatchers viewing the Work Order have no visible indicator of whether an SLA is at risk or has already been violated. The fields exist on the `WorkOrderMilestone` object and contain correct data — they are just not shown.

**When it occurs:** On any Work Order layout where the WorkOrderMilestone related list has not been customized. This is the default behavior and affects both Lightning Experience and the Salesforce mobile app.

**How to avoid:** In the page layout editor for Work Order, select the WorkOrderMilestone related list and customize its columns to include `Milestone Name`, `TargetDate`, `CompletionDate`, `IsViolated`, and `Status`. Communicate this step explicitly in FSL SLA setup documentation, as it is easy to overlook when focusing on process configuration.

---

## Gotcha 5: Geographic Response Time Differentiation Requires Separate Territories With Their Own Operating Hours — No Sub-Territory Variation Is Possible

**What happens:** There is no platform mechanism to configure varying SLA time limits (e.g., 2-hour vs. 4-hour on-site response) within a single Service Territory or a single entitlement process. Milestone-level Business Hours overrides only change the Business Hours object used for clock calculation — they do not change the time limit. A practitioner attempting to differentiate SLAs by city within one territory will find no supported configuration path.

**When it occurs:** When business requirements specify SLA differentiation by region, customer segment, or asset type, and the implementer attempts to configure this as milestone overrides or conditional actions within a single process.

**How to avoid:** Model geographic SLA differentiation as separate Service Territories, each with its own Operating Hours and its own entitlement process. Use a Flow to assign the correct entitlement to Work Orders based on their Service Territory. Accept that this approach requires one process per distinct SLA profile — this is a platform constraint, not a configuration choice.
