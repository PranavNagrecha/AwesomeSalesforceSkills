# Gotchas — Omni-Channel Capacity Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Capacity Is Consumed at Push, Not Acceptance

**What happens:** When Omni-Channel pushes a work item to an agent, the capacity units are deducted immediately — before the agent clicks Accept. If the agent is slow to accept or the item times out and gets rerouted, the capacity is tied up during the entire pending period. During high-volume periods, this "phantom capacity consumption" makes agents appear full when they are actually idle.

**When it occurs:** High-volume environments where agents have accept timeouts greater than 15 seconds and work items are frequently declined or timed out.

**How to avoid:** Keep accept timeouts short (10-15 seconds). Monitor the "Declined" and "Timed Out" work item counts. If these are high, investigate whether agents need training or whether the routing configuration is sending mismatched work.

---

## Gotcha 2: Presence Configuration Changes Do Not Live-Update

**What happens:** When an administrator changes the capacity value on a Presence Configuration (e.g., from 10 to 15), agents who are currently logged into Omni-Channel continue operating under the old capacity value. The new value only takes effect when the agent logs out of Omni-Channel and logs back in.

**When it occurs:** Any time a capacity tuning change is made during business hours. Administrators expect the change to take effect immediately, but agents continue receiving work under the old capacity model until they cycle their presence.

**How to avoid:** Schedule capacity changes during shift transitions. Communicate to agents that they need to go Offline and back Online to pick up the new configuration. If an urgent mid-shift change is needed, use a broadcast message or Chatter post instructing agents to briefly toggle their presence.

---

## Gotcha 3: Interruptible Work Stays Assigned After Interruption

**What happens:** When a higher-priority work item interrupts an agent's current interruptible work, the interrupted item remains assigned to the agent. It does not go back into the queue. The agent must manually return to the interrupted item and complete it. If agents do not realize this, interrupted items accumulate as stale assigned work, inflating the agent's consumed capacity and blocking new routing.

**When it occurs:** Orgs that use the interruptible flag on cases or messaging but do not train agents on the expected workflow after an interruption (e.g., a phone call arrives while working a case).

**How to avoid:** Train agents to check their Omni-Channel widget for "paused" work items after completing an interrupting item. Build a report on assigned work items with no agent activity in the last 30 minutes to catch stale assignments. Consider auto-reassignment flows for items idle beyond a threshold.

---

## Gotcha 4: Skills-Based Routing Ignores Capacity When No Skilled Agent Exists

**What happens:** If a work item requires a skill that no currently online agent possesses, the item sits in the queue indefinitely — it will not fall back to a non-skilled agent automatically. There is no built-in "degrade gracefully" behavior. The item waits until a skilled agent comes online, even if dozens of non-skilled agents are available and idle.

**When it occurs:** Niche skills with only 1-2 agents assigned (e.g., a specific language or product expertise). When those agents are out sick or on break, work items pile up with no fallback.

**How to avoid:** Always design a secondary routing configuration or overflow queue with relaxed skill requirements. Set a queue timeout so items that wait longer than N seconds get rerouted to the overflow path. Never have a skill assigned to fewer than 3 agents.

---

## Gotcha 5: Tab-Based and Status-Based Capacity Cannot Be Mixed Per Agent

**What happens:** An agent's capacity model is determined by their Presence Configuration. You cannot have an agent use tab-based capacity for one channel and status-based (weighted) capacity for another. It is all or nothing per Presence Configuration. Attempting to work around this by assigning agents to multiple Presence Configurations does not work — agents can only be in one Presence Status at a time.

**When it occurs:** Orgs migrating from tab-based to status-based capacity try to do a phased rollout by channel. They discover that the switch must be all-at-once for each agent group.

**How to avoid:** Plan the migration as a complete cutover per agent group. Create new Presence Configurations with status-based capacity and new Presence Statuses. Switch agent groups during shift changes, validate, then proceed to the next group.
