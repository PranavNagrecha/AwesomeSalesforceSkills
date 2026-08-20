# SFAEF-160 — Host adapters and portability

## Portable core

The portable contract includes products, commands, skills, agents, schemas, tool specs, context/evidence policy, and QA scenarios. Host adapters translate these without changing semantics.

## Requirements

SFAEF-160-001. Every adapter MUST publish a host-capability record.

SFAEF-160-002. Unsupported guarantees MUST cause a documented fallback or capability-limited status.

SFAEF-160-003. Host artifacts MUST be generated from canonical framework definitions where practical.

SFAEF-160-004. Adapter tests MUST verify discovery, invocation, tool access, output, and safety in the actual host—not only file shape.

## Cursor

Use native plugin structure, progressive Agent Skills, a small curated subagent surface, commands, MCP configuration, and hooks. Local plugin installation is the initial distribution. Local and cloud hook differences must be documented.

## Claude Code

Use plugin skills, agents, hooks, and MCP. Preserve existing Claude compatibility and migrate only when a V2 product requires stronger contracts.

## VS Code/GitHub Copilot

Use Agent Skills, custom agents/handoffs, MCP, and workspace configuration. Treat experimental forked-context behavior as capability-detected, not guaranteed.

## Agentforce Vibes

Integrate with the official Salesforce project/org context and DX MCP. SfSkills contributes evidence policy, context selection, quality products, and benchmark—not a replacement editor.

## Portable Agent Plugins

Publish a portable plugin package when licensing and package semantics are resolved. Native adapters may add hooks/subagents that the portable format does not express.

## A2A

SFAEF-160-020. A2A MUST NOT be used merely to wrap in-process subagents.

SFAEF-160-021. Future A2A exposure requires agent identity, authorization, agent-card capability scope, task lifecycle, evidence-transfer rules, retention, and compatibility tests.
