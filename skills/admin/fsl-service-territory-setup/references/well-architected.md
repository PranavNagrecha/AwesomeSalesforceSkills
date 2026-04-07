# Well-Architected Notes — FSL Service Territory Setup

## Relevant Pillars

### Operational Excellence

Territory configuration is the foundation of all scheduling operations in Field Service. Poorly designed territories — missing operating hours, incorrect member types, or wrong hierarchy — cause silent scheduling failures that are difficult to diagnose. Operational Excellence demands that every territory be auditable: all operating hours linked, all members carrying correct MemberType values, and limits tracked proactively rather than discovered at production scale.

Applying this pillar means establishing a repeatable setup checklist (the Review Checklist in SKILL.md), documenting territory design decisions (e.g., why a region uses Relocation vs. Secondary memberships), and validating configuration before go-live using the checker script.

### Reliability

The 50-resource-per-territory and 1,000-service-appointment-per-day-per-territory limits are hard boundaries. Exceeding them does not fail gracefully — scheduling throughput degrades without a clear error. Reliability requires territory granularity to be designed with headroom, not at the limit.

Relocation membership reliability depends entirely on date accuracy. A Relocation membership without dates silently excludes a resource from scheduling. Building date validation into any data integration that touches ServiceTerritoryMember is a reliability requirement.

### Performance

Scheduling optimizer performance is directly affected by territory member roster size and the complexity of the territory hierarchy. Territories with large Secondary member lists that do not satisfy the active work rules still incur matching overhead. Keeping member counts well within the 50-resource limit and pruning stale memberships (via `EffectiveEndDate`) maintains optimizer performance.

### Scalability

Territory hierarchy using `ParentTerritoryId` supports growth by allowing new local zones to be added under an existing regional parent without restructuring the entire setup. Operating hours designed for reuse across territories reduce maintenance as the territory portfolio grows.

### Security

ServiceTerritory records control which technicians are eligible for which appointments. Misconfigured territory access — for example, a technician with a Primary membership in a territory they should not service — creates a security and compliance risk in regulated industries (utilities, healthcare field service). Profile and permission set access to ServiceTerritory and ServiceTerritoryMember should be reviewed to ensure only authorized roles can modify membership records.

---

## Architectural Tradeoffs

**Territory granularity vs. optimizer performance:** Smaller territories with fewer members per territory improve dispatcher readability and enforce geographic boundaries cleanly. However, very fine-grained territories increase the number of territory records to maintain and may require technicians to have multiple Secondary memberships, complicating the data model. Design territories at the natural dispatch zone level, not at the individual zip code level.

**Shared vs. per-territory operating hours:** Sharing a single `OperatingHours` record across multiple territories reduces maintenance overhead. The tradeoff is that a change to the shared record affects all linked territories simultaneously. For territories with highly standardized schedules (same time zone, same hours), sharing is appropriate. For territories with unique holiday schedules or shift patterns, dedicated OperatingHours records provide safer isolation.

**Relocation vs. Secondary for temporary coverage:** Relocation memberships suppress cross-boundary travel calculations and satisfy Hard Boundary work rules, making them the correct tool for temporary geographic assignments. The tradeoff is that they require explicit end dates, which creates an operational burden to track and expire. Secondary memberships are lower maintenance but do not satisfy Hard Boundary and do not suppress travel calculations.

---

## Anti-Patterns

1. **Flat territory model without hierarchy** — Creating all territories at a single level with no `ParentTerritoryId` relationships limits reporting to individual territory granularity. Regional or national rollup reporting requires post-processing workarounds. Use `ParentTerritoryId` from the start to support hierarchy-aware reporting.

2. **Unbounded Secondary membership growth** — Adding Secondary memberships liberally without auditing or expiring them causes territory member rosters to approach the 50-resource limit with members who are no longer relevant. Set `EffectiveEndDate` on any membership that should be time-bounded, even Secondary ones.

3. **Single OperatingHours record spanning time zones** — Reusing a single OperatingHours record across territories in different time zones causes all those territories to use the same time zone for scheduling windows. Appointments near the boundary are booked at incorrect local times. Create separate OperatingHours records per time zone.

---

## Official Sources Used

- Guidelines for Creating Service Territories — https://help.salesforce.com/s/articleView?id=sf.fs_service_territories.htm
- Set Up Service Territories Operating Hours and Shifts — https://help.salesforce.com/s/articleView?id=sf.fs_create_operating_hours.htm
- ServiceTerritory Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_serviceterritory.htm
- ServiceTerritoryMember Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_serviceterritorymember.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Field Service Core Data Model — https://architect.salesforce.com/decision-guides/field-service
