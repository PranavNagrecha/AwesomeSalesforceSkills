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
    - apex/apex-custom-permissions-check
    - apex/apex-dynamic-soql-binding-safety
    - apex/apex-encoding-and-crypto
    - apex/apex-execute-anonymous
    - apex/apex-hardcoded-id-elimination
    - apex/apex-managed-sharing
    - apex/apex-named-credentials-patterns
    - apex/apex-rest-services
    - apex/apex-secrets-and-protected-cmdt
    - apex/apex-security-patterns
    - apex/apex-stripinaccessible-and-fls-enforcement
    - apex/apex-user-and-permission-checks
    - apex/apex-with-without-sharing-decision
    - apex/callouts-and-http-integrations
    - apex/custom-metadata-in-apex
    - apex/dynamic-apex
    - apex/error-handling-framework
    - apex/soql-security
    - apex/soql-string-escaping-and-reserved-characters
    - apex/visualforce-fundamentals
    - architect/zero-trust-salesforce-patterns
    - integration/named-credentials-setup
    - security/csp-and-trusted-urls
    - security/encrypted-field-query-patterns
    - security/guest-user-security-audit
    - security/platform-encryption
    - security/secure-coding-review-checklist
    - security/service-account-credential-rotation
    - security/visualforce-security-and-modernization
    - security/xss-and-injection-prevention
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

**Why this list is broad (30 skill reads, target is 8–25):** this agent's failure mode is the false negative — a vulnerability class it was never taught to look for gets reported as clean, and the caller acts on a report that is wrong in the one direction that matters. The list is therefore a taxonomy of finding classes (sharing and FLS, injection, secrets and callout credentials, hardcoded ids, exposed VF/REST/anonymous surfaces, crypto misuse, encryption interaction) rather than depth on any one of them; each subsection heading below is a class of finding that would go unreported if its read were dropped.

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md`
3. `agents/_shared/REFUSAL_CODES.md`

### Sharing, CRUD & FLS
4. `skills/apex/apex-security-patterns` — the enforcement baseline every finding is measured against, and the source of the remediation snippets
5. `skills/apex/apex-with-without-sharing-decision` — a class with no sharing declaration inherits its caller's context — the most common silent leak in a scan
6. `skills/apex/apex-stripinaccessible-and-fls-enforcement` — the canonical remediation this agent emits for an FLS finding
7. `skills/apex/apex-user-and-permission-checks` — distinguishes a CRUD check that actually gates the DML from one that only looks like it does
8. `skills/apex/apex-custom-permissions-check` — custom-permission gates are frequently the only control on an exposed method; a scan must recognise a correct one
9. `skills/apex/apex-managed-sharing` — hand-rolled Apex sharing is where a leak hides from any declarative review
10. `skills/apex/soql-security` — `WITH USER_MODE` / `WITH SECURITY_ENFORCED` semantics, and the cases where neither enforces what the author assumed
11. `skills/security/guest-user-security-audit` — Experience Cloud guest user 2021 changes audit — guest-reachable Apex is the highest-severity finding class
12. `standards/decision-trees/sharing-selection.md` — cite the branch when a finding's remediation changes the sharing model

### Injection & untrusted input
13. `skills/apex/dynamic-apex` — the dynamic SOQL / describe surfaces the scan has to enumerate before it can judge them
14. `skills/apex/apex-dynamic-soql-binding-safety` — bind variables and `Database.queryWithBinds` — the remediation for every concatenated query finding
15. `skills/apex/soql-string-escaping-and-reserved-characters` — `String.escapeSingleQuotes` is necessary but not sufficient; this is where it still lets injection through
16. `skills/security/xss-and-injection-prevention` — the non-SOQL injection classes — XSS in VF/Aura/LWC, SOSL, and formula injection
17. `skills/security/secure-coding-review-checklist` — the canonical checklist the scan enumerates against, so the finding set is complete rather than opportunistic

### Secrets & callouts
18. `skills/apex/apex-secrets-and-protected-cmdt` — protected Custom Metadata is the sanctioned home for a secret; anything else in source is a finding
19. `skills/apex/apex-named-credentials-patterns` — a callout that assembles its own endpoint or Authorization header bypasses the platform's credential store
20. `skills/apex/callouts-and-http-integrations` — the callout surfaces to scan, including the ones that do not look like callouts
21. `skills/integration/named-credentials-setup` — the org-side configuration a Named Credential remediation actually requires, so the fix is not hand-waved
22. `skills/security/service-account-credential-rotation` — a credential stored correctly but impossible to rotate is still a finding
23. `skills/apex/apex-encoding-and-crypto` — hand-rolled crypto, weak algorithms and `Crypto` class misuse — wrong in ways that compile fine

### Hardcoded IDs & configuration
24. `skills/apex/apex-hardcoded-id-elimination` — hardcoded Profile / RecordType / Group ids break across orgs and often encode a privilege assumption
25. `skills/apex/custom-metadata-in-apex` — the replacement for those literals, and how to reference it without a query per record

### Exposed surfaces
26. `skills/apex/apex-rest-services` — `@RestResource` is reachable by anyone with API access; the scan must judge its own authorisation, not the org's
27. `skills/apex/visualforce-fundamentals` — VF pages carry their own escaping rules and controller sharing context
28. `skills/security/visualforce-security-and-modernization` — the VF-specific finding set: `escape=false`, `<apex:includeScript>` on user data, legacy controller patterns
29. `skills/security/csp-and-trusted-urls` — a component that loads third-party script needs the CSP finding stated in terms the admin can act on
30. `skills/apex/apex-execute-anonymous` — anonymous Apex checked into source runs as whoever executes it — a distinct posture finding

### Encryption & data handling
31. `skills/security/platform-encryption` — encrypted fields change what a query may filter, sort or index on — a remediation that ignores that is a broken fix
32. `skills/security/encrypted-field-query-patterns` — the concrete filter/sort restrictions, so an encryption-aware finding names the working alternative
33. `skills/apex/error-handling-framework` — an exception surfaced to a user that carries a query, a record id or a stack trace is an information-disclosure finding
34. `skills/architect/zero-trust-salesforce-patterns` — frame TSP/RTEM/HA-Session findings as zero-trust composition (which leg the finding belongs to); flag IdentityVerificationEvent / MobileEmailEvent as detect-only

### Probes
35. `agents/_shared/probes/apex-references-to-field.md` — for field-impact analysis on FLS violations
36. `agents/_shared/probes/permission-set-assignment-shape.md` — for exposed-endpoint analysis (who can hit it)

### Templates
37. `templates/apex/SecurityUtils.cls`
38. `templates/apex/HttpClient.cls`

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
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
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
