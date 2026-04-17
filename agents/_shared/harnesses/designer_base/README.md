# Harness: designer_base

**Status:** Wave 3c shared harness.
**Consumed by:** 8 designer agents that declare `harness: designer_base` in their frontmatter.
**Refactors (does NOT deprecate):** `object-designer`, `permission-set-architect`, `flow-builder`, `omni-channel-routing-designer`, `sales-stage-designer`, `lead-routing-rules-designer`, `duplicate-rule-designer`, `sandbox-strategy-designer`.

## Why this exists — and why it's different from 3a and 3b

Wave 3a (`migration_router`) and Wave 3b (`audit_router`) **consolidated** multiple agents into one router. Wave 3c is deliberately lighter-touch: the 8 designers keep their public identity, slash-commands, and AGENT.md shape. The harness only documents the **conventions** they all already follow so new designer agents inherit them and existing ones can reference them.

Why not consolidate?

- Designers produce highly domain-specific deliverables (a sales-stage ladder ≠ a permission-set matrix ≠ a sandbox strategy). A single router's dispatcher would just be a thin switch with no logic savings.
- Their public contract (one slash-command per domain) is load-bearing — admins search for `/design-omni-channel`, not `/designer-router --domain omni_channel`.
- The shared surface is conventions, not behavior: mode routing, output shape, refusal patterns. Documenting those as harness contracts is enough.

What the harness gives us:

- A single source of truth for the designer convention.
- Validator rule: when `harness: designer_base` is declared, the harness checks shape compliance.
- Lower cost to author the 9th+ designer: read the harness, author the domain-specific parts.

## Files in this harness

| File | Purpose |
|---|---|
| `README.md` (this file) | Architecture + file index |
| `mode_contract.md` | The `design`/`audit` mode requirements: when each is mandatory, what each must return |
| `shared_output_shape.md` | Minimum required sections in every designer's output (Summary / Design / Audit / Process Observations / Citations) |
| `inventory_probes.md` | Common audit-mode probe patterns — MCP tool calls that apply to most designer domains |
| `refusal_patterns.md` | Canonical refusal conditions every designer shares (missing org, managed package, scope overload, input ambiguity) |

## Inheriting the harness

A designer agent declares inheritance via frontmatter:

```yaml
---
id: sales-stage-designer
class: runtime
harness: designer_base
modes: [design, audit]
...
```

The validator enforces:

1. Every agent with `harness: designer_base` must have `design` and/or `audit` in its `modes`.
2. The output contract must include the shared sections from `shared_output_shape.md`.
3. Refusal rules must cite canonical codes from `agents/_shared/REFUSAL_CODES.md`.

## Non-goals

- Not a Python library. Every file here is plain markdown the agent's LLM reads.
- Not a dispatcher — there is no `designer-router`. Each designer is invoked directly.
- Not a schema for design output. Each designer's AGENT.md owns the domain-specific shape; this harness only constrains the shared scaffolding.
