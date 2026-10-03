---
name: apexguru-performance-analysis
description: "Run and interpret the ApexGuru engine in Salesforce Code Analyzer v5 for Apex performance and scalability findings: verify the authenticated target org, scope .cls/.trigger files, capture JSON evidence, triage line-level recommendations, validate fixes, and avoid claiming runtime telemetry the report does not contain. Trigger keywords: ApexGuru scan, apexguru Code Analyzer, Apex performance findings, SOQL scalability issue, AI Apex optimization. NOT for general PMD/security lint — use devops/salesforce-code-analyzer. NOT for Apex debug-log or production transaction profiling."
category: apex
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "run ApexGuru against these Apex classes and explain the findings"
  - "configure the ApexGuru engine in Salesforce Code Analyzer v5"
  - "triage ApexGuru performance recommendations by severity and file"
  - "validate whether an ApexGuru finding is safe to fix"
  - "compare ApexGuru source findings before and after an Apex refactor"
tags:
  - apexguru
  - code-analyzer
  - apex-performance
  - scalability
  - source-analysis
  - target-org
inputs:
  - "Salesforce DX workspace and bounded .cls/.trigger targets"
  - "Authenticated Salesforce org alias where ApexGuru is supported and activated"
  - "Salesforce Code Analyzer v5 installation and optional code-analyzer.yml"
  - "JSON scan output and relevant tests/performance evidence for triage"
outputs:
  - "Reproducible ApexGuru command/configuration and target identity"
  - "Normalized finding inventory with severity, rule, file, location, message, resources, and evidence mode"
  - "Triage disposition: fix, validate, suppress with rationale, defer, or not-applicable"
  - "Before/after scan plus tests and performance evidence for accepted fixes"
dependencies:
  - devops/salesforce-code-analyzer
  - apex/apex-performance-profiling
  - apex/soql-optimization
runtime_orphan: true
runtime_orphan_reason: "No dedicated runtime agent owns ApexGuru finding triage as its primary deliverable; Code Analyzer packages hand off to this skill without an agent-owned ApexGuru workflow."
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-09-01
---

# ApexGuru Performance Analysis

Use ApexGuru as one evidence source for Apex performance work. In Salesforce Code Analyzer v5 it is an AI-driven remote analysis engine that requires an authenticated Salesforce org, scans Apex `.cls` and `.trigger` files, and returns line-level JSON findings. A connected org is required for the service; that fact alone does **not** prove the report contains production runtime telemetry.

---

## Preconditions

Confirm all of the following before scanning:

| Check | Required evidence | Stop condition |
|---|---|---|
| Code Analyzer generation | `sf code-analyzer --help` or installed plugin version confirms v5 commands | Legacy `sfdx scanner:*` only |
| Target identity | Exact org alias/username resolved by Salesforce CLI | Alias absent, ambiguous, or unauthenticated |
| ApexGuru availability | Org supports and has ApexGuru activated | Engine unavailable or activation unknown for a required scan |
| Workspace | Explicit project/workspace root | Accidental scan of a home or monorepo root |
| Targets | Bounded `.cls` and `.trigger` files inside the workspace | Request expects Flow, metadata XML, objects, or other unsupported files |
| Baseline | Current commit/hash, tests, and scan output path | Findings cannot be tied to source revision |
| Authority | Read/analysis operation only; no production mutation implied | Request asks the scan to approve or deploy a fix |

Authentication is reused from the Salesforce CLI session. Do not put usernames, passwords, access tokens, or refresh tokens in `code-analyzer.yml`.

---

## Reproducible CLI Scan

Use Code Analyzer v5 and write machine-readable output:

```bash
sf code-analyzer run \
  --rule-selector apexguru \
  --workspace . \
  --target "force-app/main/default/classes/**/*.cls" \
  --target "force-app/main/default/triggers/**/*.trigger" \
  --target-org my-apexguru-org \
  --view detail \
  --output-file artifacts/apexguru-results.json
```

Important behavior:

- `--target-org` identifies the authenticated org used by remote engines such as ApexGuru.
- Every target must live under the declared workspace.
- File extension on `--output-file` selects the output schema; use JSON or SARIF when downstream automation needs complete locations.
- ApexGuru scans `.cls` and `.trigger` only. A successful command is not evidence that Flow, object metadata, Visualforce, or LWC was analyzed.
- Use a severity threshold only when the team has defined which ApexGuru severities are merge-blocking and has tested false-positive handling.

For the installed CLI, verify flags with:

```bash
sf code-analyzer run --help
```

---

## Project Configuration

A project can set ApexGuru engine defaults in `code-analyzer.yml`:

```yaml
engines:
  apexguru:
    disable_engine: false
    target_org: my-apexguru-org
    api_timeout_ms: 300000
    api_initial_retry_ms: 2000
    api_max_retry_ms: 60000
    api_backoff_multiplier: 2
```

The shown timeout/backoff values are documented defaults. Change them only for an observed need and keep `api_max_retry_ms >= api_initial_retry_ms`. The overall `api_timeout_ms` remains the hard budget.

Prefer an explicit `--target-org` in CI when multiple authenticated orgs exist; it is easier to audit than relying on a developer's default org. Never commit secret material.

---

## Evidence Mode and Attribution

Classify the output before interpreting it:

| Mode | What may be claimed |
|---|---|
| Code Analyzer ApexGuru JSON | ApexGuru analyzed the identified source revision through the authenticated org service and returned these findings |
| Report explicitly carries `analysisMode: static` | Preserve the label `Static only`; do not infer production behavior |
| Report explicitly carries `analysisMode: full` or a documented equivalent | Preserve the report's exact label and evidence; identify which metrics are actually present |
| No mode field or runtime metrics | Label `Source analysis`; do not call it production telemetry, hotspot frequency, or measured runtime impact |
| Debug logs, Event Monitoring, APM, or transaction traces | Treat as separate runtime evidence and link it to the source finding without attributing it to ApexGuru unless the report says so |

A finding's severity is the engine's prioritization, not a measured CPU/heap/query cost. Validate impact in the relevant transaction and data-volume context.

---

## JSON Result Contract

Code Analyzer v5 JSON contains a root object with `runDir`, `violationCounts`, `versions`, and `violations`. Each violation should preserve:

- `rule` and `engine`;
- numeric severity 1–5;
- message and tags;
- all locations plus `primaryLocationIndex`;
- resource links and available suggestions/fixes;
- source revision, workspace, target org identity, command, and scan timestamp stored beside the report.

Do not flatten multi-location findings to one line when the analysis path matters. CSV includes only the primary location; JSON or SARIF is preferable for review and automation.

---

## Recommended Workflow

1. **Validate provenance and scope** — source revision, workspace, authenticated target org, command, Code Analyzer/engine versions, `.cls`/`.trigger` targets, timestamp, and output hash.
2. **Normalize and group findings** with the bundled checker while preserving original JSON. Group by rule, affected transaction/entry point, shared query/DML pattern, and severity—not severity alone.
3. **Inspect code context** around every primary and related location, and confirm that the finding applies to a reachable path.
4. **Cross-check runtime relevance** using tests, data volume, query plans, debug logs, transaction traces, or production insights when authorized and available.
5. **Choose a disposition and design** the smallest safe change: `fix`, `validate`, `suppress-with-rationale`, `defer`, or `not-applicable`. Preserve sharing, CRUD/FLS, transaction semantics, bulk behavior, ordering, and error handling.
6. **Test and rescan** positive, negative, bulk, and failure paths, then rerun the same targets with the same engine/config and compare result hashes/findings.
7. **Record residual risk** and supporting evidence. A zero-finding scan is not proof of runtime performance or absence of all Apex defects.

---

## Disposition Criteria

| Disposition | Use when | Required record |
|---|---|---|
| `fix` | Finding is applicable and a safe change is understood | Change, tests, before/after scan, runtime or scale rationale |
| `validate` | Applicability or impact depends on data shape or call path | Exact experiment/query plan/log evidence needed |
| `suppress-with-rationale` | Finding is accepted, false positive, generated code, or unavoidable under a documented constraint | Scope-limited suppression, owner, review trigger, risk |
| `defer` | Valid issue is lower priority than current risk/capacity | Backlog owner, severity rationale, review date/trigger |
| `not-applicable` | Code path or assumption does not apply | Reproducible evidence; do not dismiss from intuition |

Never auto-apply generated fixes. Performance changes can alter correctness, locking, sharing, query selectivity, memory, and transaction boundaries.

---

## Validation Checklist

- [ ] Exact source revision, workspace, target org, command, versions, timestamp, and output hash are recorded
- [ ] Target org is authenticated and ApexGuru availability is verified
- [ ] Only `.cls` and `.trigger` coverage is claimed
- [ ] Report mode is preserved; absent mode is labeled `Source analysis`
- [ ] Every finding retains severity, rule, message, all locations, and resources
- [ ] Applicability is checked against call path, data volume, sharing, and transaction context
- [ ] Fixes preserve security, bulk behavior, correctness, and error handling
- [ ] Tests and relevant runtime/scale evidence accompany accepted changes
- [ ] Same-target before/after scan is captured
- [ ] Remaining findings and suppressions have owners and rationale
- [ ] Zero findings is not presented as a performance certification

---

## Result Validation Command

```bash
python3 skills/apex/apexguru-performance-analysis/scripts/check_apexguru_performance_analysis.py \
  --input artifacts/apexguru-results.json \
  --output artifacts/apexguru-normalized.json
```

The checker validates the Code Analyzer JSON shape, severity/location data, Apex file scope, and evidence-mode labeling. It does not contact Salesforce or judge whether a recommendation is correct.

---

## Related Skills

- `devops/salesforce-code-analyzer` — install/configure v5, combine engines, output formats, CI gates, and suppression policy.
- `apex/apex-performance-profiling` — measure actual transaction behavior and governor consumption.
- `apex/soql-optimization` — validate query selectivity and redesign query patterns.
- `apex/bulkification-patterns` — remediate loop/query/DML patterns while preserving semantics.
- `apex/apexguru-performance-analysis` does not deploy, approve, or certify code.

See the bundled references for triage examples, attribution failures, and the official source map.
