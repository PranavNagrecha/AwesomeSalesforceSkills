---
name: fsl-scheduling-policies
description: "Use this skill to create, configure, or tune Field Service Lightning scheduling policies — including work rules (pass/fail filters) and service objectives (weighted ranking criteria). Covers the four default policies, custom policy design, work rule type selection, and objective weighting strategy. NOT for configuring service territories, resource availability calendars, or the Salesforce Scheduler (Appointment Scheduling) product."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Performance
triggers:
  - "field service scheduling ignores technician availability or working hours"
  - "create a custom scheduling policy for high-priority emergency work orders"
  - "how to configure work rules and service objectives in Field Service Lightning"
  - "technicians are being assigned to appointments outside their skills or certifications"
  - "optimize field service scheduling to minimize travel time between appointments"
  - "scheduling policy work rules and objectives not ranking candidates correctly"
  - "when should I use Customer First versus High Intensity scheduling policy"
tags:
  - field-service
  - fsl
  - scheduling-policy
  - work-rules
  - service-objectives
  - optimization
  - scheduling
inputs:
  - "Business scheduling priority (e.g., customer convenience, travel efficiency, emergency response)"
  - "List of required technician skills, certifications, or required-skill work types in use"
  - "Territory structure and whether territory boundaries must be strictly enforced"
  - "Workforce type: employee technicians, contractors, or crews with overtime constraints"
  - "Existing default policy in use (Customer First, High Intensity, Soft Boundaries, or Emergency)"
outputs:
  - "Configured FSL__Scheduling_Policy__c record with named work rules and objectives"
  - "Work rule records (FSL__Work_Rule__c) attached to the policy with correct types and parameters"
  - "Service objective records (FSL__Service_Objective__c) with calibrated percentage weights"
  - "Decision table mapping business scenario to recommended policy configuration"
  - "Validation checklist confirming Service Resource Availability work rule is present"
dependencies:
  - fsl-service-territory-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# FSL Scheduling Policies

This skill activates when a practitioner needs to create, modify, or troubleshoot a Field Service Lightning scheduling policy — the configuration object that governs how the scheduling engine filters and ranks available service resources for appointment slots. It covers work rule design, service objective weighting, and the selection between Salesforce's four built-in default policies.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm Field Service managed package is installed and Field Service is enabled in Setup > Field Service Settings. The FSL__Scheduling_Policy__c, FSL__Work_Rule__c, and FSL__Service_Objective__c objects must be accessible.
- Identify whether the org is using the Salesforce optimizer (bulk scheduling) or dispatcher-driven manual scheduling, or both. Policy behavior is the same in both cases, but the consequences of misconfiguration are more visible in bulk optimization runs.
- Determine the primary business priority: customer appointment windows, minimizing travel cost, emergency SLA compliance, or contractor overtime control. This drives which default policy to start from and which objectives to weight most heavily.
- Know the complete set of required skills and certifications defined in the org, because Match Skills and Match Required Skills work rules depend on this data being populated on resource records.
- Note that every custom policy MUST include a Service Resource Availability work rule. Without it, the scheduling engine completely ignores resource working hours and absences during candidate evaluation.

---

## Core Concepts

### FSL__Scheduling_Policy__c and Its Two Child Object Types

`FSL__Scheduling_Policy__c` is the top-level scheduling policy object. It acts as a container for two categories of child configuration records:

1. **Work Rules** (`FSL__Work_Rule__c`) — hard pass/fail filters. A candidate time slot is eliminated from consideration if it violates any active work rule. Work rules are binary: the slot either passes or it does not. There is no partial credit.

2. **Service Objectives** (`FSL__Service_Objective__c`) — weighted ranking criteria. After work rules eliminate ineligible slots, service objectives score the remaining candidates. Each objective has a percentage weight set via a slider. Weights across all objectives in a policy should sum to 100%.

A slot must pass all work rules before it is ever scored by service objectives. The two layers are sequential, not simultaneous.

### Work Rule Types

FSL includes 15+ built-in work rule types. The most frequently used types are:

| Work Rule Type | What It Filters |
|---|---|
| Service Resource Availability | Eliminates slots that fall outside the resource's working hours or during recorded absences. **Required in every custom policy.** |
| Match Skills | Eliminates resources who do not have the skills listed on the work order or work type |
| Match Required Skills | Like Match Skills but only enforces skills explicitly flagged as required |
| Match Territory | Eliminates resources who are not members of the service appointment's territory |
| Hard Boundary | Eliminates resources whose Primary or Relocation territory does not match the appointment territory |
| Match Boolean | Eliminates resources where a boolean field on the resource does not match a field on the appointment |
| Match Crews | Eliminates crew members who are not part of the assigned crew |
| Maximum Appointments | Eliminates resources who already have the configured maximum number of appointments for the day |
| Match Time Slot | Eliminates slots that fall outside the customer's preferred time windows |
| Match Job Family | Eliminates resources whose job family does not match the appointment |
| Exclude Weekends | Eliminates slots that fall on Saturday or Sunday |

Work rules can be added, removed, or duplicated within a policy. A policy with no work rules will never filter any candidate, which is rarely the correct behavior.

### Service Objectives

Service objectives score the candidate slots that survive work rule filtering. Each objective has a weight (a percentage between 0 and 100) set using a slider in the Scheduling Policy setup UI. Available objectives include:

| Objective | Scoring behavior |
|---|---|
| ASAP | Scores earlier start times higher. Prioritizes the soonest available appointment. |
| Minimize Travel | Scores lower travel distances and times higher. Reduces fleet cost. |
| Minimize Overtime | Penalizes slots that push a resource into overtime hours. |
| Preferred Resource | Scores resources marked as preferred on the service appointment higher. |
| Skill Level | Scores resources with a higher skill proficiency rating higher. |
| Minimize Unscheduled | Used during bulk optimization; rewards assignments that reduce the total unscheduled appointment count. |

A typical customer-focused policy weights ASAP and Preferred Resource heavily. A cost-focused policy weights Minimize Travel and Minimize Overtime heavily.

### The Four Default Policies

Salesforce ships four ready-to-use scheduling policies. They cannot be deleted and serve as starting points for customization:

| Policy | Primary Use Case | Key Characteristics |
|---|---|---|
| **Customer First** | Maximizing customer satisfaction and preferred windows | Weights customer time windows and preferred resource; lighter travel optimization |
| **High Intensity** | Maximizing appointment volume per technician per day | Weights ASAP and minimizes idle time; accepts longer travel for density |
| **Soft Boundaries** | Allowing cross-territory assignments without strict enforcement | No Hard Boundary work rule; technicians can be scheduled across territories |
| **Emergency** | Urgent, high-priority appointments requiring immediate dispatch | Weights ASAP heavily; lighter filtering to maximize candidate count |

Custom policies should be created by duplicating the closest default policy and adjusting rules and weights. Do not modify the default policies directly, as they are shared reference points across the org.

---

## Common Patterns

### Pattern: Custom Policy with Territory Enforcement and Skill Matching

**When to use:** The org has a defined territory structure, technicians carry certifications required for certain work types, and scheduling must enforce both territory membership and skill eligibility before ranking candidates.

**How it works:**
1. Duplicate the High Intensity or Customer First default policy as a starting point.
2. Add or confirm the following work rules are present: Service Resource Availability, Match Territory (or Hard Boundary for strict enforcement), Match Skills (or Match Required Skills).
3. Remove any work rules that are not applicable to reduce unnecessary filtering.
4. Set service objective weights based on the org's priority: if customer satisfaction drives the business, weight Preferred Resource and Minimize Travel; if throughput matters more, weight ASAP and Minimize Unscheduled.
5. Assign the custom policy to the relevant service territories or set it as the default.

**Why not the alternative:** Using a default policy as-is risks inheriting objectives and work rules that conflict with the org's specific requirements. Emergency policy, for example, has very permissive filtering which is wrong for routine maintenance scheduling.

### Pattern: Emergency Policy for SLA-Bound Urgent Appointments

**When to use:** A subset of work order types represent urgent or safety-critical appointments with strict response-time SLAs. These appointments need to be scheduled immediately regardless of territory, preferred resource, or travel optimization.

**How it works:**
1. Use the built-in Emergency policy or duplicate it as a custom emergency variant.
2. Keep ASAP weighted at or near 100%.
3. Remove Hard Boundary and Match Territory work rules so the largest possible pool of technicians is considered.
4. Keep Service Resource Availability to ensure the scheduled technician is actually available.
5. On the service appointment, set the scheduling policy to the emergency policy at creation time via Flow or Apex before the optimizer or dispatcher picks it up.

**Why not the alternative:** Applying a standard policy to emergency appointments allows the work rules to filter out nearer technicians who happen to be in an adjacent territory. The result is a longer response time, which defeats the purpose of the emergency escalation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New org with no custom policy needs | Start with Customer First default | Balanced settings; good starting point before calibrating |
| Org needs strict territory enforcement | Add Hard Boundary work rule to custom policy | Hard Boundary enforces Primary/Relocation only; blocks cross-territory leakage |
| Technicians have certifications for work types | Add Match Skills or Match Required Skills work rule | Prevents unqualified dispatch; critical for safety-regulated industries |
| Custom policy is ignoring resource absences | Verify Service Resource Availability work rule is present | Without it, absences and off-hours are invisible to the scheduler |
| Emergency appointments need fastest response | Use or duplicate Emergency policy; remove territory boundary rules | Maximize candidate pool; weight ASAP at 100% |
| Business priority is cost reduction | Weight Minimize Travel and Minimize Overtime heavily | Directly reduces mileage reimbursement and overtime payroll costs |
| Technicians are being over-dispatched daily | Add Maximum Appointments work rule with daily cap | Prevents burnout and SLA degradation from over-scheduling |
| Appointments need customer preferred windows | Add Match Time Slot work rule; weight ASAP lower | Respect customer-preferred windows before optimizing for schedule density |
| Soft cross-territory coverage needed | Use Soft Boundaries policy or remove Hard Boundary rule | Allows technicians near a territory border to pick up adjacent appointments |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Identify the business scheduling priority** — Interview the dispatcher or operations manager to determine the primary goal: customer satisfaction, travel efficiency, SLA compliance, or overtime control. This determines which default policy to start from and which objectives to emphasize.

2. **Audit existing policy configuration** — Navigate to Setup > Field Service > Scheduling Policies. Review all active policies, their work rules, and their objective weights. Identify which policy is currently applied to service territories and whether it is producing the correct scheduling behavior.

3. **Duplicate the closest default policy** — Never modify a default policy directly. Use the "Clone" or duplicate action on the most relevant default policy to create a named custom policy. This preserves the defaults as stable reference points.

4. **Configure work rules** — Add, remove, or adjust work rules on the new policy. Mandatory baseline: confirm Service Resource Availability is present. Add Match Skills or Match Territory based on org requirements. Remove rules that create unnecessary filtering for this policy's use case.

5. **Set service objective weights** — Use the objective weight sliders to reflect the business priority identified in step 1. Ensure weights sum to approximately 100% across all active objectives. Test objective weights by running a scheduling simulation on a test service appointment and reviewing the candidate ranking.

6. **Assign the policy to territories or appointments** — Set the custom policy as the default for the relevant service territories, or configure the scheduling policy field on service appointments via Flow or Apex for use-case-specific overrides (e.g., emergency appointments always use the Emergency policy).

7. **Validate and monitor** — After go-live, review the Gantt view for yellow triangle icons, which indicate work rule violations that were overridden during dispatch. A high rate of yellow triangles means the policy's work rules are too strict for real-world dispatch patterns and should be relaxed.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Service Resource Availability work rule is present in every custom policy
- [ ] No default policy (Customer First, High Intensity, Soft Boundaries, Emergency) has been modified in place
- [ ] Work rule types are appropriate for the org's territory structure and workforce model
- [ ] Service objective weights sum to approximately 100% per policy
- [ ] Emergency appointments have a separate policy with ASAP weighted heavily and boundary rules removed
- [ ] Policy is assigned to the correct service territories or applied via automation on service appointments
- [ ] Gantt yellow triangle rate has been reviewed post-deployment and policy adjusted if violations are excessive
- [ ] Match Skills or Match Required Skills work rule is present if work types use required skill records

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Missing Service Resource Availability rule causes the scheduler to ignore all working hours and absences** — A custom scheduling policy created without the Service Resource Availability work rule will silently schedule appointments during technician lunch breaks, weekends, holidays, and recorded absences. No error is shown. The scheduler treats every time slot as valid because nothing is filtering by availability.

2. **Yellow triangles on the Gantt are informational only — the dispatcher can still save** — When a dispatcher manually assigns an appointment that violates a work rule, the Gantt displays a yellow warning triangle. This does not block the save or dispatch action. Practitioners sometimes assume the yellow triangle means the operation failed; it does not. The violation is logged but not enforced.

3. **Default policies cannot be deleted but can be accidentally edited** — The four default policies (Customer First, High Intensity, Soft Boundaries, Emergency) are not protected from in-place edits. An administrator editing a default policy "just to test something" changes the shared reference point for any territory or automation still pointing to it. Always duplicate before modifying.

4. **Objective weights are percentages but do not auto-balance** — Salesforce does not enforce that service objective weights sum to 100%. A policy can have weights totaling 40% or 200% and will not show a validation error. Imbalanced weights produce unexpected candidate rankings that are difficult to diagnose. Always manually verify the total.

5. **Work rule order within a policy does not affect filtering sequence** — Practitioners sometimes reorder work rules expecting earlier rules to apply first, like firewall rules. FSL applies all work rules simultaneously as a set of filters, not sequentially. Reordering them has no effect on the outcome.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FSL__Scheduling_Policy__c record | Named scheduling policy containing the full work rule and objective configuration |
| FSL__Work_Rule__c records | Individual work rule records attached to the policy, each with a specific type and parameters |
| FSL__Service_Objective__c records | Objective records with calibrated percentage weights reflecting the org's scheduling priority |
| Policy assignment configuration | Territory-level default policy assignments or automation logic routing appointments to the correct policy |
| Validation checklist | Completed checklist confirming mandatory work rules, weight totals, and no default policy modification |

---

## Related Skills

- `fsl-service-territory-setup` — service territory and member configuration that work rules like Hard Boundary and Match Territory depend on
- `fsl-service-resource-setup` — resource skills, certifications, and availability records that Match Skills and Service Resource Availability rules evaluate
- `fsl-work-order-management` — work order and work type configuration, including required skills that drive rule matching
