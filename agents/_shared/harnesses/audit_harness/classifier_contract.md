# Classifier Contract

Every `classifiers/<domain>.md` file MUST contain these sections, in this order, with these headings. The router's LLM reads them verbatim to run a dispatch — deviations break parity.

## Required sections

### 1. `# Classifier: <domain>`

First line. The domain token here must match the filename stem and the `--domain <name>` value the router accepts.

### 2. `## Purpose`

One paragraph, plain English: what is audited, why it matters, scope boundary. Ends with the sentence that defines the one thing this classifier is NOT for (to prevent scope creep during classification).

### 3. `## Replaces`

Name the retired auditor AGENT.md this classifier absorbs. Cite the agent id (e.g. `validation-rule-auditor`) so the citation graph stays navigable during the 2-version deprecation window.

### 4. `## Inputs`

Table of typed inputs the router accepts when this classifier is active. Keys are additive over the router's global inputs — do not re-declare `target_org_alias` / `domain` (those live on the router). Typical domain-specific inputs: `object_name`, `audit_scope`, `include_inactive`, `folder_filter`, etc.

### 5. `## Inventory Probe`

The exact SOQL / MCP tool calls the classifier runs in Phase 1 of the audit. Every probe must be citable — if it's a `tooling_query(...)` call, paste the SOQL; if it's an MCP tool, name it (e.g. `list_validation_rules(object_name)`); if it's a promoted probe from `agents/_shared/probes/`, reference it by id.

Inventory output must conform to the minimum inventory row shape from `output_schema.md` (id, name, active). Domain-specific columns are declared here.

### 6. `## Rule Table`

**The core of the classifier.** A table with exactly these columns:

| code | severity | check | evidence_shape | suggested_fix |
|---|---|---|---|---|

- `code` — per `severity_rubric.md` naming convention.
- `severity` — P0 / P1 / P2 (or "P0 if X else P1" when escalation applies; every path must resolve to exactly one of P0/P1/P2).
- `check` — the condition that triggers this finding, written as a one-sentence predicate.
- `evidence_shape` — what the evidence field will contain (e.g. "fenced xml snippet from rule metadata", "SOQL result row").
- `suggested_fix` — either a one-sentence fix OR a pointer into the `Patches` section of this classifier.

Every row in this table is a deterministic finding the classifier produces when the check matches. Changing a row is a material change — increment the classifier's version date and note it in CHANGELOG (Wave 7).

### 7. `## Patches`

Optional section for classifiers that produce mechanical patches. Format:

- One subsection per patch template, keyed on the finding code it addresses.
- Each subsection contains a fenced code block with the patch template, using `{placeholders}` for per-finding values.
- Each subsection cites the skill/template the shape came from.

Example heading: `### VR_MISSING_BYPASS patch template`.

### 8. `## Mandatory Reads`

Skills / templates / decision trees the classifier depends on. Every entry must resolve at validation time. The validator's citation gate enforces this.

### 9. `## Escalation / Refusal Rules`

Domain-specific limits (e.g. "> 100 rules on object → top-20 + REFUSAL_OVER_SCOPE_LIMIT"). Use canonical refusal codes from `agents/_shared/REFUSAL_CODES.md`.

### 10. `## What This Classifier Does NOT Do`

Explicit non-goals. Prevents the classifier from growing past its scope when the router's LLM gets creative.

## What the classifier does NOT contain

- An `Output Contract` section. Output shape is fixed globally by `output_schema.md`; per-classifier variation lives in the Inventory Probe (for domain-specific columns) and the Rule Table (for finding codes).
- An `Invocation` section. The classifier is never invoked directly — only via the router.
- A `Plan` section. The router's 5-phase plan IS the plan; classifiers only supply the probes + rules it consults.
- Frontmatter. These are support documents, not agents.

## Adding a new classifier

1. Create `classifiers/<domain>.md` with all 10 required sections.
2. Add `<domain>` to the router's `--domain` enum in [`agents/audit-router/AGENT.md`](../../../audit-router/AGENT.md).
3. (If deprecating an existing auditor) Rewrite that AGENT.md as a deprecation stub per Wave 3a's pattern.
4. Update `agents/_shared/SKILL_MAP.md`.
5. Run `python3 scripts/validate_repo.py --agents` and confirm 0 errors.

## Evolving an existing classifier

- Adding a finding code: new row in the Rule Table + update of the router's version date.
- Changing a finding code's meaning: introduce a new code (e.g. `VR_MISSING_BYPASS_V2`); deprecate the old one in the Rule Table with a strikethrough; remove fully after two versions.
- Retiring a finding code: mark it deprecated in the Rule Table with the last version it fires in.
- Changing severity on an existing code: this is a material contract change. Gate it with reviewer approval; bump the router's version.
