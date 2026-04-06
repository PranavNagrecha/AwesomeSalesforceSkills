# Examples — Omni-Channel Capacity Model

## Example 1: Multi-Channel Contact Center with Weighted Capacity

**Context:** A financial services company runs a contact center with 50 agents handling cases (email), live chat, and inbound phone calls through Omni-Channel. Agents currently use tab-based capacity (1 unit per item) and complain about being assigned a phone call while already on two chats.

**Problem:** Tab-based capacity treats all work items equally. An agent with 3 open tabs (2 chats + 1 phone call) appears to have the same load as an agent with 3 open cases, even though a phone call demands full attention.

**Solution:**

```text
Presence Configuration: "Standard Agent"
  Total Capacity: 10

Service Channel Weights:
  Voice:     10 units  (fully occupies agent)
  Case:       5 units  (moderate effort, async)
  Chat:       3 units  (real-time, concurrent OK)
  Messaging:  3 units  (real-time, concurrent OK)

Interruptible Channels: Case, Messaging
Non-Interruptible Channels: Voice, Chat

Result scenarios for an agent with capacity 10:
  - 1 Voice call = 10/10 (full, no more work routed)
  - 2 Chats = 6/10 (room for 1 more chat but not a case)
  - 1 Case + 1 Chat = 8/10 (room for nothing at weight 3+)
  - 2 Cases = 10/10 (full)
```

**Why it works:** Weighted capacity prevents the platform from stacking a phone call on top of active chats. The agent's capacity is consumed proportionally to real effort, and voice calls fill the entire budget so no concurrent work is assigned.

---

## Example 2: Skills Matrix with Overflow for Insurance Claims

**Context:** An insurance company has three specialized queues: Auto Claims, Home Claims, and General Inquiries. Each queue has 10 dedicated agents. During storm season, Home Claims volume triples and the dedicated team cannot keep up.

**Problem:** Without overflow, Home Claims queue wait times spike to 30+ minutes while Auto Claims agents sit at 40% utilization.

**Solution:**

```text
Skills Setup:
  Skill: "Auto Claims"    -> assigned to 10 Auto agents + 5 cross-trained General agents
  Skill: "Home Claims"    -> assigned to 10 Home agents + 5 cross-trained General agents
  Skill: "General Support" -> assigned to all 30 agents

Routing Configuration (Primary):
  Queue: Home Claims Queue
  Routing Model: Most Available
  Required Skill: "Home Claims"
  Priority: 1

Routing Configuration (Secondary / Overflow):
  Queue: Home Claims Overflow Queue
  Routing Model: Most Available
  Required Skill: "General Support"
  Priority: 2
  Activation: After 90-second timeout on primary queue

Monitoring:
  - Weekly overflow rate report
  - Alert if overflow exceeds 20% of total Home Claims volume
  - Cross-training plan triggered when overflow exceeds 15% for 2 consecutive weeks
```

**Why it works:** Primary routing tries the specialist pool first. If no Home Claims agent has capacity within 90 seconds, the item overflows to the General Support pool. Cross-trained agents handle the overflow while specialists focus on the highest-complexity items.

---

## Anti-Pattern: Flat Capacity Across All Channels

**What practitioners do:** Set all Service Channel weights to 1 and give agents a capacity of 5, thinking "5 concurrent items is reasonable."

**What goes wrong:** An agent ends up with 1 phone call + 2 chats + 2 cases simultaneously. The phone call demands full attention, so chats go unanswered and customer satisfaction drops. Meanwhile, the system sees the agent at 5/5 capacity and routes the next phone call to a different agent who may also be juggling multiple items.

**Correct approach:** Use differentiated weights that reflect actual agent effort. A phone call should consume all or nearly all capacity. Chats should consume moderate capacity. Cases should consume a middle range since they require focus but are not real-time. Start with Voice=10, Case=5, Chat=3 and adjust from measured handle times.
