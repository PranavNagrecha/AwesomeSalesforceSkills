# Gotchas — Salesforce Code Analyzer

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Graph Engine Is Not in the Default Engine Set

**What happens:** Developers run `sf code-analyzer run --rule-selector Security` expecting full security coverage including dataflow and taint analysis. Graph Engine does not run. SOQL injection paths and path-sensitive CRUD/FLS violations that only Graph Engine can detect are silently missed.

**When it occurs:** Any scan where `--engine graph-engine` is not explicitly specified. The default engine set includes PMD, ESLint, RetireJS, and Regex. Graph Engine must be opted in because it is computationally expensive and can take significantly longer than the other engines on large codebases.

**How to avoid:** For AppExchange security reviews and security-focused pipeline stages, always add `--engine graph-engine` explicitly. Consider a two-stage CI approach: fast engines on every push, Graph Engine on a nightly or pre-release job. Document the split so developers know which checks run where.

---

## Gotcha 2: Blanket `@SuppressWarnings('PMD')` Silences All PMD Rules

**What happens:** A developer uses `@SuppressWarnings('PMD')` to suppress a false-positive `ApexCRUDViolation`. This also suppresses all other PMD rules on the same method — including rules for which there are real violations. Future violations added by PMD rule set updates are also silently suppressed.

**When it occurs:** Any time `@SuppressWarnings('PMD')` (without a specific rule name) is applied to a class, method, or constructor. The suppression scope covers every current and future PMD rule, not just the intended one.

**How to avoid:** Always use the specific rule name: `@SuppressWarnings('PMD.ApexCRUDViolation')`. For multiple rules, list them: `@SuppressWarnings('PMD.ApexCRUDViolation,PMD.ApexSOQLInjection')`. Add a justification comment explaining why the suppression is intentional. During code review, flag any blanket `@SuppressWarnings('PMD')` without a rule name as a required fix.

---

## Gotcha 3: v4 Legacy Commands in CI Silently Produce Wrong Results

**What happens:** After migrating to Salesforce Code Analyzer v5, legacy `sfdx scanner:run` commands left in CI scripts either fail with `command not found` or — worse — if any v4 compatibility shim is present, run with mismatched argument parsing. The CI step may pass while producing an empty or malformed output file.

**When it occurs:** Projects that upgraded the plugin from v4 to v5 without auditing all pipeline scripts and Makefiles. The retired v4 plugin (`@salesforce/sfdx-scanner`) was retired in August 2025. Any reference to `sfdx scanner:run` or the old argument structure (`--category` instead of `--rule-selector`) is v4 syntax.

**How to avoid:** Audit all pipeline YAML, Makefiles, and shell scripts for `sfdx scanner` references. Replace with `sf code-analyzer run`. Verify the installed plugin: `sf plugins --core | grep code-analyzer`. Pin the plugin version in CI to avoid uncontrolled upgrades.

---

## Gotcha 4: `--severity-threshold` Does Not Filter Output — It Only Controls Exit Code

**What happens:** A practitioner sets `--severity-threshold 2` expecting the output file to contain only severity 1 and 2 violations. The output file contains all violations across all severity levels. The threshold only controls whether the process exits 0 or 1.

**When it occurs:** Any time the output file is used downstream as an input to another tool that expects only threshold-failing violations. For example, a script that counts lines in the output file to report violation counts will over-count.

**How to avoid:** Filter the JSON output in a post-processing step if you need only threshold-failing violations. Use `jq` or a Python script to filter `severity <= threshold`. Do not use `--severity-threshold` as a reporting filter — it is exclusively a CI gate mechanism.

---

## Gotcha 5: RetireJS Scans All JavaScript Files Including Vendored Libraries

**What happens:** RetireJS flags known-vulnerable JavaScript libraries bundled as static resources or in `node_modules` that are not actually loaded in the browser context of the managed package. The findings are technically correct but operationally irrelevant — the library is never executed in the target environment.

**When it occurs:** Projects that bundle third-party JS in static resources or have `node_modules` present in the target path. RetireJS has no awareness of whether the file is actually reachable.

**How to avoid:** Exclude paths that are not part of the deployable package in `code-analyzer.yml`:

```yaml
global:
  exclude:
    - force-app/main/default/staticresources/vendor
    - node_modules
```

For findings that cannot be excluded, document the false positive in the AppExchange submission with evidence that the library is not loaded in the package's execution context.
