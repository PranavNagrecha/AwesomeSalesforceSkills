# Shared MCP Probe Recipes

This directory is the single source of truth for the MCP query patterns that agents re-use across domains. Before an agent inlines a `tooling_query(...)` call in its Plan, it should check here first.

## Why this exists

Every data-heavy agent was re-writing the same probes (Apex body scan, Flow metadata scan, matching-rule listing). When one probe's false-positive logic improved, the others drifted. Centralizing the recipes:

- fixes the same false-positive-avoidance logic in one place
- gives us one spot to correct pagination, word-boundary matching, and managed-package filters
- lets `validate_repo.py --agents` verify that agents cite real probes instead of inlining SOQL
- sets up the path to lift these into first-class MCP tools when one becomes stable

## How to cite a probe from an AGENT.md

In the Plan, write:

```
- Use probe `probes/apex-references-to-field` (see `agents/_shared/probes/apex-references-to-field.md`) with args `{ object: "Account", field: "Industry" }`.
```

In the output envelope's `citations[]`, emit:

```json
{
  "type": "probe",
  "id": "apex-references-to-field",
  "path": "agents/_shared/probes/apex-references-to-field.md",
  "used_for": "Enumerating Apex classes that reference Account.Industry"
}
```

## Current probe catalog

| Probe id | Purpose | Consumed by |
|---|---|---|
| [`apex-references-to-field`](./apex-references-to-field.md) | Find Apex classes + triggers whose body references a given sObject.Field, with word-boundary filtering to suppress substring false positives. | `field-impact-analyzer`, `picklist-governor`, `object-designer`, `data-model-reviewer` |
| [`flow-references-to-field`](./flow-references-to-field.md) | Find active Flows whose metadata XML references a given sObject.Field. | `field-impact-analyzer`, `validation-rule-auditor`, `picklist-governor` |
| [`matching-and-duplicate-rules`](./matching-and-duplicate-rules.md) | Enumerate Matching Rules + Duplicate Rules on an sObject with active state, bypass perms, and overlap detection hints. | `duplicate-rule-designer`, `data-loader-pre-flight`, `lead-routing-rules-designer` |
| [`permission-set-assignment-shape`](./permission-set-assignment-shape.md) | Summarize PSG composition and assignment concentration for a user or PSG. | `permission-set-architect`, `sharing-audit-agent` |

## Promoting a probe to a first-class MCP tool

When a probe is used by three or more agents and its args/return shape stabilize, it is a candidate for promotion to an MCP tool in `mcp/sfskills-mcp/src/sfskills_mcp/admin.py`. The criteria:

1. Args have stable names and types across all callers.
2. Return shape has been unchanged for at least 30 days.
3. At least one agent depends on non-trivial post-processing that belongs server-side.

Promotion checklist:

- Add the tool to `admin.py` with matching signature.
- Register it in `server.py` with a description derived from the probe's `## Purpose` section.
- Add it to `_shared/SKILL_MAP.md` under "MCP tools available to these agents".
- Update every citing AGENT.md to cite `mcp_tool` instead of `probe`.
- Leave the probe md file in place with a banner pointing to the promoted tool (lets older agent runs still validate).

## Adding a new probe

1. Copy an existing probe file and rename it `<kebab-case>.md`.
2. Fill the sections: Purpose, Arguments, Query, Post-processing, Pagination, False-positive filters, Returns, Consumed by.
3. Add a row to the catalog table above.
4. Run `python3 scripts/validate_repo.py --agents` to confirm citations resolve.
