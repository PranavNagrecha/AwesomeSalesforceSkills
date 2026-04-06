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
