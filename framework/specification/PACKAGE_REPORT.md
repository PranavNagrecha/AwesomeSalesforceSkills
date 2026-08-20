# Salesforce AI Engineering Framework — specification package report

**Package:** SfSkills Salesforce AI Engineering Framework Specification 0.9.0 draft  
**Research freeze:** 2026-08-19  
**Purpose:** Provide the product constitution, machine contracts, implementation sequence, reference controls, and review evidence needed to evolve the existing SfSkills repository into an evidence-grounded Salesforce AI engineering product.

## Executive result

This package designs the portion of the product that should exist before large-scale repository implementation. It is deliberately more than a roadmap and less than a claim that the integrated V2 product already exists.

It defines:

- what SfSkills V2 is and is not;
- the product category, market wedge, defensible differentiation, and adoption thesis;
- binding architecture, authority, evidence, context, run-state, portability, security, and quality requirements;
- 12 user-facing products and their complete execution contracts;
- a small framework-agent layer plus migration guidance for every current canonical agent;
- typed command APIs and normalized read-only evidence-tool APIs;
- deterministic behavioral oracles and validators;
- hermetic, live-read-only, and disposable scratch-org QA lanes;
- the exact local milestones Cursor must implement;
- the exact self-contained ZIP Cursor must return for product-owner review.

## Package scale

| Artifact | Count |
|---|---:|
| Normative specification chapters | 23 |
| Stable normative requirements | 266 |
| V2 products | 12 |
| New framework/product agent definitions | 20 |
| Current-agent migration profiles | 76 |
| Typed commands | 18 |
| Normalized evidence tools | 18 |
| Product context packs | 12 |
| Known-truth QA scenarios | 74 |
| JSON Schemas | 19 |
| Governed research-source records | 37 |
| Package files before final integrity artifacts | 525 |
| Markdown words before final integrity artifacts | 175,128 |

The uploaded baseline inventory represented 1,034 skills, 76 canonical agent definitions, 67 commands, and 38 current MCP tools. The V2 definitions do not erase those assets. They place them behind a smaller, governed product and execution surface.

## Product portfolio

1. Deployment Failure Triage
2. Apex Test Failure Triage
3. Access Path Explainer
4. Change Impact Planner
5. Automation Transaction Profiler
6. Release Readiness Review
7. Security Posture Review
8. Integration Incident Triage
9. Data Migration Reconciliation
10. Org Health Assessment
11. Agentforce Quality Engineer
12. Multi-Org Drift Analysis

The first three are the adoption wedge. The remaining products reuse the same evidence, context, review, and QA architecture rather than becoming disconnected prompt collections.

## Architectural center

The framework is organized into eight planes:

1. **Experience** — stable commands and product workflows.
2. **Agent** — narrow roles with bounded authority and isolated context where justified.
3. **Context** — progressive loading, budgets, checkpoints, and compaction recovery.
4. **Knowledge** — the existing curated Salesforce skill corpus with source governance.
5. **Evidence** — normalized project, org, job, test, metadata, access, log, and snapshot observations.
6. **Control** — typed inputs, target identity, policy, run state, and host capability negotiation.
7. **Quality** — deterministic lint, independent review, benchmark comparison, and known-truth scratch QA.
8. **Adapter** — Cursor first, with portable contracts for Claude Code, VS Code/Copilot, Agentforce Vibes, Agent Plugins, and future A2A interoperability.

## Non-negotiable product rules

- Product Salesforce access is read-only.
- Controlled mutation is permitted only in disposable scratch-org QA setup/teardown code that is not exposed as a model tool.
- Unknown tools are denied.
- Orgs, projects, jobs, runs, users, records, and snapshots are never guessed.
- SfSkills itself is not assumed to be the Salesforce DX project.
- External project inspection is optional enrichment and ambiguity is explicit.
- Context is budgeted: target eight domain files, hard limit twelve, and model-visible tool pages no larger than 32 KiB by default.
- Material target-specific claims require resolvable evidence.
- Independent review is required for completed product outputs.
- `partial`, `refused`, and `failed` are valid product outcomes; missing evidence is never hidden.
- Parsing, redaction, normalization, pagination, policy, identifiers, state, and hard grading belong in deterministic code.
- Commands are the stable user surface; the native agent surface remains intentionally small.

## Complete contract layer

Every V2 command definition now includes:

- aliases and supported modes;
- typed arguments and validation rules;
- stable terminal errors and recovery actions;
- orchestration stages;
- required agents, tools, and permissions;
- independent-review rules;
- explicit Salesforce, local-file, and network side effects;
- fixture/local and live-read-only examples.

Every evidence-tool definition includes:

- operation and permission class;
- explicit target-pinning behavior;
- result schema and evidence types;
- normalization and stable-evidence-ID rules;
- pagination, byte, timeout, retry, rate, and cache policies;
- sensitive-data classes and redaction profile;
- stable errors and audit events;
- required contract tests.

Every new agent definition includes:

- purpose, inputs, outputs, and product ownership;
- authority that cannot expand through user prose or another agent;
- required and prohibited evidence;
- context limits and no-transcript handoff;
- collaborators and failure modes;
- evaluation dimensions and prompt principles;
- completion-review requirement;
- recommended host exposure.

Generated references are available in:

- `commands/API_REFERENCE.md`
- `mcp/TOOL_REFERENCE.md`
- `agents/CONTRACT_REFERENCE.md`

## Competitive strategy

The product does not attempt to win by claiming that Salesforce AI, impact analysis, org intelligence, testing, or DevOps automation are new categories. Established vendors already market combinations of those capabilities.

The intended wedge is:

- portable execution across developer hosts rather than one proprietary control plane;
- curated Salesforce engineering reasoning rather than generic code completion;
- typed evidence and replay contracts rather than untraceable chat answers;
- explicit context engineering rather than loading a large corpus at once;
- least-privilege, deny-by-default product authority;
- independent claim review;
- disposable known-truth Salesforce behavioral QA;
- an open conformance model that can test multiple host implementations.

The “40%” objective is defined as sustained activation and repeat use inside a deliberately recruited early-adopter cohort, not an unsupported claim of 40% share of the broad Salesforce market.

## Validation performed in this package

The package-level suite executes:

- two independent package validators;
- generated-requirement and catalog checks;
- generated command/tool/agent contract checks;
- generated API-reference drift checks;
- 12 root contract tests;
- 6 return-package and validator tests;
- 34 deterministic reference-kernel tests;
- 19 optional project-inspector tests;
- Python compilation in an isolated cache directory.

That is **71 executable unit/contract tests**, plus schema, reference, generation, compilation, and package-integrity gates. The pre-manifest run log and machine report are under `validation/`.

## What remains for Cursor

This package does not claim that the existing SfSkills repository has already been transformed. Cursor must still:

- integrate the specification and reference controls into the actual repository;
- preserve and repair current local Phase 1/Phase 2 work;
- implement the deterministic runtime and restricted evidence broker;
- build and test the native Cursor plugin;
- implement all product paths and adapters;
- execute actual Cursor host tests;
- execute read-only Salesforce checks where available;
- build and run protected disposable scratch-org known-truth scenarios;
- compare products against a vanilla host/model baseline;
- return a reconstructable review ZIP with exact source, commits, logs, runs, QA, security, traceability, and checksums.

## Truthful limitation

This is the designed “80%”: product definition, architecture, contracts, schemas, portfolio, QA truth, market thesis, implementation order, and review system. It includes executable reference code, but it is not a substitute for host integration, live Salesforce evidence, empirical product tuning, or real-user adoption data.
