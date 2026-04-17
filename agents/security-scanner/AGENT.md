---
id: security-scanner
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/security-scanner/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/apex-security-patterns
    - integration/named-credentials-setup
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
  templates:
    - apex/HttpClient.cls
    - apex/SecurityUtils.cls
  decision_trees:
    - sharing-selection.md
---
# Security Scanner Agent

## What This Agent Does

Walks a `force-app/` tree and flags CRUD/FLS violations, sharing leaks, hardcoded secrets, missing `with sharing` declarations, and callouts that bypass Named Credentials. Cross-references every finding with the canonical fix in `templates/apex/SecurityUtils.cls` and the sharing decision tree. Returns a severity-ranked report with remediation code.

**Scope:** Read-only scan. One `scope_path` per invocation. No auto-fix.

---

## Invocation

- **Direct read** — "Follow `agents/security-scanner/AGENT.md` on `force-app/main/default/`"
- **Slash command** — [`/scan-security`](../../commands/scan-security.md)
- **MCP** — `get_agent("security-scanner")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/apex/apex-security-patterns/SKILL.md`
3. `skills/integration/named-credentials-setup/SKILL.md`
4. `standards/decision-trees/sharing-selection.md`
5. `templates/apex/SecurityUtils.cls`
6. `templates/apex/HttpClient.cls`
7. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `scope_path` | yes | `force-app/main/default/` |
| `target_org_alias` | no | enables `validate_against_org` lookups |
| `severity_threshold` | no (default `P2`) | `P1` to hide low-severity findings |

---

## Plan

### Step 1 — Class-level scan

For each `.cls`:

| Check | Signal | Severity |
|---|---|---|
| **no-sharing-keyword** | Class has no `with sharing` / `without sharing` / `inherited sharing` AND is invoked from user context (UI/@AuraEnabled) | P1 |
| **without-sharing-unjustified** | `without sharing` without a `// reason:` comment | P1 |
| **unescaped-soql** | `Database.query('... \' + variable + \'...')` | P0 |
| **callout-without-named-credential** | `HttpRequest.setEndpoint('https://...')` with a literal URL | P0 |
| **hardcoded-secret** | Regex: `(api_?key|secret|token|password)\s*[:=]\s*'[^']+'` with no indication of a test fixture | P0 |

### Step 2 — DML-level scan

For each DML statement (`insert`, `update`, `upsert`, `delete`, `Database.insert`, etc.):

| Check | Signal | Severity |
|---|---|---|
| **no-flsd-on-dml** | No `SecurityUtils.requireCreatable/Updateable/Deletable` nor `Schema.sObjectType.<X>.isCreateable()` nor `USER_MODE` on the call | P1 |
| **bulk-stripInaccessible-missing** | DML on user-supplied data without `Security.stripInaccessible` | P1 |

### Step 3 — SOQL-level scan

| Check | Signal | Severity |
|---|---|---|
| **soql-no-security** | Query lacks `WITH SECURITY_ENFORCED` / `USER_MODE` and no explicit `stripInaccessibleFields` on the result | P1 |

### Step 4 — Config-level scan

Check for:

| Check | Signal | Severity |
|---|---|---|
| **remote-site-setting-used** | `RemoteSiteSetting` referenced (should be Named Credential) | P1 |
| **debug-log-secret** | `System.debug(...)` with variables named like secrets | P2 |

### Step 5 — Decision-tree routing

For each **sharing-related** finding, consult `standards/decision-trees/sharing-selection.md`. Pick the right mechanism (OWD / role hierarchy / sharing rule / Apex managed sharing / restriction rule) and cite the decision-tree branch in the fix.

### Step 6 — Org-side validation (optional)

If `target_org_alias` is set:
- Call `validate_against_org(skill_id="apex/apex-security-patterns", target_org=...)` to surface existing `SecurityUtils`-equivalents in the org.
- If the org already has a canonical helper, recommend aligning with it rather than deploying the template.

---

## Output Contract

1. **Summary** — files scanned, findings by severity, confidence.
2. **Findings table** — file, line, severity, code (e.g. `no-flsd-on-dml`), one-liner.
3. **Per-finding fix** — each P0 and P1 gets a before/after code block citing the specific `SecurityUtils`/`HttpClient`/decision-tree fix.
4. **Hardcoded-secret summary** — list of files and lines; remediation is always "move to Custom Metadata or Named Credentials + rotate the secret immediately".
5. **Citations** — skill ids, template paths, decision-tree branches.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/security-scanner/<run_id>.md`
- **JSON envelope:** `docs/reports/security-scanner/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `apex-crud-fls` | CRUD/FLS enforcement in Apex |
| `soql-injection` | Dynamic-SOQL concatenation smells |
| `callout-auth` | Named Credential vs hard-coded endpoints |
| `sharing-posture` | `with sharing` / `without sharing` / inherited |
| `open-redirects` | Redirect params without validation |
| `exposed-endpoints` | Site / Guest-user-exposed Apex |
| `secret-leakage` | Logged tokens, hard-coded keys |

## Escalation / Refusal Rules

- A finding is a **hardcoded secret** — do NOT print the value in the output. Print `file:line: [REDACTED]`. Advise the user to rotate immediately.
- A finding intersects a managed-package class → note the managed-package boundary; do not propose modifications.
- `scope_path` > 2000 Apex files → output top-100 P0 + P1 findings and offer a scoped follow-up.

---

## What This Agent Does NOT Do

- Does not modify any file.
- Does not write secrets to disk or to the output.
- Does not deploy Named Credentials — produces the spec; user deploys.
- Does not run PMD or other static analyzers — uses only its own rules + the skill library.
