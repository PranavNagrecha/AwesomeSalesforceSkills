# LLM Anti-Patterns — Omni-Channel Capacity Model

Common mistakes AI coding assistants make when generating or advising on Omni-Channel capacity models.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Capacity Units with Concurrent Item Count

**What the LLM generates:** "Set the agent's capacity to 3 so they can handle 3 chats at once."

**Why it happens:** LLMs conflate "capacity" with "number of concurrent items" because many non-Salesforce systems work that way. In Salesforce Omni-Channel, capacity is a unit budget and each channel type consumes a configurable number of units.

**Correct pattern:**

```text
Set the agent's total capacity to 10 (PresenceUserConfig.capacity).
Set the chat routing configuration's weight to 3 units (QueueRoutingConfig.capacityWeight).
Result: the agent can handle up to 3 chats (3 x 3 = 9 units) before capacity is exhausted.
```

**Detection hint:** Look for capacity values that match a small concurrent item count (1-5) without mention of routing configuration weights.

---

## Anti-Pattern 2: Recommending Equal Weights for All Channels

**What the LLM generates:** "Set each Service Channel weight to 1 for simplicity." (The weight is actually on the routing configuration; see Anti-Pattern 5.)

**Why it happens:** LLMs default to the simplest configuration. Equal weights are easy to explain but fail to model the reality that a phone call demands full attention while cases are asynchronous.

**Correct pattern:**

```text
Routing configuration weights should reflect effort:
  Voice:     equal to the agent's total capacity (the platform requires
             voice to use the entire capacity weight, or percentage 100)
  Case:       5 (moderate effort, not real-time)
  Chat:       3 (real-time but concurrent)
  Messaging:  3 (similar to chat)
```

**Detection hint:** All routing configuration weights set to the same value, especially 1.

---

## Anti-Pattern 3: Suggesting Skills-Based Routing Without Overflow Design

**What the LLM generates:** "Create skills for Billing, Technical, and Sales. Assign agents to each skill. Enable Skills-Based Routing."

**Why it happens:** LLMs describe the happy path — skills are assigned, routing works. They omit the failure mode: what happens when no skilled agent is available. Without overflow, work items queue indefinitely.

**Correct pattern:**

```text
1. Create skills: Billing, Technical, Sales
2. Assign primary agents to each skill (minimum 3 per skill)
3. Mark nice-to-have skills as Additional Skill and set
   dropAdditionalSkillsTimeout on the routing configuration, so they drop
   after the wait and the item goes to the best-matched agent
4. For required skills, set an overflow assignee (queueOverflowAssignee or
   userOverflowAssignee) on the routing configuration
5. Monitor overflow rate and cross-train agents when overflow exceeds 15%
```

**Detection hint:** Skills-Based Routing advice that mentions skill creation and assignment but no secondary routing, overflow, or timeout configuration.

---

## Anti-Pattern 4: Marking Voice Channels as Interruptible

**What the LLM generates:** "Mark all channels as interruptible so higher-priority items can always reach agents."

**Why it happens:** LLMs optimize for throughput and see interruptible as a way to maximize agent utilization. They do not account for the fact that a phone call cannot be "paused" — the customer is on the line.

**Correct pattern:**

```text
Interruptible channels (can be paused for higher-priority work):
  - Case
  - Messaging

Non-interruptible channels (cannot be interrupted):
  - Voice (customer is on a live call)
  - Chat (interrupting a live chat causes poor customer experience)
```

**Detection hint:** The word "interruptible" applied to Voice or a blanket "mark all channels as interruptible" recommendation.

---

## Anti-Pattern 5: Ignoring Presence Configuration in Capacity Advice

**What the LLM generates:** "Set the agent's capacity to 10 in their user record" or "Configure capacity in the Service Channel settings."

**Why it happens:** LLMs hallucinate where settings live. The agent's capacity ceiling is on the Presence Configuration, which is assigned to users or profiles directly (`PresenceUserConfig.assignments`). An earlier version of this file said the Service Channel holds the weight and the Presence Status links agents to a configuration; both were wrong.

**Correct pattern:**

```text
Capacity is configured in four places (Metadata API, Version 67.0):
  1. PresenceUserConfig: capacity, interruptibleCapacity; assigned to users or profiles
  2. QueueRoutingConfig: capacityWeight or capacityPercentage per routed work item
  3. ServiceChannel: capacityModel (TAB_BASED or STATUS_BASED) and isInterruptible
  4. ServicePresenceStatus: which channels a status receives (no channels = Away)

The agent's User record does not contain capacity settings.
```

**Detection hint:** References to setting capacity on "the user record" or "the agent profile," or to a weight field on the Service Channel.

---

## Anti-Pattern 6: Proposing Real-Time Capacity Changes Without Mentioning Re-Login

**What the LLM generates:** "Update the Presence Configuration capacity from 10 to 15. The change will take effect immediately for all agents."

**Why it happens:** LLMs assume configuration changes propagate in real time, as they do in most modern SaaS platforms. Each live presence session records its own `ConfiguredCapacity` on `UserServicePresence`. UNVERIFIED (2026-10-03): the statement that configurations update only after the agent logs out and back in is from Salesforce Help, which does not fetch.

**Correct pattern:**

```text
After updating the Presence Configuration capacity value:
  - Agents currently logged in will continue using the OLD capacity
  - Agents must go Offline and back Online to pick up the new value
  - Schedule changes during shift transitions to minimize disruption
  - Verify with UserServicePresence (IsCurrentState = true): ConfiguredCapacity
```

**Detection hint:** Claims that Presence Configuration changes are "immediate," "real-time," or "instant" without mentioning agent re-login.

---

## Anti-Pattern 7: Reassigning Work By Owner Change And Trusting The Capacity Numbers

**What the LLM generates:** "When an agent is overloaded, have the supervisor change the case owner to another agent; Omni-Channel will account for it."

**Why it happens:** Ownership and Omni-Channel assignment look like the same thing in the console.

**Correct pattern:**

```text
"A work item consumes agent capacity only if it was first assigned to the agent
by Omni-Channel using queues or skills" (Object Reference, AgentWork).
- Reassign through a queue or skill so Omni-Channel creates the AgentWork.
- For status-based channels, review ServiceChannel.doesCheckCapOnOwnerChange
  and doesCheckCapOnStatusChange.
- Report on records owned by agents with no matching open AgentWork.
```

**Detection hint:** Advice to fix overload by changing `OwnerId` directly, or flows that assign cases to users without a queue.

