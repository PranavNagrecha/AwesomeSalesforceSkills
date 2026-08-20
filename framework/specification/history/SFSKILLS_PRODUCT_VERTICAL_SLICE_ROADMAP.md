# SfSkills Product Vertical Slice Roadmap

## Executive decision

Do not run the previous Platform Foundation v2 prompt.

The right direction is neither a platform-first rewrite nor a collection of disconnected product prompts. Build a product vertical slice: two high-value Salesforce diagnoses that force the smallest reusable architecture needed for installability, context control, evidence, safety, and real-org QA.

The first products are:

1. Deployment Failure Triager
2. Apex Test Failure Triager

The third candidate, after the architecture is proven, is Permission Path Explainer (`/why-cant-user`).

## What already exists

SfSkills already has a meaningful control plane:

- 1,034 skill packages and tiered Claude routers;
- 48 active runtime agents plus build/deprecated agents;
- 67 commands;
- 38 MCP tools, mostly read-only;
- structural validators and fixtures;
- live-org probe and factuality validation;
- optional builder harnesses that can validate work against an org.

The missing product capabilities are more precise:

- native Cursor plugin distribution;
- curated Cursor subagents with isolated contexts;
- real delegation and structured handoff;
- execution-time context budgets;
- bounded and normalized MCP evidence;
- real-org behavioral QA with planted, known ground truth;
- product-level quality metrics.

## Where the existing QA stops

Current live-org validation proves useful things: probe SOQL can execute, referenced fields/objects can be checked, agent dependencies resolve, and envelopes can be structurally valid. It does not prove that a model, using the actual selected skill contents and real MCP evidence, produces the correct diagnosis.

The model fixture executor is also not a complete simulation of product behavior when it lacks live tools, uses org stubs, or omits the contents of mandatory skill reads. A test can therefore pass while the user-facing reasoning path remains untested.

## Context-rot diagnosis

SfSkills has solved much of startup discovery context for Claude. It has not fully solved execution context.

Several runtime agents declare broad dependency sets, and some declare more than 40 Salesforce skill reads. Loading a union of every possibly relevant skill creates four risks:

1. Relevant rules lose salience.
2. Conflicting or conditional rules appear equally mandatory.
3. Tool evidence competes with general guidance.
4. Compaction can preserve a weak summary while dropping exact evidence and constraints.

The solution is not simply a larger context window. The product needs:

- small core context;
- conditional context packs selected from observed evidence;
- focused subagents with separate contexts;
- structured handoffs rather than transcripts;
- bounded MCP output and evidence IDs;
- context telemetry;
- tests before and after compaction or long conversations.

## Design principles

1. Start with a user job, then add the minimum platform primitive it needs.
2. Treat context as a budget, not a storage layer.
3. Use progressive disclosure for skills, source files, and org evidence.
4. Give each subagent one clear responsibility.
5. Pass facts and evidence references, not complete transcripts.
6. Preserve raw, redacted evidence outside the model prompt when practical.
7. Require evidence for material diagnoses.
8. Label repository-only, fixture-verified, live-read-only, and scratch-QA modes distinctly.
9. Keep all product Salesforce tools read-only.
10. Permit controlled mutations only in disposable scratch-org QA setup scripts that are never exposed as agent tools.
11. Use deterministic code for parsing, redaction, normalization, pagination, policy, and grading.
12. Return honest partial/refused states when evidence is unavailable.
13. Measure context consumption and outcome quality, not inventory size.
14. Use one reviewable pull request per vertical step.

## Target Cursor product

The default Cursor plugin should contain a bounded discovery and execution surface rather than 1,034 flattened rules.

Suggested product package:

```text
sfskills-cursor/
  .cursor-plugin/
    plugin.json
  skills/
    salesforce/
      SKILL.md
    salesforce-apex/
      SKILL.md
    salesforce-devops/
      SKILL.md
    ... bounded domain routers ...
  agents/
    sf-context-librarian.md
    sf-repo-mapper.md
    sf-org-grounder.md
    deployment-failure-triager.md
    apex-test-failure-triager.md
    sf-evidence-reviewer.md
  commands/
    sfskills-doctor.md
    triage-deployment.md
    triage-apex-tests.md
  hooks/
    hooks.json
  mcp.json
```

The default plugin should not expose all 48 agents. The existing specialist agents remain reachable through the repository and MCP, while only proven, focused native subagents are packaged.

## Subagent model

### `sf-context-librarian`

Select the smallest relevant skill/reference set. It returns paths, relevance reasons, and an estimated budget. It does not perform the final diagnosis.

### `sf-repo-mapper`

Inspect repository files and map failures to metadata, Apex, tests, and dependencies. It returns file/line evidence and unknowns.

### `sf-org-grounder`

Call approved read-only MCP tools and return normalized facts. It does not recommend mutations and does not return unbounded CLI output.

### `deployment-failure-triager`

Diagnose failed deployments from the compact skill context, repository map, and org evidence.

### `apex-test-failure-triager`

Cluster failing tests and diagnose shared root causes from test results, stack traces, source, and focused skills.

### `sf-evidence-reviewer`

Independently challenge unsupported claims, missing evidence, contradictory conclusions, unsafe actions, and confidence inflation.

The parent command should receive only structured handoffs from these subagents.

## Context contract

For each pilot:

- core Salesforce reads: 3-5;
- target total domain skill/reference reads: no more than 8;
- hard limit: 12 unless an explicit overflow state is returned;
- single MCP output injected into context: no more than 32 KiB;
- larger result sets must be normalized, deduplicated, and paginated;
- every selected file has a reason;
- every tool fact receives a stable evidence ID;
- telemetry records files, estimated tokens, tool bytes, truncation, subagents, citations, and compaction events.

Suggested handoff shape:

```json
{
  "run_id": "...",
  "task": "...",
  "facts": [],
  "evidence_refs": [],
  "hypotheses": [],
  "unknowns": [],
  "recommended_next_agent": null,
  "context_metrics": {
    "files_loaded": 0,
    "estimated_tokens": 0,
    "tool_output_bytes": 0,
    "truncated": false
  }
}
```

## Real-org QA model

### Lane A: Hermetic PR validation

No credentials. Test schemas, normalizers, redaction, pagination, evidence references, context budgets, policy guards, plugin generation, and captured Salesforce CLI fixtures.

### Lane B: Persistent read-only QA org

Manual or scheduled. Run existing probes, factuality checks, and read-only MCP smoke tests. This detects API and org-shape drift but does not claim end-to-end reasoning quality.

### Lane C: Ephemeral scratch-org behavioral QA

Create a scratch org through a protected Dev Hub secret. Setup scripts may deploy fixture metadata, create fixture users/data, and run tests solely inside that disposable org. Then product agents use only read-only result tools. Grade their structured findings against known ground truth and always delete the scratch org.

The product/tool boundary and QA/setup boundary must be explicit:

```text
QA setup scripts: controlled scratch-org mutation allowed
Product agents and MCP tools: read-only only
```

## Known-truth scenarios

### Deployment triage

Start with four to six:

- missing custom field or metadata dependency;
- Apex compile/type failure;
- deployment test failure;
- many duplicate symptoms caused by one component;
- reliable API/feature mismatch;
- reliable environment or permission prerequisite.

### Apex test triage

Start with four to seven:

- assertion mismatch;
- Mixed DML;
- missing callout mock;
- governor-limit amplification;
- sharing/user-context assumption;
- asynchronous test-boundary issue;
- one root cause shared across multiple methods.

Ground truth should use stable finding IDs and required evidence facts, not exact prose.

## Four pull requests

### PR 1: Native Cursor plugin plus Deployment Failure Triager

Ship the first actual product:

- native Cursor plugin and local install helper;
- bounded domain routers and bundled MCP configuration;
- `sfskills-doctor` and explicit `index_missing` behavior;
- `/triage-deployment`;
- read-only `get_deployment_result` MCP tool;
- context librarian, repo mapper, org grounder, deployment triager, evidence reviewer;
- pilot context pack and structured handoff;
- shell/MCP safety hooks;
- captured fixture tests and manual local Cursor smoke test.

Human gate: install it and use it on a real failed deployment result before PR 2.

### PR 2: Apex Test Failure Triager and context resilience

Reuse the PR 1 architecture:

- `/triage-apex-tests`;
- read-only `get_apex_test_run`;
- Apex triager and bounded context pack;
- shared-root-cause clustering;
- long-result, distractor, second-task, contradictory-evidence, and compaction-aware tests;
- context and evidence reviewer metrics.

Human gate: compare both pilots against vanilla Cursor/Claude on the same fixtures.

### PR 3: Real-org behavioral QA lab

- versioned scratch-org fixture project;
- protected scratch-org workflow with unconditional cleanup;
- at least four real deployment and four real Apex scenarios;
- actual MCP normalization path;
- actual selected skill content in the agent evaluator;
- deterministic hard assertions plus nonblocking subjective rubric;
- run metadata, context metrics, artifacts, and redaction checks.

Human gate: inspect failures and decide whether the products are credible.

### PR 4: Product hardening and release candidate

- install/uninstall polish;
- release packaging and version alignment;
- targeted queue pointer fix;
- targeted no-persist envelope fix;
- typed specs only for shipped Cursor commands;
- truthful docs and demo scripts;
- current QA report;
- decision record for `/why-cant-user` versus other next products.

## Explicitly deferred

- full capability registry/graph;
- general workflow engine;
- Backlog v2 migration;
- all 67 command schemas;
- all decision trees compiled;
- migration of every existing agent to context packs;
- Claude plugin rewrite;
- ten additional agents;
- public Cursor Marketplace claim;
- any customer-org mutation tool.

These are not rejected forever. They become eligible only when repeated pilot implementation shows a concrete maintenance problem that the abstraction would solve.

## Product success measures

The release candidate should report:

- local install success;
- correct command and subagent discovery;
- required-finding recall on known-truth scenarios;
- unsupported-claim rate;
- evidence-reference validity;
- safety-policy violations;
- context files and estimated tokens per run;
- tool bytes before/after normalization;
- truncation and compaction behavior;
- partial/refusal correctness;
- exact date and environment of real-org QA.

Do not publish a single accuracy headline without the dataset, labels, model/client versions, scoring method, and run date.
