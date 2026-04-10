# LLM Anti-Patterns — FSL Shifts and Crew

Common mistakes AI coding assistants make when generating or advising on FSL Shifts and Crew configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Shifts as Work Assignments

**What the LLM generates:** Advice like "create a Shift record to assign the technician to the appointment" or code that creates a Shift record in response to a new ServiceAppointment. The LLM conflates Shift (availability window) with ServiceAppointmentAssignment (actual work dispatch).

**Why it happens:** The word "shift" in general workforce management means a scheduled work block that includes assigned tasks. In Salesforce FSL, Shift specifically means an availability window — not an assignment. LLMs trained on general HR and scheduling content carry this semantic mismatch.

**Correct pattern:**

```text
- Shift record: "Is this resource available to be scheduled during this window?"
  -> Links ServiceResource to a time window. Status = Confirmed means "available."
  -> Does NOT represent assigned work.

- ServiceAppointmentAssignment / AssignedResource: "Which resource is doing this job?"
  -> Created when a ServiceAppointment is dispatched to a resource.
  -> Independent of Shift records.
```

**Detection hint:** Look for LLM output that references `Shift.ServiceAppointmentId` (field does not exist) or suggests inserting a Shift record from a trigger on ServiceAppointment creation.

---

## Anti-Pattern 2: Confusing Shift Get Candidates with Managed-Package Get Candidates

**What the LLM generates:** Troubleshooting advice that tells practitioners to "check the scheduling policy work rules" when resources are missing from shift-based candidate results, or vice versa — checking Shift Status when the actual issue is a failed work rule.

**Why it happens:** LLMs often compress the two separate Get Candidates operations into one. The managed-package documentation and the FSL Shifts documentation appear in the same training corpus without sufficient disambiguation of which system is responsible for what.

**Correct pattern:**

```text
Shift Get Candidates (availability check):
- Queries: Shift records with Status = Confirmed within Operating Hours
- Diagnose with: SOQL on Shift object, check Status and time windows
- Configured in: Field Service Settings > Scheduling (Shift mode)

Managed-package Get Candidates (qualification check):
- Queries: Scheduling Policies, Work Rules, Resource skills/territory/capacity
- Diagnose with: Scheduling Policy logs, work rule debug output
- Configured in: Scheduling Policy records in Field Service Setup

These are separate flows — a resource can pass one and fail the other.
```

**Detection hint:** Look for LLM output that advises checking "work rules" to fix missing Shift candidates, or advises checking "Shift status" to fix work-rule qualification failures.

---

## Anti-Pattern 3: Assigning Skills Directly to Crew ServiceResource for Static Crews

**What the LLM generates:** Apex or configuration steps that create `ServiceResourceSkill` records with `ServiceResourceId = [Crew record Id]`, expecting the crew to inherit those skills for scheduling. LLMs often model this by analogy to individual resource skill assignment, which uses the same object.

**Why it happens:** The `ServiceResourceSkill` object is used identically for both Technician and Crew ServiceResource records syntactically — there is nothing in the field schema that prevents assigning skills to a Crew record. The behavioral difference (skills on Crew records are ignored; skills must be on member records) is a runtime scheduling engine behavior, not a data model constraint.

**Correct pattern:**

```text
// WRONG — skill on Crew ServiceResource directly
ServiceResourceSkill crewSkill = new ServiceResourceSkill(
    ServiceResourceId = crewServiceResourceId,  // Crew record
    SkillId = fiberSplicingSkillId
);

// CORRECT — skill on each member's Technician-type ServiceResource
ServiceResourceSkill memberSkill = new ServiceResourceSkill(
    ServiceResourceId = techAServiceResourceId,  // Technician member record
    SkillId = fiberSplicingSkillId,
    SkillLevel = 8
);
```

**Detection hint:** Look for `ServiceResourceSkill` records where `ServiceResource.ResourceType = 'Crew'` — this is the anti-pattern. Query: `SELECT Id FROM ServiceResourceSkill WHERE ServiceResource.ResourceType = 'Crew'`.

---

## Anti-Pattern 4: Generating Shifts Without Verifying Status After Bulk Creation

**What the LLM generates:** Data Loader or Apex bulk insert scripts that create Shift records without explicitly setting `Status = 'Confirmed'`, or instructions that say "generate shifts using ShiftPattern" without mentioning the post-generation status verification step.

**Why it happens:** LLMs assume that bulk-generated Shifts default to Confirmed. In some FSL configurations or versions, the default is Tentative. The LLM does not distinguish between the two because the Shift generation documentation describes the action without always clarifying the default Status value in all org configurations.

**Correct pattern:**

```text
// After bulk shift generation, always verify:
SELECT Status, COUNT(Id) shiftCount
FROM Shift
WHERE ServiceResource.IsActive = true
  AND StartTime >= TODAY
GROUP BY Status

// If Tentative count > 0, update to Confirmed:
UPDATE [Shift] SET Status = 'Confirmed'
WHERE Status = 'Tentative' AND StartTime >= TODAY
```

**Detection hint:** Any LLM output that describes ShiftPattern generation without a follow-up Status verification step is incomplete. Flag responses that end at "click Generate Shifts" without confirming resulting statuses.

---

## Anti-Pattern 5: Dispatching Service Appointments to Individual Crew Members Instead of the Crew ServiceResource

**What the LLM generates:** Automation code or configuration steps that assign a ServiceAppointment to individual Technician-type ServiceResource records that are members of a crew, instead of to the Crew-type ServiceResource. This often appears in Apex triggers or Flow logic that tries to "spread" crew appointments across members.

**Why it happens:** The LLM's model of crew scheduling is that a crew appointment should be visible to all members, so it tries to create one assignment per member. In FSL, the correct model is one assignment to the Crew ServiceResource — the FSL mobile app handles surfacing the appointment to individual members via their ServiceCrewMember relationship.

**Correct pattern:**

```text
// WRONG — assigning to individual members
AssignedResource ar1 = new AssignedResource(
    ServiceAppointmentId = saId,
    ServiceResourceId = techAId  // individual member
);
AssignedResource ar2 = new AssignedResource(
    ServiceAppointmentId = saId,
    ServiceResourceId = techBId  // individual member
);

// CORRECT — assigning to the Crew ServiceResource
AssignedResource ar = new AssignedResource(
    ServiceAppointmentId = saId,
    ServiceResourceId = crewAlphaId  // Crew ServiceResource record
);
// Individual members see the appointment via FSL mobile through
// their ServiceCrewMember.CrewId relationship.
```

**Detection hint:** Look for `AssignedResource` records where `ServiceResource.ResourceType = 'Crew'` is NOT true but the appointment was intended for a crew — or where multiple `AssignedResource` records exist for the same appointment with resources that are ServiceCrewMembers of the same crew.
