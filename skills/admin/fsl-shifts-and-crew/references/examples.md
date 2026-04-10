# Examples — FSL Shifts and Crew

## Example 1: Bulk Weekly Shift Generation for a 40-Person Field Workforce

**Context:** A utilities company is rolling out FSL for 40 field technicians across two service territories. All technicians work a standard Monday–Friday 08:00–17:00 shift. The admin needs to seed 90 days of Shift records without manually creating 40 × 90 = 3,600 records.

**Problem:** Without ShiftPattern, the only option is to create Shift records one at a time (via the Shifts tab or the Dispatcher Console). At scale this is error-prone, inconsistent, and violates the repeatability required for scheduling reliability.

**Solution:**

```text
1. Create one ShiftPattern record:
   - Name: "Standard Weekday"
   - PatternLength: 7  (one-week cycle)
   - TimeZone: "America/Chicago"  (must match territory Operating Hours TZ)

2. Create 5 ShiftPatternEntry records (one per weekday):
   - DayOfPattern: 1, StartTime: 08:00, EndTime: 17:00  (Monday)
   - DayOfPattern: 2, StartTime: 08:00, EndTime: 17:00  (Tuesday)
   - DayOfPattern: 3, StartTime: 08:00, EndTime: 17:00  (Wednesday)
   - DayOfPattern: 4, StartTime: 08:00, EndTime: 17:00  (Thursday)
   - DayOfPattern: 5, StartTime: 08:00, EndTime: 17:00  (Friday)
   (DayOfPattern 6 and 7 — weekend — have no entries, so no shifts generated)

3. For each of the 40 ServiceResource records:
   - Open the record -> Related tab -> Generate Shifts
   - Select ShiftPattern: "Standard Weekday"
   - Set date range: today to 90 days out
   - FSL generates Shift records automatically, each with Status = Confirmed

4. Spot-check: SOQL verify 40 resources × ~65 weekdays = ~2,600 Confirmed Shift records
   SELECT ServiceResourceId, COUNT(Id) shiftCount
   FROM Shift
   WHERE Status = 'Confirmed'
   GROUP BY ServiceResourceId
```

**Why it matters:** ShiftPattern generation is idempotent when date ranges don't overlap — regenerating for the next quarter creates new records without touching existing ones. Stale Shifts from terminated employees should be deleted or set to Canceled individually, then re-generated for replacement resources.

---

## Example 2: Static Crew Configuration for a Three-Person Installation Team

**Context:** A telecom field service org has dedicated three-person installation crews. Each crew always dispatches together. Appointments require "Fiber Splicing" and "Safety Certification" skills. The admin needs to configure one crew so appointments route to the crew as a unit.

**Problem:** If the admin creates three separate Technician-type ServiceResources and schedules appointments to individuals, the crew model breaks — appointments appear on three separate Gantt rows, travel time is calculated independently, and there is no unified crew capacity view. The org wants a single Gantt row per crew.

**Solution:**

```text
1. Create a Crew ServiceResource:
   - Name: "Crew Alpha"
   - ResourceType: Crew
   - IsActive: true
   (Do NOT populate RelatedRecordId — Crew type has no User link)

2. Create 3 Technician-type ServiceResource records for the members:
   - "Tech A" (ResourceType: Technician, linked to User A)
   - "Tech B" (ResourceType: Technician, linked to User B)
   - "Tech C" (ResourceType: Technician, linked to User C)

3. Create ServiceCrewMember records linking members to Crew Alpha:
   - Crew: Crew Alpha | Member Resource: Tech A | StartDate: today
   - Crew: Crew Alpha | Member Resource: Tech B | StartDate: today
   - Crew: Crew Alpha | Member Resource: Tech C | StartDate: today

4. Assign required skills to individual members (NOT to Crew Alpha):
   - Tech A -> ServiceResourceSkill: "Fiber Splicing" (SkillLevel: 8)
   - Tech A -> ServiceResourceSkill: "Safety Certification"
   - Tech B -> ServiceResourceSkill: "Fiber Splicing" (SkillLevel: 6)
   - Tech C -> ServiceResourceSkill: "Safety Certification"
   (Crew Alpha's effective skill set is the union of all active member skills)

5. Create Shift records for Crew Alpha (not for Tech A/B/C individually):
   - ServiceResourceId: Crew Alpha
   - StartTime / EndTime: working window
   - Status: Confirmed

6. When scheduling a service appointment requiring "Fiber Splicing":
   - Dispatch to Crew Alpha (ServiceResource)
   - Appointment appears on Crew Alpha's Dispatcher Console row
   - Tech A, B, C see the appointment via FSL mobile as crew members
```

**Why it matters:** Scheduling to the Crew ServiceResource (not individual members) is essential for crew-mode routing. The Dispatcher Console Gantt row for the crew shows capacity utilization. Individual member rows show only non-crew work. Mixing crew and individual dispatch for the same physical team creates double-booking and capacity-count errors.

---

## Anti-Pattern: Using Shell/Dynamic Crew Without Setting CrewSize

**What practitioners do:** Create a Crew ServiceResource with `ResourceType = Crew` for a dynamic pooled workforce, but leave the `CrewSize` field blank (null or zero). They expect the scheduling engine to treat the crew as available for any appointment.

**What goes wrong:** A Shell crew with `CrewSize = 0` or null is treated as having zero capacity by the scheduling engine. It will not surface as a candidate in Get Candidates results regardless of whether Shift records exist for it. This manifests as the crew disappearing from Dispatcher Console candidate lists with no error message.

**Correct approach:** Always set `CrewSize` to the expected number of crew members (e.g., `CrewSize = 3` for a three-person crew). For Static Crews where membership drives capacity, the member count from active ServiceCrewMember records governs — but for Shell/Dynamic Crews, `CrewSize` is the only capacity signal the scheduler has.
