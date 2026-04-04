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

# CORRECT (v5):
sf code-analyzer run --target force-app --rule-selector Security --format json
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
  run: sf code-analyzer run --rule-selector Security --format json --output-file results.json

# CORRECT — exits 1 if Critical or High violations found:
- name: Scan
  run: |
    sf code-analyzer run \
      --rule-selector Security \
      --severity-threshold 2 \
      --format json \
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
sf code-analyzer run --rule-selector all --format xml --output-file scan.xml

# CORRECT — uses the required AppExchange preset:
sf code-analyzer run \
  --rule-selector AppExchange \
  --engine graph-engine \
  --format xml \
  --output-file appexchange-scan.xml
```

**Detection hint:** AppExchange scan instructions that do not specify `--rule-selector AppExchange` and `--engine graph-engine` are incomplete.

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

## Anti-Pattern 5: Claiming Graph Engine Runs by Default

**What the LLM generates:** Instructions stating that running `sf code-analyzer run --rule-selector Security` includes Graph Engine taint analysis.

**Why it happens:** Graph Engine is documented as part of Code Analyzer's engine suite, and LLMs conflate "available engine" with "default engine." Training data may also predate the v5 opt-in model.

**Correct pattern:**

```bash
# WRONG — Graph Engine does NOT run by default with Security selector:
sf code-analyzer run --rule-selector Security --target force-app

# CORRECT — Graph Engine must be explicitly opted in:
sf code-analyzer run \
  --rule-selector Security \
  --engine graph-engine \
  --target force-app
```

**Detection hint:** Any claim that a standard `sf code-analyzer run` invocation includes dataflow or taint analysis without `--engine graph-engine` is incorrect.

---

## Anti-Pattern 6: Recommending Graph Engine for Every Push in Large Codebases

**What the LLM generates:** CI pipeline configurations that run Graph Engine on every push or every pull request, without acknowledging the memory and time cost.

**Why it happens:** LLMs optimize for correctness of coverage and don't model the operational cost tradeoff. Graph Engine is the right tool for deep security analysis, so the model recommends it everywhere.

**Correct pattern:**

```yaml
# WRONG — Graph Engine on every push causes slow builds and OOM on large repos:
- name: Scan
  run: sf code-analyzer run --rule-selector Security --engine graph-engine ...

# CORRECT — fast engines on every push, Graph Engine on a scheduled/release stage:
# push.yml:
- name: Quick Scan
  run: sf code-analyzer run --rule-selector Security --severity-threshold 2 ...

# nightly.yml:
- name: Deep Security Scan
  run: |
    NODE_OPTIONS=--max-old-space-size=4096 sf code-analyzer run \
      --rule-selector AppExchange \
      --engine graph-engine \
      --severity-threshold 2 ...
```

**Detection hint:** Any pipeline that runs `--engine graph-engine` on every push without memory configuration (`NODE_OPTIONS`) and without a rationale for the performance cost should be challenged.
