# Well-Architected Notes — Agentforce Agent Creation

## Relevant Pillars

### Security

Agent creation introduces a privileged runtime identity (the EinsteinServiceAgent User) and a data access surface that differs from standard user profiles. Every agent channel exposes Salesforce record data to an LLM. Before activating an agent, the Trust Layer must be reviewed for data masking and zero-data-retention configuration. The agent user's permission set governs what records the agent can ground prompts with at runtime — scoping it too broadly creates data exposure risk; scoping it too narrowly breaks agent functionality.

### User Experience

The agent's Role description, Company context, and Agent Instructions directly shape the quality of every user interaction. Vague or contradictory instructions produce an agent that feels unreliable. Channel placement — which surface the agent appears on, when it appears, and what fallback behavior looks like — is a UX decision with direct impact on adoption and deflection rates.

### Reliability

An agent that is not Active, not published on its channel, or not correctly configured for its target environment cannot serve users. The activation-not-carried-across-environments behavior means reliability depends on correct promotion procedures, not just correct code. Any broken dependency (topics, actions, agent user, Trust Layer) degrades reliability silently — the agent may activate but fail to complete tasks.

## Architectural Tradeoffs

**Single agent vs. multiple specialized agents:** A single agent with many topics handles broad use cases but becomes harder to reason about and test. Multiple specialized agents with narrow topic sets are easier to govern but require routing logic at the channel layer. For Service Cloud use cases, the standard pattern is one agent per primary service domain with deliberate topic scoping.

**Embedded Service vs. Agent API channel:** Embedded Service is simpler to deploy for web chat but is tightly coupled to Experience Cloud infrastructure. Agent API is more flexible for custom or third-party surfaces but requires more integration work and custom session management.

**Admin-owned vs. developer-owned agent lifecycle:** Agent Builder provides a no-code path for creating and updating agents. A DevOps-managed metadata deployment approach provides version control and promotion integrity. Teams with regular agent changes should establish a Salesforce DX-based workflow using GenAiPlannerBundle and related metadata types to prevent manual drift between environments.

## Anti-Patterns

1. **Activating before topic design is complete** — produces an agent that appears live but cannot reliably execute tasks. Activation should be the last step after topics, actions, instructions, and the agent user are verified. An agent with placeholder topics gives users a negative first impression that is difficult to recover from.

2. **Assuming sandbox activation carries to production** — every environment requires its own explicit activation. Teams that omit a production activation step from their release runbook deploy a permanently Inactive agent. This is one of the most common Agentforce production incidents.

3. **Over-provisioning the agent user permission set** — the EinsteinServiceAgent User's permission set is the security boundary for LLM data access. Assigning a broad profile (e.g., System Administrator) bypasses field-level security and object permissions. Scope the permission set to exactly what the agent's topics and actions require.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/get-started-agents.html
- Agentforce DX Metadata Types — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-dx-metadata.html
- Agent Development Lifecycle — https://architect.salesforce.com/docs/architect/fundamentals/guide/agent-development-lifecycle
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Best Practices for Agent User Permissions — https://help.salesforce.com/s/articleView?id=ai.agent_user.htm&language=en_US&type=5
