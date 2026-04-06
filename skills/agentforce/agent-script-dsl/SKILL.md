---
name: agent-script-dsl
description: "Authoring and managing Agentforce agent definitions using the declarative Agent Script DSL (.agent files) and associated metadata types. Use when creating agents in source control, debugging agent metadata, or understanding the metadata lifecycle of GenAiPlugin/GenAiPlanner/BotVersion types. Triggers: 'how do I deploy an Agentforce agent using source control', 'what metadata types make up an Agentforce agent', 'agent test run command failing in CI pipeline', 'GenAiPlugin vs GenAiPlanner metadata relationship'. NOT for Apex-based agent actions (use custom-agent-actions-apex). NOT for UI-based agent creation (use agentforce-agent-creation)."
category: agentforce
salesforce-version: "Spring '26+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I deploy an Agentforce agent using source control"
  - "what metadata types make up an Agentforce agent"
  - "agent test run command failing in CI pipeline"
  - "GenAiPlugin vs GenAiPlanner metadata relationship"
  - "how do I write or edit .agent files for version-controlled agent development"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Agent Script DSL

Use this skill when the work involves authoring, editing, validating, or deploying Agentforce agent definitions through source-controlled metadata rather than through the Agentforce Builder UI. This skill covers the YAML-based `.agent` file format, the three composite metadata types that make up an agent (GenAiPlugin, GenAiPlanner/GenAiPlannerBundle, BotVersion), LSP validation tooling, the `sf agent test run` CLI command, and the metadata deployment lifecycle end-to-end. It does not cover Apex implementation of invocable agent actions (use `agentforce/custom-agent-actions-apex`) and does not cover UI-driven agent creation workflow (use `agentforce/agentforce-agent-creation`).

Agentforce agent definitions are stored as YAML-based declarative metadata in `.agent` files within a Salesforce DX project. These files are the machine-readable representations of the same configuration surfaced in Agentforce Builder. Understanding the relationship between the three composite metadata types — GenAiPlugin, GenAiPlanner (or GenAiPlannerBundle from API v64+), and BotVersion — is essential for correct deployment and source control management.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the target Salesforce CLI and API version? GenAiPlannerBundle was introduced at API v64 (Spring '26). Projects targeting API v60–v63 use GenAiPlanner instead. Mixing versions in the same project causes deploy failures.
- Is the Salesforce Extensions for VS Code installed along with the Agentforce extension? LSP-based DSL validation requires both. Without them, YAML errors in `.agent` files produce silent or cryptic deploy failures.
- Is the project structured as a Salesforce DX project with `sfdx-project.json`? The `sf agent` CLI commands operate on DX-structured projects only.
- What is the current state of the agent in the org? Retrieving before editing is critical — manually authored `.agent` files that diverge from the deployed BotVersion state produce merge conflicts on the next retrieve.
- Are there existing GenAiPlugin or GenAiFunction metadata files in the project? These must be co-deployed with BotVersion and GenAiPlannerBundle as a unit.

---

## Core Concepts

### The Three Composite Metadata Types

An Agentforce agent in source control is not a single file. It is composed of three linked metadata types that must be deployed together as a bundle:

**GenAiPlugin** — the action definition layer. Each GenAiPlugin corresponds to a topic in Agentforce Builder. It declares the topic label, description (used by the LLM for topic classification), and references to the `GenAiFunction` records (actions) that belong to the topic. A plugin that has a vague or overlapping description will cause the LLM planner to route incorrectly, even if the metadata deploys cleanly.

**GenAiPlanner / GenAiPlannerBundle** — the orchestration configuration layer. GenAiPlanner (API v60–v63) or GenAiPlannerBundle (API v64+) configures the LLM reasoning engine: model selection, planner instructions (the system prompt), and the set of GenAiPlugins the agent can invoke. The bundle variant introduces the ability to link the planner to a BotVersion within a single metadata record, replacing the manual cross-reference approach of the earlier type.

**BotVersion** — the conversation container and channel routing shell. BotVersion wraps the Bot record and manages conversation session parameters, language settings, and fallback behavior. It also carries the reference that links a deployed agent to the GenAiPlannerBundle. BotVersion without a linked planner produces a legacy Einstein Bot, not an Agentforce agent. The presence of the `genAiPlannerBundle` element in BotVersion XML is the authoritative indicator that a BotVersion is an Agentforce agent and not a legacy scripted bot.

All three types must be retrieved and deployed as a coherent unit. Partial deploys — for example, deploying only GenAiPlugin changes without an updated BotVersion — will either fail validation or produce a deployed state that diverges from the source of truth in version control.

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
| API v60–v63 project (older sandbox) | Use GenAiPlanner, not GenAiPlannerBundle | GenAiPlannerBundle requires API v64+ (Spring '26) |
| CI pipeline needs automated agent testing | Use `sf agent test run` with `.aiTest` metadata | Only scriptable agent test mechanism; exit codes integrate with CI |
| Topic routing is inconsistent | Edit topic descriptions in `.agent` file, not action definitions | The LLM planner uses topic descriptions for routing; actions are invoked after routing |
| Agent changes made in Builder UI | Retrieve before next deploy | Prevents overwriting org state with stale source |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm environment** — verify the Salesforce CLI version, `@salesforce/plugin-agent` plugin version, and target org API version. Confirm whether the project targets GenAiPlanner (v60–v63) or GenAiPlannerBundle (v64+).
2. **Retrieve current state** — before making any changes, retrieve the Bot, BotVersion, GenAiPlannerBundle/GenAiPlanner, and all GenAiPlugin records from the target org. Diff against the local working copy and resolve conflicts.
3. **Author or edit the `.agent` file** — use VS Code with the Salesforce Agentforce extension. Address any LSP diagnostic warnings before proceeding. Pay particular attention to topic description quality and the `plannerInstructions` block.
4. **Deploy the full metadata bundle** — deploy Bot, BotVersion, GenAiPlannerBundle, and all GenAiPlugin records together. Never deploy a subset of the bundle.
5. **Activate the agent** — navigate to Setup > Agentforce Agents (or Agentforce Builder) and explicitly activate the agent in the target org. Activation is not automated via Metadata API.
6. **Run agent tests** — execute `sf agent test run` against the target org. Review output for routing failures, action invocation failures, or assertion mismatches. Iterate on topic or planner instruction content as needed.
7. **Commit and promote** — commit the full metadata bundle (`.agent` file plus all generated XML) and promote through the pipeline. Repeat activation in each target org after deployment.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] API version confirmed; GenAiPlanner vs GenAiPlannerBundle selected correctly.
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

1. **GenAiPlannerBundle requires API v64+** — projects with `apiVersion` set to v63 or lower in `sfdx-project.json` cannot use GenAiPlannerBundle. Attempting to deploy it produces a confusing "Unknown type" error. Set `apiVersion: 64.0` or higher before building Spring '26 agents.
2. **Activation is not deployable** — the Active/Inactive/Draft state of an agent is not part of any deployable metadata record. Every org promotion requires a manual activation step in Setup. Pipelines that skip post-deploy activation steps will leave agents in Inactive state silently.
3. **Partial bundle deploys cause state divergence** — deploying GenAiPlugin records without the BotVersion, or vice versa, can leave the org in a state where the deployed agent references metadata that does not match the deployed plugin set. Always deploy the full bundle atomically.
4. **Topic description content drives routing, not metadata structure** — structural validity (correct YAML schema, correct XML element nesting) does not guarantee correct agent behavior. LLM routing is based on the natural-language quality of topic descriptions. A valid deploy of a well-structured `.agent` file with vague topic descriptions produces a broken agent with no metadata errors.
5. **`sf agent test run` requires an Active agent** — running agent tests against a Draft or Inactive agent returns an error that is easy to misread as a CLI or credential problem. Always confirm the agent is Active in the target org before running CI test jobs.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `.agent` YAML file | Declarative agent definition for VS Code authoring and version control |
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
