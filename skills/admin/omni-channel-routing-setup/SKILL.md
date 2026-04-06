---
name: omni-channel-routing-setup
description: "Configuring Salesforce Omni-Channel routing from scratch or updating existing routing: enabling Omni-Channel, creating Service Channels, configuring Routing Configurations (queue-based and skills-based), setting up Presence Statuses and Presence Configurations, assigning skills to Service Resources, and defining Skills-Based Routing Rules. Trigger keywords: Omni-Channel setup, routing configuration, queue-based routing, skills-based routing, presence status, service channel, routing rules. NOT for capacity model design (use omni-channel-capacity-model). NOT for OmniStudio FlexCards or DataRaptors. NOT for Omni-Channel Supervisor dashboard analysis."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
triggers:
  - "how do I set up Omni-Channel routing in Service Cloud for the first time"
  - "agents are not receiving work items — Omni-Channel is enabled but nothing is routing"
  - "how do I configure skills-based routing so cases go to agents with matching product expertise"
  - "what is the difference between queue-based and skills-based routing in Omni-Channel"
  - "how do I create presence statuses and presence configurations for my support team"
tags:
  - omni-channel
  - routing-configuration
  - queue-based-routing
  - skills-based-routing
  - presence-status
  - service-channel
  - service-resource
  - routing-rules
inputs:
  - List of service channels to enable (Case, Chat, Voice, Messaging, custom objects)
  - Routing model decision (queue-based vs skills-based)
  - Agent skills and competency levels (for skills-based routing)
  - Queue structure and queue membership
  - Required work acceptance timeout and push timeout values
  - Agent working modes and presence statuses needed
outputs:
  - Omni-Channel Service Channel configuration per object
  - Routing Configuration records (queue-based or skills-based)
  - Presence Status and Presence Configuration design
  - Skills, Skill Levels, and Service Resource skill assignments (skills-based only)
  - Skills-Based Routing Rules (skills-based only)
  - Queue-to-Routing Configuration mapping
  - Validated Omni-Channel setup checklist
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Omni-Channel Routing Setup

This skill activates when an administrator needs to configure Salesforce Omni-Channel end-to-end — from enabling the feature to creating Service Channels, Routing Configurations, Presence Statuses, and (for skills-based routing) Skills objects, Service Resource skill assignments, and Skills-Based Routing Rules. It covers initial setup and changes to existing routing configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Omni-Channel must be explicitly enabled.** Navigate to Service Setup > Omni-Channel Settings and turn on Omni-Channel. This is a one-way switch — it cannot be disabled once enabled in production. Confirm the org's Service Cloud license level, as some features (Enhanced Omni-Channel, Skills-Based Routing) require an add-on or specific license tier.
- **The most common wrong assumption is that enabling Omni-Channel automatically routes work.** Enabling the feature only activates the framework. Work items do not route until a Service Channel is created for the object, a Routing Configuration is created and associated with a queue, and at least one Presence Configuration allows that channel.
- **Platform limits:** A Routing Configuration can be associated with only one queue at a time. Skills-Based Routing requires the Skills-Based Routing feature to be enabled separately under Omni-Channel Settings (distinct from enabling basic Omni-Channel). Service Resources must be created for each agent — simply having a user account is not sufficient.

---

## Core Concepts

### Queue-Based Routing

Queue-based routing assigns work from a Salesforce queue to the next available agent. Two assignment algorithms are available:

- **Least Active**: routes the new work item to the agent with the fewest open work items (lowest active count). Best when work items vary widely in effort and you want to equalize agent workloads.
- **Most Available**: routes to the agent who has the most remaining capacity (highest percentage of unused capacity). Best when work items are relatively uniform in effort and you want strict capacity balancing.

The Routing Configuration record ties these settings together. Each Routing Configuration specifies the routing model, the priority (lower numbers = higher priority), capacity weight per work item, and push and accept timeout values. The Routing Configuration is then assigned to a queue. Work placed in that queue is routed according to those settings.

### Skills-Based Routing

Skills-Based Routing matches work items to agents based on required skills rather than queue membership. The setup requires several interdependent objects:

1. **Skills** — named competencies (e.g., "Billing Support", "Spanish Language", "Technical Tier 2")
2. **Skill Levels** — optional numeric levels within a skill (1–10 scale) indicating proficiency
3. **Service Resources** — agent representations in the routing engine; one Service Resource per user who receives routed work
4. **Service Resource Skills** — junction records assigning specific Skills (with optional levels) to Service Resources
5. **Skills-Based Routing Rules** — criteria that evaluate incoming work item fields and specify required skills and minimum skill levels for routing

When work arrives, the routing engine evaluates the Skills-Based Routing Rules against the work item's field values, determines the required skills, and routes to the Service Resource who matches those skills and has available capacity.

### Presence Statuses and Presence Configurations

Presence Statuses are the named availability states agents select in the Omni-Channel utility bar widget (e.g., "Available", "Available - Chat Only", "Break", "Training"). Each Presence Status is linked to a Presence Configuration, which defines:

- The total capacity ceiling for the agent in that state
- Which Service Channels the agent can receive in that state

Presence Statuses must be enabled per Service Channel. An agent will not receive work from a Service Channel unless their active Presence Status is associated with a Presence Configuration that includes that channel. This is the key mechanism for controlling which work types agents receive at any given time.

Agents must be explicitly added to Presence Configurations (via profiles or permission sets). Forgetting this step is the most common reason agents appear online but receive no work.

### Service Channels

A Service Channel is the bridge between a Salesforce object (Case, Chat Transcript, Messaging Session, Voice Call, or a custom object) and the Omni-Channel routing engine. Creating a Service Channel for an object tells Omni-Channel to manage routing for that object type. The Service Channel also sets the capacity weight — the number of capacity units one work item of this type consumes from an agent's total capacity.

---

## Common Patterns

### Pattern: Queue-Based Routing for a Multi-Queue Support Org

**When to use:** The org has distinct support queues (e.g., Tier 1 General, Tier 2 Technical, Billing) and agents are pre-assigned to queues by skillset. Work volume is the primary routing concern, not individual agent competencies.

**How it works:**

1. Enable Omni-Channel and create a Service Channel for Case (Object: Case).
2. For each queue (Tier 1, Tier 2, Billing), create a Routing Configuration:
   - Set Routing Priority (1 = highest): Tier 2 = 1, Billing = 2, Tier 1 = 3
   - Set Routing Model: Least Active (recommended for case queues with variable effort)
   - Set Units of Capacity: 5 (standard for cases)
3. Associate each Routing Configuration with its corresponding queue (Queue > Edit > Routing Configuration field).
4. Create Presence Statuses: "Available - Cases", "Break", "Training".
5. Create a Presence Configuration with capacity 10, Case channel enabled. Assign to all case agents via Profile.
6. Add agents to the relevant queues. Confirm Service Resources exist for each agent.

**Why not the alternative:** Without per-queue Routing Configurations with different priorities, all queues compete equally for agents. High-priority escalations end up behind routine requests in the same pool.

### Pattern: Skills-Based Routing for Product-Specialist Matching

**When to use:** Customers contact support about different product lines and need to reach an agent with matching product expertise. Queue membership alone cannot express this — the same agent might support Products A and B but not C.

**How it works:**

1. Enable Omni-Channel and enable Skills-Based Routing in Omni-Channel Settings.
2. Create Service Channel for Case.
3. Create Skills: "Product A Support", "Product B Support", "Product C Support".
4. Create a Service Resource for each agent. Set Type = Agent.
5. Assign Service Resource Skills: each agent gets the Skills matching their expertise. Optionally set skill levels (1–5 scale: 1 = basic, 5 = expert).
6. Create Skills-Based Routing Rules:
   - Rule Name: "Route by Product Line"
   - Criteria: Case.Product_Line__c (picklist field)
   - For each picklist value, specify the Required Skill and minimum Skill Level
7. Create a Routing Configuration with Routing Model = Skills-Based. Assign to the inbound Case queue.
8. Configure Presence Status "Available - Cases" with the Case Service Channel.

**Why not the alternative:** Using separate queues per product line requires agents to manually monitor multiple queues or be assigned to all of them, which defeats the purpose. Skills-Based Routing lets one agent receive work from a single queue while the engine dynamically matches them to the right items.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple org with 1–2 queues and agents handle all work types | Queue-based routing, Least Active model | Minimal setup, adequate for uniform workloads |
| Multi-channel org where voice calls need priority over chats | Queue-based routing with priority levels per Routing Configuration | Priority routing ensures voice beats lower-priority channels |
| Agents have distinct expertise that matters for resolution quality | Skills-Based Routing with required skills on routing rules | Queue-based routing cannot express per-agent competency matching |
| High volume with occasional specialist overflow | Queue-based primary + Skills-Based secondary with fallback rules | Handles normal load without specialist bottlenecks |
| Pilot or first-time Omni-Channel deployment | Queue-based routing first, then layer in Skills-Based later | Skills-Based has more prerequisites; queue-based validates the base plumbing |

---

## Recommended Workflow

Step-by-step instructions for configuring Omni-Channel routing:

1. **Enable Omni-Channel and determine the routing model.** Go to Service Setup > Omni-Channel Settings > Enable Omni-Channel. Decide upfront: queue-based or skills-based. If skills-based, also enable Skills-Based Routing on the same settings page. Document the decision and the reasons — this choice shapes all subsequent configuration steps.
2. **Create Service Channels.** For each object type that will be routed (Case, Chat Transcript, Messaging Session, Voice Call, custom), create a Service Channel record under Omni-Channel > Service Channels. Set the Salesforce Object and the capacity weight (default: Case = 5, Chat = 3, Voice = 10). Do not skip this step — work items from objects without a Service Channel will never enter the routing engine.
3. **Create Routing Configurations.** For queue-based routing: create one Routing Configuration per queue. Set Routing Priority, Routing Model (Least Active or Most Available), Units of Capacity, and Timeout settings. For skills-based routing: create Routing Configuration(s) with Routing Model = Skills-Based. Assign each Routing Configuration to its target queue via the Queue edit page.
4. **Configure Presence Statuses and Presence Configurations.** Create named Presence Statuses that reflect real agent working modes. Create Presence Configurations with the appropriate capacity ceiling and the Service Channels agents should receive in each state. Assign agents to Presence Configurations via their Profiles or Permission Sets. Confirm assignments before going live.
5. **For skills-based routing: Create Skills, Service Resources, and assign Service Resource Skills.** Create Skill records for each competency. Create a Service Resource record for every agent who will receive routed work (Service Resource Type = Agent, link to User). Assign Service Resource Skills — be precise about skill levels, as the routing engine filters by minimum level.
6. **For skills-based routing: Create Skills-Based Routing Rules.** Define criteria that match incoming work item field values to required skills. Test the rules using the Omni-Channel test utilities or by creating test work items in a sandbox. Verify the correct skill is being required for each scenario.
7. **Validate and test before go-live.** In a sandbox: log in as a test agent, set an Available presence status, create a test Case or Chat that matches a routing rule, and confirm the work item appears in the agent's Omni-Channel widget. Check the Omni-Channel Supervisor tab to confirm the agent shows as Available and that the work item shows routing status. Fix any gap (missing Service Resource, Presence Configuration not assigned, routing rule mismatch) before enabling in production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Omni-Channel is enabled; Skills-Based Routing enabled if using skills model
- [ ] Service Channel exists for every object type being routed
- [ ] Routing Configuration created for every queue that routes through Omni-Channel
- [ ] Each Routing Configuration is assigned to its target queue
- [ ] Presence Statuses created for all real agent working modes
- [ ] Presence Configurations include the correct Service Channels and capacity ceiling
- [ ] Agents are assigned to Presence Configurations via Profile or Permission Set
- [ ] Service Resource records exist for every routing agent (skills-based: with skill assignments)
- [ ] Skills-Based Routing Rules validated against real work item field values (skills-based only)
- [ ] End-to-end routing tested in sandbox before production deployment
- [ ] Omni-Channel Supervisor shows agents as Available and work items routing correctly

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Enabling Omni-Channel routes nothing automatically** — Simply turning on Omni-Channel in settings does not route any work. Every object needs a Service Channel, every queue needs a Routing Configuration, and every agent needs a Presence Configuration assignment. A common failure mode is enabling Omni-Channel in production without all three legs in place and then wondering why no work is flowing.
2. **Service Resources must be created manually** — A Salesforce User account does not automatically generate a Service Resource. Every agent who receives routed work needs an explicit Service Resource record (Setup > Service Resources > New, Type = Agent). If a Service Resource is missing, that agent is invisible to the routing engine regardless of their Presence Status.
3. **Presence Configuration assignments are not retroactive** — Assigning an agent to a Presence Configuration via their Profile applies to their next login. Agents currently logged in to Omni-Channel do not pick up Presence Configuration changes until they go offline and back online. During transitions or configuration changes, instruct agents to cycle their presence.
4. **Skills-Based Routing Rules require exact field API names** — Routing Rule criteria reference field API names, not field labels. A mismatch between the rule's configured field reference and the actual field API name silently fails to match, and work items fall back to the default routing behavior (or sit unrouted). Always verify field API names in Object Manager before configuring rules.
5. **Queue-based and Skills-Based Routing Configurations are mutually exclusive per queue** — A queue can only have one Routing Configuration assigned at a time. If you want to run both models (e.g., skills-based primary with queue-based fallback), you need two separate queues and two Routing Configurations, with work items moved between queues via automation if the primary fails to route.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Service Channel configuration | One record per routable object type with capacity weight set |
| Routing Configuration records | One per queue, with routing model, priority, and timeout settings documented |
| Presence Status and Configuration design | Named statuses, mapped configurations, capacity ceilings, and channel assignments |
| Service Resource roster | List of agents with confirmed Service Resource records |
| Skills matrix (skills-based only) | Agent-to-skill mapping with skill levels, used to configure Service Resource Skills |
| Skills-Based Routing Rules (skills-based only) | Rule criteria mapped to required skills and minimum levels |
| Validated routing test results | Evidence of end-to-end work item routing in sandbox |

---

## Related Skills

- omni-channel-capacity-model — Use for designing capacity units, channel weights, and overflow strategies once base routing is configured
- multi-channel-service-architecture — Use for overall queue structure and channel strategy decisions that inform routing configuration
- service-cloud-architecture — Use for holistic Service Cloud design including Omni-Channel as a component
