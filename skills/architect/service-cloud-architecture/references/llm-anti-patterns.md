# LLM Anti-Patterns — Service Cloud Architecture

Common mistakes AI coding assistants make when generating or advising on Service Cloud Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Live Agent for New Chat Implementations

**What the LLM generates:** Advice to "set up Live Agent for real-time chat" with configuration steps referencing Live Agent Setup, Chat Buttons, and Chat Deployments.

**Why it happens:** Training data heavily features Live Agent documentation from pre-2022 Salesforce releases. LLMs default to the most frequently seen chat feature name without awareness that Salesforce has replaced it with Messaging for In-App and Web for new implementations.

**Correct pattern:**

```text
For new implementations, use Messaging for In-App and Web (MIAW).
This replaces legacy Live Agent and supports asynchronous conversations,
bot integration, and persistent session history. Live Agent is in
maintenance mode — only existing deployments should continue using it.
```

**Detection hint:** Look for "Live Agent," "Chat Button," "Chat Deployment," or "liveagent" in any recommendation for a new (not migration) implementation.

---

## Anti-Pattern 2: Conflating Queue-Based and Skills-Based Omni-Channel Routing

**What the LLM generates:** Instructions that mix queue-based and skills-based routing concepts — e.g., telling the user to "create a queue and assign skills to it" or "add routing configurations with both queue members and skill requirements."

**Why it happens:** Both routing models use Omni-Channel and share some UI elements (Presence Configurations, Routing Configurations). LLMs merge documentation from both models into a single hybrid that does not exist on the platform.

**Correct pattern:**

```text
Queue-based routing: Create queues, add agents as queue members,
create routing configurations that reference queues, set priority
and capacity per routing configuration.

Skills-based routing: Install the Skills-Based Routing managed package,
define skills, create service resources for agents, assign skills to
service resources, create routing configurations with skill requirements.

These are two distinct models. An org uses one or the other per
routing configuration — they are not mixed within a single
routing flow.
```

**Detection hint:** Look for "queue" and "skill" used together in the same routing configuration step, or instructions to "assign skills to a queue."

---

## Anti-Pattern 3: Suggesting Apex Triggers for Case Routing Instead of Omni-Channel

**What the LLM generates:** An Apex trigger on Case (after insert) that queries agent availability and updates Case.OwnerId to assign cases programmatically, sometimes using custom objects to track agent capacity.

**Why it happens:** LLMs trained on general Apex patterns default to code-first solutions. Building a custom routing engine in Apex is a recognizable pattern from pre-Omni-Channel era Salesforce (before Spring '16) and from non-Salesforce platforms.

**Correct pattern:**

```text
Use Omni-Channel routing for case assignment. Omni-Channel natively
tracks agent capacity, presence status, and routing priority without
custom code. Configure routing via Setup > Omni-Channel > Routing
Configurations. Use Omni-Channel Flow for complex routing logic
that exceeds declarative configuration capabilities.

Custom Apex routing should only be considered for scenarios that
Omni-Channel genuinely cannot handle (extremely rare).
```

**Detection hint:** Look for `trigger` on `Case` with `OwnerId` assignment logic, or custom objects named like `Agent_Capacity__c` or `Routing_Queue__c`.

---

## Anti-Pattern 4: Recommending Knowledge Article Types as Separate Custom Objects

**What the LLM generates:** Instructions to create custom objects like `FAQ__c`, `Troubleshooting_Guide__c`, or `Product_Doc__c` to store different types of knowledge content, with custom lookup relationships to Cases.

**Why it happens:** Older Salesforce documentation (pre-Lightning Knowledge migration) described "Article Types" as separate objects. LLMs trained on this content generate recommendations to create custom objects that replicate what Lightning Knowledge handles natively with record types on the Knowledge (`Knowledge__kav`) object.

**Correct pattern:**

```text
Use Salesforce Knowledge (Knowledge__kav) with record types to
distinguish article types (FAQ, Troubleshooting, Product Documentation).
Each record type can have a distinct page layout, validation rules,
and approval process. Do not create custom objects to store knowledge
content — this bypasses Knowledge search, versioning, data category
visibility, and Experience Cloud publishing.
```

**Detection hint:** Look for custom object creation (`__c` suffix) described as "article types" or "knowledge types," or custom lookup fields from Case to objects other than `Knowledge__kav`.

---

## Anti-Pattern 5: Ignoring Entitlement Processes and Hardcoding SLA Logic in Flow or Apex

**What the LLM generates:** A Flow or Apex class that calculates SLA deadlines by adding hours to `Case.CreatedDate`, stores the deadline in a custom DateTime field, and uses a scheduled Flow to check for violations.

**Why it happens:** Entitlement processes are a specialized Salesforce feature that appears less frequently in training data than Flows and Apex. LLMs default to building SLA tracking from scratch because the general-purpose pattern (calculate deadline, check periodically) is more familiar than the platform-specific solution.

**Correct pattern:**

```text
Use Entitlement Processes with Milestones for SLA tracking.
Milestones natively support:
- Business-hours-aware countdown (pauses outside business hours)
- Milestone actions at configurable thresholds (warn, escalate, violate)
- Pause on specific case statuses (e.g., Waiting on Customer)
- Native reporting via Case Milestone related list and report types

Custom SLA logic in Flow/Apex cannot replicate business-hours-aware
pausing without significant complexity and is a maintenance burden.
```

**Detection hint:** Look for custom DateTime fields like `SLA_Deadline__c` or `Response_Due_By__c`, scheduled Flows that check `Case.CreatedDate` against a deadline, or Apex classes with business hours calculation logic.

---

## Anti-Pattern 6: Generating Service Console Layouts With Excessive Component Count

**What the LLM generates:** A Service Console page layout recommendation that includes 15+ Lightning components: Knowledge sidebar, Omni-Channel widget, Einstein Next Best Action, Case History, Related Lists (5+), custom dashboards, embedded analytics, utility bar with 10+ items, and multiple custom LWC components.

**Why it happens:** LLMs try to be comprehensive and include every relevant feature. They lack awareness that each component consumes browser memory and adds to page load time. The "more is better" bias produces layouts that are technically valid but practically unusable.

**Correct pattern:**

```text
Service Console page layout guidelines:
- Maximum 10 components per page (including standard components)
- Maximum 6-8 utility bar items
- Lazy-load components not needed on initial render
- Avoid synchronous Apex calls on page load
- Use conditional visibility to show components only when relevant
- Test page load time with Chrome DevTools — target under 3 seconds

Start with the minimum viable layout and add components only when
agents report a specific need.
```

**Detection hint:** Count the number of distinct component names in a layout recommendation. If it exceeds 12, flag for review. Look for "utility bar" recommendations with more than 8 items.

---

## Anti-Pattern 7: Advising Direct Amazon Connect Configuration Instead of Service Cloud Voice Setup

**What the LLM generates:** Instructions to configure Amazon Connect directly (create contact flows, configure phone numbers, set up Lambda functions) and then "integrate with Salesforce" using a custom CTI adapter or API calls.

**Why it happens:** Amazon Connect has extensive documentation that LLMs are trained on. The Service Cloud Voice integration layer (which wraps Amazon Connect and provides the Salesforce-native setup experience) is newer and less represented in training data.

**Correct pattern:**

```text
For Salesforce telephony integration using Amazon Connect, use
Service Cloud Voice — not direct Amazon Connect configuration.

Service Cloud Voice provides:
- Guided setup within Salesforce Setup
- Automatic Omni-Channel integration for voice routing
- Real-time call transcription in the Service Console
- Einstein AI recommendations during calls
- Unified agent presence across voice and digital channels

Direct Amazon Connect configuration bypasses these integrations
and creates a disconnected telephony experience.
```

**Detection hint:** Look for Amazon Connect console instructions, Lambda function creation, or CTI adapter installation in a context where Service Cloud Voice would be appropriate.
