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
    - admin/data-skew-and-sharing-performance
    - apex/apex-aggregate-queries
    - apex/apex-collections-patterns
    - apex/apex-dynamic-soql-binding-safety
    - apex/apex-polymorphic-soql
    - apex/apex-soql-relationship-queries
    - apex/batch-apex-patterns
    - apex/dynamic-apex
    - apex/formula-field-performance-and-limits
    - apex/governor-limits
    - apex/soql-aggregate-field-type-support
    - apex/soql-date-functions
    - apex/soql-for-view-and-for-reference
    - apex/soql-format-function-localization
    - apex/soql-fundamentals
    - apex/soql-multiselect-picklist-queries
    - apex/soql-null-ordering-patterns
    - apex/soql-object-limits-and-restrictions
    - apex/soql-outer-join-null-semantics
    - apex/soql-security
    - apex/soql-string-escaping-and-reserved-characters
    - apex/soql-using-scope-clause
    - apex/trigger-framework
    - data/custom-index-requests
    - data/soql-query-optimization
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - apex/BaseSelector.cls
---
# SOQL Optimizer Agent

## What This Agent Does

Scans a user-specified scope (file, folder, or entire `force-app/`) for SOQL anti-patterns — queries inside loops, missing selective filters, SELECTing unused fields, filtering on non-indexed fields at high volume, missing user-mode enforcement — and produces ranked fix recommendations with before/after code. Consults data-skew and LDV skills for high-volume scenarios.

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
2. `AGENT_RULES.md`
3. `agents/_shared/DELIVERABLE_CONTRACT.md`
4. `agents/_shared/REFUSAL_CODES.md`

### Core SOQL optimization
5. `skills/data/soql-query-optimization` — the selectivity model every rewrite in this agent is scored against
6. `skills/data/custom-index-requests` — when the right fix is an index request rather than a query rewrite
7. `skills/admin/data-skew-and-sharing-performance` — sharing-driven query cost that no rewrite removes — recognise it before promising a speedup
8. `skills/apex/soql-fundamentals` — the syntax surface being rewritten, including the clauses that quietly defeat an index
9. `skills/apex/soql-security` — a rewrite that drops `WITH USER_MODE` is a security regression sold as an optimization
10. `skills/apex/apex-soql-relationship-queries` — parent/child traversal versus a second query — the most common rewrite this agent proposes
11. `skills/apex/apex-aggregate-queries` — pushing counting and grouping into the query instead of looping in Apex
12. `skills/apex/apex-polymorphic-soql` — `TYPEOF` on polymorphic lookups, where a naive relationship rewrite silently changes the result set
13. `skills/apex/soql-null-ordering-patterns` — explicit NULLS clause + Id tiebreaker for stable + paginated results

### Dynamic SOQL safety (concatenation rewrites)
14. `skills/apex/dynamic-apex` — the dynamic query surfaces that have to be treated differently from static SOQL
15. `skills/apex/apex-dynamic-soql-binding-safety` — the bind-variable rewrite that makes a dynamic query safe without giving up the filter

### Centralization pattern (when to recommend a Selector)
16. `templates/apex/BaseSelector.cls`

### Bulk-out-of-loop refactor target
17. `skills/apex/apex-collections-patterns` — the map/set idioms behind every query-out-of-loop refactor this agent emits
18. `skills/apex/trigger-framework` — one-query-per-context discipline
19. `skills/apex/batch-apex-patterns` — Database.getQueryLocator usage

### Governor / performance context
20. `skills/apex/governor-limits` — the limit budget the optimization is buying headroom against — the number the report has to move

### Edge cases
21. `skills/apex/formula-field-performance-and-limits` — when WHERE references formula fields
22. `skills/apex/soql-outer-join-null-semantics` — a child-relationship filter does not behave like a SQL outer join; rewrites that assume it drop rows
23. `skills/apex/soql-object-limits-and-restrictions` — objects on which the usual optimizations are simply unavailable, so the recommendation has to change
24. `skills/apex/soql-string-escaping-and-reserved-characters` — required whenever the rewrite keeps any dynamic component instead of eliminating it
25. `skills/apex/soql-format-function-localization` — `FORMAT()` returns a localized string, so the result cannot be filtered, sorted or compared downstream
26. `skills/apex/soql-using-scope-clause` — `USING SCOPE` narrows the row set before filters and is often the cheapest fix available
27. `skills/apex/soql-for-view-and-for-reference` — `FOR VIEW` / `FOR REFERENCE` add write cost to a read query — a hidden multiplier on a hot path
28. `skills/apex/soql-multiselect-picklist-queries` — `INCLUDES` / `EXCLUDES` are never selective — know that before recommending one as the fix
29. `skills/apex/soql-aggregate-field-type-support` — which field types aggregate at all; an aggregate rewrite that cannot compile is not an optimization
30. `skills/apex/soql-date-functions` — date functions in a WHERE clause defeat the index unless written the supported way

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
- Security clause (`WITH USER_MODE`, `WITH SYSTEM_MODE`, legacy `WITH SECURITY_ENFORCED`, nothing)
- The enclosing class's `apiVersion`, read from its `.cls-meta.xml` — every security finding below is gated on it per `AGENT_CONTRACT.md` § *Apex security idiom by API version*. If the meta file is absent from the scope, record the version as unknown and say so in the finding.

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
| **no-security** | On a class below API 67.0: no `WITH USER_MODE`, no `AccessLevel.USER_MODE`, and no `Security.stripInaccessible` on the result. Not a finding at 67.0+, where user mode is the default | P1 |
| **security-enforced-legacy** | `WITH SECURITY_ENFORCED` present | P0 on a class at API 67.0+ (the clause is removed — the class does not compile); P2 at 57.0–66.0 (migrate to `WITH USER_MODE`) |
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
- **no-security** → add `WITH USER_MODE`; if the caller genuinely needs elevated access, use `WITH SYSTEM_MODE` and document it with a `// runs in system mode — owner: <class>` comment. Never `WITH SECURITY_ENFORCED`.
- **security-enforced-legacy** → replace the clause with `WITH USER_MODE` in place. At API 67.0+ label the fix as required-to-compile, not an improvement. See `AGENT_CONTRACT.md` § *Apex security idiom by API version* for the version table this rewrite is gated on.
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
   - **Healthy** — e.g. repo already has a `<Object>Selector extends BaseSelector` pattern in place for the most-queried objects; queries consistently use `WITH USER_MODE` even on classes whose API version does not yet default to it; `LIMIT` clauses present on every paginated query.
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
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
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
