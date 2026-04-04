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
      --target force-app/main/default \
      --severity-threshold 2 \
      --format json \
      --output-file scan-results.json
  # Exit code 1 if any severity 1 (Critical) or 2 (High) violation is found

- name: Upload Scan Results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: code-analyzer-results
    path: scan-results.json
```

The `--severity-threshold 2` flag causes the process to exit with code 1 if any Critical or High violation is detected. The artifact upload uses `if: always()` so the results are preserved even when the build fails, enabling developers to review findings without re-running the scan.

**Why it works:** Linking the process exit code to the CI step failure makes the scan a hard gate rather than advisory output. Uploading the artifact unconditionally preserves the evidence trail required for security audits.

---

## Example 2: AppExchange Security Review Scan with Graph Engine

**Context:** An ISV partner is preparing a managed package for AppExchange submission. The Partner Security team requires a Code Analyzer scan using the AppExchange rule selector and accepts XML output in the Security Review Wizard.

**Problem:** The team runs `--rule-selector all` and produces a report with hundreds of findings across multiple categories. The Partner Security reviewer cannot determine which findings are in scope for the required checks. Several required Graph Engine taint-analysis checks are not run at all because Graph Engine is not included in the default engine set.

**Solution:**

```bash
# Step 1: Run the AppExchange preset with Graph Engine
NODE_OPTIONS=--max-old-space-size=4096 sf code-analyzer run \
  --rule-selector AppExchange \
  --engine graph-engine \
  --target force-app/main/default \
  --format xml \
  --output-file appexchange-scan.xml

# Step 2: Review findings and document false positives
# Any suppressed finding needs a written justification in the submission
```

```apex
// Example: Suppressing a Graph Engine false positive where CRUD check
// is performed in the service layer the taint analysis cannot follow
@SuppressWarnings('GraphEngine.ApexFlsViolation')
public void processOrder(Id orderId) {
    // FLS verified by OrderService.assertFieldAccess() in calling context
    Order__c o = [SELECT Id, Status__c FROM Order__c WHERE Id = :orderId];
    o.Status__c = 'Processed';
    update o;
}
```

Upload `appexchange-scan.xml` to the Security Review Wizard. For each `@SuppressWarnings` annotation, include a text explanation in the false-positive documentation section of the submission.

**Why it works:** The `AppExchange` rule selector maps exactly to the Partner Security team's validation checklist, ensuring no required checks are missed and no irrelevant checks inflate the finding count. Graph Engine must be explicitly opted in because it is not part of the default engine set.

---

## Example 3: Project-Level Configuration with code-analyzer.yml

**Context:** A development team of six Apex and LWC developers wants consistent scan settings across local machines and CI without requiring each developer to remember complex CLI flags.

**Problem:** Different developers run different rule selectors and different output formats. One developer runs PMD only; another runs all engines including RetireJS, which flags a known false-positive dependency. There is no shared baseline.

**Solution:**

```yaml
# code-analyzer.yml — commit at project root
engines:
  pmd:
    enabled: true
  eslint:
    enabled: true
  retire-js:
    enabled: true
    rule-overrides:
      # Known false positive: internal dependency not exposed to untrusted input
      RetireJS-DOMXSS:
        severity: 4
  graph-engine:
    enabled: false  # Enabled only in the security pipeline stage, not on every push

global:
  target:
    - force-app/main/default
  exclude:
    - force-app/main/default/staticresources/node_modules
    - force-app/test

output:
  format: table
  severity-threshold: 3
```

With this file committed, any developer can run `sf code-analyzer run` with no additional flags and get the team's standard baseline. CI overrides specific flags (format and threshold) via CLI arguments, which take precedence over `code-analyzer.yml` values.

**Why it works:** The configuration file eliminates per-developer drift. CLI flags override file settings, so CI can tighten thresholds without changing the file that developers use locally.

---

## Anti-Pattern: Running Without a Severity Threshold

**What practitioners do:** `sf code-analyzer run --rule-selector all --target force-app` with no `--severity-threshold`. They check that the command ran, see a table of violations, and consider the step done.

**What goes wrong:** The process always exits 0. The CI pipeline passes. The violations accumulate release over release. By the time an AppExchange security review is submitted, there are hundreds of unresolved Critical and High findings with no remediation trail.

**Correct approach:** Always pair `sf code-analyzer run` with `--severity-threshold 2` in CI. Start with threshold 3 or 4 on brownfield codebases and ratchet tighter as violations are resolved. Never treat a successful process exit as evidence that code is clean — check the output file.
