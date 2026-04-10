# Well-Architected Notes — FSL Territory Data Setup

## Relevant Pillars

- **Reliability** — Territory hierarchy must be loaded in strict parent-before-child order. Skipping this causes cascading load failures that require re-sorting and re-running the entire territory load.
- **Performance** — Territory size (resource count and daily SA volume) directly impacts FSL optimization job duration. Designing territories over 50 resources or 1,000 SAs/day creates systemic optimization timeouts. Territory design decisions made during data setup affect long-term operational performance.
- **Scalability** — Operating Hours records are shared across territories. Design Operating Hours templates (e.g., one record per timezone + schedule pattern) rather than one OperatingHours record per territory to reduce data volume and configuration overhead.

## Architectural Tradeoffs

**Single large territory vs. multiple smaller territories:** A single large territory is simpler to manage but degrades optimization performance beyond 50 resources. Multiple smaller territories require more configuration but run faster optimizations. For most FSL implementations, geographic sub-territories aligned to optimization size limits is the correct design.

**Timezone-aligned territories vs. customer-convenient boundaries:** Territory boundaries are often drawn along political or operational lines (county, zip code, sales region) that may cross timezone boundaries. FSL appointment booking derives available slots from territory OperatingHours timezone — territory boundaries that cross timezones produce incorrect slot times for customers at the boundary. Timezone-aligned territories are architecturally required for correct booking behavior.

## Anti-Patterns

1. **Combining all resources in a region into one large territory** — Territories over 50 resources consistently time out during FSL Global optimization. Design for optimization scope, not administrative convenience.
2. **Loading ServiceTerritoryMember records without EffectiveStartDate** — This throws a required field error on every record and fails the entire batch.
3. **Polygon boundaries spanning timezone lines** — Creates incorrect appointment windows for customers near the boundary without any error message.

## Official Sources Used

- Set Up Service Territories Operating Hours and Shifts (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_service_territories.htm
- Import Service Territory Polygons in KML (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_polygon_import.htm
- PolygonUtils Class (Field Service Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/apex_namespace_FSL_PolygonUtils.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
