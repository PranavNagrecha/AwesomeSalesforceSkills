# Well-Architected Notes — Agent Script DSL

## Relevant Pillars

- **Operational Excellence** — This skill is primarily an Operational Excellence concern. Source-controlled agent definitions, automated testing via `sf agent test run`, and deterministic pipeline-driven promotion directly address the repeatability, auditability, and operability dimensions of agent delivery. Teams that manage agents only through the Builder UI cannot reliably reproduce, review, or roll back configuration changes.
- **Reliability** — The metadata bundle deployment pattern (GenAiPlugin + GenAiPlannerBundle + BotVersion deployed atomically) is a Reliability concern. Partial deploys produce inconsistent agent state that can cause silent routing failures in production without any error signal. Atomic bundle management is the baseline reliability practice for agent metadata.
- **Security** — Indirect concern. The `.agent` file's `plannerInstructions` block (the system prompt) is the primary surface for prompt injection and instruction override attacks. Source control review of `plannerInstructions` changes — enforced through pull request review gates — provides a security control that UI-only authoring cannot provide.

## Architectural Tradeoffs

**Source Control vs. Builder UI Authoring:** Agentforce Builder provides a low-friction, visual interface for iterating on agent configuration. YAML-based `.agent` file authoring through VS Code requires tooling setup (Salesforce CLI, Agentforce extension, DX project structure) and discipline around retrieve-before-edit. The tradeoff is iteration speed vs. auditability and repeatability. For production agents serving real users, the source-control-first approach is required for Operational Excellence; Builder-only authoring is acceptable only for prototype or experimental agents that will never reach production.

**LLM Routing vs. Deterministic FSM:** Agentforce's LLM-driven orchestration provides more capable and flexible routing than the legacy Einstein Bot finite state machine, but routing quality is dependent on the natural-language quality of topic descriptions. This is an architectural constraint: you cannot compensate for vague topic descriptions with structural metadata changes. Teams used to debugging deterministic dialog flows must develop a new skill — reviewing and iterating on natural-language prompt content — to effectively operate Agentforce agents.

**API Version Floors Are Project Decisions, Not Org Constraints:** The agent metadata stack now has two floors — GenAiPlannerBundle replaces GenAiPlanner at API v64.0 (Summer '25), and `AiAuthoringBundle` carrying the Agent Script source arrives at API v65.0 (Winter '26). Neither is an org-capability question for any currently supported org; both are decided by the `sourceApiVersion` pin in `sfdx-project.json` and the `<version>` in each `package.xml`. The architectural risk is not "our org is too old" — it is a stale project pin quietly excluding a metadata type from every retrieve, which is a silent completeness failure rather than a deploy error. Treat the manifest's type list and version as reviewed artifacts, and re-audit both whenever the authoring surface changes.

**Agent Script as the Versioned Source of Truth:** Now that Agent Script is GA (Summer '26) and new agents can only be created in the new Agentforce Builder, the design-time script — not the compiled GenAiPlugin/GenAiPlannerBundle output — is what a pull request should review and what a rollback should restore. A pipeline that versions only the runtime metadata inverts this: it stores the build artifact and discards the build input. The Operational Excellence claim of "our agents are in source control" is only true if `aiAuthoringBundles/` is in the repo.

## Anti-Patterns

1. **UI-Only Agent Management in Production** — Managing production agents exclusively through Agentforce Builder with no source control creates a single point of failure: if the Builder state is corrupted, the wrong user makes an unreviewed change, or the org is refreshed, the agent configuration is unrecoverable without manual re-entry. Every production agent's configuration must be in source control and deployable from a pipeline.

2. **Skipping Post-Deploy Activation as a Pipeline Step** — Treating a successful metadata deploy as a successful agent release. Agents arrive Inactive after every cross-org promotion. Pipelines that omit a post-deploy activation gate will release broken agents to production with no observable error signal until an end user tries to interact with the agent.

3. **Treating Topic Description Quality as a Post-Launch Concern** — Deploying an agent with placeholder or generic topic descriptions and planning to improve them after launch. Because LLM routing is entirely dependent on topic description quality, a validly deployed agent with vague descriptions is a broken agent. Topic and planner instruction quality must pass agent tests (`sf agent test run`) before promotion to production — not after.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Agent Script overview — https://developer.salesforce.com/docs/ai/agentforce/guide/agent-script.html
- Agent Script language fundamentals — https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-lang.html
- Agent Script reference — https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-reference.html
- Manage agents (org UI and Agentforce DX CLI) — https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-manage.html
- Agent Script example — https://developer.salesforce.com/docs/ai/agentforce/guide/ascript-example.html
- Introducing hybrid reasoning with Agent Script (blog) — https://developer.salesforce.com/blogs/2025/10/introducing-hybrid-reasoning-with-agent-script
- Agent Script language fundamentals (blog) — https://developer.salesforce.com/blogs/2026/02/agent-script-decoded-intro-to-agent-script-language-fundamentals
- salesforce/agentscript — open-sourced parser, linter, compiler, and LSP (Apache 2.0) — https://github.com/salesforce/agentscript
- Agentforce DX Metadata Types — https://developer.salesforce.com/docs/einstein/genai/guide/agent-dx-metadata-types.html
- Agent Development Lifecycle — https://developer.salesforce.com/docs/einstein/genai/guide/agent-development-lifecycle.html
- Metadata API Developer Guide — Bot metadata types — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_bot.htm
- Metadata API — GenAiPlanner — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiplanner.htm — confirms "GenAiPlanner components are available in API version 60.0 to 63.0. GenAiPlannerBundle replaces GenAiPlanner in API version 64.0 and later" (API v64.0 = Summer '25, not Spring '26) (verified 2026-08-13)
- Metadata API — GenAiPlannerBundle — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiplannerbundle.htm — confirms availability in API version 64.0 and later, and the `genAiPlannerBundles` folder layout (verified 2026-08-13)
- Metadata API — AiAuthoringBundle — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_aiauthoringbundle.htm — confirms the type is supported beginning with API version 65.0 (Winter '26), the `aiAuthoringBundles/` directory holding `<Name>.agent` + `<Name>.bundle-meta.xml`, and that omitting `target` deploys in draft state while setting it commits the agent version (verified 2026-08-13)
- Metadata API — GenAiPlugin — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_genaiplugin.htm — confirms the type is still documented as "an agent topic" with no occurrence of "subagent," so the April 2026 rename did not reach the metadata API (verified 2026-08-13)
- Metadata API — AiEvaluationDefinition — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_aievaluationdefinition.htm — confirms `topic_sequence_match` is still the expectation name (with `action_sequence_match`, `bot_response_rating`, `output_latency_milliseconds`, `string_comparison`, `numeric_comparison`) and that no `subagent_*` expectation exists (verified 2026-08-13)
- The Salesforce Developer's Guide to the Summer '26 Release — https://developer.salesforce.com/blogs/2026/06/the-salesforce-developers-guide-to-the-summer-26-release — confirms Agent Script and the new Agentforce Builder are GA, the week-of-July-13-2026 cutoff after which the New Agent button no longer opens the legacy builder, the legacy-agent upgrade path, and the Apache 2.0 toolchain release (verified 2026-08-13)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce CLI Plugin Agent — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_agent.htm
