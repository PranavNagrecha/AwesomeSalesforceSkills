# LLM Anti-Patterns — Omni-Channel Routing Setup

Common mistakes AI coding assistants make when generating or advising on Omni-Channel routing setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating User Records as Service Resources

**What the LLM generates:** "To configure Omni-Channel routing, just assign agents to the queue. Salesforce will automatically route work to users in the queue based on their availability."

**Why it happens:** LLMs conflate Salesforce queue membership (which uses User records) with Omni-Channel's routing model (which uses Service Resource records). The concept of a separate Service Resource entity is not prominent in general Salesforce documentation and is frequently omitted.

UNVERIFIED (2026-10-21): this anti-pattern holds for skills-based routing, where the agent's skill level sits on `ServiceResourceSkill` (object_reference 264 L263398). For queue-based routing the corpus's presence types reference users and profiles (api_meta 264 L99781-99783), and `ServiceResource` itself requires Field Service or Workforce Engagement (object_reference 264 L262591) — the claim that every queue-based agent needs one is not in the corpus.

**Correct pattern:**

```text
Queue membership alone does not make an agent receivable by Omni-Channel.
Every agent who receives routed work must have a corresponding Service Resource record:
  Setup > Service Resources > New
  Resource Type: Agent
  User: (link to the Salesforce User)
  Active: true

Without a Service Resource, the agent is invisible to the routing engine
even if they are in the queue and have an Available presence status.
```

**Detection hint:** Any skills-based Omni-Channel setup instruction that only mentions "add users to queue" without mentioning Service Resource and Service Resource Skill creation is missing this step; for queue-based setups the step is unverified (see the marker above).

---

## Anti-Pattern 2: Claiming Skills-Based Routing Is Enabled by Default with Omni-Channel

**What the LLM generates:** "Enable Omni-Channel in Service Setup, then create a Routing Configuration with Routing Model = Skills-Based to start routing by agent skills." (Two errors: a missing enable, and a routing-model value that does not exist.)

**Why it happens:** LLMs see that Skills-Based Routing is part of the Omni-Channel framework and assume it shares the same enable toggle. The separate "Enable Skills-Based Routing" checkbox in Omni-Channel Settings is not obvious from the feature name.

**Correct pattern:**

```text
Skills-Based Routing requires TWO separate enables:
1. Enable Omni-Channel            (OmniChannelSettings.enableOmniChannel)
2. Enable Skills-Based Routing    (OmniChannelSettings.enableOmniSkillsRouting)

"Skills-Based" is NOT a routing model. routingModel is LEAST_ACTIVE,
MOST_AVAILABLE or EXTERNAL_ROUTING; a skills-based routing configuration
sets isAttributeBased = true alongside one of those models.
```

Sources: api_meta 264 L126598-126606 (the two settings), L102674-102675 and L102706-102710 (the flag and the enum). The earlier version of this pattern said the "Skills-Based" option appears in the Routing Model picklist once enabled; the enum contradicts that.

**Detection hint:** If a setup guide mentions Skills-Based Routing but only references one Omni-Channel Settings action, it is likely missing the second enable.

---

## Anti-Pattern 3: Recommending Apex Trigger Routing Instead of Omni-Channel Configuration

**What the LLM generates:** An Apex trigger on Case (after insert/update) that queries agent availability and sets `Case.OwnerId` to an agent User record to "route" the case.

**Why it happens:** Apex triggers are a well-known pattern for case assignment. LLMs default to this approach because it appears in many training examples for case routing. The LLM does not recognize that this bypasses Omni-Channel entirely.

**Correct pattern:**

```text
Do NOT use Apex triggers to set Case.OwnerId for Omni-Channel routing.
Setting OwnerId directly assigns the case to the user but bypasses:
  - Omni-Channel capacity enforcement
  - Agent availability checks (the agent may be offline)
  - Omni-Channel Supervisor visibility
  - Push timeout and re-routing on decline
(UNVERIFIED (2026-10-21): the bypass list is Help-only reasoning, not a corpus line.)

The correct approach:
1. Use assignment rules or Flow to place the Case into the correct Queue
2. Let Omni-Channel's Routing Configuration push the case to an available agent
3. Never set OwnerId directly to a User in a routing trigger
```

**Detection hint:** Any Apex code that sets `Case.OwnerId` to a User Id (not a Queue Id) inside a trigger for routing purposes is likely bypassing Omni-Channel.

---

## Anti-Pattern 4: Configuring a Single Presence Status for All Channels Without Separate Channel Controls

**What the LLM generates:** "Create one Presence Status called 'Available' and assign it to the Presence Configuration. Agents select it to receive all work." (Statuses are not assigned to presence configurations at all — see below.)

**Why it happens:** LLMs simplify the model to a single on/off availability toggle, missing the design intent of Presence Statuses: they allow agents to be available for specific channel subsets (e.g., "Available - Chat Only" vs "Available - All Channels").

**Correct pattern:**

```text
Design Presence Statuses to reflect real agent working modes:
  - "Available - All Channels"   → channels: Case + Chat + Voice
  - "Available - Chat Only"      → channels: Chat
  - "Available - Cases Only"     → channels: Case
  - "Break"                      → No service channels (treated as Away)
  - "Training"                   → No service channels

The STATUS carries the channels (ServicePresenceStatus.channels).
The PRESENCE CONFIGURATION carries the capacity ceiling and is
assigned to profiles or users (PresenceUserConfig.capacity, assignments).
A lower ceiling needs a different presence configuration for a
different set of users, not a different status.

Using a single "Available" status prevents agents from controlling
which work types they receive, and prevents supervisors from
understanding actual agent availability by channel.
```

Sources: api_meta 264 L110740-110742 (status channels; none = Away), L99781-99786 (configuration assignments and Required capacity). The earlier version mapped each status to a presence configuration holding channels; the two types contradict that.

**Detection hint:** A Presence Status setup that lists only "Available" and "Offline" with all channels in one configuration is missing the channel-specific availability design; one that puts channels on a presence configuration has the two types swapped.

---

## Anti-Pattern 5: Assuming Routing Configuration Priority Is Lowest-Wins Globally Across All Queues

**What the LLM generates:** "Set Routing Priority = 1 on your most important queue so it gets agents first. Set less important queues to higher numbers."

**Why it happens:** The description is partially correct — lower values route first (api_meta 264 L102712-102715) — but LLMs miss the scoping (UNVERIFIED (2026-10-21): the per-agent scoping below is Help-only): Routing Configuration priority determines relative priority only within the same agent's work queue, not globally across all agents in the org. An agent receiving work from two queues will receive items from the priority 1 queue first, but this does not mean that queue steals agents from other queues.

**Correct pattern:**

```text
Routing Configuration Priority controls the ORDER in which pending work items
are pushed to an individual agent who is eligible to receive from multiple queues.

Priority 1 Routing Config: Escalations queue → pushed first if agent is eligible
Priority 2 Routing Config: Tier 1 queue → pushed second

Priority does NOT:
  - Reserve agents exclusively for higher-priority queues
  - Prevent agents from being assigned to lower-priority queues first
    if no higher-priority work is pending at that moment
  - Create global reservation or agent-locking across the org

For SLA-driven capacity reservation, use dedicated agent groups per queue
and control queue membership, not just routing priority.
```

**Detection hint:** Any claim that routing priority "reserves" agents for a queue or "prevents" lower-priority work from routing is overstating what the Priority field does.

---

## Anti-Pattern 6: Omitting Push Timeout Configuration and Assuming Work Is Always Accepted

**What the LLM generates:** A complete Omni-Channel setup walkthrough that creates Routing Configurations with no mention of Push Timeout, implying defaults are sufficient — or one that invents an "Accept Timeout" field.

**Why it happens:** Push Timeout is less prominently featured in Omni-Channel documentation than the routing model itself. LLMs frequently omit it because it seems like edge-case tuning rather than essential configuration.

**Correct pattern:**

```text
Always configure pushTimeout on every Routing Configuration:
  - pushTimeout: seconds before an unanswered push times out.
    0 means push timeout is NOT enabled (it does not mean "time out at once").
    Recommended baseline (this skill's heuristic): 30 seconds.
  - Pair it with presenceStatusOnPushTimeout on the presence configuration:
    the status the agent is moved to when they do not respond.
  - QueueRoutingConfig has no "accept timeout" field.

Always set pushTimeout explicitly. Do not rely on platform defaults.
```

Sources: api_meta 264 L102698-102699 (pushTimeout, 0 = off), L99845-99846 (presenceStatusOnPushTimeout). The earlier version said a 0 default makes "items time out immediately" and listed an Accept Timeout; the guide contradicts the first and has no field for the second.

**Detection hint:** Any Routing Configuration setup guidance that does not mention Push Timeout values is incomplete.
