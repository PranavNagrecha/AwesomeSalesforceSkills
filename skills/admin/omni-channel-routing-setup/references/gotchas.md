# Gotchas — Omni-Channel Routing Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Work Items Route to Queue Owner, Not Omni-Channel, When Routing Configuration Is Missing

**What happens:** If a Case is assigned to a queue that does not have a Routing Configuration set, the case is placed in the queue's list view but is never pushed to any agent via Omni-Channel. Agents must manually pick cases from the list view. This is the default pre-Omni-Channel behavior — it does not throw an error or warning anywhere.

**When it occurs:** When Omni-Channel is enabled org-wide but individual queues are not updated to include a Routing Configuration. This commonly happens during phased rollouts where only some queues are migrated to Omni-Channel while others are left on manual pickup.

**How to avoid:** After enabling Omni-Channel, audit every queue used for case routing. For each queue, verify the Routing Configuration field is set. Create a custom report on Queue records and cross-reference with Routing Configuration assignments if the org has many queues.

---

## Gotcha 2: Skills-Based Routing Rules Silently Fall Back When No Agent Matches

**What happens:** When a work item enters a queue with a Skills-Based Routing Configuration but no available agent has the required skill (or all matching agents are at capacity), the item does not throw an error or alert. It sits in the queue without routing. Agents who do not have the required skill will also not see the work item, even if they are Available and have capacity. The supervisor dashboard will show the item as "In Queue" indefinitely.

**When it occurs:** When Skills-Based Routing Rules require a specific skill but no Service Resource has been assigned that skill, or when all skilled agents are at capacity simultaneously. Also occurs when the routing rule references a field value that is null or unmapped on the incoming work item.

**How to avoid:** Always set a default fallback: either a secondary Routing Configuration on a fallback queue, or a default routing rule entry with no skill requirement that catches items that do not match any explicit rule entry. Test every rule path with a null/blank field value to confirm fallback behavior. Monitor the Omni-Channel Supervisor dashboard for items stuck "In Queue" longer than your SLA threshold.

---

## Gotcha 3: Presence Configuration Capacity Is Per-Status, Not Per-Agent

**What happens:** Administrators sometimes expect that setting a capacity of 10 on one Presence Configuration covers the agent globally. In practice, capacity is defined per Presence Configuration, not per agent. If an agent is assigned to two Presence Configurations (one with capacity 5 and one with capacity 10), their effective capacity depends entirely on which Presence Status they are currently active in. Switching statuses can cause abrupt capacity drops mid-shift, with in-flight work items still consuming their original capacity allocation.

**When it occurs:** In orgs with multiple Presence Statuses that are mapped to different Presence Configurations. Common in orgs that have a "Chat Only" status and an "All Channels" status with different capacity ceilings.

**How to avoid:** Document the intended capacity per status explicitly. Name Presence Configurations in a way that makes their capacity clear (e.g., "Support Agent - Full Capacity (10)"). Audit Presence Configuration assignments when agents report receiving fewer work items than expected.

---

## Gotcha 4: Deactivating a Service Resource Does Not Close Open Work Items

**What happens:** When an agent's Service Resource record is deactivated (Active = false), the agent stops receiving new work items. However, any work items already assigned to that agent remain assigned. They are not automatically re-queued or reassigned. If the agent is off sick and their Service Resource is deactivated, their assigned cases stay with them until manually reassigned.

**When it occurs:** During offboarding, extended leave, or when reorganizing teams and deactivating old Service Resources before creating new ones.

**How to avoid:** Before deactivating a Service Resource, use the Omni-Channel Supervisor or a SOQL query to identify and manually reassign any open work items assigned to that agent. Consider building a Flow or process that re-queues work items when a Service Resource is deactivated, rather than leaving them stranded.

---

## Gotcha 5: Push Timeout Declines Do Not Always Re-Queue Immediately

**What happens:** When a work item is pushed to an agent and the push timeout expires (the agent does not accept within the configured seconds), the item is expected to route to the next available agent. In practice, if the org's routing queue is heavily loaded or all agents are at capacity, the item may sit for a variable period between the timeout and re-routing. This can create misleading metrics where "push timeout" events appear short but actual customer wait times are much longer.

**When it occurs:** During peak volume periods when all agents are near capacity. Also occurs when routing configurations have very short push timeouts (under 10 seconds) and high agent counts, causing a rapid chain of push-and-timeout events that delays actual assignment.

**How to avoid:** Set push timeout values that reflect realistic agent response times — 30 seconds is a common baseline for case routing. Do not set push timeouts below 10 seconds. Monitor the gap between "entered queue" timestamp and "accepted" timestamp in Omni-Channel reporting to detect systemic re-queuing delays rather than relying on push timeout alone.

---

## Gotcha 6: Skills-Based Routing Requires a Separate Feature Enable — It Is Not Part of Basic Omni-Channel

**What happens:** Administrators enable Omni-Channel and expect Skills-Based Routing to be available immediately. The Routing Configuration dropdown does not show "Skills-Based" as a routing model option because Skills-Based Routing must be enabled separately under Omni-Channel Settings. This is a separate toggle from the main Omni-Channel enable switch.

**When it occurs:** During initial skills-based routing setup or when migrating an existing queue-based org to skills-based routing.

**How to avoid:** In Omni-Channel Settings, confirm both "Enable Omni-Channel" and "Enable Skills-Based Routing" are checked before creating Routing Configurations for the skills-based model. Document both enables in deployment runbooks.
