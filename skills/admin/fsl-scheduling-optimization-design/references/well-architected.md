# Well-Architected Notes — FSL Scheduling Optimization Design

## Relevant Pillars

- **Operational Excellence** — The optimizer's primary value is operational: it removes manual scheduling labor, produces consistent route sequencing, and enables dispatchers to focus on exceptions rather than rote scheduling. An optimization design that does not include monitoring (job logs, unscheduled appointment rate, run duration) degrades operational visibility and makes it impossible to know whether the optimizer is performing correctly.

- **Performance** — Global optimization runs are compute-intensive. Poorly scoped runs — large territory horizons, no appointment data quality baseline, overly complex scheduling policies — produce long run times or timeouts. Performance-conscious optimization design scopes runs appropriately to territory size, limits horizon to what the business actually needs, and ensures appointment data is clean before the run starts.

- **Reliability** — In-Day optimization triggered by automation must be resilient: if the optimization job fails (license error, timeout, API limit), a fallback notification to the dispatcher must fire. Silent failures in In-Day automation leave gaps unfilled with no human awareness. Reliability requires both automation and manual fallback paths.

## Architectural Tradeoffs

**Optimization Scope vs. Run Time:** Global optimization across many territories with a long horizon produces the highest-quality schedule but the longest run time. Organizations must decide whether to optimize across all territories in a single job (maximum consistency, higher risk of timeout) or run territory-by-territory jobs (lower risk, longer total wall-clock time). The right tradeoff depends on territory count, appointment density, and how much pre-shift lead time is available before dispatchers need the schedule.

**Automation vs. Dispatcher Control:** Fully automated In-Day optimization (triggered by Flow) removes dispatcher latency but also removes dispatcher judgment. Some disruptions (e.g., a cancellation near a VIP customer's area) may warrant manual handling rather than algorithmic backfill. A hybrid approach — automation triggers the optimization but the dispatcher confirms before schedule delivery — balances speed with control, at the cost of requiring dispatcher availability.

**Aerial vs. Street-Level Routing:** Aerial is free and fast; Street-Level Routing is accurate but costs more and slows runs marginally. The decision is a cost-accuracy tradeoff. For territories where straight-line distance approximates real drive distance (low-density rural), Aerial is sufficient. For urban territories where road networks deviate significantly from straight-line paths, Street-Level Routing prevents systematic underestimation of travel time that cascades into late appointments throughout the day.

## Anti-Patterns

1. **Running Global Optimization Mid-Day as a Disruption Response** — Global optimization with a multi-day horizon should not be triggered in response to same-day disruptions. It is too slow, may reschedule confirmed appointments, and does not scope appropriately to the current day. In-Day Optimization is the correct tool for disruption response. Using Global mid-day is an anti-pattern that produces customer-visible reschedules and dispatcher confusion.

2. **Treating All Appointments as Priority 1** — Assigning the highest priority to all appointments eliminates the optimizer's ability to protect genuinely critical work during constrained scheduling runs. This anti-pattern is commonly introduced to avoid the complexity of priority tier design, but it produces a scheduling system that behaves as if no priority configuration exists — leaving emergency appointments in the same queue position as routine maintenance.

3. **Neglecting Appointment Data Quality Before Optimization** — Running optimization against service appointments with null `DueDate` or null `Priority` produces unpredictable results and a growing backlog of perpetually unscheduled records. The optimizer is a ranking and sequencing engine, not a data quality corrector. Clean, well-populated appointment data is a prerequisite for meaningful optimization output, not an optional enhancement.

## Official Sources Used

- Understanding Optimization in Field Service Scheduling (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-lightning-quick-look/understand-optimization
- Global Optimization Planning (Trailhead) — https://trailhead.salesforce.com/content/learn/modules/field-service-scheduling/global-optimization
- Set Up Routing for Travel Time Calculations — https://help.salesforce.com/s/articleView?id=sf.fs_routing.htm
- Optimize Appointments Using Priorities — https://help.salesforce.com/s/articleView?id=sf.fs_optimizer_priorities.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
