# Well-Architected Notes — FSL Resource Management

## Relevant Pillars

- **Operational Excellence** — Resource configuration quality directly determines dispatch efficiency. Expired skill records, missing capacity records, and misconfigured preferences silently degrade scheduling outcomes without triggering alerts. Operational Excellence requires proactive monitoring of ServiceResourceSkill expiry dates and ServiceResourceCapacity coverage.

- **Reliability** — The FSL scheduler depends on ServiceResource, ServiceResourceSkill, and ResourcePreference data being consistent and current. Stale or conflicting data (expired skills, Required preferences pointing to under-skilled resources) produces silent failures — zero candidates returned, no error raised. Reliability in this domain means closing the gap between configuration state and actual resource readiness.

- **Security** — ServiceResource records linked to User records via RelatedRecordId inherit the running user's profile and permission set access for FSL mobile app authentication. Over-permissioned technician profiles may allow mobile app access to work orders outside their territory. Field-level security on SkillLevel must be restricted so technicians cannot self-modify their proficiency values.

- **Performance** — The 20-candidate-per-scheduling-search limit means that in dense territories, only a subset of resources are evaluated. Resource and skill data quality directly affects which 20 are surfaced. Dirty data (duplicate skill records, orphaned preferences) increases scheduling query cost without improving results.

- **Scalability** — The 50-resources-per-territory limit and the 20-candidate search limit set hard ceilings on territory roster size. Skill management must account for growth: a flat SkillLevel scheme (all resources at level 99) loses the ranking signal needed to surface the right 20 candidates in large orgs.

## Architectural Tradeoffs

**Certification-expiry enforcement via EndDate vs. manual deactivation:** Using `ServiceResourceSkill.EndDate` for certification expiry is data-driven and requires no dispatcher action, but expired records are silent — the scheduler drops the resource without any notification. Manual deactivation (`IsActive = false`) on the resource is visible and controlled, but is an all-or-nothing approach that removes the resource from all scheduling, not just the expired skill's work types. The EndDate approach is preferred for skill-level expiry; combine it with monitoring queries and renewal workflows to close the notification gap.

**Required vs. Preferred ResourcePreference:** `Required` preferences provide the strongest customer-resource guarantee but create a single point of failure — if the required resource is unavailable, the scheduler returns zero candidates and a human dispatcher must intervene. `Preferred` preferences provide a softer preference with fallback to other candidates. Use `Required` only where there is a genuine contractual obligation; use `Preferred` for relationship-based preferences where fallback is acceptable.

**Capacity-based vs. shift-based resources for shared assets:** Capacity-based resources model shared or pool-type assets correctly but require ongoing `ServiceResourceCapacity` record maintenance for future periods. Shift-based resources are simpler to set up but cannot model partial-use or multi-booking scenarios. Choose based on whether the asset is truly dedicated per time slot or shared across appointments.

## Anti-Patterns

1. **Ignoring ServiceResourceSkill EndDate until scheduling breaks** — Treating certification expiry as a manual dispatcher problem rather than a data-driven scheduler constraint. When EndDate passes, the resource silently drops from scheduling with no error. The correct approach is automated expiry monitoring with renewal workflows that extend EndDate before the expiry date.

2. **Setting all SkillLevel values to 99** — Inflating all resource skill levels to the maximum removes the differentiation the scheduler uses to rank the 20 candidate resources returned in a scheduling search. In large territories, this means the 20 candidates surfaced are essentially random rather than the best-matched. Maintain meaningful SkillLevel gradations (e.g., 50 for entry, 75 for journeyman, 99 for master) so scheduling uses the ranking signal effectively.

3. **Creating Required ResourcePreferences without a skill coverage audit** — Setting `PreferenceType = Required` against a resource without verifying all required skills are active creates a scheduling deadlock that surfaces as a confusing "no available resources" error. Always cross-check Required preferences against active ServiceResourceSkill records when creating or renewing preferences.

## Official Sources Used

- Guidelines for Creating Service Resources — https://help.salesforce.com/s/articleView?id=sf.fs_service_resources.htm
- Define Capacity-Based Resources — https://help.salesforce.com/s/articleView?id=sf.fs_capacity_based_resources.htm
- ServiceResourceSkill Field Reference (Field Service Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_class_ServiceResourceSkill.htm
- Field Service Limits — https://help.salesforce.com/s/articleView?id=sf.fs_limits.htm
- ResourcePreference Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_resourcepreference.htm
- ServiceResourceCapacity Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_serviceresourcecapacity.htm
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
