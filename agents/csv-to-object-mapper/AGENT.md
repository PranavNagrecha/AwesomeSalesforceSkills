---
id: csv-to-object-mapper
class: runtime
version: 1.0.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/csv-to-object-mapper/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - admin/custom-field-creation
    - admin/data-import-and-management
    - admin/object-creation-and-design
    - data/external-id-strategy
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
  templates:
    - admin/naming-conventions.md
---
# CSV to Object Mapper Agent

## What This Agent Does

Given a CSV file header (or a schema description), produces a mapping to an existing or new sObject: column → field decisions with type inference, naming per `templates/admin/naming-conventions.md`, External ID candidate identification, required-field detection, and a Data Loader CSV mapping file. The agent handles the specific case a Salesforce admin or BA faces 10× a year: "a partner sent me a spreadsheet, how do I load it?"

**Scope:** One CSV structure per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/csv-to-object-mapper/AGENT.md` for this CSV header mapping to Account"
- **Slash command** — [`/map-csv-to-object`](../../commands/map-csv-to-object.md)
- **MCP** — `get_agent("csv-to-object-mapper")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/admin/object-creation-and-design`
4. `skills/admin/custom-field-creation`
5. `skills/admin/data-import-and-management`
6. `skills/data/external-id-strategy`
7. `templates/admin/naming-conventions.md`
8. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `csv_header` | yes | comma-separated header line, OR a bullet list of column names with 1-2 sample values |
| `target_object` | no | `Account` \| `new:<ProposedName>` (if creating a new object) |
| `target_org_alias` | yes |
| `mode` | no | `map` (default — map to existing fields, create missing ones) \| `create-new-object` (design a new object from the CSV) |

---

## Plan

1. **Parse the header** — split into columns, normalize whitespace, detect common separators.
2. **Column type inference** (using up to 3 sample values per column if provided):
   - Columns matching `/email/i` or sample values matching email regex → Email type.
   - Columns matching `/phone|tel/i` → Phone.
   - Columns with only digits + length 8-15 → numeric candidate (but check: could be phone, could be external id; prefer Text unless sample strongly implies numeric computation).
   - Columns with only `0`/`1`/`true`/`false`/`yes`/`no` → Checkbox.
   - Columns matching `/date|_dt$/i` or sample values matching ISO-8601 → DateTime.
   - Columns matching `/id|external/i` → External ID candidate (Text + unique).
   - Columns matching a known picklist on the target → Picklist (verify values are a subset).
   - Default → Text, length inferred from longest sample value × 2 (rounded up to standard length: 80, 255, 1000, 32768).
3. **Mode: map** — for each column, propose a target field:
   - If `target_object` has a field whose label or API name matches (fuzzy) → map.
   - If no match → propose creating a new custom field, named per `templates/admin/naming-conventions.md`.
   - Fields already flagged as deprecated (naming convention or `Deprecated_` prefix) → warn.
4. **Mode: create-new-object** — invoke the logic of `object-designer` inline (do NOT auto-chain; just apply the same rules):
   - Propose object API name + label.
   - Propose Name field (Auto Number if no natural name, else Text).
   - Propose each field per Step 2.
   - Identify the External ID (the column most likely to be the primary key — usually named `*_id`, `uuid`, or a column with 100% unique non-null sample values).
5. **Emit the Data Loader mapping file** — the standard `.sdl` format that maps CSV header → field API name.
6. **Emit a pre-check** — required fields on the target that have no CSV column mapping (the user must provide defaults or fail the load); PII columns that require field-level encryption or restricted access.

---

## Output Contract

1. **Summary** — mode, column count, new fields proposed, confidence.
2. **Mapping table** — CSV column → target field → type → justification.
3. **New fields to create** — fenced XML per field (for sfdx deployment).
4. **New object design** — only in `create-new-object` mode; spec + scaffold as in `object-designer`.
5. **Data Loader mapping file** — fenced block labelled with target filename.
6. **Pre-check** — required-field gaps, PII warnings.
7. **Process Observations**:
   - **What was healthy** — source data has an obvious primary key, column naming hints at clean semantics.
   - **What was concerning** — columns with embedded delimiters (common with copied Excel), columns whose names are identical to standard fields (collision risk), columns that look like compound values (full name, address).
   - **What was ambiguous** — columns where the agent guessed a type; flag each.
   - **Suggested follow-up agents** — `object-designer` (if more than half the columns implied a new object), `preflight-load` (before actually running the load).
8. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/csv-to-object-mapper/<run_id>.md`
- **JSON envelope:** `docs/reports/csv-to-object-mapper/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

## Escalation / Refusal Rules

- CSV has > 200 columns → refuse single-object mapping; suggest the data is really multi-entity and recommend `data-model-reviewer` for normalization.
- Column names contain sensitive-data labels (`ssn`, `credit_card`, `dob`) → refuse to propose unencrypted fields; require Platform Encryption or redirect to Data Cloud.

---

## What This Agent Does NOT Do

- Does not read the CSV data itself (only the header + optional samples).
- Does not deploy new fields or objects.
- Does not run the data load.
- Does not auto-chain to `preflight-load`.
