---
name: omni-channel-capacity-model
description: "Designing Omni-Channel capacity models for service orgs: agent capacity allocation, channel weighting (cases, chats, calls), skills matrix design, overflow strategy, presence configuration, and interruptible work patterns. Use when planning capacity units, defining Service Channel weights, or designing agent skills-based routing capacity. NOT for Omni-Channel routing configuration or queue assignment rules (use multi-channel-service-architecture). NOT for Einstein Bot design (use einstein-bot-architecture)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "how should I set capacity weights for cases vs chats vs phone calls in Omni-Channel"
  - "agents are getting overwhelmed with too many concurrent work items — how do I fix capacity"
  - "how do I design a skills-based routing model with overflow to backup queues"
  - "what capacity units should I assign per channel and how does interruptible work factor in"
  - "how to set Omni-Channel capacity weights for cases vs chats vs phone calls"
tags:
  - omni-channel
  - capacity-model
  - service-channel
  - skills-based-routing
  - presence-configuration
  - agent-capacity
  - overflow-routing
inputs:
  - Number and types of service channels (case, chat, voice, messaging)
  - Current or target agent headcount per team/skill group
  - Average handle time per channel
  - Business priority rules for channel types
  - Existing queue and routing configuration
outputs:
  - Capacity model spreadsheet or decision record with units per channel
  - Service Channel weight configuration recommendations
  - Skills matrix mapping agents to skill sets and queues
  - Overflow and secondary routing strategy
  - Presence Status and Presence Configuration design
  - Interruptible work flag recommendations per channel
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Omni-Channel Capacity Model

This skill activates when designing or tuning the capacity model for a Salesforce Omni-Channel deployment. It provides guidance on assigning capacity units to agents, weighting work items by channel type, building a skills matrix, configuring presence statuses, and designing overflow strategies to prevent agent overload.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Omni-Channel must be enabled in the org.** Confirm that Omni-Channel is turned on under Service Setup and that at least one Service Channel and Routing Configuration exist. Without these, capacity settings have nowhere to apply.
- **Capacity is NOT the same as concurrent work count.** A common wrong assumption is that "capacity = number of open tabs." Capacity is a numeric budget (e.g., 10 units) and each work item type consumes a configurable number of units from that budget. An agent with capacity 10 can handle two chats (3 units each = 6) and one case (5 units = 5) only if total does not exceed 10 — that combination would actually exceed capacity at 11 units.
- **Platform limits:** A single agent can have at most one active Presence Status at a time. Presence Configurations define the max capacity ceiling. Skills-Based Routing requires the Skills-Based Routing feature to be enabled separately from basic Omni-Channel.

---

## Core Concepts

### Agent Capacity and Capacity Units

Every agent who receives work through Omni-Channel has a total capacity defined in their Presence Configuration. This is a numeric value — commonly 10 or 15 — representing the maximum workload budget. Each incoming work item consumes a number of capacity units defined on its Service Channel. When the agent's remaining capacity drops below the cost of a pending work item, that item routes to another agent or waits in queue.

The capacity model supports two modes: **tab-based capacity** (each tab consumes exactly 1 unit regardless of channel) and **status-based capacity** (the Presence Configuration sets the ceiling and Service Channels define variable weights). Status-based capacity is the recommended model for any org handling more than one channel type.

### Service Channel Weights

Each Service Channel (Case, Chat, Voice, Messaging, Custom) has a configurable capacity weight — the number of units one work item of that type consumes. Industry-standard starting points:

| Channel | Typical Weight | Rationale |
|---|---|---|
| Case | 5 | Moderate complexity, longer handle time, not real-time |
| Chat / Messaging | 3 | Real-time but agents can handle 2-3 concurrently |
| Voice (Phone) | 10 | Fully occupies the agent — no concurrent work possible |

These weights are starting points. Calibrate them using your org's average handle time data and agent feedback after the first two weeks of operation.

### Skills-Based Routing and the Skills Matrix

Skills-Based Routing matches work item attributes (language, product line, issue tier) to agent skills. Each agent is assigned skills with optional skill levels. A skills matrix maps every agent to their skill set and ensures coverage across all queues. The routing engine evaluates the work item's required skills against available agents' skills and remaining capacity before assignment.

A well-designed skills matrix prevents the failure mode where a narrow specialist is the only agent who can handle a work type and becomes a permanent bottleneck.

### Presence Statuses and Presence Configurations

Presence Statuses define the named states an agent can select (Available, Available - Chat Only, Break, Training). Each status maps to a Presence Configuration that sets the capacity ceiling and which Service Channels the agent can receive. This is the mechanism that controls when and what work an agent receives.

Presence Configurations also control the **interruptible** flag per channel. When a channel is marked interruptible, a higher-priority work item (e.g., a phone call) can be pushed to the agent even if they are working on an interruptible item (e.g., a case). The interruptible item is not closed — it remains assigned but the agent's focus shifts.

---

## Common Patterns

### Pattern: Tiered Capacity by Channel Mix

**When to use:** The org handles cases, chats, and phone calls and needs agents to work across channels without being overwhelmed.

**How it works:**

1. Set agent total capacity to 10 in the Presence Configuration.
2. Configure Service Channel weights: Voice = 10, Case = 5, Chat = 3.
3. Mark Case and Chat as interruptible so a phone call (weight 10) can preempt them.
4. Result: an agent handling 1 case (5) + 1 chat (3) = 8 units used, 2 remaining. A second chat (3) would exceed capacity, so it routes elsewhere. A phone call (10) interrupts the current interruptible work.

**Why not the alternative:** Using tab-based capacity (1 unit per item) treats a phone call the same as a chat, leading to agents juggling a phone call alongside two chats — a recipe for poor customer experience and agent burnout.

### Pattern: Skills Matrix with Overflow

**When to use:** Specialized queues exist (Billing, Technical, Retention) but peak volumes can exceed specialist capacity.

**How it works:**

1. Define skills for each specialty (Billing, Technical, Retention) and assign primary agents.
2. Create a secondary routing configuration with relaxed skill requirements (e.g., any agent with "General Support" skill).
3. Set a queue timeout — if a work item is not accepted within N seconds by a primary-skilled agent, it overflows to the secondary routing configuration.
4. Monitor overflow rates weekly. If a queue overflows more than 15% of the time, add primary-skilled agents or cross-train existing ones.

**Why not the alternative:** Without overflow, specialized queues become bottlenecks during peak hours. Customers wait in long queues while generalist agents sit idle.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-channel org (cases only) | Tab-based capacity, 1 unit per item | Simplicity — no weighting needed when all work is equal |
| Multi-channel org (cases + chat + voice) | Status-based capacity with channel weights | Prevents voice calls from competing equally with chats |
| Seasonal volume spikes | Overflow to secondary queues with relaxed skills | Avoids hiring for peak; cross-trained agents absorb overflow |
| High agent turnover | Fewer, broader skills per agent | Reduces single-point-of-failure risk in the skills matrix |
| Premium / VIP customers | Dedicated queue with higher routing priority | Ensures premium SLA without starving standard queues |

---

## Recommended Workflow

Step-by-step instructions for designing or tuning an Omni-Channel capacity model:

1. **Inventory channels and volumes.** List every Service Channel in use (Case, Chat, Voice, Messaging, custom). Pull average handle time (AHT) and daily volume per channel from reports or Service Analytics.
2. **Define capacity units and weights.** Choose a total capacity ceiling (10 is the standard starting point). Assign weights to each channel proportional to agent effort — use Voice=10, Case=5, Chat=3 as defaults and adjust based on AHT data.
3. **Build the skills matrix.** Map every agent to their skills (language, product, tier). Ensure no skill has fewer than 3 agents assigned to avoid single-point bottlenecks. Document the matrix in a spreadsheet or the capacity model template.
4. **Design Presence Statuses and Configurations.** Create statuses that reflect real agent modes (Available - All Channels, Available - Chat Only, Available - Cases Only). Map each status to a Presence Configuration with the appropriate capacity ceiling and allowed channels.
5. **Configure interruptible flags.** Mark channels where work can be paused (cases, messaging) as interruptible. Never mark voice as interruptible — a phone call cannot be paused.
6. **Set up overflow and secondary routing.** For each specialized queue, define a secondary routing target and a timeout threshold (recommended: 60-120 seconds). Test that overflow actually routes to backup agents.
7. **Validate and monitor.** Deploy to a pilot group of 5-10 agents. Monitor queue wait times, overflow rates, and agent utilization for two weeks. Adjust weights and capacity ceilings based on data before full rollout.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Total capacity per Presence Configuration is set and documented
- [ ] Service Channel weights are configured and reflect channel effort differences
- [ ] Skills matrix has no single-agent bottlenecks (minimum 3 agents per skill)
- [ ] Presence Statuses cover all real agent working modes
- [ ] Interruptible flag is set correctly (cases/messaging = interruptible, voice = not interruptible)
- [ ] Secondary routing / overflow is configured for every specialized queue
- [ ] Queue timeout thresholds are set (60-120 seconds recommended)
- [ ] Pilot plan defined with monitoring metrics (wait time, overflow rate, utilization)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Capacity is consumed at assignment, not acceptance.** When a work item is pushed to an agent, their capacity is reduced immediately — even before the agent clicks Accept. If the agent declines or the item times out, capacity is restored, but during the pending period the agent appears "fuller" than they actually are. This causes uneven distribution during high-volume periods.
2. **Presence Configuration changes require agent re-login.** If you update a Presence Configuration's capacity value, agents currently logged in to Omni-Channel will not pick up the change until they go offline and come back online. There is no live-push of configuration changes.
3. **Interruptible does not mean auto-close.** Marking a channel as interruptible allows a higher-priority item to be pushed to the agent, but the interrupted work item stays assigned. Agents must manually return to it. If agents forget, you end up with stale assigned items that block future routing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Capacity model decision record | Documents total capacity, channel weights, and rationale for each setting |
| Skills matrix spreadsheet | Maps agents to skills, skill levels, and primary/secondary queues |
| Presence Configuration design | Lists all Presence Statuses, their mapped Presence Configurations, and allowed channels |
| Overflow routing plan | Defines secondary routing targets, timeout thresholds, and escalation paths |

---

## Official Sources Used

- Omni-Channel Overview — https://help.salesforce.com/s/articleView?id=sf.omnichannel_intro.htm
- Service Presence Introduction — https://help.salesforce.com/s/articleView?id=sf.service_presence_intro.htm

---

## Related Skills

- multi-channel-service-architecture — Use for routing configuration, queue design, and channel strategy decisions that sit above the capacity model
- service-cloud-architecture — Use for overall Service Cloud design decisions including Omni-Channel as one component
- einstein-bot-architecture — Use when bots handle initial triage before routing to human agents through Omni-Channel
