---
name: omni-channel-routing-setup
description: "Configuring Salesforce Omni-Channel routing from scratch or updating existing routing: enabling Omni-Channel, creating Service Channels, configuring Routing Configurations (queue-based and skills-based), setting up Presence Statuses and Presence Configurations, assigning skills to Service Resources, and defining Skills-Based Routing Rules. Trigger keywords: Omni-Channel setup, routing configuration, queue-based routing, skills-based routing, presence status, service channel, routing rules. NOT for agent capacity units and channel weighting — use architect/omni-channel-capacity-model. NOT for Apex routing via PendingServiceRouting — use apex/omni-channel-custom-routing."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
triggers:
  - "omni-channel routing configuration metadata xml to deploy with sf cli"
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
  - Required push timeout values (seconds; 0 means push timeout off)
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
version: 1.1.3
author: Pranav Nagrecha
updated: 2026-10-21
---

# Omni-Channel Routing Setup

This skill activates when an administrator needs to configure Salesforce Omni-Channel end-to-end — from enabling the feature to creating Service Channels, Routing Configurations, Presence Statuses, and (for skills-based routing) Skills objects, Service Resource skill assignments, and Skills-Based Routing Rules. It covers initial setup and changes to existing routing configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Omni-Channel must be explicitly enabled.** Navigate to Service Setup > Omni-Channel Settings and turn on Omni-Channel; in metadata this is `OmniChannelSettings.enableOmniChannel`, default false (api_meta 264 L126598-126600). UNVERIFIED (2026-10-21): that the switch is one-way in production, and which features (Enhanced Omni-Channel, Skills-Based Routing) need an add-on license — the guide documents neither.
- **The most common wrong assumption is that enabling Omni-Channel automatically routes work.** Enabling the feature only activates the framework. Work items do not route until a Service Channel is created for the object, a Routing Configuration is created and associated with a queue, at least one Presence Status names that channel, and agents are in a Presence Configuration.
- **Platform limits:** A queue names one routing configuration — `Queue.queueRoutingConfig` is a single routing-configuration name (api_meta 264 L102437-102438); UNVERIFIED (2026-10-21): whether one routing configuration may serve several queues (earlier text said a configuration can serve only one queue; the guide does not say so). Skills-based routing is its own setting, `enableOmniSkillsRouting`, default false (api_meta 264 L126605-126606). Service Resources: the object reference describes `ServiceResource` as "a service technician or service crew in Field Service and Salesforce Scheduler, or an agent in Workforce Engagement" and requires Field Service or Workforce Engagement (object_reference 264 L262581, L262591); a skills-based agent's skill level lives on `ServiceResourceSkill` (L263398), whose access rule says Field Service must be enabled (L263308), while `SkillRequirement` says Omni-Channel-only use does not need Field Service (L273432). UNVERIFIED (2026-10-21): that queue-based routing needs a Service Resource per agent.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which objects are pushed, and does capacity release on close or on tab close?" | One service channel per object; `capacityModel` decides when an agent frees up | Channels that match how agents actually work |
| "How many items can an agent hold, and how much is each type worth?" | Presence configuration `capacity` versus routing configuration `capacityWeight` | A capacity model instead of a guess |
| "Least active or most available, and what is the tie-breaker?" | `routingModel` plus `secondaryRoutingPriorityField` | Predictable push order that agents can explain |
| "What happens when nobody accepts?" | `pushTimeout` (0 = off) and `presenceStatusOnPushTimeout` set what happens to the agent after a timed-out push (api_meta 264 L102698-102699, L99845-99846); UNVERIFIED (2026-10-21): whether the item then loops back to the same agent | No silent stalls |
| "Who receives work, by profile or by user?" | Presence configuration `assignments` takes profiles or users, not permission sets (api_meta 264 L99781-99783); UNVERIFIED (2026-10-21): that this is the only way an agent enters Omni-Channel | Agents who are online and actually routable |
| "Skills-based or queue-based, and is the feature enabled?" | Skills-based routing is a separate enablement with extra records | The right routing family before any metadata is written |

A proper Omni-Channel configuration adds routed work with a capacity model, a documented push order, and overflow handling; enabling the feature and pointing it at a queue adds a list view that agents still pick from by hand. Deployable shapes and order: `references/metadata-examples.md`.

---

## Core Concepts

### Queue-Based Routing

Queue-based routing assigns work from a Salesforce queue to the next available agent. Two assignment algorithms are available:

- **Least Active**: routes the new work item to the agent with the fewest open work items (lowest active count). Best when work items vary widely in effort and you want to equalize agent workloads.
- **Most Available**: routes to the agent who has the most remaining capacity (highest percentage of unused capacity). Best when work items are relatively uniform in effort and you want strict capacity balancing.

The metadata enum is `LEAST_ACTIVE`, `MOST_AVAILABLE` or `EXTERNAL_ROUTING` (api_meta 264 L102706-102710). UNVERIFIED (2026-10-21): the two definitions above — the corpus defines "Least Active" and "Most Available" only for legacy chat buttons (object_reference 264 L173933-173939), where Most Available is the largest gap between capacity and active chats, not a percentage.

The Routing Configuration record ties these settings together. Each Routing Configuration specifies the routing model, the priority (lower values route first, api_meta 264 L102712-102715), the capacity a work item consumes (`capacityWeight` or `capacityPercentage`, L102640, L102656), and a push timeout (`pushTimeout`, L102698). There is no separate "accept timeout" field on the type; earlier text listed one. The Routing Configuration is then assigned to a queue. Work placed in that queue is routed according to those settings.

### Skills-Based Routing

Skills-Based Routing matches work items to agents based on required skills rather than queue membership. The setup requires several interdependent objects:

1. **Skills** — named competencies (e.g., "Billing Support", "Spanish Language", "Technical Tier 2")
2. **Skill Levels** — optional numeric levels on the agent's skill and on the requirement; both range from 0 to 99.99 (`ServiceResourceSkill.SkillLevel`, `SkillRequirement.SkillLevel`, object_reference 264 L263398, L273515). Earlier text said "1–10 scale"; the guide's range is 0–99.99.
3. **Service Resources** — agent representations in the routing engine; one Service Resource per agent who receives skills-based work (the agent's skill level sits on `ServiceResourceSkill`; whether queue-based agents need one is UNVERIFIED (2026-10-21), see Before Starting)
4. **Service Resource Skills** — junction records assigning specific Skills (with optional levels) to Service Resources
5. **Skills-Based Routing Rules** — criteria that evaluate incoming work item fields and specify required skills and minimum skill levels for routing

When work arrives, the routing engine evaluates the Skills-Based Routing Rules against the work item's field values, determines the required skills, and routes to the Service Resource who matches those skills and has available capacity. The guide states it this way: rules or an Omni-Channel flow create a `PendingServiceRouting` with `SkillRequirement` children, and "when a work item requires multiple skills, it's routed to an agent who has all of the required skills" (object_reference 264 L273563-273565). On the routing configuration, skills-based use is the flag `isAttributeBased` = true, not a routing-model value (api_meta 264 L102674-102675). The Flow route is the `skillsBasedRouting` action, which "creates a PendingServiceRouting record used for Omni-Channel skills-based routing" (api_meta 264 L71438-71439).

### Presence Statuses and Presence Configurations

Presence Statuses are the named availability states agents select in the Omni-Channel utility bar widget (e.g., "Available", "Available - Chat Only", "Break", "Training"). The two records carry different things:

- **Presence Status** carries the channels: `ServicePresenceStatus.channels` lists the service channels the status receives, and a status with no channels is treated as Away (api_meta 264 L110740-110742). Users get a status through profile or permission-set "service presence status access" (api_meta 264 L97551-97553, L100402-100404; metadata field API 64.0+).
- **Presence Configuration** carries the capacity ceiling and who it applies to: `PresenceUserConfig.capacity` is Required, "the maximum number of work units an agent can be assigned at one time", and `assignments` takes "sets of users or ... sets of profiles" (api_meta 264 L99781-99786).

Earlier text said each status is linked to a presence configuration that holds the channels, and that agents join presence configurations via permission sets; the metadata types contradict both. An agent receives a channel's work only while in a status that names that channel.

Agents must be explicitly added to a Presence Configuration (by profile or by user). UNVERIFIED (2026-10-21): that this is the most common reason agents appear online but receive no work.

### Service Channels

A Service Channel is the bridge between a Salesforce object (Case, Chat Transcript, Messaging Session, Voice Call, or a custom object) and the Omni-Channel routing engine; `relatedEntityType` (Required) names the object (api_meta 264 L110633). Creating a Service Channel for an object tells Omni-Channel to manage routing for that object type. The channel does not set a capacity weight — `ServiceChannel` has no capacity field; the weight is the routing configuration's `capacityWeight` ("if an agent has a capacity of 6, and cases are assigned a capacity weight of 2, an agent can be assigned up to 3 cases", api_meta 264 L102656-102660). The channel's `capacityModel` decides when capacity is released: `STATUS_BASED` or `TAB_BASED` (API 65.0+, L110568-110576).

---

## Common Patterns

### Pattern: Queue-Based Routing for a Multi-Queue Support Org

**When to use:** The org has distinct support queues (e.g., Tier 1 General, Tier 2 Technical, Billing) and agents are pre-assigned to queues by skillset. Work volume is the primary routing concern, not individual agent competencies.

**How it works:**

1. Enable Omni-Channel and create a Service Channel for Case (Object: Case).
2. For each queue (Tier 1, Tier 2, Billing), create a Routing Configuration:
   - Set Routing Priority (lower routes first; 0 is valid, api_meta 264 L102712-102715): Tier 2 = 1, Billing = 2, Tier 1 = 3
   - Set Routing Model: Least Active (UNVERIFIED (2026-10-21): the fit to variable-effort queues rests on the Help-only definitions in Core Concepts)
   - Set the capacity weight per case on the routing configuration (e.g. 2 against an agent capacity of 10). The guide gives no "standard" value; earlier text called 5 standard for cases.
3. Associate each Routing Configuration with its corresponding queue (Queue > Edit > Routing Configuration field).
4. Create Presence Statuses: "Available - Cases" (channels: Case), "Break" and "Training" (no channels, so Away).
5. Create a Presence Configuration with capacity 10. Assign it to all case agents by profile or by user (api_meta 264 L99781-99783).
6. Add agents to the relevant queues, and give them access to the "Available - Cases" status through their profile or a permission set.

**Why not the alternative:** Without per-queue Routing Configurations with different priorities, all queues compete equally for agents. High-priority escalations end up behind routine requests in the same pool.

### Pattern: Skills-Based Routing for Product-Specialist Matching

**When to use:** Customers contact support about different product lines and need to reach an agent with matching product expertise. Queue membership alone cannot express this — the same agent might support Products A and B but not C.

**How it works:**

1. Enable Omni-Channel and enable Skills-Based Routing in Omni-Channel Settings.
2. Create Service Channel for Case.
3. Create Skills: "Product A Support", "Product B Support", "Product C Support".
4. Create a Service Resource for each agent. Set Type = Agent (`ResourceType` value `A`; the default is Technician, object_reference 264 L262762-262763).
5. Assign Service Resource Skills: each agent gets the Skills matching their expertise. Optionally set skill levels on the 0–99.99 range (object_reference 264 L263398) with a team convention, e.g. 10 = basic, 50 = expert. Earlier text gave a "1–5 scale".
6. Create Skills-Based Routing Rules:
   - Rule Name: "Route by Product Line"
   - Criteria: Case.Product_Line__c (picklist field)
   - For each picklist value, specify the Required Skill and minimum Skill Level
7. Create a Routing Configuration with `isAttributeBased` = true (skills-based) and a routing model of Least Active or Most Available — there is no "Skills-Based" routing-model value (api_meta 264 L102674-102675, L102706-102710). Assign to the inbound Case queue.
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

UNVERIFIED (2026-10-21): the routing-model fit in the first row (Least Active for uniform workloads) rests on the Help-only definitions in Core Concepts, which pull the other way (Least Active for variable effort); decide from the org's own push data.

---

## Recommended Workflow

Step-by-step instructions for configuring Omni-Channel routing:

1. **Enable Omni-Channel and determine the routing model.** Go to Service Setup > Omni-Channel Settings > Enable Omni-Channel. Decide upfront: queue-based or skills-based. If skills-based, also enable Skills-Based Routing on the same settings page. Document the decision and the reasons — this choice shapes all subsequent configuration steps.
2. **Create Service Channels.** For each object type that will be routed (Case, Chat Transcript, Messaging Session, Voice Call, custom), create a Service Channel record under Omni-Channel > Service Channels. Set the Salesforce Object (`relatedEntityType`) and the `capacityModel`. The channel has no capacity weight; earlier text gave channel defaults "Case = 5, Chat = 3, Voice = 10", which the guide does not hold — set the weight on the routing configuration in step 3, and give Voice the whole capacity (`capacityPercentage` 100, api_meta 264 L102640-102642). Do not skip this step — work items from objects without a Service Channel will never enter the routing engine.
3. **Create Routing Configurations.** For queue-based routing: create one Routing Configuration per queue. Set Routing Priority, Routing Model (Least Active or Most Available), `capacityWeight` or `capacityPercentage`, and Push Timeout. For skills-based routing: set `isAttributeBased` = true on the routing configuration. Assign each Routing Configuration to its target queue via the Queue edit page.
4. **Configure Presence Statuses and Presence Configurations.** Create named Presence Statuses that reflect real agent working modes, each listing the Service Channels it receives. Create Presence Configurations with the capacity ceiling and assign them by profile or by user. Grant status access through profiles or permission sets. Confirm assignments before going live.
5. **For skills-based routing: Create Skills, Service Resources, and assign Service Resource Skills.** Create Skill records for each competency. Create a Service Resource record for every agent who will receive routed work (Resource Type = Agent, link to User). Assign Service Resource Skills — be precise about skill levels (0–99.99), as the routing engine filters by minimum level.
6. **For skills-based routing: Create Skills-Based Routing Rules.** Define criteria that match incoming work item field values to required skills; mark fallback skills as additional so they drop after `dropAdditionalSkillsTimeout` (api_meta 264 L102662-102667). Test the rules by creating test work items in a sandbox. Verify the correct skill is being required for each scenario.
7. **Validate and test before go-live.** Run `python3 skills/admin/omni-channel-routing-setup/scripts/check_omni_channel_routing_setup.py --manifest-dir force-app/main/default` over the whole package (shapes in `references/metadata-examples.md`). Then in a sandbox: log in as a test agent, set an Available presence status, create a test Case or Chat that matches a routing rule, and confirm the work item appears in the agent's Omni-Channel widget. Check the Omni-Channel Supervisor tab to confirm the agent shows as Available and that the work item shows routing status. Fix any gap (missing Service Resource, Presence Configuration not assigned, routing rule mismatch) before enabling in production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Omni-Channel is enabled; Skills-Based Routing enabled if using skills model
- [ ] Service Channel exists for every object type being routed
- [ ] Routing Configuration created for every queue that routes through Omni-Channel
- [ ] Each Routing Configuration is assigned to its target queue
- [ ] Presence Statuses created for all real agent working modes
- [ ] Presence Statuses list the correct Service Channels; Presence Configurations set the capacity ceiling
- [ ] Agents are assigned to Presence Configurations by Profile or User, and have access to their statuses by Profile or Permission Set
- [ ] Service Resource records exist for every skills-based routing agent, with skill assignments
- [ ] Skills-Based Routing Rules validated against real work item field values (skills-based only)
- [ ] End-to-end routing tested in sandbox before production deployment
- [ ] Omni-Channel Supervisor shows agents as Available and work items routing correctly

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Enabling Omni-Channel routes nothing automatically** — Simply turning on Omni-Channel in settings does not route any work. Every object needs a Service Channel, every queue needs a Routing Configuration, and every agent needs a Presence Configuration assignment. A common failure mode is enabling Omni-Channel in production without all three legs in place and then wondering why no work is flowing.
2. **Service Resources must be created manually (skills-based)** — A Salesforce User account does not automatically generate a Service Resource. Every skills-based agent needs an explicit Service Resource record (Setup > Service Resources > New, Type = Agent; `ResourceType` defaults to Technician, object_reference 264 L262762-262763), because the agent's skill level lives on `ServiceResourceSkill` (L263398). UNVERIFIED (2026-10-21): that a missing Service Resource makes the agent invisible to routing regardless of Presence Status, and whether queue-based routing needs one at all.
3. **Presence Configuration assignments are not retroactive** — Assigning an agent to a Presence Configuration via their Profile applies to their next login. Agents currently logged in to Omni-Channel do not pick up Presence Configuration changes until they go offline and back online. During transitions or configuration changes, instruct agents to cycle their presence. UNVERIFIED (2026-10-21): the next-login timing is not in the corpus.
4. **Skills-Based Routing Rules require exact field API names** — Routing Rule criteria reference field API names, not field labels. A mismatch between the rule's configured field reference and the actual field API name silently fails to match, and work items fall back to the default routing behavior (or sit unrouted). Always verify field API names in Object Manager before configuring rules. UNVERIFIED (2026-10-21): routing rules have no Metadata API type in the corpus, so this behaviour is Help-only.
5. **Queue-based and Skills-Based Routing Configurations are mutually exclusive per queue** — A queue can only have one Routing Configuration assigned at a time (`Queue.queueRoutingConfig` is a single name, api_meta 264 L102437-102438). If you want to run both models (e.g., skills-based primary with queue-based fallback), you need two separate queues and two Routing Configurations, with work items moved between queues via automation if the primary fails to route.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Service Channel configuration | One record per routable object type with `relatedEntityType` and `capacityModel` set (capacity weight lives on the routing configuration) |
| Routing Configuration records | One per queue, with routing model, priority, and timeout settings documented |
| Presence Status and Configuration design | Named statuses, mapped configurations, capacity ceilings, and channel assignments |
| Service Resource roster | List of agents with confirmed Service Resource records |
| Skills matrix (skills-based only) | Agent-to-skill mapping with skill levels, used to configure Service Resource Skills |
| Skills-Based Routing Rules (skills-based only) | Rule criteria mapped to required skills and minimum levels |
| Validated routing test results | Evidence of end-to-end work item routing in sandbox |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Deploying service channels, presence statuses and configurations, decline reasons, skills, routing configurations, and the queue link, in the right order |
| `references/gotchas.md` | The six behaviours that cause most routing incidents |

---

## Related Skills

- `architect/omni-channel-capacity-model` — Use for designing capacity units, channel weights, and overflow strategies once base routing is configured
- `architect/multi-channel-service-architecture` — Use for overall queue structure and channel strategy decisions that inform routing configuration
- `architect/service-cloud-architecture` — Use for holistic Service Cloud design including Omni-Channel as a component
- `apex/omni-channel-custom-routing` — Use when routing is created in code through `PendingServiceRouting`
