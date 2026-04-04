# Gotchas — Agentforce Agent Creation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Agent API Name Is Permanent — You Cannot Rename It

**What happens:** A practitioner creates an agent with a placeholder or temporary API Name during early development (for example, `Test_Agent_1` or `Service_Agent_v2`). Later, when the name needs to match a naming convention or org standard, they discover there is no rename option. The API Name field is greyed out and read-only in Setup. The only resolution is to create a new agent with the correct API Name and manually recreate all topics and actions.

**When it occurs:** Any time the agent's API Name is not finalized before the first save. This is most common when building under time pressure or when naming conventions are decided after development starts.

**How to avoid:** Treat the Agent API Name with the same deliberateness as a custom object API Name. Confirm the naming convention with the team before navigating to Setup > Agentforce Agents > New Agent. The Label can be changed later; the API Name cannot.

---

## Gotcha 2: Deployment Does Not Carry Activation State Between Environments

**What happens:** An agent is Active in sandbox and functioning correctly. The metadata is deployed to production via Salesforce CLI, Metadata API, or a change set. In production, the agent exists but is Inactive. Users see no agent widget. The release team may spend time troubleshooting channel configuration or permissions before realizing the agent was never activated in production.

**When it occurs:** Every promotion from sandbox to any other environment — production, partial sandbox, developer org. Activation is environment-local. Salesforce does not carry the Active flag across org boundaries.

**How to avoid:** Add a mandatory "Activate agent in target org" step to every release runbook. After deployment, navigate to Setup > Agentforce Agents in the target org, open the agent in Agentforce Builder, and click Activate. Then republish any Embedded Service deployment that references the agent.

---

## Gotcha 3: Embedded Service Deployment Must Be Republished After Any Agent Change

**What happens:** A team updates agent instructions, modifies a topic, or adds a new action in sandbox and deploys to production. After deployment and activation, the chat widget on the Experience Cloud site still shows old behavior. The agent in Setup shows the correct updated configuration. Users report that the changes are not taking effect.

**When it occurs:** Any time agent metadata is updated after the Embedded Service deployment was last published. The published deployment captures a snapshot of the channel configuration at publish time. Changes to the agent after the last publish are not reflected until the deployment is republished.

**How to avoid:** Include "Republish Embedded Service Deployment" as a post-deployment step in the release runbook. Navigate to Setup > Embedded Service Deployments, open the relevant deployment, and click Publish. Allow up to 10 minutes for CDN propagation before retesting. This step is required even for minor agent instruction changes.

---

## Gotcha 4: Trust Layer Must Be Configured Before Agent Data Grounding

**What happens:** An agent is created, activated, and deployed. During testing, the agent retrieves and surfaces Salesforce record data to users. The team later discovers that PII (names, contact details, account information) is being sent to the external LLM without any masking — despite the organization's AI governance policy requiring data protection for customer data.

**When it occurs:** When the Einstein Trust Layer is not reviewed before agent activation. Specifically, when the team assumes that enabling Einstein automatically enables data masking for agent prompts. As of Spring '25, data masking through the Trust Layer applies to certain embedded Einstein features but does not apply to Agentforce agent prompt pipelines by default. The Trust Layer setup UI does not make this feature-level distinction visible at a glance.

**How to avoid:** Before activating any agent that grounds prompts with Salesforce record data, review the Trust Layer configuration using the `agentforce/einstein-trust-layer` skill. Confirm which masking policies apply to the agent's use case and whether Zero Data Retention is sufficient for the organization's compliance requirements.

---

## Gotcha 5: Topic-Action Design Is A Prerequisite, Not A Post-Launch Cleanup

**What happens:** An agent is activated with template or placeholder topics (such as the default topics included with the Agentforce Service Agent template that have not been customized). The agent appears Active and the channel widget shows up. Users interact with the agent but it consistently routes to the wrong topic, cannot complete tasks, or falls back to "I cannot help with that" for every request. The team assumes the agent needs tuning and spends time adjusting instructions before realizing the topics have no meaningful classification descriptions or actions.

**When it occurs:** When agent creation and topic design are treated as sequential rather than parallel workstreams. Creating the agent shell is fast; designing working topics and actions takes deliberate effort and should be complete before activation.

**How to avoid:** Follow the `agentforce/agent-topic-design` and `agentforce/agent-actions` skills as part of the creation workflow. Do not activate the agent until at least one topic has a clear classification description and at least one executable action that can be tested end-to-end in Conversation Preview.
