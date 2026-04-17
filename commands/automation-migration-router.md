# /migrate-automation

Invoke the [automation-migration-router](../agents/automation-migration-router/AGENT.md) agent. Wave 3a of the redesign (see [plan file](/Users/pranavnagrecha/.claude/plans/keen-napping-wombat.md)).

## Synopsis

```
/migrate-automation --source-type <wf_rule|process_builder|approval_process|auto>
                    --object <ApiName>
                    --target-org <alias>
                    [--mode analyze|plan|migrate]
                    [--consolidation-mode aggressive|conservative|auto]
                    [--include-inactive]
                    [--time-dependent-handling scheduled-path|defer-to-scheduled-flow|refuse]
                    [--canary-percent N]
                    [--parallel-run-days N]
```

## What it does

Routes one of four source automation types into the matching migration dispatch, returning an inventory, target design (Flow or Orchestrator), parallel-run validation plan, and rollback plan. See [`agents/automation-migration-router/AGENT.md`](../agents/automation-migration-router/AGENT.md) for the full contract.

## Legacy alias commands

These four aliases invoke the same router with a preset `--source-type` and emit a one-line deprecation notice. They ship until the removal window declared in `docs/MIGRATION.md` (Wave 7).

| Alias | Equivalent to |
|---|---|
| `/migrate-wfr-to-flow` | `/migrate-automation --source-type wf_rule ...` |
| `/migrate-pb-to-flow` | `/migrate-automation --source-type process_builder ...` |
| `/migrate-workflow-pb` | `/migrate-automation --source-type auto ...` |
| `/migrate-approval-to-orchestrator` | `/migrate-automation --source-type approval_process ...` |

## Safety

- The router never activates / deactivates / deploys — output is a markdown plan.
- Refusal codes are canonical (`agents/_shared/REFUSAL_CODES.md`).
- The citation gate enforces that every skill / template / decision-tree cited resolves to a real file.

## See also

- [`agents/_shared/harnesses/migration_router/decision_table.md`](../agents/_shared/harnesses/migration_router/decision_table.md) — source-type dispatch table
- [`agents/_shared/harnesses/migration_router/phase_gates.md`](../agents/_shared/harnesses/migration_router/phase_gates.md) — shared parallel-run + rollback
- [`standards/decision-trees/automation-selection.md`](../standards/decision-trees/automation-selection.md) — Flow vs Apex vs Orchestrator vs Agentforce upstream decision
