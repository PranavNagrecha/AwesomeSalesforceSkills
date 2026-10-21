# Gotchas — Omni-Channel Routing Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Work Items Route to Queue Owner, Not Omni-Channel, When Routing Configuration Is Missing

**What happens:** If a Case is assigned to a queue that does not have a Routing Configuration set, the case is placed in the queue's list view but is never pushed to any agent via Omni-Channel. Agents must manually pick cases from the list view. This is the default pre-Omni-Channel behavior — it does not throw an error or warning anywhere. UNVERIFIED (2026-10-21): the list-view fallback is Help-only; the corpus holds only that the queue's routing configuration is the optional `queueRoutingConfig` name (api_meta 264 L102437-102438).

**When it occurs:** When Omni-Channel is enabled org-wide but individual queues are not updated to include a Routing Configuration. This commonly happens during phased rollouts where only some queues are migrated to Omni-Channel while others are left on manual pickup.

**How to avoid:** After enabling Omni-Channel, audit every queue used for case routing. For each queue, verify the Routing Configuration field is set. Create a custom report on Queue records and cross-reference with Routing Configuration assignments if the org has many queues.

---

## Gotcha 2: Skills-Based Routing Rules Silently Fall Back When No Agent Matches

**What happens:** When a work item enters a queue with a Skills-Based Routing Configuration but no available agent has the required skill (or all matching agents are at capacity), the item does not throw an error or alert. It sits in the queue without routing. Agents who do not have the required skill will also not see the work item, even if they are Available and have capacity. The supervisor dashboard will show the item as "In Queue" indefinitely.

**When it occurs:** When Skills-Based Routing Rules require a specific skill but no Service Resource has been assigned that skill, or when all skilled agents are at capacity simultaneously. Also occurs when the routing rule references a field value that is null or unmapped on the incoming work item.

UNVERIFIED (2026-10-21): the heading's "silently fall back" and the "sits in the queue" / "In Queue indefinitely" behaviour are Help-only. What the guide does document is the relief valve: a skill marked Additional is dropped after `dropAdditionalSkillsTimeout` seconds "and the case is routed to the best-matched agent, even if the agent doesn't have all the skills" (api_meta 264 L102662-102667; `SkillRequirement.IsAdditionalSkill`, object_reference 264 L273445-273452).

**How to avoid:** Mark non-essential skills as additional and set `dropAdditionalSkillsTimeout`. Also set a default fallback: either a secondary Routing Configuration on a fallback queue, or a default routing rule entry with no skill requirement that catches items that do not match any explicit rule entry. Test every rule path with a null/blank field value to confirm fallback behavior. Monitor the Omni-Channel Supervisor dashboard for items stuck "In Queue" longer than your SLA threshold.

---

## Gotcha 3: Capacity Belongs to the Presence Configuration, Channels to the Presence Status

**What happens:** Administrators design a "Chat Only" status with a lower capacity than an "All Channels" status, expecting the agent's ceiling to drop when they switch. It does not: capacity is a Required field on the presence configuration (`PresenceUserConfig.capacity`), which is assigned to profiles or users (api_meta 264 L99781-99786); a presence status holds only its label and its channels (`ServicePresenceStatus.channels`, L110740-110742). Switching status changes which channels the agent receives, not their ceiling. Earlier text said capacity is "per-status" and depends on the active status; the two metadata types contradict that.

**When it occurs:** In orgs that model working modes as statuses and expect each mode to carry its own capacity.

**How to avoid:** Put a different ceiling on a different presence configuration and a different set of users or profiles. Use statuses only to choose channels. Name Presence Configurations so their capacity is clear (e.g., "Support Agent - Full Capacity (10)"). UNVERIFIED (2026-10-21): what happens when one user is listed in two presence configurations.

---

## Gotcha 4: Deactivating a Service Resource Does Not Close Open Work Items

**What happens:** When an agent's Service Resource record is deactivated (Active = false), the agent stops receiving new work items. However, any work items already assigned to that agent remain assigned. They are not automatically re-queued or reassigned. If the agent is off sick and their Service Resource is deactivated, their assigned cases stay with them until manually reassigned. UNVERIFIED (2026-10-21): the routing effect of `IsActive` = false; the object reference describes the flag only for work-order assignment and says resources "can't be deleted, so deactivating a resource is the best way to send them into retirement" (object_reference 264 L262603-262610).

**When it occurs:** During offboarding, extended leave, or when reorganizing teams and deactivating old Service Resources before creating new ones.

**How to avoid:** Before deactivating a Service Resource, use the Omni-Channel Supervisor or a SOQL query to identify and manually reassign any open work items assigned to that agent. Consider building a Flow or process that re-queues work items when a Service Resource is deactivated, rather than leaving them stranded.

---

## Gotcha 5: Push Timeout Declines Do Not Always Re-Queue Immediately

**What happens:** When a work item is pushed to an agent and the push timeout expires (the agent does not accept within the configured seconds), the item is expected to route to the next available agent. In practice, if the org's routing queue is heavily loaded or all agents are at capacity, the item may sit for a variable period between the timeout and re-routing. This can create misleading metrics where "push timeout" events appear short but actual customer wait times are much longer.

**When it occurs:** During peak volume periods when all agents are near capacity. Also occurs when routing configurations have very short push timeouts (under 10 seconds) and high agent counts, causing a rapid chain of push-and-timeout events that delays actual assignment.

UNVERIFIED (2026-10-21): the re-routing delay is a field observation; the guide only defines `pushTimeout` in seconds with 0 meaning off (api_meta 264 L102698-102699) and `presenceStatusOnPushTimeout` as the status the agent is moved to after a timeout (L99845-99846).

**How to avoid:** Set push timeout values that reflect realistic agent response times — 30 seconds is a common baseline for case routing. Do not set push timeouts below 10 seconds (both figures are this skill's heuristics, not guide values). Monitor the gap between "entered queue" timestamp and "accepted" timestamp in Omni-Channel reporting to detect systemic re-queuing delays rather than relying on push timeout alone.

---

## Gotcha 6: Skills-Based Routing Requires a Separate Feature Enable — It Is Not Part of Basic Omni-Channel

**What happens:** Administrators enable Omni-Channel and expect Skills-Based Routing to be available immediately. Skills-based routing is a separate setting, `OmniChannelSettings.enableOmniSkillsRouting`, default false (api_meta 264 L126605-126606), distinct from `enableOmniChannel` (L126598-126600). Skills-based is not a routing-model value: the enum is `LEAST_ACTIVE`, `MOST_AVAILABLE`, `EXTERNAL_ROUTING`, and skills-based use is the routing configuration's `isAttributeBased` flag (L102674-102675, L102706-102710). Earlier text said a "Skills-Based" routing model appears in the dropdown once enabled; the enum has no such value. UNVERIFIED (2026-10-21): how the Setup page shows the skills-based option.

**When it occurs:** During initial skills-based routing setup or when migrating an existing queue-based org to skills-based routing.

**How to avoid:** In Omni-Channel Settings, confirm both "Enable Omni-Channel" and "Enable Skills-Based Routing" are checked before creating Routing Configurations with `isAttributeBased` = true. Document both enables in deployment runbooks.
