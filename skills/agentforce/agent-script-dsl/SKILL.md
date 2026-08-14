---
name: agent-script-dsl
description: "Authoring and managing Agentforce agent definitions using the declarative Agent Script DSL (.agent files) and associated metadata types, including the Agent Script language for the new Agentforce Builder (hybrid-reasoning -> logic vs | prompt instructions, @actions/@subagent/@variables references, subagents). Use when creating agents in source control, writing or debugging Agent Script, debugging agent metadata, or understanding the metadata lifecycle of GenAiPlugin/GenAiPlanner/BotVersion types. Triggers: 'how do I deploy an Agentforce agent using source control', 'what metadata types make up an Agentforce agent', 'agent test run command failing in CI pipeline', 'GenAiPlugin vs GenAiPlanner metadata relationship', 'Agent Script logic vs prompt instructions'. NOT for Apex-based agent actions — use agentforce/custom-agent-actions-apex. NOT for clicking the agent together in the Builder UI — use agentforce/agentforce-agent-creation."
category: agentforce
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I deploy an Agentforce agent using source control"
  - "what metadata types make up an Agentforce agent"
  - "agent test run command failing in CI pipeline"
  - "GenAiPlugin vs GenAiPlanner metadata relationship"
  - "how do I write or edit .agent files for version-controlled agent development"
  - "agentforce agent metadata types GenAiPlugin deployment"
  - "write Agent Script logic instructions vs prompt instructions for hybrid reasoning"
  - "convert an agent topic to a subagent in Agent Script"
tags:
  - agentforce
  - agent-dsl
  - genai-plugin
  - metadata
  - bot-version
inputs:
  - "Agent definition requirements (topics, actions, system instructions)"
  - "Existing BotVersion or GenAiPlugin metadata if reviewing or migrating"
  - "VS Code with Salesforce Extensions and Agentforce extension installed"
outputs:
  - "Valid .agent file structure and GenAiPlugin/GenAiPlanner/BotVersion metadata"
  - "sf agent test run commands for CI pipeline integration"
  - "Source control layout and metadata deployment guidance for agents"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agent Script DSL

Use this skill when the work involves authoring, editing, validating, or deploying Agentforce agent definitions through source-controlled metadata rather than through the Agentforce Builder UI. This skill covers the YAML-based `.agent` file format, the runtime metadata types that make up an agent (GenAiPlugin, GenAiPlanner/GenAiPlannerBundle, BotVersion) plus the design-time `AiAuthoringBundle`, LSP validation tooling, the `sf agent test run` CLI command, and the metadata deployment lifecycle end-to-end. It does not cover Apex implementation of invocable agent actions (use `agentforce/custom-agent-actions-apex`) and does not cover UI-driven agent creation workflow (use `agentforce/agentforce-agent-creation`).

Agentforce agent definitions are stored as YAML-based declarative metadata in `.agent` files within a Salesforce DX project. These files are the machine-readable representations of the same configuration surfaced in Agentforce Builder. Understanding the relationship between the three runtime metadata types — GenAiPlugin, GenAiPlanner (or GenAiPlannerBundle from API v64.0+), and BotVersion — plus the design-time `AiAuthoringBundle` that carries the Agent Script source from API v65.0+, is essential for correct deployment and source control management.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the target Salesforce CLI and API version? Per the Metadata API guide, "GenAiPlanner components are available in API version 60.0 to 63.0. GenAiPlannerBundle replaces GenAiPlanner in API version 64.0 and later." API v64.0 is **Summer '25**, not Spring '26 — the cutover is three releases older than most agent tutorials imply. What decides which type you use is the project's `sourceApiVersion` pin in `sfdx-project.json`, not the org's release: a Summer '26 org will happily accept a project pinned to 63.0 and that project still uses GenAiPlanner. Agent Script authoring adds a fourth type, `AiAuthoringBundle`, at API v65.0 (Winter '26).
- Is the Salesforce Extensions for VS Code installed along with the Agentforce extension? LSP-based DSL validation requires both. Without them, YAML errors in `.agent` files produce silent or cryptic deploy failures.
- Is the project structured as a Salesforce DX project with `sfdx-project.json`? The `sf agent` CLI commands operate on DX-structured projects only.
- What is the current state of the agent in the org? Retrieving before editing is critical — manually authored `.agent` files that diverge from the deployed BotVersion state produce merge conflicts on the next retrieve.
- Are there existing GenAiPlugin or GenAiFunction metadata files in the project? These must be co-deployed with BotVersion and GenAiPlannerBundle as a unit.

---

## Core Concepts

### The Three Runtime Metadata Types

An Agentforce agent in source control is not a single file. Three linked runtime metadata types must be deployed together as a bundle — and for an agent authored in the new Agentforce Builder they are not the whole story, because a fourth design-time type carries the Agent Script source (see "The Fourth Type" below):

**GenAiPlugin** — the action definition layer. Each GenAiPlugin corresponds to a topic in Agentforce Builder. It declares the topic label, description (used by the LLM for topic classification), and references to the `GenAiFunction` records (actions) that belong to the topic. A plugin that has a vague or overlapping description will cause the LLM planner to route incorrectly, even if the metadata deploys cleanly.

**GenAiPlanner / GenAiPlannerBundle** — the orchestration configuration layer. GenAiPlanner (API v60.0–v63.0, i.e. Spring '24 through Spring '25) or GenAiPlannerBundle (API v64.0+, Summer '25 onward) configures the LLM reasoning engine: model selection, planner instructions (the system prompt), and the set of GenAiPlugins the agent can invoke. The bundle variant introduces the ability to link the planner to a BotVersion within a single metadata record, replacing the manual cross-reference approach of the earlier type.

**BotVersion** — the conversation container and channel routing shell. BotVersion wraps the Bot record and manages conversation session parameters, language settings, and fallback behavior. It also carries the reference that links a deployed agent to the GenAiPlannerBundle. BotVersion without a linked planner produces a legacy Einstein Bot, not an Agentforce agent. The presence of the `genAiPlannerBundle` element in BotVersion XML is the authoritative indicator that a BotVersion is an Agentforce agent and not a legacy scripted bot.

All three runtime types must be retrieved and deployed as a coherent unit. Partial deploys — for example, deploying only GenAiPlugin changes without an updated BotVersion — will either fail validation or produce a deployed state that diverges from the source of truth in version control.

### The Fourth Type: AiAuthoringBundle (API v65.0+)

Agents authored in the new Agentforce Builder are **not** fully described by the three runtime types above. The Agent Script source lives in a fourth, design-time type introduced at API v65.0 (Winter '26): `AiAuthoringBundle`, which the Metadata API guide describes as "a container for AI-related authoring content. For example, an AI authoring bundle for an Agentforce agent contains an Agent Script file and the associated metadata content."

Shape on disk — a directory per bundle under `aiAuthoringBundles/`, holding two files:

```text
force-app/main/default/aiAuthoringBundles/New_Agent/
├── New_Agent.agent              # the Agent Script source
└── New_Agent.bundle-meta.xml    # bundleType, target, versionTag, versionDescription
```

Two fields drive deployment behavior. `bundleType` is currently `AGENT` for Agent Script agents. `target` names the `{Bot}.{BotVersion}` to commit the version to — **omit `target` and the agent deploys in draft state; include it and the deploy commits the agent version**, the equivalent of Agentforce Builder's version commit. Committing a version is still not activation (see the activation gotcha).

The consequence for CI/CD: a manifest built from the 2024-era five-type list (Bot, BotVersion, GenAiPlanner, GenAiPlugin, GenAiFunction) versions an *incomplete* agent — the `.agent` blueprint never reaches the repo or the target org. Add `AiAuthoringBundle` to the manifest and set `sourceApiVersion` to 65.0 or higher.

### YAML-Based .agent File Format

The `.agent` file is the primary human-authoring surface for Agentforce agent definitions in a DX project. It is a YAML file that declaratively defines the full agent configuration: agent metadata, planner instructions (the system prompt persona), topic references, and action references. The Salesforce CLI tooling (`sf agent`) consumes `.agent` files and translates them into the correct GenAiPlugin/GenAiPlanner/BotVersion metadata records during deployment.

Key YAML keys in a typical `.agent` file:

- `name` — the agent API name (immutable after first deployment)
- `type` — `agent` for standard Agentforce agents
- `spec.agentType` — differentiates service agents from custom agents
- `spec.description` — the agent's role description (becomes part of the system context)
- `spec.topics` — array of topic definitions, each with a `label`, `description`, and list of `actions`
- `spec.plannerInstructions` — the full system prompt block governing persona, tone, and constraints

The Salesforce Agentforce VS Code extension provides LSP validation against the `.agent` schema. Hover hints, inline error diagnostics, and autocomplete are available when the extension is active. Authoring `.agent` files without LSP validation significantly increases the risk of silent schema violations that only surface at deploy time.

### Agent Script — the Language for the New Agentforce Builder

Agent Script is the authoring language for the new Agentforce Builder. Salesforce describes it as "the language for building agents in Agentforce Builder" that "combines the flexibility of natural language instructions for handling conversational tasks with the reliability of programmatic expressions for handling business rules." It is a distinct, higher-level surface than the raw `.agent`/GenAiPlugin metadata described above: Agent Script is what an author writes, and the platform compiles it down into the lower-level runtime metadata.

**Compiled, not interpreted.** Agent Script is a compiled language. Per the docs, "When you save a version of the agent, the script compiles into lower-level metadata that is used by the reasoning engine." The consequence for source control: the script is the source of truth, and the compiled metadata is a build artifact. Editing the compiled metadata directly rather than the script is the same anti-pattern as hand-editing generated output.

**Hybrid reasoning — two instruction types.** Agent Script "combines deterministic logic with LLM reasoning in a single workflow. This hybrid approach gives you predictable execution where you need it, while preserving the LLM's ability to handle nuanced conversations." There are two instruction types:

- **Logic instructions** use `->` and "run deterministically every time. Use them for business rules, running actions, setting variables, and conditional branching." These are the parts of an agent whose behavior you can guarantee.
- **Prompt instructions** use `|` and contain "natural language sent to the LLM. The LLM interprets these instructions and decides how to respond to the customer." These are the parts you cannot fully guarantee — the same routing-quality concern that applies to topic descriptions (see below) applies here.

Deciding which behavior belongs in a `->` logic instruction (deterministic: compliance checks, entitlement lookups, variable math, branching) versus a `|` prompt instruction (conversational: greeting, summarizing, empathetic handling) is the core design skill for Agent Script, and it is where hybrid reasoning earns its reliability.

**Whitespace-sensitive.** Agent Script "is whitespace-sensitive, similar to languages like Python or YAML, meaning that indentation is used to indicate structure and relationships between properties." Mixed tabs/spaces and inconsistent indentation are structural errors, not cosmetic ones.

**`@`-prefixed resource references.** Resources are accessed using the `@` symbol. The documented patterns are `@actions.<action_name>`, `@subagent.<subagent_name>`, `@variables.<variable_name>`, and `@outputs.<output_name>`. A set of built-in utilities is exposed under `@utils`, including `@utils.escalate` (escalate to a human service rep), `@utils.setVariables` (instruct the LLM to set variable values), and `@utils.transition to` (transition to a different subagent).

**Top-level statement set.** The reference documents these top-level blocks: `config` (agent configuration), `connection` (external connections such as Enhanced Chat), `language` (supported languages), `system` (agent instructions and messages), `variables` (global agent variables), `subagent` (a subagent's instructions and actions), `start_agent` (entry point for subagent classification and routing), `reasoning` (instructions and tools for the LLM), and `after_reasoning` (an optional block inside a subagent that runs after the reasoning loop exits).

**Control flow and action invocation.** Conditional branching uses `if` / `else` (for example, `if @variables.is_member == True:`), with comparison operators including `==`, `!=`, `<`, `>`, and `is None` / `is not None`. Actions are invoked with `run` (execute an action deterministically), `set` (store a value in a variable), and `with` (bind an input parameter).

**Terminology — topics are now subagents, but the API surface did not rename.** Per the reference, "Beginning in April 2026, agent topics are now called subagents. There are no changes to functionality." Treat "topic" and "subagent" as the same concept; the routing-quality concern is unchanged by the rename.

The rename landed in the docs and the Builder UI only. **The metadata and testing APIs still say "topic," and renaming them breaks the deploy:**

| Surface | Vocabulary as of Summer '26 |
|---|---|
| Agentforce dev guide, new Builder UI | subagent |
| `GenAiPlugin` metadata type | still "Represents an agent topic, which is a category of actions related to a particular job to be done by AI agents." The word *subagent* does not appear on that page. |
| `AiEvaluationDefinition` expectation names | still `topic_sequence_match` (alongside `action_sequence_match`, `bot_response_rating`, `output_latency_milliseconds`, `string_comparison`, `numeric_comparison`, and the coherence/completeness/conciseness metrics) |

So the mixed vocabulary a user sees is expected, not drift. There is no `GenAiSubagent` type and no `subagent_sequence_match` expectation.

**Three authoring surfaces in the new Builder.** The new Agentforce Builder exposes Agent Script through three views, and choosing the right one is part of the workflow:

- **AI Assistance** — chat with Agentforce and describe what you want the agent to do; the system converts the request into structured components. Best for a first draft or bootstrapping an unfamiliar surface.
- **Canvas** — Agent Script is "summarized into easily understandable blocks, which you can expand to view the underlying script." Best for review and for non-authors reasoning about behavior.
- **Script view** — "Advanced users can switch to Script view to write and edit script directly, with developer-friendly aids like syntax highlighting, autocompletion, and validation." This is the surface that corresponds most directly to source-controlled authoring.

**Maturity — GA as of Summer '26, and the legacy builder is closed to new agents.** Agent Script is no longer pre-GA. The Summer '26 developer release guide states: "Agent Script — a scripting language for AI agents that gives builders precise control by blending deterministic rules with agentic reasoning — and the new Agentforce Builder are now generally available (GA)." It also sets a hard cutover: "Starting the week of July 13, 2026, the New Agent button no longer opens the legacy builder in Setup. New agents are created only in the new Agentforce Builder." Existing legacy agents are not force-migrated; there is an explicit upgrade path — "Upgrading a legacy agent converts all subagents, actions, system messages, data, and connections to Agent Script, then optionally optimizes it for reliability." Plan any 2025-era "we'll stay on the legacy builder" position as end-of-life, not as a supported option for new work. The new Builder itself carries no additional cost: "No additional cost if you have purchased Agentforce. The new builder is available at no charge in Agentforce Studio."

**Open-sourced toolchain.** Salesforce open-sourced the Agent Script specification and its developer tooling — the parser (both a TypeScript parser and a Tree-sitter parser), an 18+-pass linter, the compiler (parsed AST → Salesforce runtime specification, with source-map support), and a Language Server Protocol implementation offering diagnostics, hover, completions, definition/references, rename, symbols, code actions, and semantic tokens — under Apache 2.0 at `github.com/salesforce/agentscript`. Because this repo is Apache 2.0, it is a viable dependency for local editor integration, CI linting, or custom validation. The **execution runtime is not open source**: "Agent Script compiles to a Salesforce-internal specification format that executes on Salesforce infrastructure," so "you can parse, lint, compile, and build tooling around Agent Script, but running agents requires Salesforce's runtime environment."

### LLM-Driven Orchestration vs. Legacy Einstein Bot FSM

Legacy Einstein Bots used a finite state machine (FSM): dialog flows defined explicit transitions between states, and conversation routing was deterministic. Agentforce agents use LLM-driven orchestration: the GenAiPlanner uses a language model to decide at runtime which topic to invoke and which action to execute within that topic, based on the user's utterance and the planner instructions.

This distinction has direct implications for metadata authoring. In an FSM bot, gaps in dialog states produce predictable fallthrough behavior. In an Agentforce agent, poorly written topic descriptions or action descriptions cause the LLM to route incorrectly — routing issues manifest as wrong-topic invocation or no-topic fallback, not as errors in the metadata itself. Debugging a misbehaving agent therefore requires reviewing the natural-language content of topic and action descriptions, not just the structural validity of the metadata.

### sf agent test run — CLI-Based Agent Testing

The `sf agent test run` command (Beta as of Spring '26) executes automated agent tests defined as `.aiTest` metadata records against a deployed agent in a target org. Tests specify input utterances and expected outcomes (expected topic classification, expected action invocation, or expected response text patterns). This command is the primary mechanism for verifying agent behavior in CI pipelines without a live UI session.

```bash
sf agent test run \
  --spec force-app/main/default/aiTests/myAgentTest.aiTest-meta.xml \
  --target-org MySandbox \
  --wait 10
```

Key behaviors:
- Requires the agent to be Active in the target org. Running `sf agent test run` against an Inactive or Draft agent returns an error.
- Tests run asynchronously in the org. The `--wait` flag sets a polling timeout in minutes (default 5).
- Exit code 1 indicates test failure or timeout; exit code 0 indicates all assertions passed.
- As a Beta feature, the command signature and assertion schema may change between Salesforce releases. Pin the `@salesforce/plugin-agent` CLI plugin version in CI pipeline tooling.

---

## Common Patterns

### Pattern 1: Source-Control-First Agent Development

**When to use:** Creating a new Agentforce agent or making topology changes (new topics, restructured actions) and managing them through version control with a CI/CD pipeline.

**How it works:**

1. Initialize the agent definition with the Salesforce CLI:
   ```bash
   sf agent generate agent --name MyServiceAgent --target-org DevSandbox
   ```
   This scaffolds a `.agent` file and the corresponding GenAiPlugin/BotVersion stubs in the DX project.
2. Edit the `.agent` file in VS Code with the Agentforce extension active. The LSP provides inline validation.
3. Iterate on `spec.plannerInstructions`, topic descriptions, and action references locally.
4. Deploy the full metadata bundle:
   ```bash
   sf project deploy start \
     --metadata Bot:MyServiceAgent \
     --metadata BotVersion:MyServiceAgent.v1 \
     --metadata GenAiPlannerBundle:MyServiceAgent \
     --metadata GenAiPlugin:MyServiceAgent_TopicOne \
     --target-org DevSandbox
   ```
5. Activate the agent in the target org (activation is not scriptable via Metadata API; it is a UI action).
6. Run agent tests:
   ```bash
   sf agent test run --spec force-app/.../myTest.aiTest-meta.xml --target-org DevSandbox
   ```

**Why not UI-only authoring:** UI-only authoring produces configuration that lives only in the org. It cannot be reviewed in pull requests, rolled back deterministically, or promoted through a pipeline without manual re-entry. YAML-based authoring provides auditability, reviewability, and repeatable deployment.

### Pattern 2: Retrieve-Before-Edit to Prevent State Divergence

**When to use:** Any time an agent has been modified in the Agentforce Builder UI and those changes need to be reconciled with the source-control version.

**How it works:**

1. Retrieve the current deployed state before editing:
   ```bash
   sf project retrieve start \
     --metadata Bot:MyServiceAgent \
     --metadata BotVersion:MyServiceAgent.v1 \
     --metadata GenAiPlannerBundle:MyServiceAgent \
     --metadata "GenAiPlugin:MyServiceAgent_*" \
     --target-org DevSandbox
   ```
2. Diff the retrieved files against the local working copy using Git.
3. Resolve conflicts before committing. Pay special attention to `plannerInstructions` blocks — these are plain-text fields and are overwritten entirely by each retrieve.
4. Commit the reconciled state, then redeploy from the branch.

**Why not skip the retrieve:** Deploying stale `.agent` files over a more recent org state can silently regress changes made in the Builder UI. In production, this can take an active agent and replace its instructions with an older version.

### Pattern 3: Debugging Routing Failures with DSL Content Inspection

**When to use:** An agent routes to the wrong topic or falls back to "I can't help with that" even when the topic clearly applies.

**How it works:**

1. Open the `.agent` file and review `spec.topics[*].description` for each topic. The description is the primary signal used by the LLM planner for classification.
2. Check for overlapping descriptions across topics — the planner may be ambiguous about which topic to invoke.
3. Review `spec.plannerInstructions` for any negative constraints that might be inadvertently excluding valid queries.
4. Redeploy updated descriptions, retest with `sf agent test run`.
5. If the problem persists, retrieve the latest `GenAiPlugin` XML for the affected topic and verify the description stored in the org matches the `.agent` file.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New agent with no source control history | Generate with `sf agent generate agent`, build in VS Code with LSP | Establishes source-of-truth in version control from the start |
| Agent exists only in org, needs to move to source control | Retrieve all metadata layers, commit, then manage via pipeline | Retrieve-first prevents state divergence from the first deploy |
| Project `sourceApiVersion` is 60.0–63.0 | Use GenAiPlanner, not GenAiPlannerBundle | GenAiPlannerBundle replaces GenAiPlanner only at API v64.0+ (Summer '25); the project pin decides, not the org release |
| Agent authored in the new Agentforce Builder needs to reach source control | Add `AiAuthoringBundle` to the manifest and raise `sourceApiVersion` to 65.0+ | The `.agent` Agent Script source lives only in that type; a Bot/BotVersion/GenAiPlugin manifest versions an incomplete agent |
| CI pipeline needs automated agent testing | Use `sf agent test run` with `.aiTest` metadata | Only scriptable agent test mechanism; exit codes integrate with CI |
| Topic routing is inconsistent | Edit topic descriptions in `.agent` file, not action definitions | The LLM planner uses topic descriptions for routing; actions are invoked after routing |
| Agent changes made in Builder UI | Retrieve before next deploy | Prevents overwriting org state with stale source |
| Behavior must run identically every time (compliance gate, entitlement check, variable math) | Author it as a `->` logic instruction in Agent Script | Logic instructions run deterministically; prompt instructions delegate to the LLM |
| Behavior is conversational (greeting, summarizing, empathy) | Author it as a `|` prompt instruction | Natural-language handling is what the LLM layer is for |
| Bootstrapping an unfamiliar agent from scratch | Start in the Builder's AI Assistance view, then refine in Script view | AI Assistance turns intent into structured components; Script view is the source-control-aligned surface |
| Need local linting/validation of Agent Script in CI | Use the open-sourced `salesforce/agentscript` parser/linter/compiler (Apache 2.0) | Apache-2.0 license permits local tooling; the runtime stays proprietary but authoring tooling does not require it |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm environment** — verify the Salesforce CLI version and `@salesforce/plugin-agent` plugin version, then read the project's `sourceApiVersion` pin in `sfdx-project.json` (not the org's release banner). It selects GenAiPlanner (60.0–63.0) or GenAiPlannerBundle (64.0+), and it must be 65.0+ if the agent was authored in the new Agentforce Builder and therefore carries an `AiAuthoringBundle`.
2. **Retrieve current state** — before making any changes, retrieve the Bot, BotVersion, GenAiPlannerBundle/GenAiPlanner, and all GenAiPlugin records from the target org. Diff against the local working copy and resolve conflicts.
3. **Author or edit the `.agent` file** — use VS Code with the Salesforce Agentforce extension. Address any LSP diagnostic warnings before proceeding. Pay particular attention to topic description quality and the `plannerInstructions` block.
4. **Deploy the full metadata bundle** — deploy Bot, BotVersion, GenAiPlannerBundle, and all GenAiPlugin records together. Never deploy a subset of the bundle.
5. **Activate the agent** — navigate to Setup > Agentforce Agents (or Agentforce Builder) and explicitly activate the agent in the target org. Activation is not automated via Metadata API.
6. **Run agent tests** — execute `sf agent test run` against the target org. Review output for routing failures, action invocation failures, or assertion mismatches. Iterate on topic or planner instruction content as needed.
7. **Commit and promote** — commit the full metadata bundle (`.agent` file plus all generated XML) and promote through the pipeline. Repeat activation in each target org after deployment.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Project `sourceApiVersion` confirmed; GenAiPlanner (60.0–63.0) vs GenAiPlannerBundle (64.0+) selected from the project pin, not the org release.
- [ ] If the agent is authored in the new Agentforce Builder: `AiAuthoringBundle` is in the manifest and `sourceApiVersion` is 65.0+.
- [ ] No API identifier was "modernized" to the subagent vocabulary — `GenAiPlugin` and `topic_sequence_match` are still correct.
- [ ] All metadata layers retrieved from the target org before editing.
- [ ] `.agent` file has no LSP diagnostic errors or warnings in VS Code with Agentforce extension.
- [ ] Topic descriptions are distinct and non-overlapping to avoid LLM routing ambiguity.
- [ ] `plannerInstructions` block contains specific, deterministic persona and constraint language.
- [ ] Agent API name is finalized — it cannot be changed after first deployment.
- [ ] Full metadata bundle (Bot + BotVersion + GenAiPlannerBundle + all GenAiPlugin) deployed together.
- [ ] Agent activated in the target org after deployment.
- [ ] `sf agent test run` passes with exit code 0.
- [ ] All metadata files committed to version control before promoting to the next environment.
- [ ] Activation repeated manually in each target environment after pipeline promotion.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **GenAiPlannerBundle requires API v64.0+ — which is Summer '25, not Spring '26** — projects with `sourceApiVersion` set to 63.0 or lower in `sfdx-project.json` cannot use GenAiPlannerBundle, and the deploy fails with an unknown-type error naming it. The common misattribution (v64 = Spring '26) puts the cutover three releases too late and leads teams to believe a Winter '26 or Spring '26 sandbox is "too old" for the bundle type when the real blocker is their own project pin. Set `"sourceApiVersion": "64.0"` or higher — that is the documented sfdx-project.json key; a hand-written `apiVersion` property is ignored by the CLI.
2. **Activation is not deployable** — the Active/Inactive/Draft state of an agent is not part of any deployable metadata record. Every org promotion requires a manual activation step in Setup. Pipelines that skip post-deploy activation steps will leave agents in Inactive state silently.
3. **Partial bundle deploys cause state divergence** — deploying GenAiPlugin records without the BotVersion, or vice versa, can leave the org in a state where the deployed agent references metadata that does not match the deployed plugin set. Always deploy the full bundle atomically.
4. **Topic description content drives routing, not metadata structure** — structural validity (correct YAML schema, correct XML element nesting) does not guarantee correct agent behavior. LLM routing is based on the natural-language quality of topic descriptions. A valid deploy of a well-structured `.agent` file with vague topic descriptions produces a broken agent with no metadata errors.
5. **`sf agent test run` requires an Active agent** — running agent tests against a Draft or Inactive agent returns an error that is easy to misread as a CLI or credential problem. Always confirm the agent is Active in the target org before running CI test jobs.
6. **Agent Script is whitespace-sensitive** — like Python or YAML, indentation carries structure. A misindented `->` logic block or `|` prompt block silently changes which subagent or reasoning block an instruction belongs to. Configure the editor to show whitespace and never mix tabs and spaces in a `.agent`/script file.
7. **Deterministic vs. LLM behavior is a choice you make, not a default** — putting a business rule in a `|` prompt instruction instead of a `->` logic instruction hands a guarantee-required check (entitlement, compliance gate, variable math) to the LLM, which may not honor it every time. Behavior that must be reliable belongs in `->` logic instructions; only conversational nuance belongs in `|` prompt instructions.
8. **"Topic" and "subagent" are the same thing after April 2026 — but only in the docs and the UI** — the rename is terminology only, with no functional change, and it never reached the API. `GenAiPlugin` is still documented as "an agent topic," and `AiEvaluationDefinition` still expects `topic_sequence_match`. Renaming either to match the new vocabulary produces an unknown metadata type or an invalid expectation name. Do not treat a diff that only swaps this vocabulary as a behavioral change, and do not "modernize" API identifiers.
9. **Do not hand-edit compiled agent metadata** — Agent Script compiles to lower-level runtime metadata on save. The script is the source of truth; the compiled metadata is a build artifact. Editing the compiled output rather than the script produces the same divergence problem as partial bundle deploys.
10. **Agent Script went GA in Summer '26 and the legacy builder no longer creates agents** — beta-era caveats ("pilot," "open beta," "no GA date") are stale. From the week of July 13, 2026 the New Agent button no longer opens the legacy builder in Setup; new agents are created only in the new Agentforce Builder. Existing legacy agents keep running and have an explicit upgrade path, so this is an end-of-life clock on legacy authoring, not an outage. Still pin CLI plugin versions and keep the open-sourced `salesforce/agentscript` tooling aligned with your target release.
11. **A five-type agent manifest is an incomplete agent** — Bot + BotVersion + GenAiPlannerBundle + GenAiPlugin + GenAiFunction captures the runtime metadata but not the Agent Script source, which lives in `AiAuthoringBundle` (API v65.0+). A pipeline built on the older list deploys a working-looking agent whose blueprint was never versioned, so the next Builder edit has nothing to diff against. Add `AiAuthoringBundle` and set `sourceApiVersion` to 65.0 or higher.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.agent` YAML file | Declarative agent definition for VS Code authoring and version control |
| Agent Script source | Hybrid-reasoning script (`->` logic and `|` prompt instructions, `subagent`/`reasoning` blocks, `@`-references) authored in the new Agentforce Builder Script view; compiles to runtime metadata on save |
| AiAuthoringBundle directory | `aiAuthoringBundles/<Name>/<Name>.agent` + `<Name>.bundle-meta.xml` (API v65.0+) — the design-time source of truth for a Builder-authored agent |
| GenAiPlugin XML records | Metadata files for each topic, containing topic description and action references |
| GenAiPlannerBundle XML | Metadata linking the planner instructions and plugins to the BotVersion |
| BotVersion XML | Agent container with channel settings and GenAiPlannerBundle reference |
| sf agent test run commands | CLI invocations for CI pipeline agent testing with exit-code integration |
| Metadata deploy command set | Full `sf project deploy start` commands targeting the complete agent bundle |

---

## Related Skills

- `agentforce/agentforce-agent-creation` — use for UI-driven agent setup, channel assignment, activation, and lifecycle management in Setup.
- `agentforce/custom-agent-actions-apex` — use when the problem is implementing invocable Apex methods that serve as agent actions, not the metadata layer.
- `agentforce/agent-channel-deployment` — use when the problem is configuring Embedded Service, Messaging for Web, or Agent API channel surfaces.
- `devops/scratch-org-management` — use when agent development involves scratch orgs, unlocked packages, or org shape-based environment management.
