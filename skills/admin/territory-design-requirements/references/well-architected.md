# Well-Architected Notes — Territory Design Requirements

## Relevant Pillars

- **Scalability** — Territory design is the most significant scalability decision in ETM. Hierarchy depth, territory count, assignment rule complexity, and user-to-territory ratio all determine whether the territory model degrades as the org and team grow. Poor territory design becomes increasingly expensive to change after go-live because reassignments trigger full recalculation cycles.

- **Operational Excellence** — A well-designed territory model is one that sales operations can maintain without developer involvement. Requirements must produce criteria that are stable, auditable, and tied to data fields that are reliably populated on account records. Models with brittle or high-volume rule sets accumulate operational debt quickly.

- **Security** — Territory membership is additive access. Territory design cannot be used to restrict access below the org-wide default. Requirements must confirm that OWD and sharing rules are the correct mechanism for any access restriction intent, and that territory design works within (not against) the sharing architecture.

- **Performance** — Assignment rule execution time scales with rule complexity and account volume. Requirements that call for more than 10 filter criteria per territory, or for rule criteria on text-pattern-match conditions, create performance risk. Design choices made in requirements gathering directly affect background job duration when the model activates or realigns.

- **Reliability** — Territory realignment (adding territories, changing criteria, expanding coverage) requires manual rule reruns to backfill existing accounts. Requirements must include operational runbooks for how realignment events will be managed without data gaps in coverage or forecasting.

## Architectural Tradeoffs

**Hierarchy depth vs. forecast granularity:** Deeper hierarchies provide more forecast rollup granularity but increase administrative complexity. A 6-level hierarchy can produce detailed regional breakdowns but makes it difficult for mid-level managers to understand which nodes are under their coverage. Balance depth against the actual number of distinct forecast consumers in the organization.

**Rule-based vs. manual assignment:** Rule-based assignment scales well for geographic segmentation where criteria are stable. Named account and strategic account lists change frequently — manual assignment (or a hybrid of rules plus manual override) is more reliable for lists that change quarterly. Choosing the wrong mechanism for a coverage type creates ongoing maintenance overhead or data quality risk.

**Geographic contiguity vs. operational convenience:** Geographically non-contiguous territories are technically supported but introduce confusion for reps and make visual territory maps misleading. Where the business genuinely requires non-contiguous coverage (e.g., a rep covering both coasts for a specific vertical), document the rationale explicitly so it is intentional rather than accidental.

**Single active model vs. transition planning:** Only one territory model can be Active at a time. Major territory redesigns (mid-year realignments, corporate reorganizations) require building the new model in Planning state alongside the active model, then coordinating a cutover. Requirements should identify whether a realignment process is needed and what the transition plan looks like before the first model is activated.

## Anti-Patterns

1. **Mirroring the role hierarchy in territory structure** — Designing territories to exactly match the role hierarchy (one territory per role node, named after the person in that role) is a common first-pass design that creates fragility. When roles change, territory structure must change. Territory names reference people instead of coverage areas, making them meaningless after reassignment. Territory hierarchy should represent stable coverage geography or account segmentation, not the people who happen to hold those roles today.

2. **Using ETM access to enforce account restriction instead of OWD** — Requirements occasionally specify that reps should only see their assigned accounts and nothing else, then attempt to achieve this by configuring ETM with Account OWD remaining Public Read/Write. This does not work — ETM access is additive. If account restriction is a genuine requirement, it belongs in the sharing model (OWD set to Private, sharing rules for controlled exceptions), and territory design must be evaluated in that context.

3. **Over-segmenting territories relative to team size** — Building 200 territories for a 30-person sales team produces a sub-1:1 user-to-territory ratio, high assignment rule maintenance overhead, and fragmented forecast visibility. Territory count should be calibrated against actual team size with a target of approximately 3:1. Over-segmentation often reflects aspirational future-state planning — if the current team is 30 people, design for the current state and plan expansion.

## Official Sources Used

- Salesforce Sales Territories Implementation Guide (Spring '26) — https://help.salesforce.com/s/articleView?id=sf.tm2_overview.htm
- Salesforce Help: Allocations and Considerations for Territories — https://help.salesforce.com/s/articleView?id=sf.tm2_allocations_limits.htm
- Salesforce Help: Territory Hierarchy — https://help.salesforce.com/s/articleView?id=sf.tm2_territory_hierarchy.htm
- Salesforce Help: Setting Up and Managing Territory Assignments — https://help.salesforce.com/s/articleView?id=sf.tm2_managing_territory_assignments.htm
- Object Reference (AccountTerritoryAssignmentRule) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_accountterritoryassignmentrule.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Record Access Under the Hood (local knowledge) — knowledge/imports/
