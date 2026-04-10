# Examples — FSL SLA Configuration Requirements

## Example 1: Metro vs. Rural Territory SLA Differentiation

**Context:** A utilities company operates in both dense metro areas and remote rural regions. Metro customers have a contractual 2-hour on-site response SLA (measured in 24/7 calendar hours); rural customers have a 4-hour response SLA measured in business hours (M–F 8am–5pm). Both regions are managed in Salesforce Field Service using Service Territories.

**Problem:** The team initially created a single entitlement process of type Work Order with one set of milestones. They could not vary the time limit by territory — all work orders got the same 4-hour on-site target regardless of which territory they were dispatched from.

**Solution:**

1. Create two Service Territories: "Metro East" (Operating Hours: 24/7) and "Rural West" (Operating Hours: M–F 8am–5pm).
2. Create two Business Hours records: "BH 24/7" and "BH Business Hours M-F".
3. Create two Work Order entitlement processes:
   - "Metro SLA Process" — type: Work Order, Business Hours: BH 24/7
     - Milestone: On-Site Arrival, 2 hours, No Recurrence
   - "Rural SLA Process" — type: Work Order, Business Hours: BH Business Hours M-F
     - Milestone: On-Site Arrival, 4 hours, No Recurrence
4. Create two Entitlement records, one per process.
5. Build a Record-Triggered Flow on Work Order (fires on create) that reads `WorkOrder.ServiceTerritoryId`, maps it to the correct Entitlement record, and sets `WorkOrder.EntitlementId`.

```text
Flow: Assign_WO_Entitlement_From_Territory
  Trigger: Work Order Created
  Get: ServiceTerritory where Id = WorkOrder.ServiceTerritoryId
  Decision:
    - If Territory.Name = "Metro East" → Set WO.EntitlementId = {Metro_Entitlement.Id}
    - Default → Set WO.EntitlementId = {Rural_Entitlement.Id}
  Update: WorkOrder record
```

**Why it matters:** Without territory-driven entitlement assignment, all work orders receive the same SLA regardless of regional commitments. The Flow ensures the correct entitlement process activates for each dispatch without dispatcher intervention.

---

## Example 2: Milestone Completion Flow for Work Order Status Transitions

**Context:** A property management company uses FSL for maintenance dispatches. Work Orders have milestones for Initial Response (2 hours) and Resolution (8 hours). Technicians close Work Orders by setting status to "Completed" in the mobile app. Milestone success actions (which stamp a custom `SLA_Met__c` checkbox on the Work Order) were never firing.

**Problem:** The team had wired success actions correctly on both milestones but the actions never fired. Investigation revealed that `WorkOrderMilestone.CompletionDate` was always null on closed Work Orders — the milestones were technically open even after the Work Order was completed.

**Root cause:** Salesforce does not auto-complete Work Order milestones. `CompletionDate` must be set by custom automation.

**Solution:**

Build a Record-Triggered Flow on Work Order:

```text
Flow: Complete_WO_Milestones_On_Close
  Object: WorkOrder
  Trigger: A record is updated
  Entry Condition: Status CHANGES TO "Completed"

  Get Records:
    Object: WorkOrderMilestone
    Filter: WorkOrderId = {!$Record.Id} AND CompletionDate = null
    Store in: {!OpenMilestones}

  Loop: {!OpenMilestones}
    Update Current Item:
      CompletionDate = {!$Flow.CurrentDateTime}

  Update Records: All items in {!OpenMilestones}
```

After deploying, test by:
1. Creating a Work Order in a sandbox with a matching entitlement.
2. Setting milestone time limit to 1 minute.
3. Updating Work Order status to "Completed" before 1 minute elapses.
4. Verifying `WorkOrderMilestone.CompletionDate` is populated and the success action (`SLA_Met__c = true`) fired.

**Why it matters:** Without CompletionDate being set, the entitlement engine never evaluates success actions. Every milestone appears permanently open in reports, making SLA performance data meaningless. This Flow is a required component of every FSL SLA implementation.

---

## Anti-Pattern: Applying a Case Entitlement Process to Work Orders

**What practitioners do:** Copy an existing Case entitlement process (already configured for Service Cloud) and attempt to use it for Work Orders by associating the same Entitlement to the Work Order's `EntitlementId` field.

**What goes wrong:** A Case entitlement process does not trigger milestone tracking on Work Order records. The `WorkOrderMilestone` records are never created. Milestone actions never fire. There is no error message — it simply does nothing silently.

**Correct approach:** Create a new entitlement process with type explicitly set to **Work Order** in the process creation wizard. This type selection is made at creation and cannot be changed after the process is saved. Case and Work Order processes must be managed separately for their respective SLA commitments.
