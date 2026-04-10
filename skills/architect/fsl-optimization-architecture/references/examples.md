# Examples — FSL Optimization Architecture

## Example 1: Territory Redesign to Resolve Optimization Timeouts

**Context:** A large utilities company has 3 FSL territories covering metropolitan areas, each with 80–120 service resources and 2,500–3,000 daily service appointments. Global optimization jobs consistently time out after 2 hours without completing, leaving the schedule partially optimized for the next day.

**Problem:** Territories are oversized — each exceeds the recommended 50 resource / 1,000 SA/day limit by 2–3x. The 2-hour hard timeout is triggered on every run.

**Solution:**
1. Redesign each metropolitan territory into 3–4 geographic sub-territories of 25–35 resources each
2. Align sub-territory boundaries to natural geographic divisions (river boundaries, highway corridors)
3. Assign secondary ServiceTerritoryMember records for resources who live near sub-territory boundaries (to allow overflow scheduling)
4. Schedule Global optimization for each sub-territory sequentially (staggered by 45 minutes per sub-territory)
5. Result: each sub-territory optimization completes in 20–35 minutes, well within the 2-hour window

**Why it works:** Territory size is the primary driver of Global optimization job duration. Splitting oversized territories into compliant-sized sub-territories brings each individual job within the timeout window.

---

## Example 2: ESO Phased Adoption Plan

**Context:** A field service organization has 45 territories and the ESO add-on license. The operations team wants to adopt ESO but is concerned about service disruption if ESO has issues in early adoption.

**Problem:** The team wants to enable ESO for all 45 territories at once to simplify configuration. Since ESO has no automatic fallback to the legacy engine, a widespread ESO issue would affect all territories simultaneously.

**Solution:**
1. Identify 3 pilot territories with medium volume (under 30 resources, under 500 SA/day) and non-critical SLAs
2. Enable ESO for pilot territories only in Setup > Field Service > Enhanced Scheduling
3. Run 3 weeks of Global optimization with ESO enabled. Compare job completion times, solution quality scores, and unscheduled appointment rates to pre-ESO baseline
4. After successful pilot, enable ESO for 5–8 territories per month, prioritizing lower-criticality territories first
5. Keep manual dispatch contingency procedures documented for each ESO-enrolled territory

**Why it works:** Phased adoption limits the blast radius of any ESO issue to a subset of territories. The legacy engine continues serving non-adopted territories, providing a natural fallback at the org level (not per-territory, but at the operations level).

---

## Anti-Pattern: Running Concurrent Global Optimization for All Territories

**What practitioners do:** Schedule a single nightly job that triggers Global optimization for all territories simultaneously at 10pm.

**What goes wrong:** Territories that share resources via Secondary ServiceTerritoryMember assignments have their shared resources claimed by two optimization jobs simultaneously. The jobs conflict, producing suboptimal schedules, and one or both jobs may fail or be partially cancelled.

**Correct approach:** Stagger optimization jobs by territory with 30–45 minute gaps. Group territories that share resources and ensure their jobs do not overlap. For 10 territories: first batch at 10pm, second at 10:45pm, third at 11:30pm, etc.
