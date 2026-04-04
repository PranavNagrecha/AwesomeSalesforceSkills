---
name: salesforce-code-analyzer
description: "Use this skill to run Salesforce Code Analyzer v5 for static analysis, CI quality gates, and AppExchange security review preparation. Trigger keywords: code analyzer, sca run, pmd apex, eslint lwc, graph engine, taint analysis, retire js, ci gate, severity threshold, AppExchange scan. NOT for manual code review workflows, runtime debugging, performance profiling, or Checkmarx/CodeScan third-party tools."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do i run salesforce code analyzer in my CI pipeline"
  - "pmd is flagging apex crud violations on my classes"
  - "what rule selector do i use for appexchange security review"
  - "graph engine dataflow taint analysis on apex"
  - "how to set a severity threshold to fail the build on high violations"
  - "retire js flagging a dependency in my lwc project"
  - "how do i suppress a false positive in salesforce code analyzer"
tags:
  - salesforce-code-analyzer
  - static-analysis
  - pmd
  - eslint
  - graph-engine
  - ci-cd
  - appexchange
  - devops
  - security
inputs:
  - "Salesforce DX project directory or metadata source path to scan"
  - "Target engines to run (PMD, ESLint, RetireJS, Regex, Graph Engine)"
  - "Severity threshold for CI gate (1=critical, 2=high, 3=moderate, 4=low)"
  - "Rule selector string or AppExchange preset if preparing a security review submission"
  - "Output format required by the CI system (table, json, csv, xml)"
outputs:
  - "Scan results report in the selected output format"
  - "Annotated list of violations with file, line, engine, rule, and severity"
  - "code-analyzer.yml configuration file for project-level defaults"
  - "Remediation guidance for each flagged rule category"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Salesforce Code Analyzer

This skill activates when a practitioner needs to configure, run, or interpret Salesforce Code Analyzer v5 — the Salesforce CLI plugin that performs static analysis of Apex, Lightning Web Components, and JavaScript dependencies. It covers CI gate configuration, AppExchange security review preparation, Graph Engine taint analysis, and custom rule authoring.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the project is using Salesforce Code Analyzer **v5** (GA, replaces v4 which was retired August 2025). The CLI command is `sf code-analyzer run`, not the legacy `sfdx scanner:run`. Mixing v4 and v5 commands in the same pipeline is a common source of breakage.
- Identify which engines are relevant: PMD targets Apex and Visualforce; ESLint targets LWC and JavaScript; RetireJS scans JavaScript dependencies for known vulnerabilities; Regex is engine-agnostic pattern matching; Graph Engine performs interprocedural dataflow and taint analysis on Apex.
- Confirm whether the output is for a CI gate (needs `--severity-threshold` and a machine-readable format like JSON or XML) or for a developer review session (table output is fine).
- For AppExchange security review submissions, the required rule selector is `AppExchange`. This preset activates a specific set of security-oriented rules that the Partner Security team validates against.

---

## Core Concepts

### Engine Selection and Rule Selectors

Salesforce Code Analyzer v5 runs one or more engines against source files. Each engine uses rules organized into categories. The `--rule-selector` flag accepts tags, rule names, category paths, or preset names. Common selectors:

- `all` — runs every rule from every enabled engine (broadest coverage, most noise)
- `Security` — all rules tagged Security across all engines
- `AppExchange` — the managed-package security review preset; required for ISV submissions
- `pmd:ApexCRUDViolation` — a single named PMD rule
- `eslint:@salesforce/lwc/no-inner-html` — a single named ESLint rule

Rule selectors are composable: `--rule-selector Security --rule-selector pmd:ApexFlowControl` adds specific rules on top of a category.

### Severity Levels and CI Gates

Code Analyzer v5 uses a 1–4 severity scale:

| Level | Label    |
|-------|----------|
| 1     | Critical |
| 2     | High     |
| 3     | Moderate |
| 4     | Low      |

The `--severity-threshold <N>` flag causes the process to exit with a non-zero code if any violation at or above severity N is found. A threshold of 2 fails the build on Critical and High violations. Most teams start with threshold 2 in CI and tune down to 3 once violations are remediated. Setting threshold to 4 fails on any violation, which is too strict for most brownfield codebases.

### Graph Engine — Dataflow and Taint Analysis

Graph Engine is the most powerful (and slowest) engine. It performs interprocedural control flow and taint analysis on Apex. It can detect:

- SOQL injection paths where user-controlled input reaches a dynamic SOQL string without sanitization
- Insecure deserialization via `JSON.deserialize` on tainted input
- Path-sensitive CRUD/FLS violations (it traces whether a permission check actually guards the DML path, unlike PMD's simpler heuristics)

Graph Engine requires more memory and run time. It is best isolated to security-focused pipeline stages or pre-submit checks rather than every push. Enable it explicitly: `--engine graph-engine`.

### Configuration File (code-analyzer.yml)

Project-level defaults live in `code-analyzer.yml` at the project root. This file controls which engines are enabled by default, which paths to exclude (e.g. `node_modules`, test data), custom rule paths, and output preferences. Committing this file ensures every developer and CI runner uses the same configuration without requiring long CLI flags on every invocation.

---

## Common Patterns

### Pattern: CI Gate with Severity Threshold

**When to use:** Any CI pipeline (GitHub Actions, Salesforce DX pipelines, Jenkins) where you want to block deployment if critical or high violations are present.

**How it works:**

```bash
# Run all Security rules, fail build on severity 2 (High) or worse, output JSON for CI
sf code-analyzer run \
  --rule-selector Security \
  --target force-app/main/default \
  --severity-threshold 2 \
  --output-file scan-results.json \
  --format json
```

The process exits with code 1 if violations at severity 1 or 2 are found. The CI system reads the exit code and fails the step. The JSON file is archived as a build artifact for review.

**Why not the alternative:** Running without `--severity-threshold` always exits 0, meaning the build passes regardless of violation severity. The results file is produced but the pipeline never fails — a common misconfiguration.

### Pattern: AppExchange Security Review Scan

**When to use:** Preparing a managed package submission to AppExchange. The Partner Security team validates against a defined rule set; using any other selector risks missing required checks.

**How it works:**

```bash
# Run the AppExchange preset, include Graph Engine, output XML for upload
sf code-analyzer run \
  --rule-selector AppExchange \
  --engine graph-engine \
  --target force-app/main/default \
  --format xml \
  --output-file appexchange-scan.xml
```

Upload `appexchange-scan.xml` to the AppExchange Security Review Wizard. Document any false positives in a separate justification file — the Partner team requires a written explanation for every suppressed or unresolved finding.

**Why not the alternative:** Running with `--rule-selector all` produces results that don't map to the AppExchange checklist, making it harder to distinguish relevant from irrelevant findings during the review.

### Pattern: Suppressing False Positives

**When to use:** A PMD or Graph Engine rule flags code that is intentionally correct — for example, a CRUD check that is performed in a parent method Graph Engine cannot trace.

**How it works:**

For PMD rules, add a `@SuppressWarnings` annotation with justification:

```apex
// Graph Engine cannot trace the permission check in the calling service layer
@SuppressWarnings('PMD.ApexCRUDViolation')
public void updateRecord(Id recordId) {
    // Permission verified by caller: AccountService.assertEditAccess()
    update new Account(Id = recordId, Name = 'Updated');
}
```

For persistent project-wide suppressions, configure path exclusions in `code-analyzer.yml`:

```yaml
engines:
  pmd:
    rule-overrides:
      ApexCRUDViolation:
        severity: 4   # downgrade, don't suppress entirely
```

**Why not the alternative:** Blanket `@SuppressWarnings('PMD')` with no rule name silences all PMD rules on the method, making it impossible to detect future violations added by rule set updates.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Pre-commit developer feedback | `sf code-analyzer run --format table` with `--severity-threshold 3` | Fast, human-readable, doesn't fail on informational findings |
| CI gate on every push | `--rule-selector Security --severity-threshold 2 --format json` | Blocks High/Critical, produces artifact for audit |
| AppExchange submission | `--rule-selector AppExchange --engine graph-engine --format xml` | Matches required ruleset; XML is accepted by Security Review Wizard |
| Security-focused deep scan | Add `--engine graph-engine` explicitly | Graph Engine is not in the default engine set; must be opted in |
| Brownfield codebase with many existing violations | Increase threshold to 3 or 4 and ratchet down over time | Avoid blocking every push while tech debt is addressed |
| Custom rule authoring (Apex) | Write PMD XML ruleset and reference via `--rule-selector path/to/rules.xml` | PMD supports custom XML rules natively; deploy alongside the project |
| Custom rule authoring (LWC) | Write custom ESLint plugin and reference in `.eslintrc` | ESLint plugin API is the extension point for JS/LWC rules |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm v5 is installed.** Run `sf plugins --core` and verify `@salesforce/plugin-code-analyzer` is present. If missing, run `sf plugins install @salesforce/plugin-code-analyzer`. Do not confuse with the retired v4 plugin (`@salesforce/sfdx-scanner`).

2. **Create or update `code-analyzer.yml`.** Place the file at the project root. Set default target paths, exclude `node_modules` and test data directories, and configure which engines are enabled by default. Commit this file so CI and all developers share the same baseline configuration.

3. **Run a baseline scan across all Security rules.** Use `sf code-analyzer run --rule-selector Security --target force-app/main/default --format table` to understand the violation landscape before setting thresholds. Count violations by severity to inform CI gate settings.

4. **Configure the CI gate.** Add `--severity-threshold 2` (or 3 for brownfield) and `--format json --output-file scan-results.json` to the pipeline command. Ensure the step fails on non-zero exit. Archive the JSON artifact.

5. **Add Graph Engine for security-critical paths.** For AppExchange packages or security-sensitive code, add `--engine graph-engine` and `--rule-selector AppExchange`. Run this as a separate, scheduled pipeline stage to avoid slowing every push.

6. **Triage and remediate violations.** Fix rule violations at severity 1 and 2 first. For intentional bypasses, add `@SuppressWarnings` with the exact rule name and a justification comment. Document all suppressions.

7. **Validate before submission.** Re-run with the full `AppExchange` selector and Graph Engine, confirm zero Critical/High violations or all suppressions are documented, then export XML for upload to the Security Review Wizard.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `code-analyzer.yml` is committed at project root with `node_modules` and test data excluded
- [ ] CI pipeline uses `--severity-threshold` and exits non-zero on violations
- [ ] All `@SuppressWarnings` annotations include the specific rule name (not blanket `PMD`) and a justification comment
- [ ] AppExchange scans use `--rule-selector AppExchange` and `--engine graph-engine`
- [ ] Output format matches the consumer: JSON/XML for CI systems, table for local review
- [ ] False positive documentation is prepared for any suppressed findings in AppExchange submissions
- [ ] Plugin version is v5; no legacy `sfdx scanner:run` commands remain in the pipeline

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **v4 commands silently succeed but produce wrong output** — If `sfdx scanner:run` (v4 syntax) is still in a pipeline after the v4 plugin was removed, the Salesforce CLI may route the command to v5 with unexpected argument mapping or fail silently. Always use the v5 command `sf code-analyzer run` explicitly and verify with `sf plugins`.

2. **Graph Engine memory exhaustion on large orgs** — Graph Engine builds an interprocedural call graph in memory. On projects with hundreds of Apex classes, it can exhaust the Node.js heap and exit with no useful error. Mitigate by running Graph Engine only on specific subdirectories (`--target force-app/main/default/classes/security`) or increasing the Node.js heap: `NODE_OPTIONS=--max-old-space-size=4096 sf code-analyzer run ...`.

3. **`--severity-threshold` exit code is not 1 on violation** — Code Analyzer exits with code 1 if a violation meets the threshold. However, some CI systems treat only specific non-zero codes as failures. Always test that your CI step is correctly failing by running with a known violation and confirming the pipeline fails, not just that the file is produced.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `scan-results.json` | Machine-readable violation report for CI archiving and downstream tooling |
| `appexchange-scan.xml` | XML report formatted for upload to the AppExchange Security Review Wizard |
| `code-analyzer.yml` | Project-level configuration file controlling engines, exclusions, and rule overrides |
| Inline `@SuppressWarnings` annotations | Code-level false-positive suppressions with rule name and justification |

---

## Related Skills

- `deployment-error-troubleshooting` — Use alongside this skill when code analyzer violations are causing deployment failures or when post-deployment errors trace back to security rule violations
- `connected-app-security-policies` — Complements AppExchange scan prep by ensuring connected app OAuth scopes and policies meet Partner Security requirements
- `apex-security-patterns` — Deep dive into Apex-level CRUD/FLS, sharing model, and injection prevention that code analyzer rules enforce
