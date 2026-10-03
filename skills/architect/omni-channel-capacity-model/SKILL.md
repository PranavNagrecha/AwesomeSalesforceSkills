---
name: omni-channel-capacity-model
description: "Designing Omni-Channel capacity models for service orgs: agent capacity allocation, channel weighting (cases, chats, calls), skills matrix design, overflow strategy, presence configuration, and interruptible work patterns. Use when planning capacity units, defining Service Channel weights, or designing agent skills-based routing capacity. NOT for enabling Omni-Channel, creating Service Channels or routing rules - use admin/omni-channel-routing-setup. NOT for cross-channel strategy and channel-to-feature mapping - use architect/multi-channel-service-architecture."
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
  - "size agent capacity so blended agents can take a call while holding messaging sessions"
  - "stop Omni-Channel from pushing new work to agents who are already full"
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
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

## Questions to Ask Before Configuring

Each question traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "What is the measured handle time and concurrency per work type, and which queues route each one?" | Weights live on routing configurations, so one work type can carry several weights (Gotcha 6) | A weight per routing configuration from data, not defaults | Capacity reflects effort, and every queue charges the same for the same work |
| "May an agent hold messaging sessions while taking a call, and how many?" | Voice must take all primary capacity; interruptible work uses its own pool (Gotchas 3, 7) | `isInterruptible` per channel and an `interruptibleCapacity` per presence configuration | Blended agents get the concurrency the platform allows, no more |
| "When is a case finished for capacity purposes: tab closed, or status says done?" | Tab-based channels free capacity on unfinished work (Gotcha 5) | A capacity model per service channel, with status mappings for case work | Agents are not over-assigned on cases that span days |
| "Which skills are required, and which can be dropped after a wait?" | Only Additional skills fall back (Gotcha 4) | Skills marked Additional with a `dropAdditionalSkillsTimeout`, and overflow assignees for the rest | Niche work reaches an agent instead of waiting all day |
| "Does anyone assign work by changing the owner instead of through queues?" | Work assigned outside Omni-Channel consumes no capacity (Gotcha 8) | A list of manual and automated assignment paths to reroute | The capacity numbers describe the agent's real load |
| "When will capacity changes be made, and how will you confirm agents picked them up?" | Each live session records its configured capacity (Gotcha 2) | A change window and a `UserServicePresence` check | Tuning takes effect when planned, and you can prove it |

What proper configuration adds over "just setting weights": the agent's total, each routing configuration's weight, the channel's capacity model, and the interruptible pool agree with each other, so routing sends the work an agent can actually take.

## Core Concepts

### Agent Capacity and Capacity Units

Every agent who receives work through Omni-Channel has a total capacity defined in their Presence Configuration (`PresenceUserConfig.capacity`). This is a numeric value, commonly 10 or 15, representing the maximum workload budget. Each incoming work item consumes the capacity set on the routing configuration that routed it (`QueueRoutingConfig.capacityWeight` or `capacityPercentage`). When the agent's remaining capacity drops below the cost of a pending work item, that item routes to another agent or waits in queue.

Each service channel chooses when capacity is released (`ServiceChannel.capacityModel`): **tab-based** releases it when the work tab is closed in the console; **status-based** keeps it consumed until the work's status field says completed or the work is reassigned. Status-based capacity is the better fit for case and email work that spans sessions. (Corrected: the earlier text described tab-based as "1 unit per tab" and placed weights on the Service Channel; see `references/gotchas.md` Gotchas 5 and 6.)

### Routing Configuration Weights

Each routing configuration carries the weight (or percentage) that one work item routed through it consumes; the Service Channel names the object and capacity model. Practitioner starting points per work type:

| Channel | Typical Weight | Rationale |
|---|---|---|
| Case | 5 | Moderate complexity, longer handle time, not real-time |
| Chat / Messaging | 3 | Real-time but agents can handle 2-3 concurrently |
| Voice (Phone) | Equal to the agent's total capacity (or `capacityPercentage` 100) | The platform requires voice to consume the entire capacity (Gotcha 7) |

These weights are starting points. Calibrate them using your org's average handle time data and agent feedback after the first two weeks of operation.

### Skills-Based Routing and the Skills Matrix

Skills-Based Routing matches work item attributes (language, product line, issue tier) to agent skills. Each agent is assigned skills with optional skill levels. A skills matrix maps every agent to their skill set and ensures coverage across all queues. The routing engine evaluates the work item's required skills against available agents' skills and remaining capacity before assignment.

A well-designed skills matrix prevents the failure mode where a narrow specialist is the only agent who can handle a work type and becomes a permanent bottleneck.

### Presence Statuses and Presence Configurations

Presence Statuses define the named states an agent can select (Available, Available - Chat Only, Break, Training) and list the Service Channels that status receives; a status with no channels is an Away status. Presence Configurations are assigned to users or profiles and set the capacity ceiling (`capacity`), the interruptible ceiling (`interruptibleCapacity`), decline and auto-accept behaviour, and the status applied on decline or push timeout. (Corrected: statuses do not map to configurations.)

Interruptibility is set on the **Service Channel** (`isInterruptible`): interruptible work consumes interruptible capacity instead of primary capacity, so primary work such as a phone call can still reach an agent who holds interruptible work. A routing configuration can override the channel with `capacityType`. (Corrected: the earlier text placed the interruptible flag on the Presence Configuration.)

---

## Common Patterns

### Pattern: Tiered Capacity by Channel Mix

**When to use:** The org handles cases, chats, and phone calls and needs agents to work across channels without being overwhelmed.

**How it works:**

1. Set agent total capacity to 10 in the Presence Configuration.
2. Configure routing configuration weights: Voice = 10 (the full capacity), Case = 5, Chat = 3.
3. Mark the chat or messaging Service Channel as interruptible and set `interruptibleCapacity` so chats draw on the interruptible pool.
4. Result: an agent handling 1 case (5 primary) and 1 chat (3 interruptible) can take a second chat if the interruptible pool allows, but not a phone call, because the case holds primary capacity and voice needs all of it. UNVERIFIED (2026-10-03): how the interruptible pool interacts with voice pushes in every edition is described in Salesforce Help only; pilot it.

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
| Single-channel org (cases only) | One routing configuration weight; status-based capacity on the case channel | Simplicity; capacity is held until the case is done |
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
5. **Configure interruptible flags.** Mark channels where work can be paused (cases, messaging) as interruptible on the Service Channel, and size `interruptibleCapacity` on the Presence Configuration. Never mark voice as interruptible: a phone call cannot be paused. Express the deployable result as metadata (`references/examples.md`, Example 3).
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

The full list with sources is in `references/gotchas.md`. The ones that most often break a capacity model:

| Gotcha | Consequence |
|---|---|
| Capacity is taken at assignment (Gotcha 1) | Slow accepts and push timeouts make agents look full while idle |
| Weights live on routing configurations (Gotcha 6) | The same work type can cost different amounts in different queues |
| Voice takes the whole agent (Gotcha 7) | Raising agent capacity without changing the voice weight breaks the voice rule |

## Output Artifacts

| Artifact | Description |
|---|---|
| Capacity model decision record | Documents total capacity, channel weights, and rationale for each setting |
| Skills matrix spreadsheet | Maps agents to skills, skill levels, and primary/secondary queues |
| Presence Configuration design | Lists all Presence Statuses, their mapped Presence Configurations, and allowed channels |
| Overflow routing plan | Defines secondary routing targets, timeout thresholds, and escalation paths |

---

## Official Sources Used

See `references/well-architected.md` for the sources read for this revision.

---

## Related Skills

- multi-channel-service-architecture — Use for routing configuration, queue design, and channel strategy decisions that sit above the capacity model
- service-cloud-architecture — Use for overall Service Cloud design decisions including Omni-Channel as one component
- einstein-bot-architecture — Use when bots handle initial triage before routing to human agents through Omni-Channel
