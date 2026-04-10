# LLM Anti-Patterns — FSL Resource and Skill Data

Common mistakes AI coding assistants make when generating or advising on FSL Resource and Skill Data.

## Anti-Pattern 1: Loading SkillLevel as Text Values

**What the LLM generates:** ServiceResourceSkill CSV with SkillLevel = "Expert", "Intermediate", "Beginner", or "Level 3".

**Why it happens:** LLMs default to text labels because that's how skill levels appear in most HR and talent management systems.

**Correct pattern:** SkillLevel is an integer (0–99999). Define a mapping table and transform source labels to integers before loading. Example: Expert = 99, Intermediate = 50, Beginner = 10.

**Detection hint:** Any ServiceResourceSkill load with non-integer SkillLevel values is wrong.

---

## Anti-Pattern 2: Linking ServiceResource to Contact Instead of User

**What the LLM generates:** ServiceResource insert with `RelatedRecordId` mapped to a Contact Id.

**Why it happens:** LLMs know FSL involves customer interactions and assume technicians are Contacts.

**Correct pattern:** `ServiceResource.RelatedRecordId` must point to a User record (for human technicians) or an Asset record (for equipment). Create User records before ServiceResource records if they don't exist.

**Detection hint:** Any ServiceResource load mapping RelatedRecordId to a Contact is wrong.

---

## Anti-Pattern 3: Not Including EffectiveEndDate for Expired Certifications

**What the LLM generates:** ServiceResourceSkill load with only EffectiveStartDate, leaving EffectiveEndDate null for all records regardless of certification expiry dates in the source data.

**Why it happens:** LLMs treat expiry tracking as optional when it's actually a required field for certification-based scheduling enforcement.

**Correct pattern:** Load EffectiveEndDate from source certification expiry dates. Records with EffectiveEndDate in the past are treated as expired by the scheduling engine.

**Detection hint:** Any ServiceResourceSkill migration guidance that doesn't mention EffectiveEndDate for certification data is incomplete.

---

## Anti-Pattern 4: Loading ServiceResourceCapacity Before Setting IsCapacityBased

**What the LLM generates:** Two-step instructions that load ServiceResource records (with default IsCapacityBased = false) and then load ServiceResourceCapacity in a separate step, assuming IsCapacityBased can be set later.

**Why it happens:** LLMs treat object field setup as non-sequential.

**Correct pattern:** Set `IsCapacityBased = true` on the ServiceResource in the initial load. ServiceResourceCapacity records will fail to insert if this field is false.

**Detection hint:** Any ServiceResourceCapacity load procedure that doesn't confirm IsCapacityBased = true first is incomplete.

---

## Anti-Pattern 5: Querying "Current Skills" Without Date Filters

**What the LLM generates:**
```soql
SELECT Id, Skill.MasterLabel FROM ServiceResourceSkill WHERE ServiceResourceId = :srId
```

**Why it happens:** LLMs generate straightforward lookups without modeling that expired skill records are never auto-deleted.

**Correct pattern:**
```soql
SELECT Id, Skill.MasterLabel, EffectiveEndDate
FROM ServiceResourceSkill
WHERE ServiceResourceId = :srId
AND (EffectiveEndDate >= TODAY() OR EffectiveEndDate = NULL)
```

**Detection hint:** Any ServiceResourceSkill SOQL query without a date range filter is likely returning expired certifications.
