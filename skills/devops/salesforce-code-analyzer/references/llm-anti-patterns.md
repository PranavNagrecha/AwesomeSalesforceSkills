# LLM Anti-Patterns — Salesforce Code Analyzer

Common mistakes AI coding assistants make when generating or advising on Salesforce Code Analyzer.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using the Retired v4 CLI Command

**What the LLM generates:** CLI commands using the v4 syntax `sfdx scanner:run` with flags like `--category` and `--pmdconfig`.

**Why it happens:** Training data contains substantial v4 documentation and community content predating the August 2025 v4 retirement. The model interpolates the old command structure without awareness that the plugin was superseded.

**Correct pattern:**

```bash
# WRONG (v4, retired August 2025):
sfdx scanner:run --target force-app --category Security --format json

# CORRECT (v5 — output format comes from the --output-file extension):
sf code-analyzer run --workspace force-app --rule-selector Security --output-file results.json
```

**Detection hint:** Any output containing `sfdx scanner:run`, `--category` (as a standalone flag), or `sfdx-scanner` in the plugin name is using v4 syntax. Flag and replace.

---

## Anti-Pattern 2: Omitting `--severity-threshold` in CI Pipeline Steps

**What the LLM generates:** A GitHub Actions or CI step that runs `sf code-analyzer run` without `--severity-threshold`, treating the step as complete because it produces an output file.

**Why it happens:** LLMs default to "run the command and collect output" patterns from general CI tooling. They don't infer that Code Analyzer always exits 0 without an explicit threshold flag, making the gate inert.

**Correct pattern:**

```yaml
# WRONG — always exits 0, never fails the build:
- name: Scan
  run: sf code-analyzer run --rule-selector Security --output-file results.json

# CORRECT — fails with a non-zero exit code if Critical or High violations found:
- name: Scan
  run: |
    sf code-analyzer run \
      --rule-selector Security \
      --severity-threshold 2 \
      --output-file results.json
```

**Detection hint:** Any CI step with `sf code-analyzer run` that does not contain `--severity-threshold` is incomplete as a quality gate.

---

## Anti-Pattern 3: Using `--rule-selector all` for AppExchange Submissions

**What the LLM generates:** Instructions to run `sf code-analyzer run --rule-selector all` when preparing an AppExchange security review, on the reasoning that "all rules gives the most complete coverage."

**Why it happens:** LLMs optimize for comprehensiveness. They don't know that the AppExchange Partner Security team validates against a specific rule preset, and that submitting results from `all` makes it harder for the reviewer to validate required coverage.

**Correct pattern:**

```bash
# WRONG — produces off-spec results for the security review:
sf code-analyzer run --rule-selector all --output-file scan.html

# CORRECT — uses the documented security-review selectors:
sf code-analyzer run \
  --rule-selector AppExchange \
  --rule-selector Recommended:Security \
  --output-file appexchange-scan.html
```

**Detection hint:** AppExchange scan instructions that do not specify `--rule-selector AppExchange --rule-selector Recommended:Security` are incomplete.

---

## Anti-Pattern 4: Blanket `@SuppressWarnings('PMD')` Without Rule Name

**What the LLM generates:** Apex code with `@SuppressWarnings('PMD')` to suppress a specific rule, without naming the rule.

**Why it happens:** `@SuppressWarnings('PMD')` is the most commonly seen suppression pattern in training data, often copied without the rule-name qualifier. LLMs reproduce the pattern as seen.

**Correct pattern:**

```apex
// WRONG — silences all current and future PMD rules on this method:
@SuppressWarnings('PMD')
public void doSomething() { ... }

// CORRECT — suppresses only the specific rule, with justification:
@SuppressWarnings('PMD.ApexCRUDViolation')
// Permission check is performed by the calling service: OrderService.assertAccess()
public void doSomething() { ... }
```

**Detection hint:** Any `@SuppressWarnings('PMD')` without a dot-separated rule name (e.g., `PMD.RuleName`) is overly broad.

---

## Anti-Pattern 5: Inventing an `--engine` Flag for Graph Engine

**What the LLM generates:** Commands like `sf code-analyzer run --engine graph-engine` to "enable" Graph Engine, or claims that a tag-based selector automatically includes Graph Engine data-flow analysis.

**Why it happens:** v4's `scanner:run` had an `--engine` flag, and older content calls the engine "Graph Engine" rather than by its v5 engine name `sfge`. LLMs blend the v4 flag surface with the v5 command name. In v5 there is no `--engine` flag — engines' rules are chosen through `--rule-selector`, and the docs state: "To select the Salesforce Graph Engine rules, use `--rule-selector sfge`."

**Correct pattern:**

```bash
# WRONG — v5 has no --engine flag, and the engine's config name is sfge, not graph-engine:
sf code-analyzer run --rule-selector Security --engine graph-engine --target force-app

# CORRECT — select the Graph Engine rules through the rule selector:
sf code-analyzer run \
  --rule-selector Security \
  --rule-selector sfge \
  --workspace force-app
```

**Detection hint:** Any v5 command containing `--engine` or `--format`, or the engine name `graph-engine` in `code-analyzer.yml`, is using invented syntax. Engines are selected via `--rule-selector` (the graph engine is `sfge`), and output format comes from the `--output-file` extension.

---

## Anti-Pattern 6: Recommending Graph Engine for Every Push in Large Codebases

**What the LLM generates:** CI pipeline configurations that run Graph Engine on every push or every pull request, without acknowledging the memory and time cost.

**Why it happens:** LLMs optimize for correctness of coverage and don't model the operational cost tradeoff. Graph Engine is the right tool for deep security analysis, so the model recommends it everywhere.

**Correct pattern:**

```yaml
# WRONG — Graph Engine data-flow rules on every push cause slow builds on large repos:
- name: Scan
  run: sf code-analyzer run --rule-selector Security --rule-selector sfge ...

# CORRECT — fast rules on every push, Graph Engine rules on a scheduled/release stage:
# push.yml:
- name: Quick Scan
  run: sf code-analyzer run --rule-selector Security --severity-threshold 2 ...

# nightly.yml:
- name: Deep Security Scan
  run: |
    sf code-analyzer run \
      --rule-selector AppExchange \
      --rule-selector Recommended:Security \
      --rule-selector sfge \
      --severity-threshold 2 ...
```

**Detection hint:** Any pipeline that runs the `sfge` rules on every push without memory tuning (`engines.sfge.java_max_heap_size` in `code-analyzer.yml` — Graph Engine limits path complexity based on the max Java heap) and without a rationale for the performance cost should be challenged.

---

## Anti-Pattern 7: Wiring Custom Rules Through CLI Flags Instead of code-analyzer.yml

**What the LLM generates:** Instructions to register a custom PMD ruleset via `--rule-selector path/to/rules.xml` or a v4-style `--pmdconfig` flag, or to invent a Code-Analyzer-specific ESLint rule format.

**Why it happens:** v4 wired custom PMD config through CLI flags, and training data blends v4 flag patterns with v5 command names. LLMs also assume every engine has a bespoke rule format rather than checking each engine's actual extension point.

**Correct pattern:**

```yaml
# WRONG — --rule-selector selects existing rules by tag/name/preset; it does not load ruleset files.
# CORRECT — register custom rules in code-analyzer.yml, per engine:
engines:
  pmd:
    custom_rulesets:
      - pmd/team-rules.xml            # ruleset XML (XPath rules need no compilation)
    java_classpath_entries:
      - libs/custom-pmd-rules.jar     # additionally required for Java-based rule classes
  regex:
    custom_rules:
      NoTodoComments:
        regex: /TODO/gi               # global modifier is mandatory
        file_extensions: [".cls", ".trigger"]
        description: "Flags TODO comments in Apex."
  eslint:
    eslint_config_file: eslint.config.js  # custom ESLint rules live in a normal ESLint config
```

**Detection hint:** Any instruction that passes a file path to `--rule-selector`, uses `--pmdconfig`, or defines ESLint rules in a non-ESLint format is wrong for v5. Custom-rule wiring lives in `code-analyzer.yml` under `engines.pmd.custom_rulesets`, `engines.regex.custom_rules`, and `engines.eslint.eslint_config_file`.
