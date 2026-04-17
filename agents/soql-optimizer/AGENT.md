---
id: soql-optimizer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/data-skew-and-sharing-performance
    - apex/apex-security-patterns
    - data/custom-index-requests
    - data/soql-query-optimization
  shared:
    - AGENT_CONTRACT.md
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

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/data/soql-query-optimization/SKILL.md` (or closest via `search_skill`)
3. `skills/admin/data-skew-and-sharing-performance/SKILL.md`
4. `skills/apex/apex-security-patterns/SKILL.md` — for `WITH SECURITY_ENFORCED` enforcement
5. `templates/apex/BaseSelector.cls` — canonical centralization pattern

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
| **select-star** | `SELECT *` or more than 30 fields | P1 |
| **non-selective-where** | No filter, or only non-indexed fields in WHERE | P1 at >100k records, P0 at >1M |
| **missing-limit** | No `LIMIT` and caller not inherently bounded | P2 |
| **no-security** | No `WITH SECURITY_ENFORCED` / `USER_MODE` / `stripInaccessibleFields` | P1 |
| **cross-object-skew** | WHERE on a lookup field to an object with >10k children per parent | P1 |
| **offset-pagination** | Uses `OFFSET` past 2000 | P1 |

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

## Escalation / Refusal Rules

- Scope has > 500 queries → produce a top-50 report by severity and offer a paginated follow-up.
- Query is generated dynamically (`Database.query(<variable>)`) → flag as "dynamic — requires manual review" and do not attempt to rewrite.
- Query references a field the agent cannot resolve from metadata → include the finding but mark `confidence: LOW`.

---

## What This Agent Does NOT Do

- Does not modify files. All output is review-only.
- Does not deploy custom indexes — only recommends.
- Does not run `sf data query` — uses only static analysis + optional `describe_org`.
