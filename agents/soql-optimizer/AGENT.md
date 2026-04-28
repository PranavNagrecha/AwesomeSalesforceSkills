---
id: soql-optimizer
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/soql-optimizer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/agent-output-formats
    - admin/data-skew-and-sharing-performance
    - apex/apex-aggregate-queries
    - apex/apex-class-decomposition-pattern
    - apex/apex-collections-patterns
    - apex/apex-cpu-and-heap-optimization
    - apex/apex-design-patterns
    - apex/apex-dynamic-soql-binding-safety
    - apex/apex-execute-anonymous
    - apex/apex-limits-monitoring
    - apex/apex-performance-profiling
    - apex/apex-polymorphic-soql
    - apex/apex-security-patterns
    - apex/apex-soql-relationship-queries
    - apex/apex-stripinaccessible-and-fls-enforcement
    - apex/batch-apex-patterns
    - apex/cross-object-formula-and-rollup-performance
    - apex/dynamic-apex
    - apex/formula-field-performance-and-limits
    - apex/governor-limit-recovery-patterns
    - apex/governor-limits
    - apex/platform-cache
    - apex/recursive-trigger-prevention
    - apex/soql-fundamentals
    - apex/soql-security
    - apex/trigger-framework
    - data/custom-index-requests
    - data/soql-query-optimization
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - apex/BaseSelector.cls
---
# SOQL Optimizer Agent

## What This Agent Does

Scans a user-specified scope (file, folder, or entire `force-app/`) for SOQL anti-patterns — queries inside loops, missing selective filters, SELECTing unused fields, filtering on non-indexed fields at high volume, missing `WITH SECURITY_ENFORCED` — and produces ranked fix recommendations with before/after code. Consults data-skew and LDV skills for high-volume scenarios.

**Scope:** Read-only analysis. Ranked findings list; no auto-fix.

---

## Invocation

- **Direct read** — "Follow `agents/soql-optimizer/AGENT.md` on `force-app/main/default/classes/`"
- **Slash command** — [`/optimize-soql`](../../commands/optimize-soql.md)
- **MCP** — `get_agent("soql-optimizer")`

---

## Mandatory Reads Before Starting

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md`
3. `agents/_shared/REFUSAL_CODES.md`

### Core SOQL optimization
4. `skills/data/soql-query-optimization`
5. `skills/data/custom-index-requests`
6. `skills/admin/data-skew-and-sharing-performance`
7. `skills/apex/soql-fundamentals`
8. `skills/apex/soql-security`
9. `skills/apex/apex-soql-relationship-queries`
10. `skills/apex/apex-aggregate-queries`
11. `skills/apex/apex-polymorphic-soql`

### Dynamic SOQL safety (concatenation rewrites)
12. `skills/apex/dynamic-apex`
13. `skills/apex/apex-dynamic-soql-binding-safety`

### Centralization pattern (when to recommend a Selector)
14. `skills/apex/apex-design-patterns`
15. `skills/apex/apex-class-decomposition-pattern`
16. `templates/apex/BaseSelector.cls`

### Bulk-out-of-loop refactor target
17. `skills/apex/apex-collections-patterns`
18. `skills/apex/trigger-framework` — one-query-per-context discipline
19. `skills/apex/recursive-trigger-prevention` — re-query on re-entry
20. `skills/apex/batch-apex-patterns` — Database.getQueryLocator usage

### Governor / performance context
21. `skills/apex/governor-limits`
22. `skills/apex/governor-limit-recovery-patterns`
23. `skills/apex/apex-limits-monitoring`
24. `skills/apex/apex-cpu-and-heap-optimization`
25. `skills/apex/apex-performance-profiling`
26. `skills/apex/platform-cache` — cache vs query trade-off

### Security wrap on SOQL fixes
27. `skills/apex/apex-security-patterns` — for `WITH USER_MODE` / `WITH SECURITY_ENFORCED` enforcement
28. `skills/apex/apex-stripinaccessible-and-fls-enforcement`

### Edge cases
29. `skills/apex/formula-field-performance-and-limits` — when WHERE references formula fields
30. `skills/apex/cross-object-formula-and-rollup-performance` — cross-object formula query cost
31. `skills/apex/apex-execute-anonymous` — manual query verification helpers

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope_path` | yes | `force-app/main/default/classes/` or a single `.cls` |
| `expected_record_count` | no | `2_000_000` — used to escalate findings for LDV |
| `target_org_alias` | no | if set, call `describe_org` to grab record counts for sObjects referenced |

---

## Plan

### Step 1 — Extract every SOQL query

Walk the scope. Parse each Apex file. Record every `[SELECT ...]` occurrence with:
- Enclosing method
- Inside a loop? (lexical check for `for`, `while`, map iteration)
- Filter clause (`WHERE`)
- Limit clause
- Security clause (`WITH SECURITY_ENFORCED`, `USER_MODE`, `SYSTEM_MODE`, nothing)

### Step 2 — Classify each query

Assign each query one or more findings:

| Finding | Signal | Severity |
|---|---|---|
| **query-in-loop** | Query is lexically inside a `for`/`while` | P0 |
| **dml-then-query-in-loop** | Query inside loop AND DML inside loop on same SObject | P0 |
| **select-star** | `SELECT *` or more than 30 fields | P1 |
| **non-selective-where** | No filter, or only non-indexed fields in WHERE | P1 at >100k records, P0 at >1M |
| **missing-where** | No `WHERE` clause at all on a non-aggregate query | P0 at any volume |
| **leading-wildcard-like** | `LIKE '%...'` or `LIKE '%...%'` — non-selective | P1 |
| **negative-filter** | `!= null`, `NOT IN`, `<>` only — never selective | P1 |
| **missing-limit** | No `LIMIT` and caller not inherently bounded | P2 |
| **no-security** | No `WITH SECURITY_ENFORCED` / `USER_MODE` / `stripInaccessibleFields` | P1 |
| **system-mode-unjustified** | `AccessLevel.SYSTEM_MODE` without a `// reason:` comment | P1 |
| **cross-object-skew** | WHERE on a lookup field to an object with >10k children per parent | P1 |
| **owner-skew** | `OwnerId = :userId` on object with >10k records owned by one user | P1 |
| **offset-pagination** | Uses `OFFSET` past 2000 | P1 |
| **string-concat-soql** | `Database.query('... ' + var + ' ...')` — injection risk + non-cached query plan | P0 (cite `apex-dynamic-soql-binding-safety`) |
| **escapeSingleQuotes-only** | `String.escapeSingleQuotes` followed by concat into Database.query | P0 |
| **dynamic-soql-no-bind** | `Database.query(soql)` where SOQL built without `:bindVar` and no `queryWithBinds` | P1 |
| **aggregate-no-group-by-limit** | `SELECT COUNT()` without WHERE on indexed field | P1 |
| **subquery-without-limit** | `SELECT Id, (SELECT Id FROM Children__r)` with no LIMIT on subquery | P2 |
| **formula-in-where** | Formula field referenced in WHERE clause (cite `formula-field-performance-and-limits`) | P1 |
| **cross-object-formula-where** | Cross-object formula in WHERE — typically not indexed | P1 |
| **redundant-fields-via-relationship** | Same field selected via parent and child paths | P2 |
| **select-locator-outside-batch** | `Database.getQueryLocator` outside a Batch / iteration context | P1 |
| **all-rows-without-justification** | `ALL ROWS` without `// reason:` comment | P1 |
| **for-update-in-trigger** | `FOR UPDATE` inside a trigger context (lock-then-replicate hazard) | P1 |
| **mass-bulk-list-iteration** | Returning `List<SObject>` and iterating to extract a single field — should use SOQL projection | P2 |

Severity bumps one tier if `expected_record_count` crosses LDV threshold for the sObject.

### Step 3 — Propose fixes

For each P0/P1 finding, produce a before/after code block:

- **query-in-loop** → lift the query out of the loop, bulk the keys into a `Set<Id>`, query once, build a `Map<Id, SObject>`, look up inside the loop.
- **non-selective-where** → add a selective filter; if none exists, recommend a custom index (see `skills/data/custom-index-requests`) or a skinny table for LDV.
- **no-security** → add `WITH SECURITY_ENFORCED` (or `USER_MODE` on API 61+); if caller needs elevated access, document the runtime with a `// runs in system mode — owner: <class>` comment.
- **select-star** → list exactly the fields the code consumes; remove the rest.
- **offset-pagination** → replace with keyset pagination on `Id` or another indexed field.

### Step 4 — Centralization recommendation

If > 3 queries on the same sObject exist in different classes and no `<Object>Selector extends BaseSelector` exists, recommend creating one per `templates/apex/BaseSelector.cls`.

### Step 5 — Optional: org-side validation

If `target_org_alias` is provided:
- `describe_org` to confirm the org
- For each sObject referenced, note the live record count if available via the Tooling API (best-effort; do not fail the report if unavailable)

---

## Output Contract

1. **Summary** — files scanned, queries analyzed, findings by severity.
2. **Findings table** — one row per finding: file, line, severity, finding code, one-line description.
3. **Per-finding fix** — each P0 and P1 gets a before/after code block and a citation.
4. **Centralization recommendation** — if applicable.
5. **Process Observations** — peripheral signal noticed while scanning, separate from the direct findings. Each observation cites its evidence (file, query count, sObject name).
   - **Healthy** — e.g. repo already has a `<Object>Selector extends BaseSelector` pattern in place for the most-queried objects; queries consistently use `WITH SECURITY_ENFORCED` even where not yet required; `LIMIT` clauses present on every paginated query.
   - **Concerning** — e.g. more than 3 `SELECT` on a single sObject are distributed across unrelated classes (centralization gap); dynamic-SOQL string concatenation patterns that the agent can't safely rewrite; use of `Database.getQueryLocator` outside of Batch contexts.
   - **Ambiguous** — e.g. a query that is `query-in-loop` only in a code path guarded by a flag the agent can't evaluate; a non-selective WHERE where the agent cannot confirm live record count.
   - **Suggested follow-ups** — `apex-refactorer` when centralization is needed (to introduce a Selector); `security-scanner` on any `no-security` P1 finding; `test-class-generator` when new Selectors are created.
6. **Citations** — skill + template ids.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/soql-optimizer/<run_id>.md`
- **JSON envelope:** `docs/reports/soql-optimizer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions: `query-in-loop`, `selectivity`, `field-projection`, `security-clause`, `dynamic-soql-safety`, `pagination`, `aggregation`, `relationship-shape`, `formula-references`, `centralization`. Record skipped dimensions with reason (e.g. dynamic SOQL → `selectivity` = `not-run`).

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `scope_path` not provided. |
| `REFUSAL_INPUT_AMBIGUOUS` | `scope_path` exists but contains zero `.cls` files. |
| `REFUSAL_OVER_SCOPE_LIMIT` | Scope has > 500 queries — produce top-50 by severity and offer paginated follow-up. |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Query is generated dynamically via `Database.query(<variable>)` — flag with `confidence: LOW`, recommend `apex-dynamic-soql-binding-safety`, do not rewrite. |
| `REFUSAL_FIELD_NOT_FOUND` | Query references a field the agent cannot resolve from metadata — finding emitted with `confidence: LOW`. |
| `REFUSAL_OUT_OF_SCOPE` | Request to deploy custom indexes (recommend submitting via `data/custom-index-requests` workflow); request to modify files (this agent is read-only — recommend `apex-refactorer`). |
| `REFUSAL_MANAGED_PACKAGE` | Query is in a managed-package class — emit finding but recommend the managed-package author rather than proposing a rewrite. |

---

## What This Agent Does NOT Do

- Does not modify files. All output is review-only.
- Does not deploy custom indexes — only recommends.
- Does not run `sf data query` — uses only static analysis + optional `describe_org`.
