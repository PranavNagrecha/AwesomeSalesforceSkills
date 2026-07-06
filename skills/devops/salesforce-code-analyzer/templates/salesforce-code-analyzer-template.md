# Salesforce Code Analyzer — Work Template

Use this template when configuring, running, or interpreting Salesforce Code Analyzer v5 results.

## Scope

**Skill:** `salesforce-code-analyzer`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer these before starting work:

- **Code Analyzer version confirmed:** [ ] v5 (`sf code-analyzer run`) — NOT v4 (`sfdx scanner:run`)
- **Salesforce DX project root:** _______________
- **Target source path(s):** _______________
- **Engines required:** [ ] PMD  [ ] CPD  [ ] ESLint  [ ] RetireJS  [ ] Regex  [ ] Flow  [ ] Graph Engine (`sfge`)
- **Purpose of scan:** [ ] CI gate  [ ] AppExchange submission  [ ] Developer review  [ ] Security audit
- **Output file format (set by `--output-file` extension):** [ ] json  [ ] xml  [ ] csv  [ ] html  [ ] sarif  [ ] terminal only (`--view table` or `--view detail`)
- **Severity threshold for CI:** [ ] 1 (Critical)  [ ] 2 (High)  [ ] 3 (Moderate)  [ ] 4 (Low)  [ ] 5 (Info)  [ ] None

---

## Approach

**Which pattern from SKILL.md applies?**

- [ ] CI Pipeline Gate (use `--severity-threshold`, `--output-file scan-results.json`, archive artifact)
- [ ] AppExchange Security Review (`--rule-selector AppExchange --rule-selector Recommended:Security`, HTML report)
- [ ] Project Configuration (`code-analyzer.yml` setup)
- [ ] False Positive Suppression (`@SuppressWarnings` with specific rule name)
- [ ] Custom Rule Authoring (`engines.pmd.custom_rulesets`, `engines.regex.custom_rules`, or `engines.eslint.eslint_config_file`)

**Reason this pattern was chosen:**

_______________

---

## Commands

```bash
# Standard CI gate (fill in your values; output format follows the file extension):
sf code-analyzer run \
  --rule-selector Security \
  --workspace <path-to-source> \
  --severity-threshold 2 \
  --output-file scan-results.json

# AppExchange submission scan (documented selectors; add sfge for data-flow rules):
sf code-analyzer run \
  --rule-selector AppExchange \
  --rule-selector Recommended:Security \
  --rule-selector sfge \
  --workspace <path-to-source> \
  --output-file appexchange-scan.html
```

---

## code-analyzer.yml Configuration

```yaml
# Place at project root and commit
engines:
  sfge:
    disable_engine: true  # Graph Engine: enable only in security pipeline stages
  # Custom rules (fill in as needed):
  # pmd:
  #   custom_rulesets:
  #     - pmd/team-rules.xml
  #   java_classpath_entries:        # only for Java-based rule classes
  #     - libs/custom-pmd-rules.jar
  # regex:
  #   custom_rules:
  #     RuleName:
  #       regex: /pattern/gi         # global modifier is mandatory
  #       file_extensions: [".cls", ".trigger"]
  #       description: "What this rule flags."
  # eslint:
  #   eslint_config_file: eslint.config.js

# Override existing rules (rules -> engine -> rule -> properties):
# rules:
#   pmd:
#     SomeRule:
#       severity: Low

ignores:
  - "force-app/main/default/staticresources/node_modules/**"
  - "force-app/test/**"
```

---

## Violation Triage

| Rule Name | Severity | File | Line | Status | Notes |
|-----------|----------|------|------|--------|-------|
| | | | | Fix / Suppress / Accept | |
| | | | | Fix / Suppress / Accept | |
| | | | | Fix / Suppress / Accept | |

---

## Suppression Log

Document every `@SuppressWarnings` annotation added:

| File | Method/Class | Rule Suppressed | Justification |
|------|-------------|-----------------|---------------|
| | | | |

---

## Checklist

- [ ] Plugin version confirmed: v5 (`sf plugins --core | grep code-analyzer`)
- [ ] `code-analyzer.yml` committed at project root with `node_modules` excluded
- [ ] CI pipeline uses `--severity-threshold` and exits non-zero on violations
- [ ] All `@SuppressWarnings` use specific rule names with justification comments
- [ ] AppExchange scan uses `--rule-selector AppExchange --rule-selector Recommended:Security` (plus `--rule-selector sfge` for data-flow coverage)
- [ ] Output matches the consumer (`--output-file` extension for CI artifacts, `--view table` for local review)
- [ ] False positive documentation prepared for any suppressed AppExchange findings
- [ ] Zero severity 1 or 2 violations remaining (or all accounted for with suppressions)

---

## Notes

Record any deviations from the standard pattern and why:

_______________
