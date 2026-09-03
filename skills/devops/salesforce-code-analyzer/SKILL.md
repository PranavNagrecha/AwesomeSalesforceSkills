---
name: salesforce-code-analyzer
description: "Use this skill to configure and run Salesforce Code Analyzer v5 across PMD, ESLint, RetireJS, Regex, Flow, CPD, SFGE, and remote ApexGuru analysis for CI quality gates and AppExchange review preparation. Trigger keywords: code analyzer, sca run, pmd apex, eslint lwc, graph engine, apexguru. NOT for triaging ApexGuru findings and proving performance impact — use apex/apexguru-performance-analysis. NOT for manual code review or runtime debugging."
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
  - "add a custom pmd rule to salesforce code analyzer"
  - "run the remote ApexGuru engine against authenticated-org Apex source"
  - "write a custom regex rule in code-analyzer.yml"
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
  - "Target engines to run (PMD, CPD, ESLint, RetireJS, Regex, Flow, Graph Engine/sfge, ApexGuru)"
  - "Severity threshold for CI gate (1=critical, 2=high, 3=moderate, 4=low, 5=info)"
  - "Rule selector string or AppExchange preset if preparing a security review submission"
  - "Authenticated target org alias when a remote engine such as ApexGuru is selected"
  - "Output format required by the CI system (json, xml, csv, html, or sarif — set by the --output-file extension)"
outputs:
  - "Scan results report in the selected output format"
  - "Annotated list of violations with file, line, engine, rule, and severity"
  - "code-analyzer.yml configuration file for project-level defaults"
  - "Remediation guidance for each flagged rule category"
dependencies: []
version: 1.2.0
author: Pranav Nagrecha
updated: 2026-09-01
---

# Salesforce Code Analyzer

This skill activates when a practitioner needs to configure, run, or interpret Salesforce Code Analyzer v5 — the Salesforce CLI plugin that performs static analysis of Apex, Lightning Web Components, and JavaScript dependencies. It covers CI gate configuration, AppExchange security review preparation, Graph Engine taint analysis, remote ApexGuru engine setup, and custom rule authoring. Deep triage of ApexGuru performance recommendations belongs to `apex/apexguru-performance-analysis`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the project is using Salesforce Code Analyzer **v5** (GA, replaces v4 which was retired August 2025). The CLI command is `sf code-analyzer run`, not the legacy `sfdx scanner:run`. Mixing v4 and v5 commands in the same pipeline is a common source of breakage.
- Identify which engines are relevant: PMD targets Apex and Visualforce; ESLint targets JavaScript, TypeScript, and LWC; RetireJS scans JavaScript dependencies for known vulnerabilities; Regex is engine-agnostic pattern matching; Graph Engine (engine name `sfge`) performs data-flow analysis on Apex. v5 also ships Flow and CPD engines. ApexGuru is a remote, AI-driven Apex performance engine that requires an authenticated org and scans `.cls` and `.trigger` files only.
- Confirm whether the output is for a CI gate (needs `--severity-threshold` and a machine-readable `--output-file` such as JSON or XML — the extension selects the format) or for a developer review session (`--view table` is fine).
- For AppExchange security review submissions, the documented selectors are `--rule-selector AppExchange --rule-selector Recommended:Security`, with an HTML report generated via `--output-file` and attached in the Security Review Wizard.

---

## Core Concepts

### Engine Selection and Rule Selectors

Salesforce Code Analyzer v5 runs one or more engines against source files. Each engine uses rules organized into categories. The `--rule-selector` flag accepts tags, rule names, category paths, or preset names. Common selectors:

- `all` — runs every rule from every enabled engine (broadest coverage, most noise)
- `Recommended` — the default selector: rules from all available engines tagged `Recommended`
- `Security` — all rules tagged Security across all engines
- `AppExchange` — the managed-package security review rules; the security-review docs pair it with `Recommended:Security`
- `sfge` — all Graph Engine rules, selected by engine name
- `pmd:ApexCRUDViolation` — a single named PMD rule
- `eslint:@salesforce/lwc/no-inner-html` — a single named ESLint rule

Rule selectors are composable: `--rule-selector Security --rule-selector pmd:ApexFlowControl` adds specific rules on top of a category.

### ApexGuru Is a Remote Engine, Not a Generic Runtime Profiler

Select ApexGuru with `--rule-selector apexguru` and pass an explicit authenticated org using `--target-org <alias>` when more than one org is available. Authentication comes from the Salesforce CLI session; credentials never belong in `code-analyzer.yml`. The engine returns line-level Apex findings in the same Code Analyzer output formats, but it does not scan Flow, object metadata, LWC, or other files.

```bash
sf code-analyzer run \
  --rule-selector apexguru \
  --workspace . \
  --target "force-app/main/default/classes/**/*.cls" \
  --target-org perf-sandbox \
  --view detail \
  --output-file artifacts/apexguru-results.json
```

A connected org is a service prerequisite, not proof that the JSON includes production telemetry. Preserve an explicit report mode if one exists; otherwise label the output `Source analysis` and route interpretation, validation, and before/after evidence to `apex/apexguru-performance-analysis`. The historical Code Analyzer MCP tool surface did not include ApexGuru and Salesforce states that that MCP integration is no longer supported as of June 2026. SfSkills exposes this guidance as MCP prompts/resources, while execution remains the CLI or supported Salesforce tooling.

### Severity Levels and CI Gates

Code Analyzer v5 uses a 1–5 severity scale:

| Level | Label    |
|-------|----------|
| 1     | Critical |
| 2     | High     |
| 3     | Moderate |
| 4     | Low      |
| 5     | Info     |

The `--severity-threshold <N>` flag causes the command to fail with a non-zero exit code when a violation meets or exceeds the threshold. A threshold of 2 fails the build on Critical and High violations. Most teams start with threshold 2 in CI and tighten to 3 once violations are remediated. Setting the threshold to 5 fails on any violation, including Info-level findings, which is too strict for most brownfield codebases.

### Graph Engine — Dataflow and Taint Analysis

Graph Engine is the most powerful (and slowest) engine. It performs interprocedural control flow and taint analysis on Apex. It can detect:

- SOQL injection paths where user-controlled input reaches a dynamic SOQL string without sanitization
- Insecure deserialization via `JSON.deserialize` on tainted input
- Path-sensitive CRUD/FLS violations (it traces whether a permission check actually guards the DML path, unlike PMD's simpler heuristics)

Graph Engine requires more memory and run time — it runs on Java and dynamically calculates the allowed path complexity from the maximum Java heap size. It is best isolated to security-focused pipeline stages or pre-submit checks rather than every push. Select its rules explicitly with `--rule-selector sfge`. In `code-analyzer.yml` the engine's name is `sfge`: set `engines.sfge.disable_engine: true` to keep it out of fast pipeline stages, and tune memory with `engines.sfge.java_max_heap_size`.

### Configuration File (code-analyzer.yml)

Project-level defaults live in `code-analyzer.yml` at the project root. This file controls which engines are enabled by default, which paths to exclude (e.g. `node_modules`, test data), custom rule paths, and output preferences. Committing this file ensures every developer and CI runner uses the same configuration without requiring long CLI flags on every invocation.

### Custom Rules — Three Mechanisms, One Config File

All three custom-rule mechanisms are wired through `code-analyzer.yml`, but each engine has its own key and format:

**1. Regex engine — config-only rules.** Define rules directly under `engines.regex.custom_rules` as a mapping keyed by rule name. `regex`, `file_extensions`, and `description` are required; `violation_message`, `severity`, `tags`, and `regex_ignore` (a negative pattern to exclude false positives) are optional. Severity accepts `1`/`'Critical'` through `5`/`'Info'`; default is `3` (Moderate), default tags are `['Recommended']`.

```yaml
engines:
  regex:
    custom_rules:
      NoDebugStatements:
        regex: /System\.debug\s*\(/gi
        file_extensions: [".cls", ".trigger"]
        description: "Flags leftover System.debug statements in Apex."
        severity: "Info"
        tags: ["TechDebt"]
```

The pattern **must include the global modifier** — `/System\.debug/gi` is valid, `/System\.debug/i` is not. A pattern without it makes the regex engine return an error when the rule runs.

**2. PMD engine — ruleset XML, two authoring paths.** Register custom ruleset XML files via the `engines.pmd.custom_rulesets` array. Each entry is either an on-disk path (absolute or relative to `config_root`) or a resource path on the Java classpath (e.g. inside a JAR). Two ways to author the rules themselves:

- **XPath-based** — the rule is defined entirely inside the ruleset XML using an XPath expression against the AST. No Java compilation required. Use the `ast-dump` command to inspect the AST when writing the expression.
- **Java-based** — custom rule classes compiled into a JAR, referenced by a ruleset XML. The JAR must additionally be registered in `engines.pmd.java_classpath_entries` — `custom_rulesets` alone is not enough.

```yaml
engines:
  pmd:
    custom_rulesets:
      - pmd/apex-team-rules.xml          # relative to config_root
      - com/example/custom-rules.xml     # classpath resource inside a JAR
    java_classpath_entries:
      - libs/custom-pmd-rules.jar        # required for Java-based rule classes
```

Code Analyzer automatically adds a `Custom` tag to every custom PMD rule, and the ruleset's `name` attribute (spaces removed) becomes a second filterable tag — `<ruleset name="My Custom PMD Rules">` yields tags `Custom` and `MyCustomPMDRules`. Verify registration with `sf code-analyzer rules --rule-selector Custom`.

**3. ESLint engine — bring your own ESLint config.** There is no Code-Analyzer-specific rule format; point `engines.eslint.eslint_config_file` at your project's ESLint config (absolute or relative to `config_root`), or set `auto_discover_eslint_config: true` to have Code Analyzer find and apply it. Custom rules and plugins in that config are merged with the built-in base configurations.

```yaml
engines:
  eslint:
    eslint_config_file: eslint.config.js
```

### Overriding Existing Rules

Independent of adding new rules, any rule from any engine can be re-tuned in a top-level `rules:` block — nesting is `rules → engine name → rule name → properties`. Overridable properties: `severity`, `tags`, and `disabled` (suppress a rule's violations workspace-wide).

```yaml
rules:
  eslint:
    sort-vars:
      severity: Info
      tags: [Recommended, Suggestions]
  regex:
    NoTrailingWhiteSpace:
      tags: []
```

---

## Common Patterns

### Pattern: CI Gate with Severity Threshold

**When to use:** Any CI pipeline (GitHub Actions, Salesforce DX pipelines, Jenkins) where you want to block deployment if critical or high violations are present.

**How it works:**

```bash
# Run all Security rules, fail build on severity 2 (High) or worse, output JSON for CI
sf code-analyzer run \
  --rule-selector Security \
  --workspace force-app/main/default \
  --severity-threshold 2 \
  --output-file scan-results.json
```

The command fails with a non-zero exit code if violations at severity 1 or 2 are found. The CI system reads the exit code and fails the step. The `.json` extension on `--output-file` selects the JSON format, and the file is archived as a build artifact for review.

**Why not the alternative:** Running without `--severity-threshold` always exits 0, meaning the build passes regardless of violation severity. The results file is produced but the pipeline never fails — a common misconfiguration.

### Pattern: AppExchange Security Review Scan

**When to use:** Preparing a managed package submission to AppExchange. The security-review documentation names the exact selectors to run; using any other selector risks missing required checks.

**How it works:**

```bash
# Run the documented security-review selectors plus the Graph Engine rules, output HTML
sf code-analyzer run \
  --rule-selector AppExchange \
  --rule-selector Recommended:Security \
  --rule-selector sfge \
  --workspace force-app/main/default \
  --output-file appexchange-scan.html
```

Attach `appexchange-scan.html` to your submission in the AppExchange Security Review Wizard. The scans don't have to be 100% passing — run them, address the violations you can fix, re-run, and submit the reports, with a written explanation for every suppressed or unresolved finding.

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

For persistent project-wide adjustments, override the rule in the top-level `rules:` block of `code-analyzer.yml`:

```yaml
rules:
  pmd:
    ApexCRUDViolation:
      severity: Low   # downgrade, don't suppress entirely
```

**Why not the alternative:** Blanket `@SuppressWarnings('PMD')` with no rule name silences all PMD rules on the method, making it impossible to detect future violations added by rule set updates.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Pre-commit developer feedback | `sf code-analyzer run --view table` with `--severity-threshold 3` | Fast, human-readable terminal output |
| CI gate on every push | `--rule-selector Security --severity-threshold 2 --output-file scan-results.json` | Blocks High/Critical, produces artifact for audit |
| AppExchange submission | `--rule-selector AppExchange --rule-selector Recommended:Security --output-file appexchange-scan.html` | The documented security-review selectors; the HTML report is attached in the Security Review Wizard |
| Security-focused deep scan | Add `--rule-selector sfge` explicitly | Selects all Graph Engine data-flow rules regardless of which tag-based selectors are in play |
| Apex performance source scan | `--rule-selector apexguru --target-org <alias> --output-file results.json` | Uses the remote ApexGuru engine with explicit target identity; triage in `apex/apexguru-performance-analysis` |
| Brownfield codebase with many existing violations | Start at threshold 1 or 2 (Critical, or Critical+High only) and tighten toward 3+ over time | Avoid blocking every push while tech debt is addressed |
| Custom rule authoring (Apex) | Write a PMD ruleset XML (XPath-based, no compilation) and register it in `engines.pmd.custom_rulesets` in `code-analyzer.yml` | `custom_rulesets` is the v5 wiring mechanism; XPath rules avoid the Java build + `java_classpath_entries` overhead |
| Custom rule authoring (LWC) | Write custom ESLint rules/plugins in your ESLint config and point `engines.eslint.eslint_config_file` at it | ESLint config is the extension point; Code Analyzer merges it with its base configurations |
| Custom rule authoring (any text pattern) | Define `engines.regex.custom_rules` entries in `code-analyzer.yml` | Config-only, no XML or plugin needed; remember the mandatory global modifier on the pattern |
| Re-tune or disable an existing rule | Top-level `rules:` block override (`severity`, `tags`, `disabled`) | Works on any rule from any engine without authoring anything new |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm v5 is installed.** Run `sf plugins --core` and verify `@salesforce/plugin-code-analyzer` is present. If missing, run `sf plugins install @salesforce/plugin-code-analyzer`. Do not confuse with the retired v4 plugin (`@salesforce/sfdx-scanner`).

2. **Create or update `code-analyzer.yml`.** Place the file at the project root. Set default target paths, exclude `node_modules` and test data directories, and configure which engines are enabled by default. Register any team custom rules here too — `engines.pmd.custom_rulesets` (plus `java_classpath_entries` for Java-based rules), `engines.regex.custom_rules`, `engines.eslint.eslint_config_file` — and re-tune built-in rules in the top-level `rules:` block. Commit this file so CI and all developers share the same baseline configuration.

3. **Run a baseline scan across all Security rules.** Use `sf code-analyzer run --rule-selector Security --workspace force-app/main/default --view table` to understand the violation landscape before setting thresholds. Count violations by severity to inform CI gate settings.

4. **Configure the CI gate.** Add `--severity-threshold 2` (or 1, Critical-only, for heavily indebted brownfield code) and `--output-file scan-results.json` to the pipeline command — the `.json` extension selects the format. Ensure the step fails on non-zero exit. Archive the JSON artifact.

5. **Add remote ApexGuru analysis when performance review requires it.** Pass an explicit `--target-org`, scope `.cls`/`.trigger` targets, write JSON, and preserve source revision and output hash. Do not claim runtime telemetry unless the report actually contains it.

6. **Add Graph Engine rules for security-critical paths.** For AppExchange packages or security-sensitive code, add `--rule-selector sfge` alongside `--rule-selector AppExchange --rule-selector Recommended:Security`. Run this as a separate, scheduled pipeline stage to avoid slowing every push.

7. **Triage, remediate, and validate.** Fix severity 1 and 2 first; for intentional bypasses, add `@SuppressWarnings` with the exact rule name and a justification comment. Re-run with `AppExchange` and `Recommended:Security` (plus `sfge` when required), confirm zero Critical/High findings or document every suppression, then generate the HTML report for Security Review submission.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `code-analyzer.yml` is committed at project root with `node_modules` and test data excluded
- [ ] CI pipeline uses `--severity-threshold` and exits non-zero on violations
- [ ] All `@SuppressWarnings` annotations include the specific rule name (not blanket `PMD`) and a justification comment
- [ ] AppExchange scans use `--rule-selector AppExchange --rule-selector Recommended:Security` (plus `--rule-selector sfge` for data-flow coverage)
- [ ] Output matches the consumer: JSON/XML `--output-file` for CI systems, `--view table` for local review
- [ ] False positive documentation is prepared for any suppressed findings in AppExchange submissions
- [ ] Plugin version is v5; no legacy `sfdx scanner:run` commands remain in the pipeline
- [ ] Custom PMD rulesets are registered in `engines.pmd.custom_rulesets`; Java-based rule JARs are also in `engines.pmd.java_classpath_entries`
- [ ] Custom regex rules include the global modifier (`/pattern/g...`) and a `description`
- [ ] Rule severity/tag adjustments use the top-level `rules:` block, not ad-hoc suppressions
- [ ] ApexGuru runs identify the authenticated target org, scope only `.cls`/`.trigger`, preserve JSON and source revision, and avoid unsupported runtime-telemetry claims

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **v4 commands silently succeed but produce wrong output** — If `sfdx scanner:run` (v4 syntax) is still in a pipeline after the v4 plugin was removed, the Salesforce CLI may route the command to v5 with unexpected argument mapping or fail silently. Always use the v5 command `sf code-analyzer run` explicitly and verify with `sf plugins`.

2. **Graph Engine memory limits on large orgs** — Graph Engine walks code paths on the Java VM and dynamically limits the allowed path complexity based on the maximum Java heap size, skipping paths it detects might cause OutOfMemory errors. Mitigate by scoping the scan (`--workspace force-app/main/default/classes/security`) or raising the heap via `engines.sfge.java_max_heap_size` in `code-analyzer.yml`; long-running analyses may also need a higher `engines.sfge.java_thread_timeout`.

3. **ApexGuru is not included in the retired Code Analyzer MCP engine list** — Do not assume an LLM-facing Code Analyzer MCP call ran ApexGuru. Use the supported CLI/VS Code path and expose the resulting evidence through SfSkills resources or reports.

4. **`--severity-threshold` failures are "non-zero", not a documented specific code** — Code Analyzer fails with a non-zero exit code when a violation meets or exceeds the threshold. Some CI systems treat only specific non-zero codes as failures. Always test that your CI step is correctly failing by running with a known violation and confirming the pipeline fails, not just that the file is produced.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `scan-results.json` | Machine-readable violation report for CI archiving and downstream tooling |
| `appexchange-scan.html` | HTML report attached to the submission in the AppExchange Security Review Wizard |
| `code-analyzer.yml` | Project-level configuration file controlling engines, exclusions, and rule overrides |
| Inline `@SuppressWarnings` annotations | Code-level false-positive suppressions with rule name and justification |

---

## Related Skills

- `deployment-error-troubleshooting` — Use alongside this skill when code analyzer violations are causing deployment failures or when post-deployment errors trace back to security rule violations
- `connected-app-security-policies` — Complements AppExchange scan prep by ensuring connected app OAuth scopes and policies meet Partner Security requirements
- `apex-security-patterns` — Deep dive into Apex-level CRUD/FLS, sharing model, and injection prevention that code analyzer rules enforce
- `apex/apexguru-performance-analysis` — Target identity, evidence-mode attribution, finding triage, runtime validation, and before/after proof for ApexGuru results
