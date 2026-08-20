# Market map — August 2026

## Layer 1: Salesforce platform and official agent tooling

Salesforce’s official DX MCP server exposes more than sixty tools across toolsets and warns that enabling all tools can overwhelm model context. It includes both read and write capabilities. Headless 360 takes the opposite surface design: four stable tools backed by a growing skill library. Salesforce Code Analyzer has also moved agent workflows toward portable skills. Agentforce Builder is graph-based around subagents and state transitions, while Agentforce testing has CLI and evaluation workflows.

**Implication:** SfSkills must not compete by wrapping every Salesforce API. It should use official capabilities selectively and own product contracts, context, evidence normalization, policy, review, and QA above them.

Relevant source records: `SRC-SF-DX-MCP`, `SRC-SF-HEADLESS-360`, `SRC-SF-CODE-ANALYZER-SKILLS`, `SRC-SF-AGENTFORCE-BUILDER-2026`, `SRC-SF-AGENT-TESTING-CLI`.

## Layer 2: Agentic hosts

Cursor can package plugins, skills, subagents, commands, MCP, and hooks. Skills load progressively; subagents use separate contexts; hooks can observe and gate the agent loop, but local/cloud support differs. Claude Code and VS Code/Copilot provide related plugin/skill/agent surfaces. Agent Plugins offers an emerging portable packaging shape.

**Implication:** Build one canonical product model and thin adapters. Cursor is the first full-fidelity host, not the permanent proprietary runtime.

Relevant source records: `SRC-CURSOR-PLUGINS`, `SRC-CURSOR-SKILLS`, `SRC-CURSOR-HOOKS`, `SRC-CURSOR-SUBAGENTS`, `SRC-CLAUDE-PLUGINS`, `SRC-VSCODE-SKILLS`, `SRC-AGENT-PLUGINS`.

## Layer 3: Salesforce DevOps and release platforms

Gearset combines deterministic org/dependency analysis, AI-assisted investigation, testing, observability, and delivery. Copado Agentia embeds coordinated agents across planning, build, test, release, and operations. Flosum and DevOps Center address controlled delivery and governance.

**Implication:** Do not claim “AI DevOps platform” parity. Integrate pipeline/job evidence and provide portable diagnosis, independent validation, and model-output QA before and after release operations.

Relevant source records: `SRC-GEARSET-AI`, `SRC-COPADO-AGENTIA`, `SRC-SF-DEVOPS-CENTER`.

## Layer 4: Org intelligence and impact analysis

Elements.cloud, Salto, Gearset Org Intelligence, and Metazoa provide metadata/dependency maps, impact analysis, technical debt, documentation, and change intelligence.

**Implication:** SfSkills’ early project/org analysis should be evidence-aware and useful without pretending it has a complete enterprise dependency graph. It should ingest or link vendor evidence where possible and add cross-host reasoning, context control, and run assurance.

Relevant source records: `SRC-ELEMENTS-ORG-INTELLIGENCE`, `SRC-SALTO-SALESFORCE`, `SRC-GEARSET-AI`.

## Layer 5: Salesforce testing

Salesforce, Provar, Copado, Gearset, and others provide test creation/execution and regression systems.

**Implication:** SfSkills begins with failure diagnosis and agent-quality grading, not broad test automation replacement. It can become the cross-system explanation and benchmark layer.

## Layer 6: Community skill/prompt/tool repositories

Community repositories maximize breadth and reuse but often lack product outcomes, target evidence, permission boundaries, behavioral QA, and current-host conformance.

**Implication:** The existing SfSkills corpus is a strong knowledge substrate, but V2 succeeds only when users install one product and resolve a real problem.

## Market opening

The opening is the intersection of:

- practitioners already adopting agentic IDEs;
- Salesforce work whose answer depends on org/project/job evidence;
- teams unwilling to give a diagnostic agent write access;
- organizations that already own delivery/graph tools but lack portable AI assurance;
- consultants who need repeatable behavior across customers and hosts;
- builders who need to evaluate Agentforce agents themselves.
