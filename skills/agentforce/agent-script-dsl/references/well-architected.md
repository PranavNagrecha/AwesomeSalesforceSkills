# Well-Architected Notes — Agent Script DSL

## Relevant Pillars

- **Operational Excellence** — This skill is primarily an Operational Excellence concern. Source-controlled agent definitions, automated testing via `sf agent test run`, and deterministic pipeline-driven promotion directly address the repeatability, auditability, and operability dimensions of agent delivery. Teams that manage agents only through the Builder UI cannot reliably reproduce, review, or roll back configuration changes.
- **Reliability** — The metadata bundle deployment pattern (GenAiPlugin + GenAiPlannerBundle + BotVersion deployed atomically) is a Reliability concern. Partial deploys produce inconsistent agent state that can cause silent routing failures in production without any error signal. Atomic bundle management is the baseline reliability practice for agent metadata.
- **Security** — Indirect concern. The `.agent` file's `plannerInstructions` block (the system prompt) is the primary surface for prompt injection and instruction override attacks. Source control review of `plannerInstructions` changes — enforced through pull request review gates — provides a security control that UI-only authoring cannot provide.

## Architectural Tradeoffs

**Source Control vs. Builder UI Authoring:** Agentforce Builder provides a low-friction, visual interface for iterating on agent configuration. YAML-based `.agent` file authoring through VS Code requires tooling setup (Salesforce CLI, Agentforce extension, DX project structure) and discipline around retrieve-before-edit. The tradeoff is iteration speed vs. auditability and repeatability. For production agents serving real users, the source-control-first approach is required for Operational Excellence; Builder-only authoring is acceptable only for prototype or experimental agents that will never reach production.

**LLM Routing vs. Deterministic FSM:** Agentforce's LLM-driven orchestration provides more capable and flexible routing than the legacy Einstein Bot finite state machine, but routing quality is dependent on the natural-language quality of topic descriptions. This is an architectural constraint: you cannot compensate for vague topic descriptions with structural metadata changes. Teams used to debugging deterministic dialog flows must develop a new skill — reviewing and iterating on natural-language prompt content — to effectively operate Agentforce agents.

**API Version Lock-In:** GenAiPlannerBundle (v64+) is functionally superior to GenAiPlanner (v60–v63) but introduces a hard dependency on Spring '26+ org versions. Teams with mixed-release environments (production on one release, sandboxes on preview) must maintain API version discipline across all metadata files. Skipping this discipline produces deploy failures that are hard to diagnose.

## Anti-Patterns

1. **UI-Only Agent Management in Production** — Managing production agents exclusively through Agentforce Builder with no source control creates a single point of failure: if the Builder state is corrupted, the wrong user makes an unreviewed change, or the org is refreshed, the agent configuration is unrecoverable without manual re-entry. Every production agent's configuration must be in source control and deployable from a pipeline.

2. **Skipping Post-Deploy Activation as a Pipeline Step** — Treating a successful metadata deploy as a successful agent release. Agents arrive Inactive after every cross-org promotion. Pipelines that omit a post-deploy activation gate will release broken agents to production with no observable error signal until an end user tries to interact with the agent.

3. **Treating Topic Description Quality as a Post-Launch Concern** — Deploying an agent with placeholder or generic topic descriptions and planning to improve them after launch. Because LLM routing is entirely dependent on topic description quality, a validly deployed agent with vague descriptions is a broken agent. Topic and planner instruction quality must pass agent tests (`sf agent test run`) before promotion to production — not after.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Agentforce DX Metadata Types — https://developer.salesforce.com/docs/einstein/genai/guide/agent-dx-metadata-types.html
- Agent Development Lifecycle — https://developer.salesforce.com/docs/einstein/genai/guide/agent-development-lifecycle.html
- Metadata API Developer Guide — Bot metadata types — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_bot.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce CLI Plugin Agent — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_agent.htm
