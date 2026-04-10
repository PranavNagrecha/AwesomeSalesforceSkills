# Well-Architected Notes — FSL Optimization Architecture

## Relevant Pillars

- **Reliability** — FSL Global optimization has a 2-hour hard timeout with silent cancellation. Optimization failures are not exception-raised — they must be monitored via FSL optimization job records. Design for graceful degradation: optimization failure should fall back to manual dispatch, not block operations.
- **Performance** — Territory size directly determines optimization job duration. The recommended 50 resource / 1,000 SA/day limit per territory is a performance design constraint, not just a guideline. Architecture decisions about territory design are performance architecture decisions.
- **Scalability** — As organizations grow, territory resource counts and SA volumes increase. Build territory design with headroom below the optimization limits so that growth doesn't immediately require redesign. A territory at 40 resources today can absorb organic growth without hitting the 50-resource limit for 12–18 months.

## Architectural Tradeoffs

**Large territories vs. sub-territories:** Large territories simplify configuration but risk optimization timeouts. Sub-territories require more configuration (more OperatingHours records, more STM assignments, staggered optimization schedules) but scale reliably. The correct choice is sub-territories sized for optimization performance.

**ESO vs. legacy engine:** ESO provides better throughput and work chain support but has no automatic fallback and requires per-territory adoption. For orgs with critical operations, the "no fallback" risk must be mitigated with manual dispatch contingencies, not delayed by avoiding ESO adoption.

**Global vs. In-Day optimization:** Global optimization builds the next day's schedule in advance. In-Day optimization handles real-time disruptions. Both are typically needed in operations with any meaningful disruption rate (>5% same-day changes). Using only Global optimization in a high-disruption environment leaves dispatchers manually rescheduling all same-day changes.

## Anti-Patterns

1. **Designing territories above 50 resources for administrative convenience** — Large territories are administratively simpler but cause consistent Global optimization timeouts. Territory size is a performance constraint.
2. **All-at-once ESO adoption across all territories** — ESO has no automatic fallback. All-at-once adoption means any ESO issue affects all territories. Phased adoption limits blast radius.
3. **No monitoring on optimization job completion** — Silent cancellation from timeout means dispatchers don't know optimization failed until the next morning when the schedule is incomplete. Build monitoring.

## Official Sources Used

- How Does the FSL Optimization Engine Work (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_optimization_how.htm
- Enhanced Scheduling and Optimization (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_enhanced_scheduling.htm
- Limits for Enhanced Scheduling (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_enhanced_scheduling_limits.htm
- Global Optimization (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-scheduling-foundations/global-optimization
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
