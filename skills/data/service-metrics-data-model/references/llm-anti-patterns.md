# LLM Anti-Patterns — Service Metrics Data Model

Common mistakes AI coding assistants make when generating or advising on Service Metrics Data Model.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating IsViolated = false as the SLA Compliance Filter

**What the LLM generates:**

```sql
-- WRONG: "get all compliant milestones"
SELECT Id, CaseId, ElapsedTimeInMins
FROM CaseMilestone
WHERE IsViolated = false
```

Or in a report filter: `IsViolated = false` → label: "Compliant Milestones."

**Why it happens:** `IsViolated = false` sounds like "not violated = compliant." LLMs generalize from boolean field names without understanding that open in-progress milestones also have `IsViolated = false` until their `TargetDate` passes.

**Correct pattern:**

```sql
-- CORRECT: only terminal-state milestones in denominator
SELECT Id, CaseId, IsCompleted, IsViolated, ElapsedTimeInMins
FROM CaseMilestone
WHERE (IsCompleted = true OR IsViolated = true)
-- Compliant = IsCompleted = true AND IsViolated = false
-- Non-compliant = IsViolated = true (regardless of IsCompleted)
```

**Detection hint:** Look for `WHERE IsViolated = false` without a corresponding `AND IsCompleted = true`. If present, the query likely includes open in-progress milestones in a compliance calculation.

---

## Anti-Pattern 2: Assuming ElapsedTimeInMins Is Case-Level MTTR

**What the LLM generates:**

```sql
-- WRONG: using ElapsedTimeInMins to compute mean time to resolve cases
SELECT AVG(ElapsedTimeInMins) mttr
FROM CaseMilestone
WHERE MilestoneType.Name = 'Resolution'
```

Or: "Use `CaseMilestone.ElapsedTimeInMins` to get the MTTR for each case."

**Why it happens:** `ElapsedTimeInMins` sounds like a case resolution time metric. LLMs conflate "resolution milestone elapsed time" with "case resolution time from open to close."

**Correct pattern:**

```
MTTR should be measured at the Case level:
  - Calendar MTTR: Formula field on Case — IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)
  - BH-aware MTTR: Apex trigger storing BusinessHours.diff(bhId, CreatedDate, ClosedDate) in MTTR_BH_Mins__c

ElapsedTimeInMins on CaseMilestone is correct for:
  - "How long did it take to achieve First Response?" (per-milestone measurement)
  - SLA compliance per milestone type
```

**Detection hint:** If output suggests reporting `AVG(ElapsedTimeInMins)` as "MTTR" without specifying milestone scope, flag it. MTTR and milestone elapsed time are different metrics.

---

## Anti-Pattern 3: Hardcoding the Default Business Hours ID in BusinessHours.diff()

**What the LLM generates:**

```apex
// WRONG: hardcoded or always-default Business Hours ID
Id bhId = [SELECT Id FROM BusinessHours WHERE IsDefault = true LIMIT 1].Id;
Long mttr = BusinessHours.diff(bhId, c.CreatedDate, c.ClosedDate);
```

Always using the default Business Hours regardless of which Entitlement or Business Hours record is linked to the case.

**Why it happens:** LLMs default to the simplest query pattern (default BH) without considering that different entitlement tiers have different Business Hours. Training data frequently shows the default BH pattern as it is the most common example.

**Correct pattern:**

```apex
// CORRECT: use the Business Hours from the linked Entitlement
Case c = [SELECT Id, CreatedDate, ClosedDate, Entitlement.BusinessHoursId
          FROM Case WHERE Id = :caseId];
Id bhId = c.Entitlement?.BusinessHoursId
          ?? [SELECT Id FROM BusinessHours WHERE IsDefault = true LIMIT 1].Id;
Long mttrMillis = BusinessHours.diff(bhId, c.CreatedDate, c.ClosedDate);
```

**Detection hint:** Search generated Apex for `BusinessHours WHERE IsDefault = true` without a conditional fallback. If there is no check against `Entitlement.BusinessHoursId`, flag it.

---

## Anti-Pattern 4: Attempting to Update CaseMilestone.TargetDate via DML

**What the LLM generates:**

```apex
// WRONG: trying to extend a milestone deadline
CaseMilestone cm = [SELECT Id, TargetDate FROM CaseMilestone WHERE Id = :milestoneId];
cm.TargetDate = cm.TargetDate.addHours(4); // extend by 4 hours
update cm; // This will fail — TargetDate is read-only after creation
```

Or in Flow: updating `TargetDate` field on a `CaseMilestone` record update element.

**Why it happens:** `TargetDate` appears to be a standard DateTime field. LLMs generate update logic without knowing the Salesforce platform rule that `TargetDate` is immutable after milestone creation.

**Correct pattern:**

```
CaseMilestone.TargetDate is set by the Entitlement Process at creation and cannot
be changed via DML, Process Builder, Flow, or trigger after-insert.

Alternatives for deadline extensions:
  1. Manually complete the existing milestone (set IsCompleted=true via admin UI or API — note: also restricted).
  2. Design a separate "Extended Resolution" milestone type within the Entitlement Process.
  3. Document the exception outside Salesforce for audit purposes.

Do not attempt TargetDate DML updates.
```

**Detection hint:** Any Apex or Flow that sets `CaseMilestone.TargetDate` in an update context. Flag immediately — it will throw a runtime exception or silently fail depending on API version.

---

## Anti-Pattern 5: Using Case.ClosedDate in SOQL WHERE Clauses Without Null Handling

**What the LLM generates:**

```sql
-- WRONG: ClosedDate is null for open cases — this filter silently drops them
SELECT Id, CreatedDate, ClosedDate
FROM Case
WHERE ClosedDate >= LAST_N_DAYS:30
  AND EntitlementId != null
```

Or a formula: `ClosedDate - CreatedDate` used without `IF(IsClosed, ..., NULL)` guard.

**Why it happens:** LLMs treat `ClosedDate` like any other date field and assume it is always populated. They do not know that `ClosedDate` is null on open cases in Salesforce.

**Correct pattern:**

```sql
-- CORRECT: explicit IsClosed filter to scope to resolved cases
SELECT Id, CreatedDate, ClosedDate, MTTR_Calendar_Mins__c
FROM Case
WHERE IsClosed = true
  AND ClosedDate >= LAST_N_DAYS:30
  AND EntitlementId != null
```

For formula fields on Case:

```
-- CORRECT: guard against null ClosedDate
IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)
```

**Detection hint:** SOQL on `Case` filtering or selecting `ClosedDate` without an `IsClosed = true` filter. Formula fields computing `ClosedDate - CreatedDate` without an `IF(IsClosed, ...)` guard.

---

## Anti-Pattern 6: Confusing EntitlementId Presence With Active SLA Coverage

**What the LLM generates:** "If a case has an `EntitlementId` set, it has an active SLA and `CaseMilestone` records will be created."

Or a validation check: `IF(ISBLANK(EntitlementId), 'Missing SLA', 'SLA Active')` — treating non-null `EntitlementId` as proof of active SLA coverage.

**Why it happens:** LLMs infer that a populated lookup field means the related record is valid and active. They do not know that Salesforce requires the Entitlement to be Active and within its `StartDate`–`EndDate` range to trigger milestone creation.

**Correct pattern:**

```
EntitlementId populated ≠ active SLA coverage

For CaseMilestone records to be created:
  1. Entitlement.Status = 'Active'
  2. Case.CreatedDate is within Entitlement.StartDate AND Entitlement.EndDate
  3. A matching Entitlement Process is assigned to the Entitlement
  4. The Entitlement Process has active Milestones configured

Data quality check for gap detection:
SELECT CaseId, COUNT(Id) milestone_count
FROM CaseMilestone
WHERE CaseId IN (SELECT Id FROM Case WHERE EntitlementId != null AND CreatedDate = THIS_MONTH)
GROUP BY CaseId
HAVING COUNT(Id) = 0
-- Returns cases with EntitlementId but zero milestones — potential SLA coverage gaps
```

**Detection hint:** Any assertion that `EntitlementId != null` guarantees SLA milestone creation. Flag and add entitlement status and date range validation.
