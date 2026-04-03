# Flow Bulkification Review Template

## Context

| Item | Value |
|---|---|
| Flow type | |
| Trigger volume | UI / import / integration / schedule |
| Queries performed | |
| Related-record writes | |
| Apex actions used | |

## Loop Audit

| Loop Name | Elements executed per iteration | Risk | Refactor needed |
|---|---|---|---|
| | | | |

## Checklist

- [ ] No query, DML, or Apex action runs per loop iteration without justification.
- [ ] Same-record field updates use before-save when possible.
- [ ] Related-record updates are collected and committed intentionally.
- [ ] Import and API scenarios were considered.
- [ ] Async or Apex escalation was evaluated for high-volume logic.

## Recommended Refactor

State whether the flow should use query-once patterns, collection DML, before-save refactoring, or a move to Apex.
