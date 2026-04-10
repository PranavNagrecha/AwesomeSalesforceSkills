# Gotchas — FSL Optimization Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Global Optimization Timeout Is Silent

**What happens:** When a Global optimization job exceeds the 2-hour limit, it is cancelled by the server without raising an exception or sending a notification. The submitting Apex code has already completed normally. The FSL optimization job history record shows "Cancelled" or "Failed" status.

**When it occurs:** Any territory with more than 50 resources or 1,000 SA/day running Global optimization.

**How to avoid:** Monitor FSL optimization job records with a scheduled report or Flow alert. If a job doesn't show "Completed" status by the time dispatchers start their morning, investigation is needed.

---

## Gotcha 2: ESO Adoption Is Per-Territory and Has No Fallback

**What happens:** Once ESO is enabled for a territory, that territory uses ESO exclusively. There is no automatic fallback to the legacy engine if ESO is unavailable or produces errors for that territory.

**When it occurs:** Any territory enrolled in Enhanced Scheduling and Optimization.

**How to avoid:** Maintain documented manual dispatch procedures for every ESO-enrolled territory. Phase adoption starting with lower-criticality territories. Test ESO stability for 2–3 weeks per territory before declaring adoption complete.

---

## Gotcha 3: Concurrent Optimization for Territories Sharing Resources Produces Conflicts

**What happens:** When two Global optimization jobs run simultaneously for territories that share resources via Secondary ServiceTerritoryMember, both jobs attempt to assign the shared resource. The result is either one job "winning" (producing a suboptimal schedule for the other) or both jobs failing partial assignments.

**When it occurs:** Any multi-territory deployment where resources serve as secondary members in more than one territory and optimization is not serialized.

**How to avoid:** Serialize optimization jobs for territories that share resources. Schedule them sequentially with time gaps, not concurrently.

---

## Gotcha 4: Pinned Appointments Are Excluded From ALL Optimization Modes

**What happens:** A "pinned" ServiceAppointment is excluded from Global, In-Day, Resource Schedule, and Reshuffle optimization. It is never moved, rescheduled, or reassigned by any optimization operation, regardless of better scheduling options that emerge.

**When it occurs:** Customer-facing committed appointments that are marked pinned remain fixed even when optimization could significantly improve the surrounding schedule.

**How to avoid:** Use pinning deliberately and sparingly — only for firm customer commitments. Advise operations teams that over-pinning degrades optimization quality because the engine has less flexibility to optimize around fixed anchor points.

---

## Gotcha 5: ESO Operation Limits Differ From Legacy Engine Limits

**What happens:** ESO has its own operation limits (concurrently running jobs, jobs per hour, etc.) that are documented per-release and differ from legacy engine limits. Teams that migrated to ESO and assumed the same limits as the legacy engine may hit ESO-specific limits they weren't aware of.

**When it occurs:** High-volume ESO deployments running multiple optimization operations per hour.

**How to avoid:** Review the Limits for Enhanced Scheduling help article for the current release. Update your optimization monitoring to include ESO-specific limit thresholds.
