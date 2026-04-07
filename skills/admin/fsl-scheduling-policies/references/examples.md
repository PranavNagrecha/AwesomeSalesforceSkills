# Examples — FSL Scheduling Policies

## Example 1: Custom Policy for Skilled-Trade Dispatch with Territory Enforcement

**Context:** A utilities company dispatches licensed electricians and plumbers across multiple regional territories. Each work order type has required skill records attached. Technicians are members of a single Primary territory. The existing Customer First default policy is producing cross-territory assignments and dispatching unqualified technicians because no skill or boundary enforcement is in place.

**Problem:** Without Match Required Skills and Hard Boundary work rules, the scheduler considers all available resources regardless of certification and territory membership. A plumbing work order is being offered to electricians in adjacent territories, and dispatchers are manually overriding every suggestion.

**Solution:**

```
Scheduling Policy: Utilities - Skilled Dispatch
Work Rules:
  1. Service Resource Availability     (type: Service Resource Availability)
  2. Match Required Skills             (type: Match Required Skills)
  3. Hard Boundary                     (type: Hard Boundary)

Service Objectives:
  - ASAP:              40%
  - Minimize Travel:   40%
  - Preferred Resource: 20%
```

Steps:
1. Clone Customer First into a new policy named "Utilities - Skilled Dispatch".
2. Remove the existing Match Territory rule (if present) and replace with Hard Boundary.
3. Add Match Required Skills work rule.
4. Confirm Service Resource Availability is present (it should carry over from the clone).
5. Set objective weights: ASAP 40%, Minimize Travel 40%, Preferred Resource 20%.
6. Assign this policy as the default on all regional service territories.

**Why it works:** Hard Boundary restricts candidates to technicians whose Primary or Relocation territory matches the appointment's territory, eliminating cross-territory noise. Match Required Skills filters out resources missing the certification before scoring begins. Service Resource Availability ensures only genuinely available slots surface. The 40/40/20 objective split balances quick response with cost control.

---

## Example 2: Emergency Override Policy for Safety-Critical Incidents

**Context:** A field operations company has two appointment classes: routine maintenance (uses the standard policy) and emergency safety incidents (must be responded to within 2 hours). Currently both classes use the same policy, resulting in emergency appointments sitting in a queue while the optimizer waits for territory-matched resources.

**Problem:** The standard policy enforces Hard Boundary and Match Skills, which limits the candidate pool for emergency appointments to a small number of in-territory certified technicians. When those technicians are busy, the appointment goes unscheduled rather than escalating to the nearest available technician in any territory.

**Solution:**

```
Scheduling Policy: Emergency Response
Work Rules:
  1. Service Resource Availability     (type: Service Resource Availability)
  — (no territory boundary rules)
  — (no skill matching rules)

Service Objectives:
  - ASAP:              100%
```

Flow / Apex on ServiceAppointment creation:
```
IF WorkOrder.Priority = 'Emergency'
THEN ServiceAppointment.FSL__Scheduling_Policy__c = [Emergency Response policy Id]
ELSE ServiceAppointment.FSL__Scheduling_Policy__c = [Standard Skilled Dispatch policy Id]
```

**Why it works:** Removing Hard Boundary and skill matching from the Emergency policy expands the candidate pool to every available technician in every territory. Service Resource Availability remains to prevent scheduling during recorded absences. Weighting ASAP at 100% means the scheduler always selects the earliest available slot, regardless of travel distance. Setting the policy on the appointment record at creation time ensures the correct policy governs scheduling from the start without requiring dispatcher intervention.

---

## Anti-Pattern: Modifying a Default Policy In-Place

**What practitioners do:** An administrator navigates to the Customer First default policy and adjusts the objective weights or removes a work rule to "test the effect" of the change, intending to revert it later.

**What goes wrong:** Any service territory using Customer First as its default policy immediately inherits the change. If the revert is forgotten or the administrator leaves the project, the modified default silently affects all appointments scheduled against that territory. Because the policy is named "Customer First," subsequent administrators assume it matches the Salesforce documentation for the default policy and do not audit it.

**Correct approach:** Always clone the default policy before making changes. Name the clone to reflect its purpose (e.g., "Customer First - West Region"). Make all changes on the clone. The four default policies (Customer First, High Intensity, Soft Boundaries, Emergency) should remain untouched as stable reference points.
