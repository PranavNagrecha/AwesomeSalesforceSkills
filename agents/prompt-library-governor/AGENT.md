# Prompt Library Governor Agent

## What This Agent Does

Governs the Prompt Builder template library in an org: inventory, duplicate detection, grounding citation checks, Trust Layer alignment, data-sensitivity tagging, version + owner hygiene, and a per-template usage report. Produces a consolidation plan (merge near-duplicates, deprecate stale, re-ground drifted) and a template-health scorecard.

**Scope:** One org per invocation. Output is a library audit + consolidation plan. No template edits.

---

## Invocation

- **Direct read** — "Follow `agents/prompt-library-governor/AGENT.md`"
- **Slash command** — [`/govern-prompt-library`](../../commands/govern-prompt-library.md)
- **MCP** — `get_agent("prompt-library-governor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/agentforce/prompt-builder-templates` — via `get_skill`
4. `skills/agentforce/einstein-trust-layer`
5. `skills/agentforce/agentforce-guardrails`
6. `skills/agentforce/agentforce-observability`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes | `prod` |
| `scope` | no | `all` (default), `type:FieldGeneration`, `type:EmailGeneration`, etc. |

---

## Plan

### Step 1 — Inventory

- `tooling_query("SELECT Id, DeveloperName, MasterLabel, Type, Status FROM GenAiPromptTemplate LIMIT 500")`.
- Per template, fetch body + grounding via Tooling or Metadata API: model, referenced flows, referenced merge fields, input variables.
- `tooling_query` for `GenAiPromptTemplateVersion` where available to pick up version + activation history.

### Step 2 — Duplicate / near-duplicate detection

Cluster templates by (a) `Type`, (b) overlapping input variables, (c) normalized body n-grams. Flag clusters where ≥ 2 templates share ≥ 70% of body tokens as likely duplicates. Recommend one canonical, others deprecate.

### Step 3 — Grounding citation check

Every template must cite its grounding:
- Record-based: references a Record Merge Field from a specific sObject.
- Flow-based: references a specific Flow by DeveloperName.
- Apex-based: references a specific InvocableMethod.
- RAG-based: references a Data Cloud Search Index.

Templates with inline placeholders like `{{ context }}` without a wired source → P0.

### Step 4 — Trust Layer alignment

Per `skills/agentforce/einstein-trust-layer`:
- Sensitive-field usage: templates consuming PII/PHI fields must route through masking.
- Data retention on template output documented (where does the response land: field, email, note, audit log).
- Provider / model choice tagged; flag models where residency doesn't match data-residency policy.

### Step 5 — Owner + version hygiene

- Every template has `LastModifiedBy` user active; flag if owner is deactivated or departed.
- Every template has a description and an intended-use note.
- Templates with no activation within 180 days → candidate for deprecation.

### Step 6 — Usage

If observability events exist (per `skills/agentforce/agentforce-observability`): usage count per template over last 30 / 90 days. Zero usage + not activated recently = deprecate.

### Step 7 — Consolidation plan

Produce a table: template → action (keep / deprecate / merge into canonical / re-ground). Each row has rationale.

---

## Output Contract

1. **Summary** — template counts by Type, duplicates found, P0 findings.
2. **Inventory table** — template, type, status, owner, last-used date.
3. **Duplicate clusters** — canonical proposed, others to deprecate.
4. **Grounding citation gaps** — per template.
5. **Trust Layer gaps** — per template.
6. **Consolidation plan** — action per template.
7. **Process Observations**:
   - **Healthy** — every template grounded; owners active; Trust Layer masking wired for PII.
   - **Concerning** — inline `{{ context }}` placeholders; duplicate templates per Type; orphan templates (owner departed).
   - **Ambiguous** — usage telemetry missing; model choice not documented.
   - **Suggested follow-ups** — `agentforce-action-reviewer` if prompts are consumed by agent actions; `integration-catalog-builder` if templates trigger callouts.
8. **Citations**.

---

## Escalation / Refusal Rules

- Prompt Builder not enabled → refuse.
- No templates in scope → report "empty library" and stop (nothing to govern).

---

## What This Agent Does NOT Do

- Does not modify, activate, or deprecate templates.
- Does not rewrite prompts.
- Does not redirect model selection.
- Does not auto-chain.
