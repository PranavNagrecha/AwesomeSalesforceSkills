# LLM Anti-Patterns — FSL Capacity Planning

Common mistakes AI coding assistants make when generating or advising on FSL Capacity Planning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating ServiceResourceCapacity Records Without Verifying IsCapacityBased

**What the LLM generates:** DML or Data Loader instructions that insert `ServiceResourceCapacity` records for a list of resources, often omitting any check that `ServiceResource.IsCapacityBased = true`.

**Why it happens:** LLMs learn from documentation and code samples that describe the object's fields without always including the prerequisite flag check. The object insert succeeds without error whether or not the flag is set, so there is no runtime signal that the records are inert.

**Correct pattern:**

```soql
-- Always verify before inserting capacity records
SELECT Id, Name, IsCapacityBased
FROM ServiceResource
WHERE IsCapacityBased = false
  AND Id IN :resourceIdSet
-- If any rows return, update IsCapacityBased = true BEFORE inserting capacity records
```

**Detection hint:** Any generated DML targeting `ServiceResourceCapacity` that does not include a prior check or assertion on `ServiceResource.IsCapacityBased` is suspect. Look for missing prerequisite validation before the insert.

---

## Anti-Pattern 2: Conflating ServiceResourceCapacity with WorkCapacityLimit

**What the LLM generates:** Advice that treats `ServiceResourceCapacity` and `WorkCapacityLimit` as interchangeable mechanisms for the same purpose — e.g., "to limit appointments per territory, create a `ServiceResourceCapacity` record for each resource in that territory."

**Why it happens:** Both objects relate to capacity and scheduling constraints. LLMs trained on general Salesforce documentation often blur the distinction because both appear in the same conceptual section of FSL docs. The scoping difference (resource-level vs. territory-level) is not always made explicit in training text.

**Correct pattern:**

```
- ServiceResourceCapacity: controls capacity for ONE resource (IsCapacityBased = true required)
  Use for: shared assets, pooled equipment, contractors billed per appointment
- WorkCapacityLimit: controls how many appointments a TERRITORY accepts per work type per window
  Use for: demand-side throttling, parts supply limits, territory throughput management
Both mechanisms are independent and can be active simultaneously.
```

**Detection hint:** If generated advice recommends `ServiceResourceCapacity` for territory-level or aggregate throughput control, or recommends `WorkCapacityLimit` for individual resource caps, the mechanisms have been conflated.

---

## Anti-Pattern 3: Assuming a Standard Report Type Exists for Capacity vs. Utilization

**What the LLM generates:** Instructions like "navigate to Reports > FSL Capacity Utilization" or "use the standard Field Service Capacity report type to compare ServiceResourceCapacity against actual appointment hours."

**Why it happens:** LLMs trained on CRM or scheduling system documentation often assume standard reporting dashboards exist for common operational needs. In FSL, the absence of a native capacity vs. utilization report type is a documented gap that generic training data does not capture.

**Correct pattern:**

```
There is no standard FSL report type that aggregates ServiceResourceCapacity.Capacity
against ServiceAppointment durations. To build a capacity utilization report:
1. Create a custom report type: ServiceResource (primary) -> ServiceAppointment (related)
2. Add formula fields to approximate utilization against capacity records (queried separately)
OR
3. Use CRM Analytics with a dataset recipe joining ServiceResourceCapacity and ServiceAppointment
```

**Detection hint:** Any generated step referring to a "standard FSL capacity report," "built-in utilization dashboard," or navigation path that implies a native capacity vs. actuals report should be flagged as unverified.

---

## Anti-Pattern 4: Recommending Resource Deactivation to Reduce Scheduling Volume

**What the LLM generates:** Advice to set `ServiceResource.IsActive = false` on lower-priority technicians during peak or holiday periods to reduce the candidate pool and prevent overbooking.

**Why it happens:** LLMs draw on general workforce management patterns where "deactivating" a worker is equivalent to making them unavailable. In FSL, deactivation is a permanent availability control that removes the resource from all scheduling and disrupts existing appointments — not a capacity reduction tool.

**Correct pattern:**

```
To reduce scheduling volume for a period:
- Territory level: Create a WorkCapacityLimit record with a lower CapacityLimit for the date range
- Resource level: Create a ServiceResourceCapacity record with reduced Capacity for the date range
Do NOT set IsActive = false — this removes the resource from all scheduling,
disrupts existing appointments, and requires re-verification of all assignments on reactivation.
```

**Detection hint:** Any generated instruction to modify `ServiceResource.IsActive` in response to a capacity or throughput management request (rather than a genuine resource departure or decommission) should be flagged.

---

## Anti-Pattern 5: Omitting Date Continuity Validation After Capacity Record Updates

**What the LLM generates:** DML or Data Loader instructions that split or update `ServiceResourceCapacity` records for a seasonal adjustment without including a subsequent validation step to confirm no date gaps were introduced.

**Why it happens:** LLMs optimize for completing the stated task (insert the holiday-period records) and often omit operational validation steps that are not explicit in the user's request. The consequences of date gaps are also non-obvious — there is no runtime error, only silent scheduling failures.

**Correct pattern:**

```soql
-- After any capacity record insert or update, always run this adjacency check:
SELECT ServiceResourceId, StartDate, EndDate
FROM ServiceResourceCapacity
WHERE ServiceResource.IsCapacityBased = true
  AND ServiceResourceId IN :updatedResourceIds
ORDER BY ServiceResourceId, StartDate

-- Review manually or in Apex: for each resource, confirm that each record's
-- StartDate = (previous record's EndDate + 1 day). Any gap = unschedulable day.
```

**Detection hint:** Any generated capacity record update workflow that does not include a post-update validation query or adjacency check is incomplete. Look for the absence of a `ORDER BY ServiceResourceId, StartDate` query following any insert or update DML.
