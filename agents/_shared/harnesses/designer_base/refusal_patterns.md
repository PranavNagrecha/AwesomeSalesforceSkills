# Designer Refusal Patterns

Canonical refusal conditions every designer inheriting `designer_base` must cover. Codes come from [`agents/_shared/REFUSAL_CODES.md`](../../REFUSAL_CODES.md).

## Mandatory refusals (every designer must handle)

| Condition | Refusal code |
|---|---|
| Required input missing | `REFUSAL_MISSING_INPUT` |
| `mode=audit` and `target_org_alias` missing | `REFUSAL_MISSING_ORG` |
| `target_org_alias` not authenticated with `sf` CLI | `REFUSAL_ORG_UNREACHABLE` |
| Target object is a managed-package object | `REFUSAL_MANAGED_PACKAGE` |
| Input is ambiguous enough that any design would be speculation | `REFUSAL_INPUT_AMBIGUOUS` |
| Scope too large for a single reviewable run (> domain threshold) | `REFUSAL_OVER_SCOPE_LIMIT` |
| Audit finds nothing to audit (domain not yet in use) | `REFUSAL_OUT_OF_SCOPE` with "not yet using <feature>" summary |

## Domain-specific refusals

Each designer's AGENT.md may add refusal conditions beyond this list. Those refusals must still use a canonical code — adding a new refusal code requires editing `REFUSAL_CODES.md` and reviewer sign-off, not just inventing a new one inline.

## Refusal format

When a designer refuses, the output envelope must include:

```
## Refusal

- code: <REFUSAL_*>
- reason: <one-sentence human-readable explanation>
- remediation_hint: <what the user needs to do to unblock>
```

The Refusal block lives at the top of the envelope (before Summary) so a consumer parsing the output knows immediately whether the run produced a deliverable or a block.

## Partial runs

If the designer can partially complete the work (e.g. inventory succeeds but capacity math fails because a required input is missing), the envelope contains BOTH:

1. A Refusal block at the top listing what was blocked.
2. The partial output (Summary + whatever design/audit sections could be built) with `confidence: LOW`.

This is preferable to an all-or-nothing refusal — admins get useful intermediate state and know exactly what input to provide to unblock.

## Prohibited refusals

Some conditions are handled by the harness + the base agent contract — designers must NOT re-implement their own version:

- Slash-command not found → handled by the command resolver, not the agent.
- Frontmatter malformed → handled by the validator, not the agent.
- Agent version mismatch — not a runtime refusal; it's a CI gate.

If a designer's runtime detects one of these conditions, emit `REFUSAL_NEEDS_HUMAN_REVIEW` — the underlying problem lives outside the agent's mandate.

## Validator enforcement

Designers declaring `harness: designer_base` must:

1. Include an `Escalation / Refusal Rules` (or `Escalation Rules` alias) section in their AGENT.md.
2. Every refusal condition in that section uses a code from `REFUSAL_CODES.md`.
3. At least the "Required input missing" and "Managed-package object" conditions are present (they're universal).

Violations emit validator ERRORs at PR time.
