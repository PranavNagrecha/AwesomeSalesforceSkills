# LLM Anti-Patterns — FSL SLA Configuration Requirements

Common mistakes AI coding assistants make when generating or advising on FSL SLA configuration using Salesforce Entitlement Management for Work Orders.

## Anti-Pattern 1: Recommending a Case Entitlement Process for Work Orders

**What the LLM generates:** Advice to create or reuse a Case entitlement process and associate it to Work Orders via the EntitlementId field, often without specifying the process type.

**Why it happens:** Most Salesforce entitlement training data covers Case-based SLAs. Work Order entitlement processes are a FSL-specific feature with less documentation density. LLMs conflate the two because both use the Entitlement and EntitlementProcess objects.

**Correct pattern:**

```text
Create entitlement process → Select type: Work Order (not Case)
This selection is permanent and cannot be changed after save.
Case processes produce no milestone tracking on Work Order records.
```

**Detection hint:** Any response that does not specify "type: Work Order" when discussing FSL entitlement processes, or that says "use your existing entitlement process" without confirming its type, should be challenged.

---

## Anti-Pattern 2: Claiming Salesforce Auto-Completes Work Order Milestones

**What the LLM generates:** Instructions that say something like "when the Work Order is closed, Salesforce will automatically mark the milestone as complete" or "the entitlement engine updates CompletionDate when the work order status changes."

**Why it happens:** Case milestones in some configurations can be closed via milestone status transitions. LLMs generalize this behavior to Work Order milestones incorrectly. The Trailhead module for FSL entitlements implies completion tracking without explicitly stating that it requires custom automation.

**Correct pattern:**

```text
Salesforce does NOT auto-complete WorkOrderMilestone records.
CompletionDate must be set by a Record-Triggered Flow or Apex trigger.
Required: Flow on WorkOrder update → Status = "Completed" → 
  Get WorkOrderMilestone where WorkOrderId = WO.Id AND CompletionDate = null →
  Update CompletionDate = Now()
```

**Detection hint:** Any response that omits a milestone completion Flow or Apex trigger when advising on FSL SLA setup is incomplete. Flag any claim that milestones auto-close on Work Order completion.

---

## Anti-Pattern 3: Treating Operating Hours and Business Hours as the Same Object

**What the LLM generates:** Advice such as "set the Operating Hours on the Service Territory to match your SLA windows" as if this controls the entitlement milestone timer. Or, conversely, advice to set Business Hours on the entitlement process without mentioning Operating Hours alignment.

**Why it happens:** Both objects model time windows and both are relevant to FSL. LLMs often conflate them because the names are semantically similar and they serve related purposes. The distinction that Business Hours drives the milestone clock and Operating Hours drives scheduling availability is not consistently captured in training data.

**Correct pattern:**

```text
Business Hours (core platform object) → controls when milestone timer ticks
Operating Hours (FSL object on ServiceTerritory) → controls when techs can be scheduled
These are independent and must be aligned manually per territory.
Mismatch: SLA clock pauses at 5pm even if the territory has 24/7 Operating Hours.
```

**Detection hint:** Any response that says "configure Operating Hours to control SLA timing" or that does not distinguish between the two objects should be corrected.

---

## Anti-Pattern 4: Suggesting Milestone-Level Overrides Can Vary Time Limits by Territory

**What the LLM generates:** Advice like "use milestone-level business hours overrides to give metro customers a 2-hour response and rural customers a 4-hour response within the same entitlement process."

**Why it happens:** Milestone-level Business Hours overrides exist and are documented. LLMs extrapolate from this that other milestone properties (like time limits) can also be varied per-territory within one process, which is incorrect.

**Correct pattern:**

```text
Milestone-level Business Hours override: changes WHICH Business Hours object 
  the milestone clock uses — does NOT change the time limit.
To vary time limits by territory: create separate entitlement processes,
  one per SLA profile. Use a Flow to assign the correct process/entitlement
  based on the Work Order's Service Territory.
```

**Detection hint:** Any response that claims milestone overrides can produce different time limits (not just different Business Hours objects) within one process should be corrected.

---

## Anti-Pattern 5: Omitting the EntitlementId Population Step

**What the LLM generates:** Configuration steps that describe creating entitlement processes and milestones but do not address how the correct entitlement record gets linked to each Work Order. The response assumes entitlements are manually assigned or that Salesforce auto-matches them.

**Why it happens:** In simple Service Cloud demos, entitlements are manually associated to cases. LLMs carry this assumption into FSL contexts where high Work Order volume makes manual assignment impractical, and where territory-based routing requires automated selection logic.

**Correct pattern:**

```text
WorkOrder.EntitlementId must be populated for any milestone process to activate.
For FSL at scale:
  Build a Record-Triggered Flow on Work Order (fires on Create).
  Read the Work Order's ServiceTerritoryId.
  Map ServiceTerritoryId to the correct Entitlement record.
  Set WorkOrder.EntitlementId = matched Entitlement.Id
Without this: Work Orders have no entitlement, no milestones activate, 
  and no SLA tracking occurs — silently.
```

**Detection hint:** Any FSL SLA configuration advice that does not address automated EntitlementId population on Work Order creation is incomplete. Flag responses that say "associate the entitlement to the Work Order" without specifying how this is automated.

---

## Anti-Pattern 6: Forgetting to Add Key Fields to the WorkOrderMilestone Related List

**What the LLM generates:** Configuration instructions that end with "add the WorkOrderMilestone related list to the Work Order page layout" without specifying which fields to include.

**Why it happens:** The default related list column set is not documented prominently. LLMs assume the default layout includes the key operational fields (TargetDate, CompletionDate, IsViolated) by analogy with the Case Milestone related list, which is more feature-rich.

**Correct pattern:**

```text
After adding WorkOrderMilestone related list to Work Order layout:
Customize columns to include:
  - Milestone Name
  - TargetDate
  - CompletionDate
  - IsViolated
  - Status
Without these columns: dispatchers cannot see SLA risk from the Work Order record.
Fields exist on the object but are not shown by default.
```

**Detection hint:** Any layout configuration advice that says "add the related list" without specifying column customization for TargetDate, CompletionDate, and IsViolated should be flagged as incomplete.
