---
id: security-scanner
class: runtime
version: 1.1.0
status: stable
requires_org: false
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/security-scanner/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/apex-collections-patterns
    - apex/apex-custom-permissions-check
    - apex/apex-design-patterns
    - apex/apex-dml-patterns
    - apex/apex-dynamic-soql-binding-safety
    - apex/apex-encoding-and-crypto
    - apex/apex-execute-anonymous
    - apex/apex-flow-invocation-from-apex
    - apex/apex-hardcoded-id-elimination
    - apex/apex-managed-sharing
    - apex/apex-named-credentials-patterns
    - apex/apex-regex-and-pattern-matching
    - apex/apex-rest-services
    - apex/apex-secrets-and-protected-cmdt
    - apex/apex-security-patterns
    - apex/apex-stripinaccessible-and-fls-enforcement
    - apex/apex-system-runas
    - apex/apex-user-and-permission-checks
    - apex/apex-with-without-sharing-decision
    - apex/callout-and-dml-transaction-boundaries
    - apex/callouts-and-http-integrations
    - apex/change-data-capture-apex
    - apex/common-apex-runtime-errors
    - apex/continuation-callouts
    - apex/custom-metadata-in-apex
    - apex/dynamic-apex
    - apex/error-handling-framework
    - apex/exception-handling
    - apex/platform-events-apex
    - apex/soql-fundamentals
    - apex/soql-security
    - apex/trigger-framework
    - apex/visualforce-fundamentals
    - integration/named-credentials-setup
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  probes:
    - apex-references-to-field.md
    - permission-set-assignment-shape.md
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

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md`
3. `agents/_shared/REFUSAL_CODES.md`

### Sharing & FLS / CRUD
4. `skills/apex/apex-security-patterns`
5. `skills/apex/apex-with-without-sharing-decision` — keyword choice
6. `skills/apex/apex-stripinaccessible-and-fls-enforcement`
7. `skills/apex/apex-user-and-permission-checks`
8. `skills/apex/apex-custom-permissions-check`
9. `skills/apex/apex-managed-sharing`
10. `skills/apex/apex-system-runas`
11. `skills/apex/soql-security`
12. `skills/apex/soql-fundamentals`
13. `standards/decision-trees/sharing-selection.md`

### SOQL injection
14. `skills/apex/dynamic-apex`
15. `skills/apex/apex-dynamic-soql-binding-safety`
16. `skills/apex/apex-regex-and-pattern-matching`

### Secrets & callouts
17. `skills/apex/apex-secrets-and-protected-cmdt`
18. `skills/apex/apex-named-credentials-patterns`
19. `skills/apex/callouts-and-http-integrations`
20. `skills/apex/callout-and-dml-transaction-boundaries`
21. `skills/integration/named-credentials-setup`
22. `skills/apex/continuation-callouts`
23. `skills/apex/apex-encoding-and-crypto`

### Hardcoded IDs / config
24. `skills/apex/apex-hardcoded-id-elimination`
25. `skills/apex/custom-metadata-in-apex`

### Exposed surfaces
26. `skills/apex/apex-rest-services` — REST endpoint security
27. `skills/apex/visualforce-fundamentals` — VF security
28. `skills/apex/platform-events-apex`
29. `skills/apex/change-data-capture-apex`
30. `skills/apex/apex-flow-invocation-from-apex` — Flow invocation context
31. `skills/apex/trigger-framework` — handler security
32. `skills/apex/apex-execute-anonymous` — security posture in anon

### DML / data flow
33. `skills/apex/apex-dml-patterns`
34. `skills/apex/apex-collections-patterns`
35. `skills/apex/apex-design-patterns`

### Error / exception leakage
36. `skills/apex/error-handling-framework`
37. `skills/apex/exception-handling`
38. `skills/apex/common-apex-runtime-errors`

### Probes
39. `agents/_shared/probes/apex-references-to-field.md` — for field-impact analysis on FLS violations
40. `agents/_shared/probes/permission-set-assignment-shape.md` — for exposed-endpoint analysis (who can hit it)

### Templates
41. `templates/apex/SecurityUtils.cls`
42. `templates/apex/HttpClient.cls`

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
| **no-sharing-keyword** | Class has no `with sharing` / `without sharing` / `inherited sharing` AND is invoked from user context (UI/@AuraEnabled/@RestResource/Site guest) | P1 (cite `apex-with-without-sharing-decision`) |
| **without-sharing-unjustified** | `without sharing` without a `// reason:` comment | P1 |
| **unescaped-soql** | `Database.query('... ' + variable + ...)` — string concatenation inside Database.query | P0 (cite `apex-dynamic-soql-binding-safety`) |
| **escapeSingleQuotes-only** | `String.escapeSingleQuotes` followed by `Database.query` concat — false safety | P0 |
| **dynamic-soql-no-bind** | `Database.query(soql)` with `soql` built across methods, no `:bind` and no `queryWithBinds` | P1 |
| **callout-without-named-credential** | `HttpRequest.setEndpoint('https://...')` with a literal URL | P0 |
| **hardcoded-secret** | Regex: `(api_?key|secret|token|password)\s*[:=]\s*'[^']+'` with no indication of a test fixture | P0 (cite `apex-secrets-and-protected-cmdt`) |
| **hardcoded-id** | 15/18-char Salesforce Id literal in non-test class | P1 (cite `apex-hardcoded-id-elimination`) |
| **rest-resource-no-auth-check** | `@RestResource` class with no `FeatureManagement.checkPermission` / Custom Permission gate, AND class is `without sharing` | P0 |
| **aura-enabled-without-sharing** | `@AuraEnabled` method on a class declared `without sharing` (or no keyword) | P1 |
| **vf-controller-without-sharing** | Visualforce controller class declared `without sharing` | P1 |

### Step 2 — DML-level scan

For each DML statement (`insert`, `update`, `upsert`, `delete`, `Database.insert`, etc.):

| Check | Signal | Severity |
|---|---|---|
| **no-flsd-on-dml** | No `SecurityUtils.requireCreatable/Updateable/Deletable` nor `Schema.sObjectType.<X>.isCreateable()` nor `USER_MODE` on the call | P1 |
| **bulk-stripInaccessible-missing** | DML on user-supplied data without `Security.stripInaccessible` | P1 (cite `apex-stripinaccessible-and-fls-enforcement`) |
| **stripInaccessible-on-original** | `Security.stripInaccessible(...).getRecords()` chain, but DML executed on original parameter | P0 |
| **dml-on-setup-and-data** | Same method does DML on Setup + non-Setup objects without `System.runAs` boundary | P1 |
| **system-mode-dml-unjustified** | `Database.insert(records, AccessLevel.SYSTEM_MODE)` without a `// reason:` comment | P1 |

### Step 3 — SOQL-level scan

| Check | Signal | Severity |
|---|---|---|
| **soql-no-security** | Query lacks `WITH SECURITY_ENFORCED` / `USER_MODE` and no explicit `stripInaccessibleFields` on the result | P1 |
| **soql-system-mode-unjustified** | `WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE` without `// reason:` comment | P1 |
| **soql-all-rows-unjustified** | `ALL ROWS` keyword without `// reason:` (returns soft-deleted records — privacy implications) | P1 |

### Step 4 — Config-level scan

| Check | Signal | Severity |
|---|---|---|
| **remote-site-setting-used** | `RemoteSiteSetting` referenced (should be Named Credential) | P1 |
| **debug-log-secret** | `System.debug(...)` with variables named like secrets | P2 |
| **secret-in-customMetadata** | `customMetadata/*.md-meta.xml` contains a value field named `*Key__c` / `*Secret__c` / `*Token__c` (committed!) | P0 |
| **continuation-without-auth** | Continuation-based callout without auth-context check | P1 |
| **flow-invocation-with-elevated-context** | `Flow.Interview.createInterview` invoked from `without sharing` class | P1 |
| **catch-empty-on-security-exception** | `catch (SecurityException e) { }` empty body — leaks of "denied" info | P1 |

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
6. **Process Observations** — the `process_observations` field in the envelope MUST be populated whenever the scan reveals patterns worth flagging beyond raw findings. Bucket signals into:
   - **Healthy** — e.g. `SecurityUtils` consistently invoked across the codebase, Named Credentials used uniformly, all `without sharing` declarations carry `// reason:` comments.
   - **Concerning** — e.g. mixed sharing posture across handlers for the same SObject, repeated `escapeSingleQuotes`-only patterns, secret-shaped values found in Custom Metadata XML, REST endpoints lacking permission gates.
   - **Ambiguous** — e.g. `without sharing` with a comment that doesn't actually justify the choice; SOQL using `USER_MODE` but downstream DML in `SYSTEM_MODE`; class with mixed Setup + non-Setup DML where `runAs` boundary is unclear.
   - **Suggested follow-ups** — recommend (do not auto-chain) `/refactor-apex` for `SecurityUtils` rollout, `/audit-sharing` for OWD/role decisions, `/architect-perms` for permission-set redesign when REST/Aura endpoints have no gate.

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
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. The dimensions that MUST appear in either `dimensions_compared[]` or `dimensions_skipped[]` are: `apex-crud-fls`, `soql-injection`, `callout-auth`, `sharing-posture`, `open-redirects`, `exposed-endpoints`, `secret-leakage`. If a scan only counts findings without resolving severity for a dimension (e.g. dynamic-SOQL flagged but `escapeSingleQuotes`-only false-positive triage skipped), record it under `dimensions_skipped[]` with `state: count-only` and a one-line `reason`.

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

Per `agents/_shared/REFUSAL_CODES.md`, this agent emits the following refusal codes. Refusals MUST be emitted as a single JSON object with `code`, `message`, and (where relevant) `details` — never as prose alone.

| Code | When to emit | Notes |
|---|---|---|
| `REFUSAL_MISSING_INPUT` | `scope_path` is unset, empty, or does not resolve to a directory | Ask the user to supply a concrete path under `force-app/`. |
| `REFUSAL_INPUT_AMBIGUOUS` | `scope_path` resolves to a multi-package monorepo root with no obvious Apex root | Ask the user to narrow to a specific package directory. |
| `REFUSAL_OVER_SCOPE_LIMIT` | `scope_path` contains > 2000 `.cls` / `.trigger` files | Output top-100 P0 + P1 findings; record remaining dimensions under `dimensions_skipped[]` with `state: partial`; offer a scoped follow-up by package or SObject. |
| `REFUSAL_SECURITY_GUARD` | A finding contains the **value** of a hardcoded secret | NEVER print the value. Output `file:line: [REDACTED]` and instruct the user to rotate immediately. This is unconditional — applies even when the user explicitly requests the value. |
| `REFUSAL_MANAGED_PACKAGE` | A finding intersects a managed-package namespaced class | Note the managed-package boundary; do not propose modifications; recommend the user file a partner ticket. |
| `REFUSAL_OUT_OF_SCOPE` | User asks the agent to **fix** code, deploy a `SecurityUtils` template, or run a refactor | This agent is read-only. Recommend `/refactor-apex` (does not auto-chain). |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | A finding's severity hinges on runtime context the agent cannot resolve (e.g. is a class invoked from a Site Guest profile? is a `without sharing` keyword justified by a documented incident?) | Emit the finding at the conservative severity, mark `confidence: LOW`, and route to human review. |
| `REFUSAL_POLICY_MISMATCH` | The org has a documented exception (e.g. a `// security-exception:` annotation tied to a Custom Metadata record) that overrides a finding | Acknowledge the exception, downgrade severity to `informational`, and cite the exception record. |

---

## What This Agent Does NOT Do

- Does not modify any file.
- Does not write secrets to disk or to the output.
- Does not deploy Named Credentials — produces the spec; user deploys.
- Does not run PMD or other static analyzers — uses only its own rules + the skill library.
