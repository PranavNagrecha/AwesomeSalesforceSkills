# Well-Architected Notes — FSL Multi-Region Architecture

## Relevant Pillars

- **Reliability** — Concurrent optimization for territories with shared resources produces conflicting assignments without any error or alert. Serializing optimization jobs eliminates this reliability risk.
- **Performance** — Territory size limits apply per-region. A multi-region deployment with one oversized territory per region still hits the optimization timeout in that region. Each territory must be independently within the 50 resource / 1,000 SA/day limit.
- **Scalability** — Multi-region designs should include headroom in territory sizing to accommodate organic growth in each region independently. A territory at 45 resources in Region A and 48 in Region B will both breach the 50-resource limit within 1–2 hiring cycles.

## Architectural Tradeoffs

**Single-org vs. multi-org for international deployments:** Multi-region FSL can be implemented in a single org (one set of territories per timezone/country) or across multiple orgs. Single-org is simpler for shared customer data and reporting but requires careful timezone, language, and compliance configuration. Multi-org isolates regional data but adds integration overhead. This skill covers single-org multi-region; multi-org strategy is covered separately.

**Territory granularity for optimization vs. administrative simplicity:** Finer territories (aligned to optimization limits and timezone boundaries) produce better optimization results but require more configuration effort. Coarser territories are easier to manage but risk optimization timeouts and timezone boundary problems. The optimization performance requirement overrides administrative convenience.

## Anti-Patterns

1. **Single OperatingHours record for all territories across multiple timezones** — All territories show slots in the OperatingHours record's timezone regardless of customer location. Each timezone must have its own OperatingHours record.
2. **Territory polygons crossing timezone lines** — Produces incorrect slot times for customers at boundaries with no error.
3. **Concurrent optimization for territories sharing resources** — Causes conflicting assignments. Must be serialized by region.

## Official Sources Used

- Salesforce Help — Time Zones and Appointment Booking — https://help.salesforce.com/s/articleView?id=sf.fs_appointment_booking_timezones.htm
- Salesforce Help — Guidelines for Creating Service Territories — https://help.salesforce.com/s/articleView?id=sf.fs_service_territories_guidelines.htm
- Trailhead — Configure Territories and Set Operating Hours — https://trailhead.salesforce.com/content/learn/modules/field-service-scheduling-foundations/configure-territories
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
