# Well-Architected Notes — FSL Scheduling Policies

## Relevant Pillars

- **Operational Excellence** — Scheduling policies are the primary operational control surface for field service dispatch. A well-designed policy reduces manual dispatcher overrides, shrinks appointment queue backlogs, and makes scheduling behavior auditable and repeatable. Using descriptively named custom policies instead of modified defaults is a core operational hygiene practice.

- **Reliability** — The mandatory Service Resource Availability work rule is a reliability gate. Without it, the scheduler silently produces invalid assignments. Policies that enforce this rule ensure that the scheduling output is dependably grounded in actual resource availability, preventing appointment failures due to absent or off-hours technicians.

- **Performance** — Service objective weight calibration directly impacts scheduling throughput. An over-constrained policy (too many work rules with narrow tolerances) reduces the candidate pool and increases time-to-schedule. An under-weighted Minimize Travel objective inflates fleet costs. Tuning policies is a performance optimization activity.

- **Security** — Scheduling policies themselves do not carry field-level or record-level access controls, but the resources and territories they expose to the dispatcher do. Ensure that object-level permissions for FSL__Scheduling_Policy__c, FSL__Work_Rule__c, and FSL__Service_Objective__c are restricted to administrators and not editable by dispatcher profiles.

- **Scalability** — As territory count and appointment volume grow, policy complexity must remain manageable. Use a small number of named policies (typically 3–6) that cover distinct scheduling scenarios rather than creating per-territory policies. Proliferating policies creates maintenance overhead and makes behavior unpredictable at scale.

## Architectural Tradeoffs

**Work rule strictness vs. scheduling fill rate:** Adding more work rules — especially strict ones like Hard Boundary and Match Required Skills — produces higher-quality candidate matches but reduces the available slot count. In high-volume environments, an overly strict policy can leave a significant percentage of appointments unscheduled because no candidate passes all filters. The tradeoff requires periodic monitoring of the unscheduled appointment rate against the violation rate.

**Single policy vs. per-scenario policies:** Using one policy for all appointment types is simple to maintain but forces compromise on objective weights. Separate policies for routine, urgent, and emergency appointments allow each to be optimized for its use case, at the cost of routing logic (which policy gets applied when) living in automation outside the policy itself.

**Default policies as baseline vs. custom from scratch:** Starting from a cloned default reduces configuration time and inherits tested rule combinations, but inherits assumptions that may not match the org's needs. Building from scratch is slower but produces a policy where every rule is intentional.

## Anti-Patterns

1. **Using the Emergency default policy for all appointment types** — Emergency policy has minimal work rule filtering and ASAP-weighted objectives. Applying it to routine scheduling bypasses skill and territory matching, dispatches over-qualified technicians to low-priority work, and inflates costs. Use Emergency policy only for appointments with SLA-bound urgent response requirements.

2. **Creating a policy with no Service Resource Availability rule** — This anti-pattern causes the scheduler to treat the entire calendar as available for every resource, producing invalid assignments at scale. It is the most common misconfiguration in new FSL implementations and is detected by the check script in this skill.

3. **Proliferating per-territory custom policies** — Creating a unique scheduling policy for every service territory results in dozens or hundreds of policy records that are nearly identical but diverge over time as different administrators make uncoordinated changes. Consolidate to a small set of role-based or priority-based policies assigned to territories by category, not individually.

## Official Sources Used

- Create and Manage Field Service Scheduling Policies — https://help.salesforce.com/s/articleView?id=sf.fs_scheduling_policies.htm
- Field Service Work Rules — https://help.salesforce.com/s/articleView?id=sf.fs_work_rules.htm
- Field Service Objectives — https://help.salesforce.com/s/articleView?id=sf.fs_objectives.htm
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
