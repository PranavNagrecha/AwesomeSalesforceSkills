# Examples — FSL Resource and Skill Data

## Example 1: Migrating Technician Skills with Certification Expiry Dates

**Context:** An HVAC service company migrates technician certification data from their HR system into FSL. Each technician has between 1 and 8 certifications with earned dates and expiry dates. FSL must enforce that technicians without valid certifications are not scheduled for work types requiring those skills.

**Problem:** The migration team loads ServiceResourceSkill records without EffectiveEndDate for expired certifications. Expired technicians continue appearing as scheduling candidates because the scheduling policy sees an active skill record with no end date.

**Solution:**
1. Load Skill records (e.g., "EPA 608 Certified", "R-410A Certified") with External IDs
2. Load ServiceResource records linked to User records
3. Load ServiceResourceSkill records with:
   - `EffectiveStartDate` = certification earned date
   - `EffectiveEndDate` = certification expiry date (set for expired AND future-expiring certs)
   - `SkillLevel` = numeric mapping (e.g., 99 for certified, 50 for provisional)
4. On Work Types, set `SkillRequirement.MinimumSkillLevel = 90` for work requiring certification
5. The scheduling engine automatically excludes resources whose `EffectiveEndDate < today` when evaluating SkillRequirement

**Why it works:** FSL's scheduling engine evaluates `EffectiveEndDate` when matching resource skills to SkillRequirements. Setting EffectiveEndDate on the certification record is the mechanism for certification-based scheduling exclusion.

---

## Example 2: Capacity-Based Resource Setup for Crew Scheduling

**Context:** An electrical utility uses crews of 2-3 technicians for high-voltage work. In FSL, the crew is scheduled as a single resource with capacity hours, not as individual members.

**Problem:** The team tries to load `ServiceResourceCapacity` records before setting `IsCapacityBased = true` on the ServiceResource. The load fails with a validation error.

**Solution:**
1. Load ServiceResource with `IsCapacityBased = true`, `ResourceType = Crew`
2. After confirming ServiceResource records, load ServiceResourceCapacity records:
   ```
   CSV headers: ServiceResourceId, CapacityInHours, StartDate, EndDate, Legacy_Cap_Id__c
   ```
3. Use the ServiceResource External ID to look up ServiceResourceId in the capacity CSV

**Why it works:** `ServiceResourceCapacity` has a validation that the parent `ServiceResource.IsCapacityBased = true`. Setting this at resource creation time satisfies the dependency.

---

## Anti-Pattern: Using Text SkillLevel Values

**What practitioners do:** Load ServiceResourceSkill records with SkillLevel = "Expert" or SkillLevel = "Level 3" directly from the source system export.

**What goes wrong:** SkillLevel is a numeric field (Integer). Attempting to load text values throws `INVALID_TYPE_FOR_OPERATOR_OR_VALUE` or silent type coercion to 0, making all resources appear to have the same base skill level.

**Correct approach:** Build a mapping table before migration:

| Source Label | FSL SkillLevel |
|---|---|
| Beginner | 1 |
| Intermediate | 50 |
| Advanced | 75 |
| Expert / Certified | 99 |

Transform all source skill level values through the mapping table before generating the load CSV.
