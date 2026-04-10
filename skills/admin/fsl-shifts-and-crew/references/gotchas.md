# Gotchas — FSL Shifts and Crew

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Shift Get Candidates and Managed-Package Get Candidates Are Entirely Separate Operations

**What happens:** Practitioners enable shift-based scheduling and expect the existing "Get Candidates" button in the Dispatcher Console to respect Shift records. It does not. There are two distinct Get Candidates operations: the **Shift Get Candidates** (checks availability windows from Shift records) and the **managed-package Get Candidates** (evaluates scheduling policies, work rules, and resource qualifications). Enabling FSL Shifts adds a separate interface element for shift-based candidate lookup — it does not modify the behavior of the existing Get Candidates flow.

**When it occurs:** Any time an org transitions from non-shift to shift-based scheduling. Dispatchers continue using the familiar Get Candidates button expecting it to now honor shift windows, and cannot understand why technicians with Confirmed Shifts still don't appear as shift-available candidates.

**How to avoid:** Explicitly train dispatchers on the two separate flows. Shift Get Candidates is accessed via the shift-aware scheduling interface in the Dispatcher Console (enabled via Field Service Settings > Scheduling). Do not use managed-package Get Candidates logs to diagnose shift availability problems — look at Shift record Status and time window alignment instead.

---

## Gotcha 2: Tentative Shift Status Silently Excludes Resources from Scheduling

**What happens:** A Shift record with `Status = Tentative` does not make the associated ServiceResource available for scheduling. The scheduler evaluates only `Status = Confirmed` Shifts. No error is thrown, no warning appears — the resource simply does not surface in candidate results. Bulk-generated Shifts from some flows default to Tentative.

**When it occurs:** When ShiftPattern generation defaults the status to Tentative (org-specific behavior depending on version and settings), or when dispatchers create draft shifts and forget to confirm them before the scheduling window opens. Also occurs when Shift records are imported via Data Loader without explicitly setting Status.

**How to avoid:** After bulk Shift generation, always run a SOQL check: `SELECT COUNT(Id) FROM Shift WHERE Status = 'Tentative'`. Update all to Confirmed before the scheduling window. Consider adding a validation rule or Flow to prevent saving Shifts without an explicit Status selection during import workflows.

---

## Gotcha 3: Shift Windows Outside Operating Hours Are Silently Truncated

**What happens:** If a Shift's `StartTime` or `EndTime` falls outside the Operating Hours window of the service territory, the out-of-window portion is silently ignored by the scheduling engine. For example, if Operating Hours run 08:00–17:00 and a Shift runs 07:00–18:00, the scheduler treats the resource as available only from 08:00–17:00. There is no error or warning — the discrepancy is invisible unless the Dispatcher Console is used to manually inspect candidate windows.

**When it occurs:** Common when Operating Hours are configured conservatively (e.g., 08:00–17:00) but field managers create Shifts for overtime or early-start windows (06:00–19:00) expecting the shift to override the Operating Hours constraint.

**How to avoid:** Operating Hours govern the hard outer boundary; Shifts govern availability within that boundary. To allow scheduling outside the default Operating Hours, the Operating Hours record itself must be updated — not the Shift. Always cross-check Shift time ranges against the associated Operating Hours record before diagnosing "missing candidate" issues.

---

## Gotcha 4: Static Crew Skills Must Be on Member Records, Not the Crew ServiceResource

**What happens:** An admin attaches `ServiceResourceSkill` records directly to the Crew-type ServiceResource (e.g., "Crew Alpha" has Fiber Splicing skill). The scheduling engine ignores skills placed directly on Crew records for Static Crew skill aggregation. During Get Candidates evaluation, the crew appears to lack the required skill and is excluded from results — even though a skill record is clearly visible on the Crew's related list.

**When it occurs:** Whenever an admin tries to shortcut crew skill setup by assigning skills at the crew level rather than at each member's individual ServiceResource record. Also common when a new crew member is added but their individual skills are not updated.

**How to avoid:** For Static Crews, always assign `ServiceResourceSkill` records to the individual member Technician-type ServiceResource records. The scheduler aggregates the union of active member skills to evaluate crew-level skill requirements. Shell/Dynamic Crews do not use skill aggregation at all — they rely on CrewSize for capacity.

---

## Gotcha 5: ResourceType Cannot Be Changed After ServiceResource Creation

**What happens:** A Crew-type ServiceResource is created by mistake as a Technician, or a Technician is incorrectly registered as a Crew. Attempting to change the `ResourceType` field on the existing record fails with a validation error. The record cannot be repurposed — a new ServiceResource must be created.

**When it occurs:** During initial FSL setup when admins are unfamiliar with the Crew model and create placeholder records to test. Also occurs during migrations when source data maps crew groups to Technician records incorrectly.

**How to avoid:** Before creating ServiceResource records, confirm the correct ResourceType by reviewing the crew model requirements. For Shell/Dynamic Crew setups, also confirm CrewSize is populated at creation time. If a wrong-type record was created, deactivate it (IsActive = false), create the correct record, and re-associate any existing related records (ServiceCrewMember, Shift, territory membership) to the new record.
