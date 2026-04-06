# Examples — Service Cloud Architecture

## Example 1: Mid-Size B2B SaaS — Skills-Based Routing with Language and Product Skills

**Context:** A B2B SaaS company with 120 support agents across three regions (US, EMEA, APAC) supporting four product lines. Agents have varying language capabilities (English, Spanish, French, German, Japanese) and product certifications. Case volume is 8,000 per month with an SLA of 4-hour first response for Premium tier and 24-hour for Standard.

**Problem:** Without skills-based routing, cases were assigned to queues by product line only. Language-mismatched cases bounced between agents 2-3 times before reaching someone who could help, inflating average handle time by 35% and violating SLAs for 12% of Premium cases.

**Solution:**

```text
Routing Configuration:
  - Skills defined: Language (English, Spanish, French, German, Japanese),
    Product (Billing, Analytics, Integration, Core Platform),
    Tier (Premium, Standard)
  - Routing logic:
    1. Match on Language (required) + Product (required) + Tier (preferred)
    2. Timeout after 90 seconds: drop Tier requirement
    3. Timeout after 180 seconds: drop Product requirement
  - Capacity model:
    - Email cases: 8 capacity units per agent
    - Messaging: 4 capacity units per agent
    - Phone (Service Cloud Voice): 1 capacity unit per agent
```

**Why it works:** Skills-based routing eliminates the bounce pattern entirely. The tiered timeout ensures that no case waits indefinitely for a perfect match — it gracefully degrades to any available agent. First-contact resolution improved from 62% to 81%, and SLA compliance went from 88% to 97%.

---

## Example 2: Retail Brand — Messaging-First Channel Migration

**Context:** A retail brand with 2 million customers was running legacy Live Agent chat with 40 agents. Chat sessions averaged 12 minutes, but 60% of that time was customer idle time (browsing, checking order numbers). Agents could handle only 2 concurrent chats due to the synchronous nature of Live Agent.

**Problem:** During peak holiday season, chat queue wait times exceeded 20 minutes. The company was considering doubling its agent headcount — a $1.2M annual cost increase.

**Solution:**

```text
Migration Plan:
  1. Deploy Messaging for In-App and Web to replace Live Agent
  2. Configure Embedded Service deployment on web and mobile app
  3. Deploy Einstein Bot as first responder:
     - Authenticate customer (lookup by email or order number)
     - Attempt self-service: order status, return initiation, FAQ deflection
     - Escalate to human agent with full conversation context
  4. Set agent messaging capacity to 5 concurrent sessions
  5. Implement auto-close Flow: close messaging sessions after
     4 hours of customer inactivity with a "We'll close this for now"
     message and case summary
  6. Track deflection: bot-resolved sessions that never escalated
```

**Why it works:** Messaging's asynchronous model means customers can take 10 minutes between responses without burning agent capacity. Agent concurrency went from 2 (Live Agent) to 5 (Messaging). The Einstein Bot deflected 28% of sessions without human intervention. The company handled 140% more volume with the same 40 agents and avoided the $1.2M headcount increase.

---

## Example 3: Financial Services — Entitlement-Driven SLA Architecture

**Context:** A financial services company with three support tiers: Platinum (1-hour response, 4-hour resolution), Gold (4-hour response, 1-business-day resolution), Standard (1-business-day response, 3-business-day resolution). Each tier is tied to the customer's account level and licensed products.

**Problem:** SLAs were tracked manually in a spreadsheet. Escalations happened when a manager noticed, not when a deadline approached. The company was fined $240K in a single quarter for SLA breaches on Platinum accounts.

**Solution:**

```text
Entitlement Process Design:
  - Three entitlement processes: Platinum, Gold, Standard
  - Each process has two milestones: First Response, Resolution
  - Milestone actions:
    - At 50% elapsed: send warning email to case owner
    - At 75% elapsed: reassign to queue lead, send Slack notification
    - At 90% elapsed: escalate to VP of Support, create Chatter post
    - At 100% (violation): log the violation, notify compliance team
  - Auto-assignment: Entitlement lookup on Case uses Account.Support_Tier__c
    to find the matching Entitlement record
  - Business hours: configured per region (US, EMEA, APAC) with holidays
  - Reporting: custom report type on Cases with Milestones to show
    SLA compliance trends by tier, product, and region
```

**Why it works:** Automated milestone tracking replaced manual spreadsheet management. The escalation ladder at 50/75/90/100% thresholds gives teams multiple opportunities to intervene before a violation. SLA breach rate dropped from 8.3% to 1.1% in the first quarter after go-live.

---

## Anti-Pattern: Routing Everything Through a Single Queue

**What practitioners do:** Create one "Support" queue, add all agents as members, and rely on agents to manually pick cases that match their skills. Sometimes combined with list view sorting by priority.

**What goes wrong:** High-priority cases sit behind low-priority ones if agents cherry-pick easy work. Cases requiring specialized skills get ignored until a manager manually reassigns them. No capacity management — agents can grab 20 cases while others sit idle. There is no data on routing efficiency because everything goes through one queue.

**Correct approach:** Implement Omni-Channel routing (queue-based at minimum, skills-based if agent specialization exists). Define capacity per agent per channel. Use routing configurations to set priority ordering. This gives the platform control over assignment rather than relying on agent behavior, and it generates routing analytics that expose bottlenecks.
