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
    - admin/connected-app-troubleshooting
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
    - architect/zero-trust-salesforce-patterns
    - integration/named-credentials-setup
    - security/api-security-and-rate-limiting
    - security/clickjack-and-frame-protection
    - security/csp-and-trusted-urls
    - security/data-classification-labels
    - security/encrypted-field-query-patterns
    - security/event-monitoring
    - security/ferpa-compliance-in-salesforce
    - security/field-audit-trail
    - security/file-upload-virus-scanning
    - security/gdpr-data-privacy
    - security/guest-user-security-audit
    - security/ip-relaxation-and-restriction
    - security/login-forensics
    - security/mfa-enforcement-strategy
    - security/network-security-and-trusted-ips
    - security/oauth-redirect-and-domain-strategy
    - security/oauth-token-management
    - security/org-hardening-and-baseline-config
    - security/platform-encryption
    - security/recaptcha-and-bot-prevention
    - security/sandbox-data-masking
    - security/scim-provisioning-integration
    - security/secure-coding-review-checklist
    - security/security-health-check
    - security/security-incident-response
    - security/service-account-credential-rotation
    - security/shield-event-log-retention-strategy
    - security/sso-saml-troubleshooting
    - security/transaction-security-policies
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

2. `skills/admin/connected-app-troubleshooting` — Connected app troubleshooting
3. `skills/security/api-security-and-rate-limiting` — Api security and rate limiting
4. `skills/security/clickjack-and-frame-protection` — Clickjack and frame protection
5. `skills/security/csp-and-trusted-urls` — Csp and trusted urls
6. `skills/security/data-classification-labels` — Data classification labels
7. `skills/security/encrypted-field-query-patterns` — Encrypted field query patterns
8. `skills/security/event-monitoring` — Event monitoring
9. `skills/security/ferpa-compliance-in-salesforce` — Ferpa compliance in salesforce
10. `skills/security/field-audit-trail` — Field audit trail
11. `skills/security/file-upload-virus-scanning` — File upload virus scanning
12. `skills/security/gdpr-data-privacy` — Gdpr data privacy
13. `skills/security/ip-relaxation-and-restriction` — Ip relaxation and restriction
14. `skills/security/login-forensics` — Login forensics
15. `skills/security/mfa-enforcement-strategy` — Mfa enforcement strategy
16. `skills/security/network-security-and-trusted-ips` — Network security and trusted ips
17. `skills/security/oauth-redirect-and-domain-strategy` — Oauth redirect and domain strategy
18. `skills/security/oauth-token-management` — Oauth token management
19. `skills/security/org-hardening-and-baseline-config` — Org hardening and baseline config
20. `skills/security/platform-encryption` — Platform encryption
21. `skills/security/recaptcha-and-bot-prevention` — Recaptcha and bot prevention
22. `skills/security/sandbox-data-masking` — Sandbox data masking
23. `skills/security/scim-provisioning-integration` — Scim provisioning integration
24. `skills/security/secure-coding-review-checklist` — Secure coding review checklist
25. `skills/security/security-health-check` — Security health check
26. `skills/security/security-incident-response` — Security incident response
27. `skills/security/service-account-credential-rotation` — Service account credential rotation
28. `skills/security/shield-event-log-retention-strategy` — Shield event log retention strategy
29. `skills/security/transaction-security-policies` — Transaction security policies
30. `skills/security/xss-and-injection-prevention` — Xss and injection prevention

### Contract layer
30. `agents/_shared/AGENT_CONTRACT.md`
31. `agents/_shared/DELIVERABLE_CONTRACT.md`
32. `agents/_shared/REFUSAL_CODES.md`

### Sharing & FLS / CRUD
33. `skills/apex/apex-security-patterns`
34. `skills/apex/apex-with-without-sharing-decision` — keyword choice
35. `skills/apex/apex-stripinaccessible-and-fls-enforcement`
36. `skills/apex/apex-user-and-permission-checks`
37. `skills/apex/apex-custom-permissions-check`
38. `skills/apex/apex-managed-sharing`
39. `skills/apex/apex-system-runas`
40. `skills/apex/soql-security`
41. `skills/apex/soql-fundamentals`
42. `standards/decision-trees/sharing-selection.md`
43. `skills/security/guest-user-security-audit` — Experience Cloud guest user 2021 changes audit

### SOQL injection
44. `skills/apex/dynamic-apex`
45. `skills/apex/apex-dynamic-soql-binding-safety`
46. `skills/apex/apex-regex-and-pattern-matching`

### Secrets & callouts
47. `skills/apex/apex-secrets-and-protected-cmdt`
48. `skills/apex/apex-named-credentials-patterns`
49. `skills/apex/callouts-and-http-integrations`
50. `skills/apex/callout-and-dml-transaction-boundaries`
51. `skills/integration/named-credentials-setup`
52. `skills/apex/continuation-callouts`
53. `skills/apex/apex-encoding-and-crypto`

### Hardcoded IDs / config
54. `skills/apex/apex-hardcoded-id-elimination`
55. `skills/apex/custom-metadata-in-apex`

### Exposed surfaces
56. `skills/apex/apex-rest-services` — REST endpoint security
57. `skills/apex/visualforce-fundamentals` — VF security
58. `skills/apex/platform-events-apex`
59. `skills/apex/change-data-capture-apex`
60. `skills/apex/apex-flow-invocation-from-apex` — Flow invocation context
61. `skills/apex/trigger-framework` — handler security
62. `skills/apex/apex-execute-anonymous` — security posture in anon

### DML / data flow
63. `skills/apex/apex-dml-patterns`
64. `skills/apex/apex-collections-patterns`
65. `skills/apex/apex-design-patterns`

### Error / exception leakage
66. `skills/apex/error-handling-framework`
67. `skills/apex/exception-handling`
68. `skills/apex/common-apex-runtime-errors`

### Probes
69. `agents/_shared/probes/apex-references-to-field.md` — for field-impact analysis on FLS violations
70. `agents/_shared/probes/permission-set-assignment-shape.md` — for exposed-endpoint analysis (who can hit it)

### Templates
71. `templates/apex/SecurityUtils.cls`
72. `templates/apex/HttpClient.cls`
73. `skills/architect/zero-trust-salesforce-patterns` — frame TSP/RTEM/HA-Session findings as zero-trust composition (which leg the finding belongs to); flag IdentityVerificationEvent / MobileEmailEvent as detect-only
74. `skills/security/sso-saml-troubleshooting` — SAML response inspection, SSO debugging

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
