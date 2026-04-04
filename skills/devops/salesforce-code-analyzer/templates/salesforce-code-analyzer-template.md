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
- **Engines required:** [ ] PMD  [ ] ESLint  [ ] RetireJS  [ ] Regex  [ ] Graph Engine
- **Purpose of scan:** [ ] CI gate  [ ] AppExchange submission  [ ] Developer review  [ ] Security audit
- **Output format required:** [ ] table  [ ] json  [ ] csv  [ ] xml
- **Severity threshold for CI:** [ ] 1 (Critical)  [ ] 2 (High)  [ ] 3 (Moderate)  [ ] 4 (Low)  [ ] None

---

## Approach

**Which pattern from SKILL.md applies?**

- [ ] CI Pipeline Gate (use `--severity-threshold`, `--format json`, archive artifact)
- [ ] AppExchange Security Review (`--rule-selector AppExchange --engine graph-engine --format xml`)
- [ ] Project Configuration (`code-analyzer.yml` setup)
- [ ] False Positive Suppression (`@SuppressWarnings` with specific rule name)
- [ ] Custom Rule Authoring (PMD XML ruleset or ESLint plugin)

**Reason this pattern was chosen:**

_______________

---

## Commands

```bash
# Standard CI gate (fill in your values):
sf code-analyzer run \
  --rule-selector Security \
  --target <path-to-source> \
  --severity-threshold 2 \
  --format json \
  --output-file scan-results.json

# AppExchange submission scan:
NODE_OPTIONS=--max-old-space-size=4096 sf code-analyzer run \
  --rule-selector AppExchange \
  --engine graph-engine \
  --target <path-to-source> \
  --format xml \
  --output-file appexchange-scan.xml
```

---

## code-analyzer.yml Configuration

```yaml
# Place at project root and commit
engines:
  pmd:
    enabled: true
  eslint:
    enabled: true
  retire-js:
    enabled: true
  graph-engine:
    enabled: false  # Enable only in security pipeline stages

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
- [ ] AppExchange scan uses `--rule-selector AppExchange` and `--engine graph-engine`
- [ ] Output format matches the consumer (JSON/XML for CI, table for local review)
- [ ] False positive documentation prepared for any suppressed AppExchange findings
- [ ] Zero severity 1 or 2 violations remaining (or all accounted for with suppressions)

---

## Notes

Record any deviations from the standard pattern and why:

_______________
