# Well-Architected Notes — FSL Shifts and Crew

## Relevant Pillars

- **Operational Excellence** — Shift configuration directly affects dispatcher productivity and scheduling throughput. Poorly structured ShiftPatterns or incorrect Shift statuses cause recurring "missing candidates" support tickets. Bulk generation via ShiftPattern reduces manual maintenance overhead and ensures consistency at scale.
- **Reliability** — Shift records that fall outside Operating Hours or remain in Tentative status silently degrade scheduling reliability without throwing errors. Reliable FSL deployments establish automated checks (SOQL monitors, validation rules) to catch silent exclusion conditions before they affect dispatching.
- **Scalability** — ShiftPattern + ShiftPatternEntry is the scalable approach for organizations with 10+ resources or multi-week rotating schedules. Manually-created Shift records do not scale past ~50 resources without significant operational overhead. Crew models (Static and Shell/Dynamic) scale appointment routing by treating the crew as a single schedulable unit rather than managing individual technician assignments.
- **Security** — Shift records inherit FSL sharing rules. In orgs with territory-based sharing, Shift visibility may be restricted to dispatchers assigned to the relevant territory. Incorrect sharing or profile configuration can cause dispatchers to see empty candidate results for Shifts that exist but are not shared to their data access scope.
- **Performance** — The scheduling engine evaluates up to 20 candidates per search. Shift-based availability filtering runs before work-rule evaluation, so well-scoped Shift windows (matching actual working patterns) reduce the candidate pool early and improve scheduler response time.

## Architectural Tradeoffs

**ShiftTemplate vs. ShiftPattern:** ShiftTemplate is a lightweight option for small teams or ad-hoc shift creation. ShiftPattern is required for automation and scale. The tradeoff is setup time (ShiftPattern requires more upfront configuration) against ongoing maintenance burden (ShiftTemplate requires manual shift creation per resource per day). Organizations with more than 10 resources or recurring schedules should default to ShiftPattern.

**Static Crew vs. Shell/Dynamic Crew:** Static crews provide stronger scheduling accuracy because the scheduler knows the exact composition and skills available. Shell crews provide operational flexibility for variable job types but require dispatchers to manually assign members post-dispatch. The tradeoff is scheduling precision (Static) vs. workforce flexibility (Shell). Organizations with fixed specialized teams should use Static. Organizations with pooled labor should use Shell.

**Crew Scheduling vs. Individual Scheduling:** Scheduling service appointments to Crew ServiceResources simplifies the Dispatcher Console view and centralizes crew capacity management. The tradeoff is that individual technician-level time tracking is not directly visible on appointment records — crew members see work via the FSL mobile app and ServiceCrewMember relationships, not through individual appointment dispatch records.

## Anti-Patterns

1. **Manual Shift Creation for Large Workforces** — Creating individual Shift records for every resource, every day, without ShiftPattern is unsustainable past ~20 resources. The resulting shift data is inconsistent (different admins create different window boundaries), hard to bulk-update, and creates Shift record bloat that degrades Dispatcher Console performance. Use ShiftPattern for any workforce requiring consistent repeating schedules.

2. **Mixing Crew and Individual Dispatch for the Same Team** — Dispatching some appointments to a Crew ServiceResource and other appointments to individual member Technician records for the same physical team creates double-booking blind spots. The Dispatcher Console shows separate Gantt rows for the crew and each member, and the scheduling engine cannot detect conflicts across the two routing paths. Choose one routing model per team and enforce it consistently.

3. **Relying on Shift Status Defaults Without Verification** — Assuming all bulk-generated Shifts default to Confirmed and skipping post-generation verification. Silent Tentative Shifts cause "no candidates" errors that are hard to diagnose without SOQL inspection. Operational excellence requires an automated check (SOQL query, Flow alert, or monitoring dashboard) to detect Tentative Shifts before the scheduling window opens.

## Official Sources Used

- Set Up Shifts for Field Service — https://help.salesforce.com/s/articleView?id=sf.fs_shifts_setup.htm
- Simplify Shift Creation with Templates and Patterns (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-shifts/simplify-shift-creation
- Understanding Shift Scheduling (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-shifts
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
