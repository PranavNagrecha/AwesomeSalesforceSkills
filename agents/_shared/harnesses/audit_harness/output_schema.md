# Audit Router — Output Schema

**Status:** APPROVED at Wave 3b-1 user-approval gate #4.
**Frozen after:** Wave 3b-1 ships. Wave 3b-2 classifiers use this schema as-is; changing it later rewrites all 15 classifiers.

Every domain dispatch returns the same top-level envelope. Domain-specific columns nest inside the `inventory` table and the `patches` array — everything outside those two blocks is shared.

## Envelope

```markdown
## Summary

- domain: <validation_rule | picklist | approval_process | ...>
- target_org_alias: <alias>
- scope: <object:<Name> | folder:<Name> | process:<Name> | org>
- inventory_count: <int>
- finding_count: <P0_count>/<P1_count>/<P2_count>
- max_severity: <P0 | P1 | P2 | NONE>
- confidence: <HIGH | MEDIUM | LOW>

## Inventory

(domain-specific columns; every row has id + name + active at minimum)
| id | name | active | <domain-specific columns...> |
|---|---|---|---|

## Findings

(one row per finding; strictly-typed)
| code | severity | subject_id | subject_name | description | evidence | suggested_fix |
|---|---|---|---|---|---|---|

## Patches

(optional — omit this block entirely if no mechanical patches available)
Each patch is a fenced code block labelled with the target metadata path.
Every patch cites the finding it addresses and the skill/template the shape came from.

```xml
<!-- target: force-app/main/default/objects/Opportunity/validationRules/Stage_Required.validationRule-meta.xml -->
<!-- addresses: VR_MISSING_BYPASS on Opportunity.Stage_Required -->
<!-- cites: templates/admin/validation-rule-patterns.md -->
... patch content ...
```

## Process Observations

- **Healthy** — [...]
- **Concerning** — [...]
- **Ambiguous** — [...]
- **Suggested follow-ups** — agent-name (because ...); ...

## Citations

(per AGENT_CONTRACT — every skill / template / decision_tree / mcp_tool / probe used)
```

## Conformance rules

1. **Every finding has all 7 fields.** `code` and `severity` from the classifier's rule table; `subject_id` / `subject_name` / `description` / `evidence` / `suggested_fix` from the check.
2. **`code` format** — `<DOMAIN>_<SUBJECT>_<CONDITION>` per `severity_rubric.md`. No severity suffix.
3. **`severity`** — exactly one of P0 / P1 / P2. No extensions.
4. **`evidence`** — concrete pointer to the data that triggered the check (file path + line, SOQL result row, MCP probe output). Never a vague reference.
5. **`suggested_fix`** — one sentence or one code block. If the fix is mechanical, the full patch goes in the Patches block and the finding's `suggested_fix` cites it by target path.
6. **`confidence`** — follow the AGENT_CONTRACT rubric:
   - **HIGH**: all probes returned without truncation or pagination warnings; every recommendation cites a skill/template; no freestyling.
   - **MEDIUM**: one probe paginated, one recommendation freestyled, or a soft-optional input was missing and a sensible default was used.
   - **LOW**: probe truncated severely; inactive rules couldn't be fully fetched; a required input was substituted; > 1 recommendation freestyled.
7. **`Patches` is optional.** If the classifier produces no mechanical patches (e.g. report_dashboard's findings are usually advisory), omit the entire block rather than emitting an empty one.
8. **`Process Observations`** — at least one bullet per category, OR the literal string "nothing notable outside the direct findings" if the agent genuinely observed nothing. Empty honesty beats padded signal.
9. **`Citations`** — every skill / template / decision-tree / MCP tool / probe the classifier cited. Validator enforces resolution.

## Field reference

### Findings columns (strict)

- `code` (string, required) — finding code per `severity_rubric.md`.
- `severity` (enum, required) — `P0` | `P1` | `P2`.
- `subject_id` (string, required) — the org id of the thing the finding is about (rule id, process id, report id, etc.). Empty string allowed only when the subject is the entire object/org.
- `subject_name` (string, required) — human-readable label for the subject.
- `description` (string, required) — one sentence, <= 200 chars.
- `evidence` (string, required) — one sentence or a short fenced block; points at the raw signal that triggered the check.
- `suggested_fix` (string, required) — one sentence or a cross-reference to a `Patches` entry.

### Inventory row (minimum)

- `id` (string, required)
- `name` (string, required)
- `active` (boolean, required)

Additional columns per domain are defined in `classifier_contract.md` and the classifier's own file.

### Patch entry (strict)

- Fenced block labelled `<!-- target: <path> -->` as the first line inside the block.
- Second line `<!-- addresses: <finding_code> on <subject_name> -->`.
- Third line `<!-- cites: <skill-or-template-path> -->`.
- Body: the mechanical patch (XML, formula, etc.).

## Non-envelope content

The router's AGENT.md body (narrative explanation, escalation rules outside the classifier's per-domain refusals, general-purpose guidance) lives in [`../../../audit-router/AGENT.md`](../../../audit-router/AGENT.md) — NOT in this schema. This document is the machine-readable contract; the agent file is the human-facing wrapper.
