# Classifier: prompt_library

## Purpose

Govern the Prompt Builder template library in an org: inventory, duplicate / near-duplicate detection, grounding citation checks, Trust Layer alignment (PII masking, residency), version + owner hygiene, per-template usage report. Produces a consolidation plan (merge near-duplicates, deprecate stale, re-ground drifted) and a template-health scorecard. No template edits — this is governance, not authoring.

## Replaces

`prompt-library-governor` (now a deprecation stub pointing at `audit-router --domain prompt_library`).

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope` | no | `all` (default) \| `type:FieldGeneration` \| `type:EmailGeneration` |

## Inventory Probe

1. `tooling_query("SELECT Id, DeveloperName, MasterLabel, Type, Status, LastModifiedById, LastModifiedBy.IsActive FROM GenAiPromptTemplate LIMIT 500")`.
2. Per template: fetch body + grounding via Tooling / Metadata API — model choice, referenced Flows, referenced merge fields, input variables.
3. `tooling_query` on `GenAiPromptTemplateVersion` for activation + version history (where available).
4. Usage telemetry (if observability is wired per `skills/agentforce/agentforce-observability`): counts per template over last 30/90 days.

Inventory columns (beyond id/name/active): `type`, `status`, `model`, `grounding_kind` (record / flow / apex / rag / inline), `last_used_days`, `owner_active`.

## Rule Table

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|
| `PROMPT_INLINE_PLACEHOLDER` | P0 | Body contains `{{ context }}` / unbacked placeholder with no wired grounding source | template + placeholder | Wire grounding to record / flow / apex / RAG source |
| `PROMPT_OWNER_INACTIVE` | P1 | `LastModifiedBy.IsActive=false` | template + owner | Transfer ownership to an active admin |
| `PROMPT_NO_DESCRIPTION` | P2 | Template has no description or intended-use note | template | Author intent note |
| `PROMPT_STALE_NOT_USED` | P2 | No activation in > 180 days AND zero usage events (if telemetry available) | template + last used | Deprecate |
| `PROMPT_DUPLICATE_CLUSTER` | P1 | Template cluster ≥ 2 templates sharing ≥ 70% body tokens + same Type + overlapping input variables | cluster + canonical proposal | Pick canonical; merge/deprecate others |
| `PROMPT_PII_NO_MASKING` | P0 | Template consumes a PII/PHI field but Trust Layer masking is not wired | template + field + Trust Layer config | Route through Trust Layer masking per `skills/agentforce/einstein-trust-layer` |
| `PROMPT_DATA_RESIDENCY_MISMATCH` | P1 | Provider / model choice doesn't match org's data-residency policy | template + model + policy | Swap model OR document approved exception |
| `PROMPT_NO_RETENTION_DOC` | P2 | Template output destination (field / email / note / log) is not documented | template | Add retention note |
| `PROMPT_MODEL_UNDOCUMENTED` | P2 | Template's model choice is not tagged / documented | template + current model | Document model selection + rationale |
| `PROMPT_UNTESTED` | P2 | Template has no associated eval / test run in the last 90 days | template + last test date | Wire a baseline eval per `skills/agentforce/agent-testing-and-evaluation` |

## Patches

None. Prompt Builder templates have semantic fragility that makes mechanical patching unsafe — a single word change can flip model behavior unexpectedly. Findings surface the target state; humans apply.

## Mandatory Reads

- `skills/agentforce/prompt-builder-templates`
- `skills/agentforce/einstein-trust-layer`
- `skills/agentforce/agentforce-guardrails`
- `skills/agentforce/agentforce-observability`

## Escalation / Refusal Rules

- Prompt Builder not enabled in the org → `REFUSAL_FEATURE_DISABLED`.
- No templates in scope → "empty library" summary + `REFUSAL_OUT_OF_SCOPE`.
- > 500 templates → top-50 by Type × usage count + `REFUSAL_OVER_SCOPE_LIMIT`.

## What This Classifier Does NOT Do

- Does not modify, activate, or deprecate templates.
- Does not rewrite prompts.
- Does not redirect model selection.
- Does not wire grounding sources — routes the work via `agentforce-action-reviewer` / `agentforce-builder`.
