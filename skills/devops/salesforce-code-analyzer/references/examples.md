# Examples — Salesforce Code Analyzer

## Example 1: CI Pipeline Gate Using Severity Threshold

**Context:** A Salesforce DX project uses GitHub Actions for CI/CD. The team wants to block pull request merges if any Critical or High security violations are introduced, but allow the build to pass with lower-severity informational findings while they address existing tech debt.

**Problem:** Without a severity gate, `sf code-analyzer run` always exits 0. The violations file is produced and ignored. Developers learn that the scan "always passes" and stop paying attention to results.

**Solution:**

```yaml
# .github/workflows/code-quality.yml (relevant step)
- name: Run Salesforce Code Analyzer
  run: |
    sf code-analyzer run \
      --rule-selector Security \
      --workspace force-app/main/default \
      --severity-threshold 2 \
      --output-file scan-results.json
  # Non-zero exit code if any severity 1 (Critical) or 2 (High) violation is found

- name: Upload Scan Results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: code-analyzer-results
    path: scan-results.json
```

The `--severity-threshold 2` flag causes the command to fail with a non-zero exit code if any Critical or High violation is detected. The `.json` extension on `--output-file` selects the JSON output format — v5 has no separate `--format` flag. The artifact upload uses `if: always()` so the results are preserved even when the build fails, enabling developers to review findings without re-running the scan.

**Why it works:** Linking the process exit code to the CI step failure makes the scan a hard gate rather than advisory output. Uploading the artifact unconditionally preserves the evidence trail required for security audits.

---

## Example 2: AppExchange Security Review Scan with Graph Engine

**Context:** An ISV partner is preparing a managed package for AppExchange submission. The official guidance is to run Code Analyzer with `--rule-selector AppExchange --rule-selector Recommended:Security`, generate an HTML report with `--output-file`, and attach the scan reports to the submission in the AppExchange Security Review Wizard.

**Problem:** The team runs `--rule-selector all` and produces a report with hundreds of findings across multiple categories. The Partner Security reviewer cannot determine which findings are in scope for the required checks, and nothing in the team's selector guarantees the Graph Engine (`sfge`) data-flow rules were included.

**Solution:**

```bash
# Step 1: Run the documented security-review selectors, plus the Graph Engine rules
sf code-analyzer run \
  --rule-selector AppExchange \
  --rule-selector Recommended:Security \
  --rule-selector sfge \
  --workspace force-app/main/default \
  --output-file appexchange-scan.html

# Step 2: Review findings and document false positives
# Any unresolved finding needs a written justification in the submission
```

Attach `appexchange-scan.html` to the submission in the Security Review Wizard. The scans don't have to be 100% passing — the requirement is that you run the scans, address the violations you can fix, re-run, and submit the reports, with a written explanation for every remaining finding.

**Why it works:** `AppExchange` plus `Recommended:Security` are exactly the selectors the security-review documentation tells partners to run, so the report maps to what the reviewer validates. Adding `--rule-selector sfge` explicitly selects all Graph Engine data-flow rules, and the `.html` extension on `--output-file` produces the report format the guidance describes.

---

## Example 3: Project-Level Configuration with code-analyzer.yml

**Context:** A development team of six Apex and LWC developers wants consistent scan settings across local machines and CI without requiring each developer to remember complex CLI flags.

**Problem:** Different developers run different rule selectors and different output formats. One developer runs PMD only; another runs all engines including RetireJS, which flags a known false-positive dependency. There is no shared baseline.

**Solution:**

```yaml
# code-analyzer.yml — commit at project root
engines:
  sfge:
    disable_engine: true  # Graph Engine runs only in the security pipeline stage, not on every push

rules:
  retire-js:
    # Known false positive: internal dependency not exposed to untrusted input
    RetireJS-DOMXSS:
      severity: Low

ignores:
  - "force-app/main/default/staticresources/node_modules/**"
  - "force-app/test/**"
```

With this file committed, any developer can run `sf code-analyzer run` with no additional flags and get the team's standard baseline. CI overrides specific flags (rule selectors, threshold, output file) via CLI arguments, which take precedence over `code-analyzer.yml` values.

**Why it works:** The configuration file eliminates per-developer drift. CLI flags override file settings, so CI can tighten thresholds without changing the file that developers use locally.

---

## Example 4: Team-Standard Custom Rules in code-analyzer.yml

**Context:** A team wants to enforce its own coding standards on top of the built-in rules: no `System.debug` left in Apex, a house PMD ruleset for naming conventions, and the project's existing ESLint config (with custom plugins) applied to LWC.

**Problem:** The team tries to pass a PMD ruleset XML path to `--rule-selector` (v4 muscle memory) and it does nothing — in v5, `--rule-selector` selects rules by tag/name/preset; custom rules are registered in `code-analyzer.yml`, each engine with its own key and format.

**Solution:**

```yaml
# code-analyzer.yml — all three custom-rule mechanisms in one place
engines:
  regex:
    custom_rules:
      NoDebugStatements:
        # Global modifier is mandatory: /pattern/gi works, /pattern/i is an error
        regex: /System\.debug/gi
        file_extensions: [".cls", ".trigger"]
        description: "Flags System.debug statements left in Apex code."
        violation_message: "Remove System.debug before merging; use a logging framework instead."
        severity: "Info"
        tags: ["TechDebt"]

  pmd:
    custom_rulesets:
      - pmd/team-naming-rules.xml     # XPath-based ruleset on disk, relative to config_root
      - com/example/custom-rules.xml  # ruleset shipped as a classpath resource inside a JAR
    java_classpath_entries:
      - libs/custom-pmd-rules.jar     # required ONLY for Java-based rule classes

  eslint:
    eslint_config_file: eslint.config.js  # custom rules/plugins merge with the base configs

# Re-tune built-in rules without authoring anything (rules -> engine -> rule -> properties)
rules:
  eslint:
    sort-vars:
      severity: Info
      tags: [Recommended, Suggestions]
```

Verify everything registered:

```bash
# All custom PMD rules are auto-tagged 'Custom'; the ruleset name (spaces removed)
# becomes a second tag, e.g. <ruleset name="Team Naming Rules"> -> TeamNamingRules
sf code-analyzer rules --rule-selector Custom
```

**Why it works:** Each engine's extension point is used as designed — `custom_rules` for config-only regex rules, `custom_rulesets` (+ `java_classpath_entries` for compiled rules) for PMD, and a normal ESLint config for LWC. The automatic `Custom` tag makes the team's rules selectable in CI (`--rule-selector Custom`) and auditable separately from built-in findings.

---

## Anti-Pattern: Running Without a Severity Threshold

**What practitioners do:** `sf code-analyzer run --rule-selector all --workspace force-app` with no `--severity-threshold`. They check that the command ran, see a table of violations, and consider the step done.

**What goes wrong:** The process always exits 0. The CI pipeline passes. The violations accumulate release over release. By the time an AppExchange security review is submitted, there are hundreds of unresolved Critical and High findings with no remediation trail.

**Correct approach:** Always pair `sf code-analyzer run` with `--severity-threshold` in CI — the command fails with a non-zero exit code when a violation meets or exceeds the threshold. Start with a lenient threshold (1, Critical-only) on brownfield codebases and tighten toward 2 or 3 as violations are resolved. Never treat a successful process exit as evidence that code is clean — check the output file.
