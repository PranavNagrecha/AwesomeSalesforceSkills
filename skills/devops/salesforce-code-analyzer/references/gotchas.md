# Gotchas — Salesforce Code Analyzer

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Graph Engine (`sfge`) Coverage Depends Entirely on Your Rule Selector

**What happens:** Developers run `sf code-analyzer run` with a tag-based selector expecting full security coverage including Graph Engine data-flow analysis, and never verify that any `sfge` rules were actually selected. Path-sensitive violations that only Graph Engine's data-flow analysis can detect (such as `ApexFlsViolation` findings) are silently missed.

**When it occurs:** Which rules run is governed by `--rule-selector` (the default is `Recommended`); nothing about a tag-based selector guarantees the `sfge` data-flow rules are included. The engine can also be turned off outright via `engines.sfge.disable_engine: true` in `code-analyzer.yml` — a sensible default for fast pipeline stages that then silently applies to security scans too.

**How to avoid:** For security-focused pipeline stages, add `--rule-selector sfge` explicitly — per the official docs, "To select the Salesforce Graph Engine rules, use `--rule-selector sfge`." Verify what will run with `sf code-analyzer rules --rule-selector sfge`, and confirm the engine isn't disabled in `code-analyzer.yml`. Consider a two-stage CI approach: fast rules on every push, Graph Engine rules on a nightly or pre-release job, since data-flow analysis is significantly more expensive. Document the split so developers know which checks run where.

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

**How to avoid:** Exclude paths that are not part of the deployable package via the top-level `ignores` section of `code-analyzer.yml` (ignores take priority when a file appears in both `target` and `ignores`):

```yaml
ignores:
  - "force-app/main/default/staticresources/vendor/**"
  - "**/node_modules/**"
```

For findings that cannot be excluded, document the false positive in the AppExchange submission with evidence that the library is not loaded in the package's execution context.

---

## Gotcha 6: Custom Regex Rules Without a Global Modifier Fail at Run Time

**What happens:** A custom rule under `engines.regex.custom_rules` is defined with a pattern like `/Todo/i`. Configuration parsing appears fine, but when the rule runs, the regex engine returns an error instead of scan results.

**When it occurs:** Any custom regex rule whose pattern omits the global modifier. Per the official docs, `/Todo/gi` is valid; `/Todo/i` is not — a pattern without the global modifier causes the regex engine to error when the rule is run.

**How to avoid:** Always include `g` in the modifier set of every `regex` (and `regex_ignore`) value. Add a smoke run of `sf code-analyzer rules --rule-selector Custom` plus a scan of a known-matching fixture file to CI whenever custom rules change, so an invalid pattern fails fast rather than in a release-gate scan.

---

## Gotcha 7: Java-Based PMD Rule JARs Need Two Config Entries, Not One

**What happens:** A team compiles custom Java PMD rule classes into a JAR, lists the JAR's ruleset XML in `engines.pmd.custom_rulesets`, and the rules fail to load — PMD cannot find the rule classes.

**When it occurs:** `custom_rulesets` only tells Code Analyzer where the ruleset XML definitions live (on disk relative to `config_root`, or as a classpath resource). The JAR containing the compiled rule classes must be separately registered in the `engines.pmd.java_classpath_entries` array so it is added to the Java classpath when PMD runs. XPath-based rules defined entirely in the ruleset XML don't have this problem — they need no compilation and no classpath entry.

**How to avoid:** For Java-based rules, always pair the two keys: the ruleset XML (or its classpath resource path) in `custom_rulesets`, and the JAR path (absolute or relative to `config_root`) in `java_classpath_entries`. Verify loading with `sf code-analyzer rules --rule-selector Custom` — Code Analyzer auto-tags every custom PMD rule with `Custom`, and the ruleset's `name` attribute (spaces removed) becomes a second tag you can filter on.
