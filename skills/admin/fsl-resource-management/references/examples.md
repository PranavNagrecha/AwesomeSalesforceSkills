# Examples — FSL Resource Management

## Example 1: Technician with an Expiring Electrical Certification

**Context:** A utility company onboards a licensed electrician who holds a state electrical certification that expires annually. The certification must be tracked so that after expiry the scheduler automatically stops assigning them to jobs requiring the `Electrical-LicensedJourneyman` skill, without any manual dispatcher action.

**Problem:** If the ServiceResourceSkill record is created without an EndDate, the resource continues to appear as a scheduling candidate indefinitely, even after the real-world certification lapses. Dispatchers have no automated signal to stop assigning the technician to regulated work.

**Solution:**

```soql
-- Step 1: Find the existing Skill record to avoid duplicates
SELECT Id, MasterLabel FROM Skill WHERE MasterLabel = 'Electrical-LicensedJourneyman'

-- Step 2: Create the ServiceResourceSkill with expiry date
INSERT ServiceResourceSkill (
    ServiceResourceId = '<technician_resource_id>',
    SkillId           = '<electrical_skill_id>',
    SkillLevel        = 75,          -- journeyman proficiency level
    StartDate         = 2026-04-07,
    EndDate           = 2027-04-06   -- one year from certification date
)

-- Step 3: Periodic audit query to surface expiring or expired certifications
SELECT Id, ServiceResource.Name, Skill.MasterLabel, SkillLevel, EndDate
FROM ServiceResourceSkill
WHERE EndDate <= NEXT_N_DAYS:30
ORDER BY EndDate ASC
```

**Why it works:** Setting `EndDate` on `ServiceResourceSkill` causes the FSL scheduler to treat the skill as inactive once the date passes. No dispatcher intervention is needed — the resource drops out of candidates automatically. The audit query provides a 30-day warning window so administrators can renew or deactivate records before they expire silently.

---

## Example 2: Shared Calibration Equipment as a Capacity-Based Resource

**Context:** A field service org has one calibration rig that multiple technicians use during service visits. The rig can be booked for a maximum of 6 appointments per day. It needs to appear as a schedulable resource in the FSL Dispatcher Console so appointment planners can track whether it is available.

**Problem:** Modeling the calibration rig as a standard Technician-type resource with shift-based availability treats it as if it is dedicated to one appointment at a time and one technician's shift, which does not reflect shared, count-limited equipment correctly.

**Solution:**

```soql
-- Step 1: Create the ServiceResource for the equipment
INSERT ServiceResource (
    Name             = 'Calibration Rig - Unit 1',
    ResourceType     = 'Technician',   -- Equipment uses Technician type
    IsActive         = true,
    IsCapacityBased  = true            -- Capacity model, not shift-based
    -- No RelatedRecordId: equipment has no User link
)

-- Step 2: Create capacity records for the scheduling horizon
-- Cover April and May so there are no unschedulable date gaps
INSERT ServiceResourceCapacity (
    ServiceResourceId = '<rig_resource_id>',
    StartDate         = 2026-04-01,
    EndDate           = 2026-04-30,
    TimeSlotType      = 'Normal',
    Capacity          = 6,
    CapacityUnit      = 'Appointments'
)
INSERT ServiceResourceCapacity (
    ServiceResourceId = '<rig_resource_id>',
    StartDate         = 2026-05-01,
    EndDate           = 2026-05-31,
    TimeSlotType      = 'Normal',
    Capacity          = 6,
    CapacityUnit      = 'Appointments'
)

-- Step 3: Assign the equipment skill so it matches work types requiring it
INSERT ServiceResourceSkill (
    ServiceResourceId = '<rig_resource_id>',
    SkillId           = '<calibration-skill-id>',
    SkillLevel        = 99
    -- No EndDate: equipment skill does not expire
)
```

**Why it works:** `IsCapacityBased = true` instructs the scheduler to evaluate availability via `ServiceResourceCapacity` records rather than shift blocks. The `CapacityUnit = Appointments` setting means the rig can take up to 6 bookings per day regardless of time overlap, correctly modeling shared equipment. Creating records for both April and May eliminates silent date gaps that would make the rig unschedulable in May.

---

## Example 3: ResourcePreference for a High-Value Account

**Context:** A key enterprise customer has a relationship with one specific senior technician and expects that technician to handle all on-site visits. This is a contractual expectation documented in the account record.

**Problem:** Without a `ResourcePreference` record, any qualified technician can be auto-assigned by the scheduler. Dispatchers must remember to manually select the preferred technician every time, which fails when dispatchers rotate or when bulk scheduling is used.

**Solution:**

```soql
-- Step 1: Locate the Account and ServiceResource records
SELECT Id FROM Account WHERE Name = 'Acme Industrial'
SELECT Id FROM ServiceResource WHERE Name = 'Jordan Smith'

-- Step 2: Create the Required preference
INSERT ResourcePreference (
    RelatedRecordId   = '<acme_account_id>',
    ServiceResourceId = '<jordan_smith_resource_id>',
    PreferenceType    = 'Required'
)

-- Step 3: Verify the required resource holds all active skills
-- (missing or expired skills + Required preference = zero candidates)
SELECT Id, Skill.MasterLabel, SkillLevel, EndDate
FROM ServiceResourceSkill
WHERE ServiceResourceId = '<jordan_smith_resource_id>'
  AND (EndDate = null OR EndDate >= TODAY)
```

**Why it works:** `PreferenceType = Required` causes the FSL scheduler to return only Jordan Smith as a candidate for any service appointment linked to the Acme Industrial account. The verification query in Step 3 confirms the required technician has no expired skill records, preventing the silent zero-candidates failure mode.

---

## Anti-Pattern: Creating a New Skill Record for Every Resource

**What practitioners do:** When assigning a skill to a resource, some practitioners create a brand-new `Skill` record for each assignment rather than reusing the shared Skill catalog. This results in duplicate Skill records with slightly different names (e.g., "HVAC Repair", "HVAC-Repair", "HVAC repair").

**What goes wrong:** Work types reference a specific Skill record by ID. A technician whose `ServiceResourceSkill` points to a differently-named duplicate Skill record will not match work type requirements, causing them to be excluded from scheduling for HVAC jobs even though they appear to have the right qualification. The problem is invisible in the UI unless you compare Skill IDs directly.

**Correct approach:** Before creating any `ServiceResourceSkill` record, query the `Skill` object and reuse an existing record if the skill already exists. Establish a naming convention governance process so that new skills are added to the shared catalog only after confirming no equivalent exists.
