# Examples — Multi Channel Service Architecture

## Example 1: Greenfield Five-Channel Deployment for Financial Services

**Context:** A mid-size bank is launching Service Cloud with phone, email, chat, SMS, and social channels. They have 200 agents and expect 60% phone volume, 25% email, 10% chat, 3% SMS, and 2% social.

**Problem:** Without a unified architecture, each channel team independently configures routing. Phone agents sit idle during low-call periods while chat queues overflow. Email cases are not visible to agents handling phone calls from the same customer, creating a fragmented experience.

**Solution:**

```text
Channel Architecture:
  Phone  -> Service Cloud Voice (Amazon Connect) -> VoiceCall -> Case
  Email  -> Email-to-Case (on-demand)            -> Case (direct)
  Chat   -> Messaging for In-App/Web             -> MessagingSession -> Case
  SMS    -> Messaging (SMS number)                -> MessagingSession -> Case
  Social -> Social Customer Service               -> Case (direct)

Omni-Channel Configuration:
  Routing: Skills-based routing
  Queues: Organized by topic (Account Issues, Loan Support, Card Services)
  Capacity: Agent total = 100 units
    - VoiceCall weight: 100 (1 call = full capacity)
    - MessagingSession weight: 25 (up to 4 concurrent chats/SMS)
    - Case (email) weight: 10 (background work alongside other channels)
    - Case (social) weight: 20 (similar to chat but may need more context)
```

**Why it works:** Topic-based queues ensure any agent with the right skills can serve any channel. Capacity weights let agents handle email cases while waiting for calls, maximizing utilization. Every interaction links to Case, so the full customer history is visible regardless of channel.

---

## Example 2: Live Agent to Messaging Migration for Retail

**Context:** A retail company has been using Live Agent for 3 years with 50 agents. They have custom reports on `LiveChatTranscript`, a Flow that assigns chats based on department, and a Lightning component showing chat history.

**Problem:** Live Agent is legacy. The company wants persistent conversations (customer can leave and return to the same thread) and asynchronous messaging, which only Messaging for In-App/Web supports.

**Solution:**

```text
Migration Plan (8-week phased approach):

Week 1-2: Sandbox setup
  - Deploy Messaging for In-App/Web in sandbox
  - Configure Embedded Service with Messaging channel
  - Map existing Live Agent routing to Messaging routing rules
  - Create new Service Channel for MessagingSession with weight = 25

Week 3-4: Parallel running in production
  - Deploy Messaging channel in production alongside Live Agent
  - Route 10% of web traffic to Messaging (A/B by page)
  - Monitor: agent handle time, CSAT, routing accuracy

Week 5-6: Expand and migrate reports
  - Route 50% of traffic to Messaging
  - Rebuild reports: LiveChatTranscript -> MessagingSession
  - Update Flow: replace Live Agent references with Messaging objects
  - Update Lightning component to show MessagingSession history

Week 7-8: Complete cutover
  - Route 100% of traffic to Messaging
  - Disable Live Agent chat buttons
  - Decommission Live Agent configuration
  - Archive LiveChatTranscript historical data (read-only)
```

**Why it works:** The phased approach catches broken automations and report references early when only 10% of traffic is affected. Running both channels concurrently ensures no service disruption during migration.

---

## Anti-Pattern: Channel-Siloed Queue Design

**What practitioners do:** Create separate Omni-Channel queues per channel: "Phone Queue," "Chat Queue," "Email Queue." Agents are assigned to a single channel queue.

**What goes wrong:** During peak phone hours, phone agents are overwhelmed while chat agents are idle. There is no cross-channel load balancing. When call volume drops in the evening, phone agents have nothing to do while email cases pile up in a separate queue. Agent utilization swings wildly.

**Correct approach:** Organize queues by topic or skill (Billing, Technical Support, Returns) and let Omni-Channel capacity weights control how many of each channel type an agent can handle simultaneously. A "Billing" agent can receive a billing phone call, a billing chat, and a billing email — the capacity weights ensure they are not overloaded.

---

## Example 3: Capacity Calibration Queries and a Worked Routing Decision Record

**Context:** An insurer runs Service Cloud Voice, Email-to-Case, and Messaging for In-App and Web with 120 blended agents. Agents complain of being overloaded with email cases; customers wait on the phone while agents work email.

**Step 1: measure.** `AgentWork` records every routed item with its channel, capacity, and timings.

```soql
-- Q1. Handle time and speed to answer per service channel, last 30 days
SELECT ServiceChannelId, COUNT(Id) items, AVG(HandleTime) avgHandleSecs,
       AVG(SpeedToAnswer) avgSpeedSecs
FROM AgentWork
WHERE Status = 'Closed' AND CreatedDate = LAST_N_DAYS:30
GROUP BY ServiceChannelId

-- Q2. Capacity actually consumed per item, by channel (shows mis-set weights)
SELECT ServiceChannelId, CapacityWeight, CapacityPercentage, COUNT(Id) items
FROM AgentWork
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY ServiceChannelId, CapacityWeight, CapacityPercentage

-- Q3. Inbound volume by case origin (email, web, phone) for the same window
SELECT Origin, COUNT(Id) cases
FROM Case
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY Origin
```

`HandleTime` is close time minus accept time and stops at the end of after-conversation work; `ActiveTime` exists only for the tab-based capacity model, so compare channels on `HandleTime`. UNVERIFIED (2026-10-03): averaging `HandleTime` and `SpeedToAnswer` in SOQL assumes both are aggregatable numeric fields as documented (int, groupable); confirm with a test query.

**Step 2: the decision record** at `docs/adr/0121-omni-channel-capacity-and-priority.md`. It changes routing metadata only; the member forms for the release manifest follow the record.

```markdown
# ADR-0121: Status-based capacity for email; voice first by routing priority

## Status
Accepted (2026-10-03), Contact Centre Design Authority

## Context
- Q1: voice handle 410 s; messaging 690 s across ~3 concurrent
  sessions; email 1,250 s per case, often reopened next day.
- Q2: email cases run at weight 10 on a TAB_BASED channel. Agents close
  tabs on unfinished cases, freeing capacity and pulling more email.
- Voice must consume 100% of capacity (Metadata API, QueueRoutingConfig);
  an agent on a call takes no other work.
- Priority across channels is routingPriority; lower routes first.
- Email-to-Case overEmailLimitAction is Discard today.

## Decision
1. Email case service channel: capacityModel = STATUS_BASED; status
   mappings New/Working = IN_PROGRESS, Waiting on Customer = PAUSED,
   Closed = COMPLETED. Paused capacity 0.25 of the normal weight.
2. Routing priority: Voice 0, Messaging 1, Email 2.
3. Capacity: agent total 100; messaging 30; email 20 (was 10).
4. overEmailLimitAction = Requeue.
5. Presence statuses: Available - All; Available - Digital Only.

## Consequences
### Positive
- Capacity reflects unfinished email; calls reach agents first.
### Negative
- Email throughput per agent drops; backlog visible on the dashboard.
- Paused capacity requires Enhanced Omni-Channel and status-based
  capacity; both must stay enabled.
- Two presence statuses for agents to manage.

## Alternatives Considered
### Keep tab-based capacity and raise the email weight to 35
Rejected: still frees capacity when a tab closes on unfinished work.
### Separate voice-only and digital-only agent pools
Rejected for now: 120 agents is too few to split without longer waits.

## Date
2026-10-03
```

**Release manifest members** (types and file locations from the Metadata API; member names are this org's):

| Component | Type | `package.xml` member form |
|---|---|---|
| Email case service channel | `ServiceChannel` | `<members>Email_Case</members><name>ServiceChannel</name>` |
| Voice, messaging, and email routing configurations | `QueueRoutingConfig` | `<members>Voice_Routing</members><name>QueueRoutingConfig</name>` |
| Presence statuses | `ServicePresenceStatus` | `<members>Available_Digital_Only</members><name>ServicePresenceStatus</name>` |
| Agent capacity | `PresenceUserConfig` | `<members>Blended_Agents</members><name>PresenceUserConfig</name>` |
| Email-to-Case limit behavior | `CaseSettings` (settings type) | `<members>Case</members><name>Settings</name>` |

The `Case` member under `Settings` is grounded: CaseSettings "values are stored in the Case.settings file", and settings types "are accessed using the Settings name" in the manifest (Metadata API v67.0).

**Why it works:** the measurements point at the real fault (capacity released on unfinished work), every change maps to a documented field, and the record states its costs.

