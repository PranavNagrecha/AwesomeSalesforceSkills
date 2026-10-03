---
name: agentforce-agent-creation
description: "Use when creating, configuring, auditing, or troubleshooting an Agentforce agent end-to-end: agent definition, agent user setup, channel assignment, system instructions, activation, and lifecycle management. Triggers: 'create agentforce agent', 'agent not appearing to users', 'how to activate agent', 'agent channel setup', 'agent lifecycle', 'deploy agent to production'. NOT for designing what the agent can DO — an agent that looks up an order, checks a case, or creates a record is action design, use agentforce/agent-actions. NOT for topic boundary design — use agentforce/agent-topic-design."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - User Experience
  - Reliability
triggers:
  - "how do I create a new Agentforce agent from scratch"
  - "agent is not appearing in the channel after activation"
  - "what permissions does the agent user need to work"
  - "how do I assign an agent to a messaging channel or embedded service deployment"
  - "agent was deployed to production but is not active"
  - "what is the difference between Draft Active and Inactive agent states"
  - "create agentforce agent deployment"
  - "move my agent from sandbox to production with metadata"
  - "set up the agent user for a service agent"
tags:
  - agentforce
  - agent-creation
  - agent-lifecycle
  - agent-channels
  - agent-deployment
  - agent-permissions
inputs:
  - "agent name, purpose, and target channel (Embedded Service, Experience Cloud, Messaging for Web, Agent API)"
  - "org readiness: Einstein enabled, Agentforce toggle on, Trust Layer reviewed"
  - "agent user identity and permission set assignments"
  - "topic and action inventory (handled by agent-topic-design and agent-actions skills)"
outputs:
  - "step-by-step agent creation and activation guidance"
  - "channel assignment and deployment checklist"
  - "lifecycle management and promotion-to-production guidance"
  - "permission and agent user configuration findings"
dependencies: []
version: 1.0.2
author: Pranav Nagrecha
updated: 2026-10-03
---

# Agentforce Agent Creation

Use this skill when the work is standing up a new Agentforce agent or troubleshooting one that will not activate, will not appear to users, or behaves unexpectedly after deployment. This skill covers the agent definition, agent user, channel assignment, instructions and system prompt, activation, and lifecycle across environments. It does not cover subagent boundary design or action contract design — those have their own skills.

Agentforce is Salesforce's autonomous AI agent platform (formerly Einstein Copilot). Agents are powered by a reasoning engine (GenAiPlannerBundle) layered on top of a Bot/BotVersion shell that governs the channel surface. A fully working agent requires the right platform prerequisites, a correctly configured agent definition, at least one subagent with one action, and a channel to surface it on. Missing any layer produces silent failures or a blank agent panel.

> **Terminology.** This skill leads with *subagent* because that is the current
> product term — beginning in April 2026, agent topics are called subagents,
> with no change to functionality. It deliberately keeps *topic* in metadata and
> API names (`GenAiPlugin` is still documented as "an agent topic"), in the
> `agent-topic-design` skill path, and in search keywords — those did not
> change, and readers arriving with the older vocabulary still need to find
> this skill.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is Einstein enabled? Navigate to Setup > Einstein Setup and confirm the Einstein toggle is On.
- Is the Agentforce toggle active? Setup > Agentforce Agents must show the Agentforce feature toggle as Active.
- Is the Einstein Trust Layer configured? Zero-data-retention and grounding settings affect what data the agent can access. Review with `agentforce/einstein-trust-layer` if not confirmed.
- Which channel will the agent surface on? Embedded Service, Messaging for Web, Experience Cloud Embedded Messaging, or Agent API each have different prerequisites.
- Does a dedicated agent user exist with a permission set that carries the Agent User license (the Generative AI guide names "Agentforce Service Agent User" as the example for a Service Agent)?

---

## Questions to Ask Before Configuring

Ask these before creating the agent. Each one traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| "Which channel will customers or employees use?" | Only Agentforce Service Agent connects to enhanced Messaging and Bring Your Own Channel; Agent API does not support Agentforce (Default) (Gotcha 7) | The agent type, chosen from the channel | No rebuild after discovering the channel cannot connect |
| "Who is the agent user, and what exactly must it read and write?" | The agent user determines what the agent can access and do (Gotcha 4, and `agentforce/agent-security-review`) | A dedicated user, its license permission set, and a narrow data-access permission set | Least privilege from day one instead of a cloned admin |
| "How will the agent move from sandbox to production?" | Agent metadata has strict promotion rules and carries the source org's username (Gotchas 2, 8) | A manifest, a string-replacement entry for the agent user, and an activation step | Repeatable releases with no hand edits in production |
| "What is the API name, and does it follow the naming convention?" | The name must be unique and well formed, and changing it later is costly (Gotcha 1) | An agreed `developer_name` before the first save | No placeholder names in production |
| "When can the live agent change, and who approves activation?" | Editing an active agent drops live conversations (Gotcha 10) | A versioning rule and a named approver | Changes tested on a new version, activated in a quiet window |
| "Is the agent within the org's agent limit and licenses?" | The org allows 20 agents and license-limited types disappear from guided setup (Gotcha 11) | An inventory of existing agents and licenses | No blocked build halfway through |

## Core Concepts

### The Agent Is A Layered Metadata Bundle

An Agentforce agent is not a single record. It consists of three linked metadata layers:

- **Bot + BotVersion** — the top-level shell and channel routing definition. Provides the conversation container (session, language, fallback).
- **GenAiPlannerBundle** (API v64+; GenAiPlanner in API v60–63) — the reasoning engine. Attaches to the BotVersion and gives the bot agent-level reasoning capability. Deploying BotVersion without GenAiPlannerBundle produces a chatbot, not an agent.
- **GenAiPlugin** (Subagents) and **GenAiFunction** (Actions) — the capability payload. Subagents define jobs the agent performs; actions define tools within those jobs.

All layers must be deployed together and remain consistent. When retrieving or deploying agent metadata, treat the bundle as one unit.

### Agent User Is A Separate Runtime Identity

Every Agentforce Service agent runs as a dedicated agent user. The Generative AI guide says to identify or create a user for the agent and assign it a permission set that contains the Agent User license, and that "the agent user determines what your agent can access and do". In guided setup you select an existing user or create one with New Agent User from the dropdown. In Agent Script the same setting is `default_agent_user` in the access block, required for Agentforce Service agents. UNVERIFIED (2026-10-03): the earlier names "EinsteinServiceAgent User" and "Einstein Agent User permission set", and the claim that typing the user instead of selecting it fails silently.

### Lifecycle: Draft, Committed, Active

The Agentforce Developer Guide (Define Agent Metadata, v67 and earlier) describes three kinds of agent version:

| Version kind | Metadata | Editable |
|---|---|---|
| Draft | `AiAuthoringBundle` | Yes |
| Committed | `AiAuthoringBundle` plus `Bot` and `BotVersion` | No; create a new version |
| Legacy (no commit stage) | `Bot` and `BotVersion` | Inactive versions yes, the active version no |

Only one version is active at a time, and activating a committed version deactivates the one that was active. Activation is an explicit step in each org, in Agentforce Builder or with `sf agent activate`. UNVERIFIED (2026-10-03): the earlier statement that a deployed agent always arrives inactive; treat activation as a release step regardless.

### Channel Assignment Is A Separate Configuration Step

Creating and activating an agent in Setup does not make it available to users. The agent must be assigned to a channel surface:

- **Embedded Service Deployment** — surfaces the agent in a web chat widget on Experience Cloud or an external site.
- **Messaging for In-App and Web / Enhanced Chat v2**: routes inbound messaging sessions to the agent through Omni-Channel with a routing configuration pointing at the agent.
- **Agent API**: exposes the agent over a REST API for custom or third-party channel integration. Not supported for agents of type Agentforce (Default), and calls time out after 120 seconds.

Each channel type has its own prerequisites. The embedded deployment can be hosted on an external website or an Experience Builder site; the earlier statement that it requires a published Experience Cloud site was too narrow. Enhanced Chat v2 runs on Messaging and Omni-Channel, the agent must be active before a channel can route to it, and escalation to a human needs a fallback queue that supports the Messaging Session object (Agentforce Developer Guide, Build and Deploy an Enhanced Chat Agent). UNVERIFIED (2026-10-03): the earlier requirement for "a queue with the agent user as a member". Messaging channel links on a `Bot` are set in the UI and are not visible in Metadata API.

---

## Common Patterns

### Mode 1: Create A New Agent End-To-End

**When to use:** Greenfield agent creation — nothing exists yet.

**How it works:**

1. Confirm prerequisites: Einstein On, Agentforce toggle On, Trust Layer reviewed.
2. Setup > Agentforce Agents > **+ New Agent**. Select the appropriate template (Agentforce Service Agent for Service Cloud; custom agent for other use cases).
3. Fill in the required fields:

   | Field | Notes |
   |---|---|
   | Label and API Name | The API Name is immutable after creation; choose it with the same deliberateness as a custom object API Name. |
   | Role | Natural-language description of the agent's job and persona (e.g., "customer service representative for a hospitality company"). Becomes part of the system context fed to the reasoning engine. |
   | Company | Organizational context included in system instructions. |
   | Agent User | Select an existing agent user or create one with New Agent User from the dropdown. The user needs a permission set that contains the Agent User license. |
   | Enhanced Event Logs | Enable for conversation tracing during testing and audit. |
4. Add subagents and actions via Agentforce Builder (see `agentforce/agent-topic-design` and `agentforce/agent-actions`).
5. Review **Agent Instructions** — the system-prompt persona block that shapes tone, constraints, and fallback behavior. Specific, deterministic instructions produce more predictable agent behavior than vague persona statements.
6. Click **Activate** in Agentforce Builder (upper-right corner). The agent transitions from Draft to Active.
7. Assign to channel. For Embedded Service: Setup > Embedded Service Deployments > New (Messaging for In-App and Web). Configure the routing rule to target the agent. Add the Embedded Messaging component in Experience Builder and publish the site, or embed the deployment on an external website. UNVERIFIED (2026-10-03): the earlier guidance to allow up to 10 minutes for propagation.

### Mode 2: Review Or Audit An Existing Agent Configuration

**When to use:** An agent is behaving unexpectedly, routing incorrectly, or failing silently.

**How it works:**

1. Confirm the agent is Active (Setup > Agentforce Agents — check the status indicator).
2. Confirm the Agent User has the correct permission set and can access the records the agent needs at runtime.
3. Open the agent in Agentforce Builder. Review:
   - Agent instructions and system prompt for contradictions or vague scope.
   - Subagent classification descriptions — do they match the queries being tested?
   - Action availability within each subagent and whether action configurations are complete.
4. Use the **Conversation Preview** panel in Agentforce Builder to reproduce the failure interactively.
5. For production agents, review **Enhanced Event Logs** conversation records to inspect the prompt and response pipeline.
6. Verify the channel configuration has not drifted. If a Flow routes to the agent, confirm the flow targets the correct agent name and the flow version is Active.

### Mode 3: Troubleshoot Agent Not Appearing To Users

**When to use:** The agent is Active in Setup but users see no chat widget or the agent does not respond.

**How it works:**

1. Confirm the agent is Active — not Draft or Inactive.
2. Confirm the channel deployment has been published or re-published *after* the agent was activated. Publishing order matters; an Embedded Service deployment published before activation will not carry the active agent.
3. If using Experience Cloud, republish the Experience Cloud site after any Embedded Messaging configuration change.
4. If the "New Agent" button is missing in Setup or agent changes are not reflecting, refresh the page. The Agentforce DX troubleshooting guide gives the same advice for a newly published agent ("New agents aren't always reflected immediately").
5. If routing flows reference the agent but the agent name does not appear in the flow dropdown, confirm the agent is active; the agent must be active before a channel can route to it. UNVERIFIED (2026-10-03): the earlier remedy of deactivating and reactivating the Agentforce toggle.
6. Confirm the channel's fallback queue exists and supports the Messaging Session object, so escalation has somewhere to go. UNVERIFIED (2026-10-03): the earlier step to add the agent user to the Omni-Channel queue.
7. UNVERIFIED (2026-10-03): the earlier guidance to allow up to 10 minutes for CDN propagation of embedded deployment changes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New agent for Service Cloud web chat | Agentforce Service Agent template + Embedded Service Deployment | Template pre-populates standard service subagents; Embedded Service routes through Omni-Channel |
| New agent for internal Salesforce app use | Standard Agentforce (Default) agent in standard footer | No external channel setup required |
| Agent for a custom or third-party channel | Agent API REST endpoint | Decouples channel surface from Salesforce UI entirely |
| Agent needs to move from sandbox to production | Deploy metadata, then manually activate in production | Activation state does not carry across org boundaries |
| API Name chosen incorrectly at creation | Create a new agent with the correct name; migrate subagents and actions | API Name is immutable |
| Actions not appearing in channel after agent change | Confirm the new version is the active one; republish the deployment | Changes land on a version, and only the active version serves users. UNVERIFIED (2026-10-03): the earlier toggle-reset remedy |

---


## Recommended Workflow

1. **Choose agent type from channel.** Confirm the channel (enhanced Messaging, web deployment, Agent API, Agentforce panel), then the agent type that can serve it, and check the org's agent count and licenses.
2. **Prepare the org and the agent user.** Deploy `EinsteinGpt.settings` with `enableEinsteinGptPlatform`, turn on Agentforce, and create the agent user with its license permission set plus a narrow data-access permission set (`agentforce/agent-security-review`).
3. **Build the agent on a version.** Create it from a type or generate an authoring bundle from a detailed spec; finish at least one subagent with tested actions; set system messages (welcome under 800 characters, introducing the agent as an AI assistant) and enhanced event logs.
4. **Promote with a manifest.** Deploy Apex and flows first, then the agent with the manifest and string replacement in `references/metadata-examples.md`; run `python3 scripts/check_agent_creation.py --manifest-dir force-app/main/default` against the retrieved agent metadata.
5. **Activate and connect.** Activate the exact version with `sf agent activate`, then route the channel to the agent, publish the embedded deployment, and run a smoke test against the active version.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Einstein is enabled (Einstein Setup toggle is On).
- [ ] Agentforce feature toggle is Active in Setup > Agentforce Agents.
- [ ] Agent definition has a clear Role description and Company context in system instructions.
- [ ] Agent API Name is finalized before creation — it cannot be changed afterward.
- [ ] A dedicated agent user is assigned to the agent.
- [ ] The agent user has a permission set that carries the Agent User license, plus only the data access its actions need.
- [ ] At least one subagent with at least one action exists before activation.
- [ ] The intended version is the active one (one active version per agent).
- [ ] Channel deployment (Embedded Service or Messaging) has been published after agent activation.
- [ ] Enhanced Event Logs are enabled for post-launch conversation audit.
- [ ] If deploying to production, activation has been performed in the target org after metadata deployment, and the agent username was replaced for that org.
- [ ] Einstein Trust Layer configuration has been reviewed for data access and grounding patterns.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Agent API Name deserves care**: choose it before the first save; it must be unique, at most 80 characters, and well formed. UNVERIFIED (2026-10-03): the earlier claim that it can never be changed.
2. **Activation is a separate step in every org**: deploying agent metadata does not replace an explicit activation in the target org. Put `sf agent activate` in the runbook.
3. **The embedded deployment is a separately published artefact**: publish it after the channel routes to the active agent. UNVERIFIED (2026-10-03): the earlier claims that every agent change needs a republish and that propagation takes up to 10 minutes.
4. **The agent user decides what the agent can do**: select or create it in guided setup, or set `default_agent_user` in Agent Script. UNVERIFIED (2026-10-03): the earlier claim that typing the user name instead of selecting it fails silently.
5. **An active agent without well-designed subagents is still broken** — activating an agent that has only placeholder or template subagents produces an agent that appears live but cannot reliably route or complete tasks. Treat subagent design as a prerequisite to activation, not a post-launch cleanup task.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Agent creation checklist | Step-by-step checklist for new agent setup, user assignment, and activation |
| Channel deployment guide | Channel-specific steps for Embedded Service, Messaging for Web, or Agent API |
| Lifecycle promotion checklist | Steps to safely move an agent from sandbox to production |
| Agent audit findings | Review of agent definition, user permissions, and channel configuration against common failure modes |

---

## Related Skills

- `agentforce/agent-topic-design` — use when the problem is subagent boundary design, not agent definition or channel setup.
- `agentforce/agent-actions` — use when the problem is action contract quality, naming, or error handling within a subagent.
- `agentforce/einstein-trust-layer`: use alongside this skill to validate ZDR, toxicity detection and audit settings before activating an agent; note that Trust Layer data masking is disabled for agents.
- `agentforce/agent-security-review`: least-privilege agent user and pre-production security checks.
- `devops/scratch-org-management` — use when the agent lifecycle includes scratch org-based development or package creation workflows.
