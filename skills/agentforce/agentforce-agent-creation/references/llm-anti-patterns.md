# LLM Anti-Patterns — Agentforce Agent Creation

Common mistakes AI coding assistants make when generating or advising on Agentforce agent creation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Skipping Agent User Setup and Permission Configuration

**What the LLM generates:** "Create the agent in Agent Builder and activate it" without configuring the agent user — the dedicated Salesforce user identity under which the agent executes actions, queries data, and enforces security.

**Why it happens:** Agent Builder's UI focuses on topics and actions. The agent user setup (creating or selecting the user, assigning the correct profile, adding permission sets for Einstein and Agentforce) is a prerequisite that happens outside Agent Builder and is easy to overlook.

**Correct pattern:**

```text
Agent user setup checklist:

1. Create or designate the agent user:
   - Dedicated user (not a shared admin account)
   - License: Salesforce or appropriate platform license
   - Profile: custom profile with minimum necessary permissions
   - Do NOT use System Administrator profile

2. Assign required permission sets:
   - "Agentforce Service Agent" or equivalent Agentforce PS
   - Object and field permissions for all data the agent accesses
   - Apex class access for all invocable actions

3. Configure sharing and access:
   - Sharing rules that grant the agent user access to relevant records
   - If serving portal users: verify the agent user can see
     records owned by portal accounts

4. Verify in Setup > Users:
   - Agent user is Active
   - Permission sets are assigned
   - Profile permissions are correct

The agent runs AS this user. Every SOQL query, DML operation,
and API callout respects this user's permissions.
```

**Detection hint:** Flag agent creation guides that do not mention agent user setup. Check for agents running under System Administrator profiles. Flag missing Agentforce permission set assignments.

---

## Anti-Pattern 2: Not Assigning the Agent to the Correct Channel

**What the LLM generates:** "Activate the agent and it will be available to users" without specifying channel assignment — the agent must be explicitly connected to a deployment channel (Embedded Service, Messaging for Web, Experience Cloud, or Agent API).

**Why it happens:** Activation in Agent Builder makes the agent "Active" but does not expose it to end users. Channel assignment is a separate configuration step in Setup. LLMs conflate "active" with "deployed and visible."

**Correct pattern:**

```text
Agent channel deployment:

After activation in Agent Builder, assign to a channel:

1. Embedded Service Deployment:
   - Setup > Embedded Service Deployments
   - Select or create a deployment
   - Set the agent as the bot/agent for the deployment
   - Add the deployment snippet to the website

2. Messaging for Web:
   - Setup > Messaging Settings
   - Create a Messaging for Web channel
   - Assign the agent to the messaging channel

3. Experience Cloud:
   - Setup > Experience Builder
   - Add the agent component to the site
   - Configure the agent assignment

4. Agent API (headless):
   - Use the Agentforce API to invoke the agent programmatically
   - No UI channel needed

Common failure: agent is Active in Agent Builder but users say
"I don't see the agent" — the channel assignment is missing.
```

**Detection hint:** Flag agent activation instructions that do not include channel assignment steps. Check for agents in Active state with no channel deployment configured.

---

## Anti-Pattern 3: Writing Overly Generic System Instructions

**What the LLM generates:** System instructions like "You are a helpful assistant. Answer customer questions accurately and politely" — which provide no business context, tone guidance, compliance boundaries, or behavioral constraints.

**Why it happens:** LLMs default to generic chatbot instructions. Agentforce system instructions are the highest-priority behavioral directive — they override topic instructions when there is a conflict. Generic instructions waste this high-value configuration point.

**Correct pattern:**

```text
System instruction template:

You are [Company Name]'s [Agent Role] agent.
You serve [target user segment] through [channel].

Tone: [Professional and empathetic / Casual and friendly / Formal]
Language: Respond in the same language the customer uses.

You MUST:
- Verify the customer's identity before discussing account details
- Use data from Salesforce records only — never make up information
- Confirm before taking any action that modifies records

You MUST NOT:
- Discuss competitor products or pricing
- Share internal company policies not meant for customers
- Provide legal, medical, or financial advice
- Disclose that you are an AI unless directly asked

When uncertain: "Let me connect you with a team member who
can help with this specific question."

Compliance: [HIPAA / PCI / GDPR / industry-specific rules]
- Do not ask for or display full SSN, credit card numbers,
  or other PII in the conversation.

Length: 100-300 words is typical. Be specific, not verbose.
```

**Detection hint:** Flag system instructions shorter than 50 words. Check for missing MUST NOT constraints. Flag instructions that do not mention the company name, agent role, or escalation behavior.

---

## Anti-Pattern 4: Deploying to Production Without Testing Agent Conversation Flows

**What the LLM generates:** "Build the agent, activate it, and deploy to production" as a linear process without a testing phase that validates conversation routing, action execution, error handling, and escalation across all topics.

**Why it happens:** LLMs treat agent creation as a configuration task (build and ship). Agentforce agents are probabilistic — the LLM planner's action selection depends on conversation context, topic instructions, and action descriptions. Without testing, edge cases cause incorrect action invocation, data leakage, or failure to escalate.

**Correct pattern:**

```text
Agent testing protocol:

1. Unit test each action independently:
   - Invoke each Flow or Apex action with sample inputs
   - Verify output structure and error handling
   - Test with invalid inputs (null, wrong type, missing required)

2. Topic routing test:
   - Prepare 5-10 test utterances per topic
   - Include 5 ambiguous utterances
   - Include 3 out-of-scope utterances
   - Verify correct topic selection for each

3. End-to-end conversation test:
   - Use Agent Builder's test panel
   - Walk through complete user journeys per topic
   - Test the happy path and at least 2 error paths
   - Test escalation triggers

4. Permission boundary test:
   - Simulate conversations that request data the agent
     user should NOT see
   - Verify the agent does not expose restricted data

5. Sandbox validation:
   - Deploy to a sandbox with production-equivalent data
   - Test with real user profiles (not admin)
   - Validate channel integration (Embedded Service, etc.)

Only deploy to production after all test categories pass.
```

**Detection hint:** Flag deployment guides that move directly from configuration to production activation. Check for agents with no test conversation history in Agent Builder. Flag agents deployed without sandbox validation.

---

## Anti-Pattern 5: Confusing Agent States — Draft, Active, and Inactive

**What the LLM generates:** "Deactivate the old agent version and activate the new one" as if agents have version-based activation like OmniStudio components. Agentforce agents have three states (Draft, Active, Inactive) but do not support side-by-side versioning — there is one agent definition that is either active or not.

**Why it happens:** LLMs apply versioning mental models from Flows, OmniScripts, or managed packages. Agentforce agents are not versioned in the same way. Changes to an active agent take effect immediately (or after save and re-activation), and there is no rollback to a "previous version."

**Correct pattern:**

```text
Agent lifecycle states:

Draft:
- Agent is being configured
- Not visible to any channel or user
- Safe to make changes

Active:
- Agent is live and handling conversations
- Changes require careful planning
- Editing topics or actions on an active agent affects
  live conversations after save

Inactive:
- Agent is disabled — no conversations routed to it
- Channel deployments using this agent will show fallback behavior
- Use to temporarily disable an agent

Change management:
- There is NO built-in versioning or rollback
- Before making breaking changes to an active agent:
  1. Document current configuration (export or screenshot)
  2. Test changes in sandbox first
  3. Schedule a maintenance window if possible
  4. Make changes and monitor conversation quality immediately

For significant refactors:
- Create a NEW agent with the updated configuration
- Test the new agent end-to-end
- Swap the channel assignment from old agent to new agent
- Deactivate the old agent
```

**Detection hint:** Flag instructions that reference "agent versions" or "activate version 2." Check for active agents being edited without a rollback plan. Flag agents being deactivated without updating channel assignments.

---
