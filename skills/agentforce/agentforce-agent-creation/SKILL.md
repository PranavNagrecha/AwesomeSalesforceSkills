---
name: agentforce-agent-creation
description: "Use when creating, configuring, auditing, or troubleshooting an Agentforce agent end-to-end: agent definition, agent user setup, channel assignment, system instructions, activation, and lifecycle management. Triggers: 'create agentforce agent', 'agent not appearing to users', 'how to activate agent', 'agent channel setup', 'agent lifecycle', 'deploy agent to production'. NOT for topic design or action contract design — use agentforce/agent-topic-design and agentforce/agent-actions respectively."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Agentforce Agent Creation

Use this skill when the work is standing up a new Agentforce agent or troubleshooting one that will not activate, will not appear to users, or behaves unexpectedly after deployment. This skill covers the agent definition, agent user, channel assignment, instructions and system prompt, activation, and lifecycle across environments. It does not cover topic boundary design or action contract design — those have their own skills.

Agentforce is Salesforce's autonomous AI agent platform (formerly Einstein Copilot). Agents are powered by a reasoning engine (GenAiPlannerBundle) layered on top of a Bot/BotVersion shell that governs the channel surface. A fully working agent requires the right platform prerequisites, a correctly configured agent definition, at least one topic with one action, and a channel to surface it on. Missing any layer produces silent failures or a blank agent panel.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is Einstein enabled? Navigate to Setup > Einstein Setup and confirm the Einstein toggle is On.
- Is the Agentforce toggle active? Setup > Agentforce Agents must show the Agentforce feature toggle as Active.
- Is the Einstein Trust Layer configured? Zero-data-retention and grounding settings affect what data the agent can access. Review with `agentforce/einstein-trust-layer` if not confirmed.
- Which channel will the agent surface on? Embedded Service, Messaging for Web, Experience Cloud Embedded Messaging, or Agent API each have different prerequisites.
- Does a dedicated agent user (EinsteinServiceAgent User or equivalent) exist with the correct permission set?

---

## Core Concepts

### The Agent Is A Layered Metadata Bundle

An Agentforce agent is not a single record. It consists of three linked metadata layers:

- **Bot + BotVersion** — the top-level shell and channel routing definition. Provides the conversation container (session, language, fallback).
- **GenAiPlannerBundle** (API v64+; GenAiPlanner in API v60–63) — the reasoning engine. Attaches to the BotVersion and gives the bot agent-level reasoning capability. Deploying BotVersion without GenAiPlannerBundle produces a chatbot, not an agent.
- **GenAiPlugin** (Topics) and **GenAiFunction** (Actions) — the capability payload. Topics define jobs the agent performs; actions define tools within those jobs.

All layers must be deployed together and remain consistent. When retrieving or deploying agent metadata, treat the bundle as one unit.

### Agent User Is A Separate Runtime Identity

Every Agentforce agent runs under a dedicated system user — the EinsteinServiceAgent User. This user must exist, have the Einstein Agent User permission set assigned, and be selected (not typed) from the dropdown in the Agent User field during setup. The agent's record access at runtime is governed by this user's profile and permission set assignments.

### Lifecycle Has Three States

- **Draft** — the agent is under construction or has been deactivated. Not accessible to end users on any channel.
- **Active** — the agent is live and accessible on its assigned channel. Activation is a deliberate, explicit click action in Agentforce Builder.
- **Inactive** — a previously active agent that has been deactivated. Previous BotVersions are retained for rollback.

Activation does not carry over between environments. An agent deployed from sandbox to production via Metadata API or change set arrives in Inactive state and must be explicitly activated in production before it serves users.

### Channel Assignment Is A Separate Configuration Step

Creating and activating an agent in Setup does not make it available to users. The agent must be assigned to a channel surface:

- **Embedded Service Deployment** — surfaces the agent in a web chat widget on Experience Cloud or an external site.
- **Messaging for In-App and Web** — routes inbound messaging sessions to the agent through Omni-Channel with a routing configuration pointing at the agent.
- **Agent API** — exposes the agent over a REST API for custom or third-party channel integration.

Each channel type has its own prerequisites. Embedded Service requires a published Experience Cloud site. Messaging requires Omni-Channel, a routing configuration, and a queue with the agent user as a member.

---

## Common Patterns

### Mode 1: Create A New Agent End-To-End

**When to use:** Greenfield agent creation — nothing exists yet.

**How it works:**

1. Confirm prerequisites: Einstein On, Agentforce toggle On, Trust Layer reviewed.
2. Setup > Agentforce Agents > **+ New Agent**. Select the appropriate template (Agentforce Service Agent for Service Cloud; custom agent for other use cases).
3. Fill in the required fields:
   - **Label** and **API Name** — the API Name is immutable after creation; choose it with the same deliberateness as a custom object API Name.
   - **Role** — natural-language description of the agent's job and persona (e.g., "customer service representative for a hospitality company, helping guests with reservations and experiences"). This becomes part of the system context fed to the reasoning engine.
   - **Company** — organizational context included in system instructions.
   - **Agent User** — select the EinsteinServiceAgent User from the dropdown; do not type manually.
   - **Enhanced Event Logs** — enable for conversation tracing during testing and audit.
4. Add topics and actions via Agentforce Builder (see `agentforce/agent-topic-design` and `agentforce/agent-actions`).
5. Review **Agent Instructions** — the system-prompt persona block that shapes tone, constraints, and fallback behavior. Specific, deterministic instructions produce more predictable agent behavior than vague persona statements.
6. Click **Activate** in Agentforce Builder (upper-right corner). The agent transitions from Draft to Active.
7. Assign to channel. For Embedded Service: Setup > Embedded Service Deployments > New (Messaging for In-App and Web). Configure the routing rule to target the agent. Add the Embedded Messaging component in Experience Builder and publish the site. Allow up to 10 minutes for changes to propagate.

### Mode 2: Review Or Audit An Existing Agent Configuration

**When to use:** An agent is behaving unexpectedly, routing incorrectly, or failing silently.

**How it works:**

1. Confirm the agent is Active (Setup > Agentforce Agents — check the status indicator).
2. Confirm the Agent User has the correct permission set and can access the records the agent needs at runtime.
3. Open the agent in Agentforce Builder. Review:
   - Agent instructions and system prompt for contradictions or vague scope.
   - Topic classification descriptions — do they match the queries being tested?
   - Action availability within each topic and whether action configurations are complete.
4. Use the **Conversation Preview** panel in Agentforce Builder to reproduce the failure interactively.
5. For production agents, review **Enhanced Event Logs** conversation records to inspect the prompt and response pipeline.
6. Verify the channel configuration has not drifted. If a Flow routes to the agent, confirm the flow targets the correct agent name and the flow version is Active.

### Mode 3: Troubleshoot Agent Not Appearing To Users

**When to use:** The agent is Active in Setup but users see no chat widget or the agent does not respond.

**How it works:**

1. Confirm the agent is Active — not Draft or Inactive.
2. Confirm the channel deployment has been published or re-published *after* the agent was activated. Publishing order matters; an Embedded Service deployment published before activation will not carry the active agent.
3. If using Experience Cloud, republish the Experience Cloud site after any Embedded Messaging configuration change.
4. If the "New Agent" button is missing in Setup or agent changes are not reflecting, refresh the page — this is a known platform UI state issue.
5. If routing flows reference the agent but the agent name does not appear in the flow dropdown, deactivate and reactivate the Agentforce toggle, then retry.
6. Confirm the EinsteinServiceAgent User is assigned to the channel's Omni-Channel queue.
7. Allow up to 10 minutes for embedded deployment changes to propagate through CDN edge caches.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New agent for Service Cloud web chat | Agentforce Service Agent template + Embedded Service Deployment | Template pre-populates standard service topics; Embedded Service routes through Omni-Channel |
| New agent for internal Salesforce app use | Standard Agentforce (Default) agent in standard footer | No external channel setup required |
| Agent for a custom or third-party channel | Agent API REST endpoint | Decouples channel surface from Salesforce UI entirely |
| Agent needs to move from sandbox to production | Deploy metadata, then manually activate in production | Activation state does not carry across org boundaries |
| API Name chosen incorrectly at creation | Create a new agent with the correct name; migrate topics and actions | API Name is immutable |
| Actions not appearing in channel after agent change | Deactivate and reactivate Agentforce toggle; republish deployment | Known platform state issue with action registration |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Einstein is enabled (Einstein Setup toggle is On).
- [ ] Agentforce feature toggle is Active in Setup > Agentforce Agents.
- [ ] Agent definition has a clear Role description and Company context in system instructions.
- [ ] Agent API Name is finalized before creation — it cannot be changed afterward.
- [ ] EinsteinServiceAgent User is assigned to the agent using the dropdown picker (not typed).
- [ ] The agent user has the Einstein Agent User permission set assigned.
- [ ] At least one topic with at least one action exists before activation.
- [ ] Agent is in Active state (not Draft or Inactive).
- [ ] Channel deployment (Embedded Service or Messaging) has been published after agent activation.
- [ ] Enhanced Event Logs are enabled for post-launch conversation audit.
- [ ] If deploying to production, activation has been performed manually in the target org after metadata deployment.
- [ ] Einstein Trust Layer configuration has been reviewed for data access and grounding patterns.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Agent API Name is permanent** — the API Name assigned at creation cannot be changed. A wrong API Name requires creating a new agent from scratch and migrating all topics and actions. Choose it carefully before the first save.
2. **Activation does not transfer between environments** — deploying agent metadata via Metadata API or a change set leaves the agent in Inactive state in the target org. Teams that assume sandbox activation carries to production will go live with a broken, invisible agent.
3. **Embedded Service deployment must be republished after agent changes** — changes to agent instructions, topics, or actions do not reach users until the Embedded Service deployment is republished. CDN propagation can take up to 10 minutes after republishing.
4. **EinsteinServiceAgent User must be selected from the dropdown, never typed** — manually typing the user name in the Agent User field fails silently or creates a misconfigured agent that passes validation but cannot execute actions at runtime.
5. **An active agent without well-designed topics is still broken** — activating an agent that has only placeholder or template topics produces an agent that appears live but cannot reliably route or complete tasks. Treat topic design as a prerequisite to activation, not a post-launch cleanup task.

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

- `agentforce/agent-topic-design` — use when the problem is topic boundary design, not agent definition or channel setup.
- `agentforce/agent-actions` — use when the problem is action contract quality, naming, or error handling within a topic.
- `agentforce/einstein-trust-layer` — use alongside this skill to validate data masking, ZDR, and grounding policies before activating an agent.
- `devops/scratch-org-management` — use when the agent lifecycle includes scratch org-based development or package creation workflows.
