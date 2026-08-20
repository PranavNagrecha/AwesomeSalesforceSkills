# Agentic platform and open-standards landscape

## Cursor as the first full-fidelity host

Cursor’s current customization surface composes plugins, progressively loaded skills, isolated subagents, commands, MCP servers, and lifecycle hooks. Local plugins can be tested from the current supported local directory. Hooks can observe and gate shell/MCP actions, subagents, file operations, prompts, and compaction, but local and cloud support are not identical and fail-closed behavior must be configured explicitly for security-critical hooks.

### Framework decision

Build a native Cursor plugin first, verify actual host behavior, and record a host-capability object per release. Never infer enforcement from file shape alone.

Sources: `SRC-CURSOR-PLUGINS`, `SRC-CURSOR-CUSTOMIZE`, `SRC-CURSOR-SKILLS`, `SRC-CURSOR-SUBAGENTS`, `SRC-CURSOR-HOOKS`, `SRC-CURSOR-CLOUD-AGENTS`.

## Agent Skills

Agent Skills is a portable package shape for instructions, scripts, templates, and references that loads progressively. Cursor, Claude, VS Code/Copilot, and Salesforce tooling increasingly align with this pattern.

### Framework decision

Existing SfSkills packages map naturally to the standard. Keep `SKILL.md` packages intact and load supporting resources only when selected. Do not flatten 1,034 packages into always-discoverable rules.

## Agent Plugins

Agent Plugins defines a portable package for skills and MCP servers. Cursor supports it alongside a richer native format; Claude and other hosts have related but different extension systems.

### Framework decision

Maintain portable product/skill/evidence contracts, then generate thin adapters. Native packages may add host-specific commands, subagents, hooks, and UX, but cannot alter product safety or evidence semantics.

Sources: `SRC-AGENT-PLUGINS`, `SRC-CLAUDE-PLUGINS`, `SRC-VSCODE-SKILLS`.

## MCP

MCP standardizes agent access to tools and data. Tool annotations communicate intent but are not an authorization boundary. Tool surfaces can also consume substantial context.

### Framework decision

The evidence broker independently enforces authority, target pinning, normalization, redaction, bounds, and unknown-tool denial. Upstream MCP is replaceable; evidence contracts remain stable.

Sources: `SRC-MCP-ANNOTATIONS`, `SRC-SF-DX-MCP`.

## A2A

A2A supports communication between independent agent systems and complements MCP. It is more appropriate for future cross-service or cross-organization work than ordinary in-host subagent delegation.

### Framework decision

Use host-native subagents and structured handoffs in V2. Defer A2A until task identity, authorization, evidence transfer, and conformance are proven.

Sources: `SRC-A2A-1`.

## Security and standards direction

NIST’s agent standards work emphasizes interoperability, identity, authorization, security, and trusted adoption. OWASP emphasizes agentic threat models, tool/supply-chain risk, memory, and the limits of human oversight.

### Framework decision

Explicit identity, least authority, untrusted evidence handling, memory boundaries, audit, and scenario-based assurance are baseline product requirements rather than enterprise extras.

Sources: `SRC-NIST-AGENTS`, `SRC-OWASP-AGENTIC`.
