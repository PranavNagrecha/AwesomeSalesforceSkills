# Well-Architected Notes — Agentforce Agent Creation

## Relevant Pillars

### Security

Agent creation introduces a privileged runtime identity (the agent user) and a data access surface that differs from standard user profiles. Every agent channel exposes Salesforce record data to an LLM. Before activating an agent, review the Trust Layer for zero-data retention and audit; Trust Layer data masking is disabled for agents, so data exposure is controlled through the agent user's permissions. The agent user's permission set governs what records the agent can ground prompts with at runtime, scoping it too broadly creates data exposure risk; scoping it too narrowly breaks agent functionality.

### User Experience

The agent's Role description, Company context, and Agent Instructions directly shape the quality of every user interaction. Vague or contradictory instructions produce an agent that feels unreliable. Channel placement — which surface the agent appears on, when it appears, and what fallback behavior looks like — is a UX decision with direct impact on adoption and deflection rates.

### Reliability

An agent that is not Active, not published on its channel, or not correctly configured for its target environment cannot serve users. Activation is a separate step in each org, so reliability depends on correct promotion procedures, not just correct code. Any broken dependency, subagents (called topics before April 2026), actions, agent user, Trust Layer, degrades reliability silently: the agent may activate but fail to complete tasks.

## Architectural Tradeoffs

**Single agent vs. multiple specialized agents:** A single agent with many subagents handles broad use cases but becomes harder to reason about and test. Multiple specialized agents with narrow subagent sets are easier to govern but require routing logic at the channel layer. For Service Cloud use cases, the standard pattern is one agent per primary service domain with deliberate subagent scoping.

**Embedded Service vs. Agent API channel:** Embedded Service is simpler to deploy for web chat but is tightly coupled to Experience Cloud infrastructure. Agent API is more flexible for custom or third-party surfaces but requires more integration work and custom session management.

**Admin-owned vs. developer-owned agent lifecycle:** Agent Builder provides a no-code path for creating and updating agents. A DevOps-managed metadata deployment approach provides version control and promotion integrity. Teams with regular agent changes should establish a Salesforce DX-based workflow using GenAiPlannerBundle and related metadata types to prevent manual drift between environments.

## Anti-Patterns

1. **Activating before subagent design is complete** — produces an agent that appears live but cannot reliably execute tasks. Activation should be the last step after subagents, actions, instructions, and the agent user are verified. An agent with placeholder subagents gives users a negative first impression that is difficult to recover from.

2. **Assuming sandbox activation carries to production**: every environment requires its own explicit activation (`sf agent activate`). Teams that omit a production activation step from their release runbook ship an agent nobody can reach. UNVERIFIED (2026-10-03): the earlier claim that this is one of the most common production incidents.

3. **Over-provisioning the agent user permission set**: the agent user's permission sets are the security boundary for LLM data access. Assigning a broad profile (e.g., System Administrator) bypasses field-level security and object permissions. Scope the permission set to exactly what the agent's subagents and actions require.

## Official Sources Used

Read and checked on 2026-10-03 for this revision:

- Generative AI guide, Spring '26: Set Up Agents, Create an Agent from a Type (agent user and license permission set), Explore Agent Types, Manage Agent Settings, Enable Enhanced Event Logs, Define System Messages (800 characters), Update Language Settings, Activate or Deactivate Your Agent, Considerations for Agents (channels, languages), Agents Limits (20 agents), Trust and Agents (masking disabled for agents): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/generative_ai.pdf
- Metadata API Developer Guide, Summer '26 (API 67.0): Bot (type values, messaging channel providers set in the UI, `defaultOutboundFlow`), BotVersion, GenAiPlannerBundle, GenAiPlanner (API 60.0 to 63.0), EinsteinGptSettings (`enableEinsteinGptPlatform`; malformed sample): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Agentforce Developer Guide, Agent Metadata V67 and Earlier: A Shallow Dive: https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-metadata.html
- Agentforce Developer Guide, Use Metadata to Move an Agent to a New Org (API 68.0 types, agent username, committed agents, matching versions): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-deploy-metadata.html
- Agentforce Developer Guide, Define Agent Metadata (v67 and Earlier) and Manifest Defining a Single Agent Version (v67 and Earlier): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-api-v67-earlier.html and https://developer.salesforce.com/docs/ai/agentforce/guide/package-singleagent67.html
- Agentforce Developer Guide, Example: Configure String Replacement for Agent Username: https://developer.salesforce.com/docs/ai/agentforce/guide/string-replace-example.html
- Agentforce Developer Guide, Manage an Agent (activate and deactivate from the CLI): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-manage.html
- Agentforce Developer Guide, Troubleshoot Agentforce DX Issues (publish does not deploy Apex or flows; activation in CI; committed agents need Bot/BotVersion; template packaging limitation): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-troubleshooting.html
- Agentforce Developer Guide, Agent Script Blocks (config `developer_name` rules, `agent_type`, `enable_enhanced_event_logs`, access `default_agent_user`): https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-blocks.html
- Agentforce Developer Guide, Multi-Surface Example: Build and Deploy an Enhanced Chat Agent (agent must be active before routing; fallback queue; embedded deployment on external or Experience Builder sites): https://developer.salesforce.com/docs/ai/agentforce/guide/headless-examples-enhanced-chat-agent.html
- Agentforce Developer Guide, Agent API Considerations (not for Agentforce (Default); 120-second timeout): https://developer.salesforce.com/docs/ai/agentforce/guide/agent-api-considerations.html
- Agentforce Developer Guide, Customizing User Interface Using Custom Lightning Types with Top-Level Editor and Top-Level Renderer Overrides (activating a committed version deactivates the active one): https://developer.salesforce.com/docs/ai/agentforce/guide/lightning-types-example-full-editor-renderer.html
- Salesforce CLI help text, `sf agent activate --help` (CLI 2.151.7: one active version; `--version` is the number of `vX`)

### Carried forward from earlier versions (not re-read on 2026-10-03)

These were not re-read for this revision. help.salesforce.com articles do not return their text to a fetch, so claims that rest only on a Help article are marked UNVERIFIED in the skill.

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/get-started-agents.html
- Agentforce DX Metadata Types — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-metadata.html
- Agent Development Lifecycle — https://architect.salesforce.com/docs/architect/fundamentals/guide/agent-development-lifecycle
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Best Practices for Agent User Permissions — https://help.salesforce.com/s/articleView?id=ai.agent_user.htm&language=en_US&type=5
