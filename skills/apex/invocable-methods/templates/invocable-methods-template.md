# Invocable Action Worksheet

Fill this in before writing the class. Every row maps to a rule in
`references/gotchas.md`; leaving one blank is how an action ships that passes its
first test and mis-attributes results the first time a flow batches interviews.

## Contract

| Item | Value |
|---|---|
| Action class name (one action per outer class — apexdev L5422) | |
| Method name and `label` shown on the Flow canvas | |
| `category` (blank ⇒ Uncategorized — apexdev L5411) | |
| Calling automation (record-triggered / screen / scheduled / orchestration / REST / Apex / Agentforce) | |
| Bulk volume expectation per invocation | |
| Throw on error, or return per-input result? | |
| Request wrapper needed? | Yes / No |
| Response wrapper needed? | Yes / No |
| Calls an external system? (`callout=true` — apexdev L5407) | Yes / No |
| `flowTransactionModel` on the action element | Automatic / CurrentTransaction / NewTransaction |
| Visibility: `public` or `global` (packaged / Agentforce ⇒ global — apexdev L5462, L43653) | |
| Will ship in a managed package? (signature becomes permanent — apexdev L5460) | Yes / No |

## DTO Fields

| Direction | Apex field name (case-sensitive in the flow — apexdev L5731) | Type | `label` | `required` | `defaultValue` |
|---|---|---|---|---|---|
| in | | | | | |
| in | | | | | |
| out | | | | *(ignored on outputs — apexdev L5691)* | |
| out | | | | | |

`required` and `defaultValue` cannot both be set on one variable (apexdev L5693).
`List<List<sObject>>` is a legal method return type and a runtime error as a
wrapper field (apexdev L5440–5442).

## Governor budget

| Resource | Cost for N inputs | Target |
|---|---|---|
| SOQL queries | | 1, constant in N |
| DML statements | | 1, constant in N |
| Callouts | | 0, or ≤ 100 with a screen-flow caller (apexdev L19563) |

## Guardrails

- [ ] Exactly one `@InvocableMethod`, `public`/`global static`, on an outer class
- [ ] One `List<...>` parameter; return is `List<...>` or `void`
- [ ] Result list seeded from the input list before any work, filled by index
- [ ] Per-input failures returned as data; only whole-call failures throw
- [ ] Annotation class delegates to a service
- [ ] `faultConnector` attached on the flow's action element
- [ ] Permission set with `classAccesses` ships alongside the class (apexdev L5172)
- [ ] Test class drives ≥ 200 inputs and asserts positional correspondence
- [ ] `scripts/check_invocable_methods.py --manifest-dir <src>` returns no CRITICAL
