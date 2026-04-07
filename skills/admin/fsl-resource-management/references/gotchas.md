# Gotchas — FSL Resource Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Expired ServiceResourceSkill Records Silently Block Scheduling

**What happens:** When a `ServiceResourceSkill` record has an `EndDate` value that is in the past, the FSL scheduler treats the resource as if it does not have that skill at all. The resource is excluded from scheduling candidates without any error message, warning in the Dispatcher Console, or entry in optimization logs. From the dispatcher's perspective, the resource simply does not show up for jobs requiring that skill.

**When it occurs:** Any time a skill certification expires — including records created with a specific EndDate as a legitimate expiry mechanism — and the record is not renewed or removed. It is especially common after annual certification cycles when many records expire simultaneously.

**How to avoid:** Run a recurring query to surface expiring and expired skill records before they silently affect scheduling:
```soql
SELECT Id, ServiceResource.Name, Skill.MasterLabel, EndDate
FROM ServiceResourceSkill
WHERE EndDate <= NEXT_N_DAYS:30
ORDER BY EndDate ASC
```
Establish a process to either extend the EndDate (if the certification is renewed) or deactivate the resource (if the certification lapsed). Do not delete expired records — retain them for audit history and create new records when certifications are renewed.

---

## Gotcha 2: Capacity-Based Resources with Date Gaps Are Unschedulable Without Error

**What happens:** A capacity-based resource (`IsCapacityBased = true`) with no active `ServiceResourceCapacity` record covering the current date returns as having zero available capacity. The scheduler excludes it from all appointment candidates during that gap period. No error is shown — the resource appears "unavailable" as if it were fully booked.

**When it occurs:** Most commonly at month or quarter boundaries when ServiceResourceCapacity records are created for fixed periods and the next period's records have not yet been created. Also occurs when a new capacity-based resource is created but its capacity records are forgotten.

**How to avoid:** When creating or managing capacity-based resources, always create `ServiceResourceCapacity` records that extend into the future beyond the current scheduling horizon (typically 30–90 days ahead, depending on how far out appointments are booked). Consider creating a monitoring query or scheduled job:
```soql
SELECT Id, Name
FROM ServiceResource
WHERE IsCapacityBased = true
  AND IsActive = true
  AND Id NOT IN (
    SELECT ServiceResourceId FROM ServiceResourceCapacity
    WHERE StartDate <= TODAY AND EndDate >= TODAY
  )
```
Any records returned by this query are capacity resources with a current-day gap — they cannot be scheduled.

---

## Gotcha 3: Required ResourcePreference Plus Expired Skill Equals Zero Candidates, No Explanation

**What happens:** When a `ResourcePreference` with `PreferenceType = Required` is set for an account, the scheduler will only return that specific resource as a candidate. If the required resource's relevant `ServiceResourceSkill` record is expired or missing, the scheduler returns zero candidates for appointments on that account. The dispatcher sees "no available resources" with no indication that the root cause is the preference-plus-expired-skill combination.

**When it occurs:** Most frequently after certification renewal cycles when `Required` resources have their skill records expire. It is invisible because the two problems (ResourcePreference and ServiceResourceSkill expiry) are in separate objects with no cross-object validation.

**How to avoid:** After renewing any skill records, cross-check whether the affected resource appears in any `Required` ResourcePreference records. Add this to the certification renewal checklist:
```soql
SELECT rp.RelatedRecord.Name, rp.ServiceResource.Name, rp.PreferenceType
FROM ResourcePreference rp
WHERE rp.ServiceResourceId IN (
  SELECT ServiceResourceId FROM ServiceResourceSkill WHERE EndDate < TODAY
)
AND rp.PreferenceType = 'Required'
```
This surfaces all Required preferences where the required resource has at least one expired skill.

---

## Gotcha 4: The 20-Candidate Scheduling Search Limit Hides Over-Qualified Resources

**What happens:** The FSL scheduling engine returns a maximum of 20 candidate resources per scheduling search. In large territories with many qualified technicians, only 20 are evaluated. Resources beyond the 20-candidate cutoff are never considered for the appointment, even if they are available, closer, or better matched.

**When it occurs:** In territories approaching or exceeding 50 active ServiceTerritoryMember records. The limit interacts with sorting logic — resources are evaluated in an internal order influenced by travel distance estimates, skill level, and prior assignment patterns. Resources consistently outside the top 20 will never appear in results regardless of their qualifications.

**How to avoid:** Keep territory rosters lean. If a territory consistently has more than 20 well-qualified resources, consider splitting the territory into smaller zones. Use the `SkillLevel` field intentionally — higher-skilled resources are prioritized in candidate selection, so inflating all SkillLevel values to the maximum removes a useful ranking signal.

---

## Gotcha 5: ResourceType Cannot Be Changed After Record Creation

**What happens:** The `ResourceType` field on `ServiceResource` is set at record creation and cannot be modified afterward. A resource created as `Technician` cannot be converted to `Crew`, and vice versa. There is no platform error if you attempt a field update via the API — the update silently fails and the field retains its original value.

**When it occurs:** When a data migration or bulk load creates resources with the wrong type, or when business requirements change (e.g., a solo contractor becomes part of a permanent crew). The silent failure in API updates makes this particularly hard to diagnose.

**How to avoid:** Verify `ResourceType` values during bulk loads before inserting. If the wrong type was set, the only fix is to deactivate the incorrectly-typed record, create a new `ServiceResource` with the correct type, and re-link all related records (ServiceTerritoryMember, ServiceResourceSkill, ResourcePreference) to the new resource Id.
