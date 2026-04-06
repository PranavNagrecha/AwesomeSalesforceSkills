# LLM Anti-Patterns — Omni-Channel Capacity Model

Common mistakes AI coding assistants make when generating or advising on Omni-Channel capacity models.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Capacity Units with Concurrent Item Count

**What the LLM generates:** "Set the agent's capacity to 3 so they can handle 3 chats at once."

**Why it happens:** LLMs conflate "capacity" with "number of concurrent items" because many non-Salesforce systems work that way. In Salesforce Omni-Channel, capacity is a unit budget and each channel type consumes a configurable number of units.

**Correct pattern:**

```text
Set the agent's total capacity to 10 (via Presence Configuration).
Set the Chat Service Channel weight to 3 units.
Result: the agent can handle up to 3 chats (3 x 3 = 9 units) before capacity is exhausted.
```

**Detection hint:** Look for capacity values that match a small concurrent item count (1-5) without mention of Service Channel weights.

---

## Anti-Pattern 2: Recommending Equal Weights for All Channels

**What the LLM generates:** "Set each Service Channel weight to 1 for simplicity."

**Why it happens:** LLMs default to the simplest configuration. Equal weights are easy to explain but fail to model the reality that a phone call demands full attention while cases are asynchronous.

**Correct pattern:**

```text
Service Channel weights should reflect effort:
  Voice:     10 (fully occupies agent)
  Case:       5 (moderate effort, not real-time)
  Chat:       3 (real-time but concurrent)
  Messaging:  3 (similar to chat)
```

**Detection hint:** All Service Channel weights set to the same value, especially 1.

---

## Anti-Pattern 3: Suggesting Skills-Based Routing Without Overflow Design

**What the LLM generates:** "Create skills for Billing, Technical, and Sales. Assign agents to each skill. Enable Skills-Based Routing."

**Why it happens:** LLMs describe the happy path — skills are assigned, routing works. They omit the failure mode: what happens when no skilled agent is available. Without overflow, work items queue indefinitely.

**Correct pattern:**

```text
1. Create skills: Billing, Technical, Sales
2. Assign primary agents to each skill (minimum 3 per skill)
3. Create secondary routing configuration with relaxed skill requirements
4. Set queue timeout (90 seconds) to trigger overflow to secondary routing
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

**Why it happens:** LLMs hallucinate where settings live. Agent capacity ceiling is not on the User record or the Service Channel — it is on the Presence Configuration, which is linked to agents via Presence Status assignments.

**Correct pattern:**

```text
Capacity is configured in three places:
  1. Presence Configuration: sets the total capacity ceiling for the agent
  2. Service Channel: sets the weight (units consumed) per work item type
  3. Presence Status: links the agent to a Presence Configuration and controls which channels they receive

The agent's User record does not contain capacity settings.
```

**Detection hint:** References to setting capacity on "the user record," "the agent profile," or "the Service Channel capacity field."

---

## Anti-Pattern 6: Proposing Real-Time Capacity Changes Without Mentioning Re-Login

**What the LLM generates:** "Update the Presence Configuration capacity from 10 to 15. The change will take effect immediately for all agents."

**Why it happens:** LLMs assume configuration changes propagate in real time, as they do in most modern SaaS platforms. Salesforce Omni-Channel Presence Configurations only update for an agent when they log out and back in.

**Correct pattern:**

```text
After updating the Presence Configuration capacity value:
  - Agents currently logged in will continue using the OLD capacity
  - Agents must go Offline and back Online to pick up the new value
  - Schedule changes during shift transitions to minimize disruption
```

**Detection hint:** Claims that Presence Configuration changes are "immediate," "real-time," or "instant" without mentioning agent re-login.
