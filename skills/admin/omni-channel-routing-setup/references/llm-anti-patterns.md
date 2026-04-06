# LLM Anti-Patterns — Omni-Channel Routing Setup

Common mistakes AI coding assistants make when generating or advising on Omni-Channel routing setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating User Records as Service Resources

**What the LLM generates:** "To configure Omni-Channel routing, just assign agents to the queue. Salesforce will automatically route work to users in the queue based on their availability."

**Why it happens:** LLMs conflate Salesforce queue membership (which uses User records) with Omni-Channel's routing model (which uses Service Resource records). The concept of a separate Service Resource entity is not prominent in general Salesforce documentation and is frequently omitted.

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

**Detection hint:** Any Omni-Channel setup instruction that only mentions "add users to queue" without mentioning Service Resource creation is likely missing this step.

---

## Anti-Pattern 2: Claiming Skills-Based Routing Is Enabled by Default with Omni-Channel

**What the LLM generates:** "Enable Omni-Channel in Service Setup, then create a Routing Configuration with Routing Model = Skills-Based to start routing by agent skills."

**Why it happens:** LLMs see that Skills-Based Routing is part of the Omni-Channel framework and assume it shares the same enable toggle. The separate "Enable Skills-Based Routing" checkbox in Omni-Channel Settings is not obvious from the feature name.

**Correct pattern:**

```text
Skills-Based Routing requires TWO separate enables:
1. Service Setup > Omni-Channel Settings > Enable Omni-Channel (checkmark)
2. Service Setup > Omni-Channel Settings > Enable Skills-Based Routing (separate checkmark)

If only step 1 is completed, the "Skills-Based" option does NOT appear
in the Routing Model picklist on Routing Configuration records.
```

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
  - Push/accept timeout and re-routing on decline

The correct approach:
1. Use assignment rules or Flow to place the Case into the correct Queue
2. Let Omni-Channel's Routing Configuration push the case to an available agent
3. Never set OwnerId directly to a User in a routing trigger
```

**Detection hint:** Any Apex code that sets `Case.OwnerId` to a User Id (not a Queue Id) inside a trigger for routing purposes is likely bypassing Omni-Channel.

---

## Anti-Pattern 4: Configuring a Single Presence Status for All Channels Without Separate Channel Controls

**What the LLM generates:** "Create one Presence Status called 'Available' and assign it to the Presence Configuration. Agents select it to receive all work."

**Why it happens:** LLMs simplify the model to a single on/off availability toggle, missing the design intent of Presence Statuses: they allow agents to be available for specific channel subsets (e.g., "Available - Chat Only" vs "Available - All Channels").

**Correct pattern:**

```text
Design Presence Statuses to reflect real agent working modes:
  - "Available - All Channels"   → Presence Config with Case + Chat + Voice
  - "Available - Chat Only"      → Presence Config with Chat only (lower capacity ceiling)
  - "Available - Cases Only"     → Presence Config with Case only
  - "Break"                      → No service channels (no work pushed)
  - "Training"                   → No service channels

Each status maps to a Presence Configuration that specifies:
  - Which Service Channels the agent receives
  - The capacity ceiling for that working mode

Using a single "Available" status prevents agents from controlling
which work types they receive, and prevents supervisors from
understanding actual agent availability by channel.
```

**Detection hint:** A Presence Status setup that lists only "Available" and "Offline" with all channels in one configuration is missing the channel-specific availability design.

---

## Anti-Pattern 5: Assuming Routing Configuration Priority Is Lowest-Wins Globally Across All Queues

**What the LLM generates:** "Set Routing Priority = 1 on your most important queue so it gets agents first. Set less important queues to higher numbers."

**Why it happens:** The description is partially correct — lower numbers are higher priority — but LLMs miss the scoping: Routing Configuration priority determines relative priority only within the same agent's work queue, not globally across all agents in the org. An agent receiving work from two queues will receive items from the priority 1 queue first, but this does not mean that queue steals agents from other queues.

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

**What the LLM generates:** A complete Omni-Channel setup walkthrough that creates Routing Configurations with no mention of Push Timeout or Accept Timeout settings, implying defaults are sufficient.

**Why it happens:** Push Timeout and Accept Timeout are less prominently featured in Omni-Channel documentation than the routing model itself. LLMs frequently omit them because they seem like edge-case tuning rather than essential configuration.

**Correct pattern:**

```text
Always configure Push Timeout and Accept Timeout on every Routing Configuration:
  - Push Timeout: seconds before a pushed work item is considered declined
    if the agent does not click Accept. Recommended baseline: 30 seconds.
  - Accept Timeout: seconds after Accept before the work is considered
    abandoned (used for some channel types).

Without explicit Push Timeout:
  - The default is 0 seconds in some releases, meaning items time out immediately
  - Or the default is a very long value, meaning stuck items block agent capacity
    for minutes without re-routing

Always set Push Timeout explicitly. Do not rely on platform defaults.
```

**Detection hint:** Any Routing Configuration setup guidance that does not mention Push Timeout values is incomplete.
