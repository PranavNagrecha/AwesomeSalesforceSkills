---
name: fsl-optimization-architecture
description: "Use this skill when designing or evaluating the FSL scheduling engine architecture: optimization mode selection (Global/In-Day/Resource/Reshuffle), ESO adoption strategy, territory sizing for optimization, and fallback planning. Trigger keywords: FSL optimization engine, ESO enhanced scheduling, global optimization timeout, in-day optimization, OAAS architecture, territory optimization design. NOT for admin-level scheduling policy configuration, scheduling rule setup in Setup, or per-appointment scheduling API calls (covered by apex/fsl-scheduling-api)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Scalability
triggers:
  - "How do I design FSL optimization architecture for 200 territories across 5 regions"
  - "Should I use Enhanced Scheduling and Optimization (ESO) or the legacy engine"
  - "FSL Global optimization timing out at 2 hours — architecture changes needed"
  - "In-Day vs Global optimization — when to use each mode"
  - "No automatic fallback when ESO fails — what is the contingency plan"
tags:
  - fsl
  - field-service
  - optimization
  - scheduling-engine
  - eso
  - architect
  - fsl-optimization-architecture
inputs:
  - "Number of territories, resources per territory, and daily SA volume"
  - "Whether ESO (Enhanced Scheduling and Optimization) add-on is licensed"
  - "Operational disruption patterns (appointment cancellations, resource unavailability)"
  - "Real-time vs batch optimization requirements"
outputs:
  - "Optimization mode selection recommendation with rationale"
  - "Territory sizing guidance to stay within optimization performance limits"
  - "ESO adoption strategy: phased territory-by-territory approach"
  - "Contingency plan for optimization failures or timeouts"
dependencies:
  - architect/fsl-multi-region-architecture
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Optimization Architecture

This skill activates when an architect needs to design or evaluate the FSL scheduling optimization engine configuration: selecting between optimization modes, planning Enhanced Scheduling and Optimization (ESO) adoption, sizing territories for optimization performance, and designing fallback strategies for optimization failures. It covers the architectural decisions that determine whether optimization runs reliably at scale.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the Enhanced Scheduling and Optimization (ESO) add-on is licensed. ESO provides better throughput, work chain support, and reduced timeout risk but is a separate add-on SKU.
- Determine the resource and SA volumes per territory. The FSL optimization engine has recommended limits of 50 resources and 1,000 SAs per day per territory. Territories exceeding these limits consistently experience Global optimization timeouts.
- Understand the operational disruption patterns: how often do cancellations, no-shows, and emergency insertions occur? High disruption frequency requires In-Day optimization in addition to Global.
- Confirm whether real-time individual appointment optimization (OAAS.schedule) is needed alongside territory-level optimization. The two operate independently.

---

## Core Concepts

### Four Optimization Modes

| Mode | Scope | Trigger | Timeout |
|---|---|---|---|
| **Global** | Full territory, 1–7 day horizon | Scheduled or on-demand | 2 hours hard limit |
| **In-Day** | Same-day disruptions | Triggered by cancellation/no-show | No published timeout (faster) |
| **Resource Schedule** | Single resource's schedule | On-demand | No published timeout |
| **Reshuffle** | Pinned appointments + gaps | On-demand | No published timeout |

Global optimization is the primary batch scheduling run (nightly or weekly). In-Day optimization handles real-time disruptions during the work day. Resource Schedule optimizes an individual technician's route. Reshuffle fills gaps around pinned (locked) appointments.

**Pinned appointments are never moved by any optimization mode** — this is the mechanism for protecting customer commitments from being rescheduled by the engine.

### ESO vs. Legacy Engine

Enhanced Scheduling and Optimization (ESO) is a Hyperforce-backed optimization engine introduced to replace the legacy engine:

| Attribute | Legacy Engine | ESO |
|---|---|---|
| Per-territory adoption | Not applicable — global | Territory-by-territory in Setup |
| Fallback | N/A | None — no automatic fallback |
| Work chain support | No | Yes |
| Throughput | Lower | Higher |
| ESO operation limits | N/A | See release notes per release |

**Critical architecture decision:** ESO adoption is per-territory and irreversible in the current release cycle. Once enabled for a territory, that territory uses ESO exclusively. Plan ESO rollout in phases: start with lower-criticality territories, validate, then expand.

### Optimization Performance Limits

The recommended maximums per territory for Global optimization to complete within the 2-hour timeout:
- **50 resources** per territory
- **1,000 service appointments per day**

Exceeding these limits does not prevent optimization from starting but consistently causes jobs to exceed the 2-hour timeout and be silently cancelled. The FSL optimization history record shows a cancelled status.

**Architecture implication:** Territory design is a performance design decision, not just an organizational one. Territories that exceed size limits will have unreliable optimization. Redesign large territories into geographic sub-territories before reaching scale.

---

## Common Patterns

### Phased ESO Adoption

**When to use:** Org has multiple territories and wants to migrate to ESO without risking all territory optimization simultaneously.

**How it works:**
1. Identify pilot territories: 2–3 with medium volume and non-critical SLAs
2. Enable ESO for pilot territories in Setup > Field Service > Enhanced Scheduling
3. Run 2 weeks of Global optimization with ESO and compare job completion times and solution quality to legacy
4. If successful, adopt territory-by-territory in priority order, deferring high-criticality territories last
5. Document that adopted territories have no fallback — build a manual dispatch contingency plan

**Why not all at once:** ESO has no automatic fallback. A rollout issue affecting all territories simultaneously leaves no fallback for any territory.

### Nightly Global + Daytime In-Day Architecture

**When to use:** Operations that have significant daytime disruptions (cancellations, emergency insertions, resource unavailability) in addition to regular scheduled appointments.

**How it works:**
- Schedule Global optimization nightly (e.g., 10pm–2am) for each territory to build the next day's schedule
- Configure In-Day optimization triggers for same-day disruptions: appointment cancellation → trigger In-Day for that territory
- Use Resource Schedule optimization when an individual technician's day changes significantly (personal emergency, vehicle breakdown)

**Why both modes:** Global optimization builds the optimal schedule before the day starts. In-Day reacts to disruptions without rebuilding the entire territory's schedule.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Territory > 50 resources | Split into geographic sub-territories | Reduces Global timeout risk |
| ESO available, ready to adopt | Phased territory-by-territory adoption | Limits blast radius of any ESO issues |
| High daily disruption rate | Global + In-Day combo | In-Day handles real-time disruptions |
| Emergency insertion | OAAS Resource Schedule for affected tech | Faster than full territory re-optimization |
| Pinned appointments during optimization | Use Pinned status — never manually lock | Pinned is the mechanism; manual locks don't persist |
| Legacy engine, no ESO | Keep Global under 50 resources/1000 SA/territory | Only mitigation for legacy engine timeout risk |

---

## Recommended Workflow

1. **Inventory territories and volumes** — Document resource count and daily SA volume per territory. Flag any territory exceeding 50 resources or 1,000 SA/day.
2. **Design territory sizing** — If territories exceed limits, propose geographic sub-territory splits. Model the new structure before ESO or optimization configuration.
3. **Choose optimization modes** — Determine which modes are needed: Global (always), In-Day (if disruptions are frequent), Resource Schedule (if individual-level changes are common).
4. **Plan ESO adoption** — If ESO is licensed, design a phased territory-by-territory adoption plan. Identify pilot territories and success criteria. Build a manual dispatch contingency.
5. **Configure optimization schedules** — Set up scheduled Global optimization jobs per territory (one territory at a time, not concurrent overlapping territories).
6. **Monitor optimization job history** — Build a dashboard or scheduled report on FSL optimization job records to detect silent cancellations from timeouts.
7. **Document fallback procedures** — For each territory, document what dispatchers do if optimization fails: manual dispatch sequence, escalation path, customer communication.

---

## Review Checklist

- [ ] No territory exceeds 50 resources or 1,000 SA/day recommendation
- [ ] ESO adoption plan is phased, not all-at-once
- [ ] Manual dispatch contingency documented for optimization failures
- [ ] Global optimization scheduled to complete before business hours start
- [ ] In-Day optimization triggered by disruption events (if needed)
- [ ] Pinned appointment mechanism documented (not manual locking)
- [ ] Optimization job history monitoring in place

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Global optimization has a 2-hour hard server-side timeout** — Silent cancellation with no exception thrown. The FSL optimization job record shows cancelled status. Monitor job records rather than relying on exception alerting.
2. **ESO has no automatic fallback to the legacy engine** — A territory enrolled in ESO uses ESO exclusively. Plan manual dispatch procedures for all ESO-enrolled territories.
3. **Concurrent Global optimization jobs for overlapping territories conflict** — Run optimization per-territory sequentially, not in parallel for territories that share resources (cross-territory resource assignment via Secondary ServiceTerritoryMember).
4. **Pinned appointments are excluded from ALL optimization modes** — Once pinned, an appointment is never moved, rescheduled, or reassigned by any optimization operation. Use pinning deliberately.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Territory sizing analysis | Table showing current resource/SA volumes vs. optimization limits |
| ESO adoption phasing plan | Ordered territory list for ESO rollout with pilot criteria |
| Optimization mode architecture diagram | Which modes run when and on what trigger |

---

## Related Skills

- architect/fsl-multi-region-architecture — Multi-region territory design that affects optimization scope
- apex/fsl-scheduling-api — Individual appointment scheduling API calls (OAAS, schedule())
- data/fsl-territory-data-setup — Territory data structure that determines optimization scope
