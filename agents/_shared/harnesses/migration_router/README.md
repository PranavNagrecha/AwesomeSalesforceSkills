# Harness: migration_router

**Status:** Wave 3a shared harness.
**Consumed by:** [`agents/automation-migration-router/AGENT.md`](../../../automation-migration-router/AGENT.md).
**Replaces:** the duplicated backbone in (deprecated) `workflow-rule-to-flow-migrator`, `process-builder-to-flow-migrator`, `approval-to-flow-orchestrator-migrator`, `workflow-and-pb-migrator`.

## Why this exists

All four retired migrators performed the same five phases in the same order:

1. Inventory the source automation on the target object
2. Classify each source artifact by action / branch type
3. Emit the target design (Flow or Orchestrator)
4. Parallel-run validation plan with a shadow field
5. Rollback plan + Process Observations

They diverged only on **Step 2** (classification) and **Step 3** (target shape). Every other concern — refusal codes, shadow-field patterns, scheduled-path handling, cutover gates, metrics to watch — was duplicated verbatim across the four AGENT.md files. Every change cost four edits.

This harness owns the four common phases. The router cites the harness documents for the shared concerns and uses a per-source-type **decision table** (see `decision_table.md`) to dispatch the classification + target-shape logic.

## Files in this harness

| File | Purpose |
|---|---|
| `README.md` (this file) | Architecture + file index |
| `decision_table.md` | Source-type → classification + target + skill citations mapping. **This is the thing user-approval gate #3 validates.** |
| `output_schema.md` | Canonical output contract shared by all three source-type dispatches |
| `phase_gates.md` | Parallel-run + rollback + scheduled-path phases (shared across source types) |

## Non-goals

- Not a Python library. Every file here is plain markdown the agent's LLM reads.
- Not a runtime. The MCP server does not execute migrations — agents return plans, humans deploy.
- Not a schema for new source types. Adding a new automation source (e.g. "old-style Validation Rules that should migrate to Flow decision elements") requires a new row in `decision_table.md` and explicit reviewer sign-off; this harness does not auto-extend.
