# LLM Anti-Patterns — FSL Resource Management

Common mistakes AI coding assistants make when generating or advising on FSL Resource Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using ResourceType = 'Equipment' for Non-Human Assets

**What the LLM generates:** Code or instructions that set `ResourceType = 'Equipment'` or `ResourceType = 'Asset'` when modeling vehicles or tools as ServiceResource records.

**Why it happens:** The word "equipment" or "asset" is semantically natural for a truck or a calibration rig, so LLMs trained on general descriptions assume a corresponding enum value exists. The actual Salesforce schema only has two valid values: `Technician` and `Crew`.

**Correct pattern:**

```soql
-- Correct: non-human assets use ResourceType = 'Technician' with no RelatedRecordId
INSERT ServiceResource (
    Name            = 'Calibration Rig Unit 1',
    ResourceType    = 'Technician',
    IsCapacityBased = true,
    IsActive        = true
    -- RelatedRecordId intentionally omitted for non-human assets
)
```

**Detection hint:** Any generated code or instruction that references `ResourceType = 'Equipment'`, `ResourceType = 'Asset'`, or `ResourceType = 'Vehicle'` is wrong.

---

## Anti-Pattern 2: Treating ServiceResourceSkill EndDate Expiry as Visible to Dispatchers

**What the LLM generates:** Guidance that says "when the certification expires, the dispatcher will be notified" or "the system will prompt for renewal when EndDate passes," implying the expiry is surfaced proactively.

**Why it happens:** LLMs infer from general software patterns that an expiry mechanism would include a user-visible alert. Salesforce FSL does not surface expired ServiceResourceSkill records as warnings — the scheduler silently drops the resource from candidates.

**Correct pattern:**

```
The FSL scheduler silently excludes resources whose ServiceResourceSkill EndDate
has passed. There is no platform notification. A proactive monitoring query is
required:

SELECT Id, ServiceResource.Name, Skill.MasterLabel, EndDate
FROM ServiceResourceSkill
WHERE EndDate <= NEXT_N_DAYS:30
ORDER BY EndDate ASC

Pair this with an operational workflow that reviews results weekly and
extends or deactivates records before they expire.
```

**Detection hint:** Any claim that Salesforce "notifies," "alerts," or "warns" when a ServiceResourceSkill expires is incorrect.

---

## Anti-Pattern 3: Setting SkillLevel as an Integer 1–10 Scale

**What the LLM generates:** Instructions that map SkillLevel to a 1–10 scale (e.g., "beginner = 1, expert = 10") or that truncate values to integers.

**Why it happens:** A 1–10 proficiency scale is a common real-world convention that LLMs pattern-match onto the SkillLevel field. The actual Salesforce field accepts a decimal from 0 to 99.99.

**Correct pattern:**

```
SkillLevel is a decimal field with a range of 0 to 99.99.
Work type required skill levels reference this scale.
A common convention:
  0–49  = trainee / entry-level
  50–74 = qualified / journeyman
  75–98 = senior / experienced
  99    = master / highest proficiency

Using integers in the 0–99 range is valid; values above 99.99 are rejected.
```

**Detection hint:** Any SkillLevel value above 99.99 or the use of a "1 to 10" framing should be corrected.

---

## Anti-Pattern 4: Advising Deletion of Expired ServiceResourceSkill Records

**What the LLM generates:** A cleanup script or instruction that deletes `ServiceResourceSkill` records whose `EndDate` is in the past to "clean up" the org.

**Why it happens:** Expired records look like stale data, and LLMs default to suggesting deletion as a cleanup strategy. In FSL, expired skill records serve as audit history and may be needed for compliance, reporting, or dispute resolution about which certifications a technician held on a given date.

**Correct pattern:**

```
Do not delete expired ServiceResourceSkill records.
They are the certification audit trail.

To prevent expired records from affecting scheduling:
- If the certification was renewed: update EndDate to the new expiry date
- If the certification was not renewed: leave the record in place (it is already
  inactive in the scheduler) and create a new record when the technician
  re-certifies

Deletion is appropriate only if the record was created in error (wrong Skill,
wrong Resource) and has never reflected a real certification.
```

**Detection hint:** Any generated script that runs `DELETE FROM ServiceResourceSkill WHERE EndDate < TODAY` or equivalent should be flagged and stopped.

---

## Anti-Pattern 5: Creating ResourcePreference Without Verifying Skill Coverage

**What the LLM generates:** A `ResourcePreference` insert with `PreferenceType = 'Required'` without any verification that the required resource holds all active skills needed for the account's work types.

**Why it happens:** LLMs focus on the immediate request (set up the preference) without modeling the downstream dependency (the preference is useless or harmful if the resource lacks the required skills).

**Correct pattern:**

```soql
-- Before creating a Required ResourcePreference, verify active skills:
SELECT Id, Skill.MasterLabel, SkillLevel, StartDate, EndDate
FROM ServiceResourceSkill
WHERE ServiceResourceId = '<target_resource_id>'
  AND (EndDate = null OR EndDate >= TODAY)

-- Then check what skills the work types require for this account's appointments
-- Only insert the Required preference if the resource has all necessary active skills

INSERT ResourcePreference (
    RelatedRecordId   = '<account_id>',
    ServiceResourceId = '<resource_id>',
    PreferenceType    = 'Required'
)
```

**Detection hint:** Any LLM output that creates a `Required` ResourcePreference without a preceding skill verification query or comment about skill coverage is incomplete and potentially harmful.

---

## Anti-Pattern 6: Assuming IsCapacityBased Resources Also Need Shift Records

**What the LLM generates:** Instructions to create both `ServiceResourceCapacity` records AND shift/operating hours records for a capacity-based resource, implying both are needed simultaneously.

**Why it happens:** LLMs blend the two scheduling models (shift-based and capacity-based) because they appear in the same domain. The models are mutually exclusive for a given resource.

**Correct pattern:**

```
ServiceResource scheduling model is determined by IsCapacityBased:

IsCapacityBased = false (default):
  - Availability is governed by ServiceTerritoryMember and OperatingHours
  - Shift records define when the technician is available
  - ServiceResourceCapacity records are NOT used

IsCapacityBased = true:
  - Availability is governed exclusively by ServiceResourceCapacity records
  - Operating hours / shift blocks are NOT evaluated for this resource
  - The only limit is the Capacity value in the active capacity record
```

**Detection hint:** Any output that creates ServiceResourceCapacity records for a resource with `IsCapacityBased = false`, or creates shift records for a resource with `IsCapacityBased = true`, is mixing the two models incorrectly.
