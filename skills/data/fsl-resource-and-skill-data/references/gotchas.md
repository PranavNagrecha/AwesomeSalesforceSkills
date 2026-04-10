# Gotchas — FSL Resource and Skill Data

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Expired ServiceResourceSkill Records Are Not Auto-Deleted

**What happens:** When a ServiceResourceSkill's `EffectiveEndDate` passes, the record remains in the database. Reporting on "active skills" that doesn't filter by date returns all skill records including expired ones, inflating resource capability counts and creating inaccurate scheduling eligibility reports.

**When it occurs:** Orgs that load certification data with EffectiveEndDate and then query skills without date filters months later.

**How to avoid:** All SOQL queries for "current" resource skills must include: `WHERE EffectiveEndDate >= TODAY() OR EffectiveEndDate = NULL`. Build standard reports with this filter as the default.

---

## Gotcha 2: SkillLevel Is Numeric — Text Values Cause Silent Load Errors

**What happens:** SkillLevel is an integer field (0–99999). Loading text values like "Expert" or "Level 3" causes either a type conversion error that fails the record or silent coercion to 0, making all resources appear equal regardless of skill level.

**When it occurs:** Direct exports from HR systems or legacy field service platforms that store skill levels as text labels.

**How to avoid:** Define a numeric mapping table before migration. Transform source skill level labels to integer values. Validate: `SELECT SkillLevel, COUNT(Id) FROM ServiceResourceSkill GROUP BY SkillLevel` to confirm distribution matches expectations.

---

## Gotcha 3: IsCapacityBased Must Be Set at ServiceResource Creation

**What happens:** Attempting to create `ServiceResourceCapacity` records for a ServiceResource with `IsCapacityBased = false` (the default) throws a validation error. Setting IsCapacityBased to true after ServiceResourceCapacity is attempted does not fix records that failed.

**When it occurs:** Migrations that load ServiceResource records with default settings and then try to add capacity data in a separate step.

**How to avoid:** Set `IsCapacityBased = true` in the ServiceResource load CSV for all crew/capacity resources. Validate before loading ServiceResourceCapacity.

---

## Gotcha 4: ServiceResource Links to User or Asset — Not Contact

**What happens:** Attempting to set `RelatedRecordId` on ServiceResource to a Contact Id throws `FIELD_INTEGRITY_EXCEPTION: RelatedRecordId: id value of incorrect type`. ServiceResource requires User or Asset.

**When it occurs:** Migrations from systems where the "resource" entity was modeled as a Contact or Person Account.

**How to avoid:** Map each source resource record to a Salesforce User record (create User records if they don't exist) or to an Asset (for equipment resources). Do not attempt to link to Contacts.

---

## Gotcha 5: SkillRequirement MinimumSkillLevel Must Be Calibrated to Loaded SkillLevel Scale

**What happens:** If Work Type SkillRequirement records have `MinimumSkillLevel = 90` but migrated technician SkillLevel values were loaded on a 1–10 scale (where Expert = 10), no resources match any work type — appointments are unschedulable.

**When it occurs:** Any migration where the numeric mapping scale is defined independently from the existing SkillRequirement configurations on Work Types.

**How to avoid:** Before loading ServiceResourceSkill records, query all SkillRequirement records and their MinimumSkillLevel values. Define the SkillLevel mapping scale to be consistent with existing SkillRequirements.
