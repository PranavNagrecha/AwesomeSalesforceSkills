# Executive product thesis

## The category

SfSkills should create the **Salesforce AI Engineering Framework** category: a portable, evidence-grounded reasoning and QA layer that makes agentic development tools behave like a disciplined Salesforce engineering team.

It does not need to replace mature CI/CD, metadata graph, test automation, or Salesforce-native developer platforms. It should connect to them, constrain them, explain their evidence, and independently measure whether agent outputs are useful and safe.

## The unmet need

General-purpose coding agents are fast but inconsistent on Salesforce because the platform combines metadata, org configuration, security, automation ordering, deployment state, API/version behavior, and customer-specific context. A model can produce plausible advice while missing the exact org condition that matters.

SfSkills already owns a valuable raw material: 1,034 curated Salesforce skill packages with anti-pattern guidance, tiered discovery, 48 active runtime agents, 67 commands, and a mostly read-only MCP surface. The missing layer is a product runtime that turns that knowledge into bounded, evidenced, reviewed outcomes.

## The product promise

> Give SfSkills a Salesforce job, project, org, or captured result. It will gather the smallest relevant knowledge and read-only evidence, produce explicit claims linked to provenance, challenge its own answer, and return a replayable result with honest unknowns.

## Why now

Salesforce now ships an official DX MCP server with a broad tool surface and Agentforce Vibes as an org-aware development experience. Cursor, Claude Code, and VS Code/Copilot support portable skills, agents, MCP, hooks, and increasingly rich agent workflows. Open protocols are maturing around tools, plugins, skills, and agent-to-agent communication.

Those platforms reduce the value of building another generic tool wrapper. They increase the value of a Salesforce-specific control and intelligence layer that is portable, least-privilege, evidence-aware, context-efficient, and empirically evaluated.

## Initial wedge

The first three products are:

1. deployment failure triage;
2. Apex test failure triage;
3. access-path explanation.

They are frequent, expensive, evidence-rich, easy to demonstrate, and difficult for generic models to solve reliably. They also force reusable architecture for project discovery, org identity, result normalization, evidence IDs, context selection, independent review, and scratch-org known truth.

## Defensible moat

- A large anti-pattern-rich Salesforce knowledge corpus with source governance.
- A claim/evidence architecture rather than prose-only prompting.
- Context budgets and compaction-resilient checkpoints.
- A read-only policy broker over official and local tools.
- A versioned scratch-org behavioral benchmark.
- Host-neutral contracts and multiple adapters.
- A contribution model where new knowledge, products, and scenarios improve one shared quality system.

## North star

**Weekly evidenced resolutions:** product runs that a user accepts or acts on, whose material claims have valid evidence and whose independent review has no blocker.
