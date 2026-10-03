# Well-Architected Notes — Salesforce Code Analyzer

## Relevant Pillars

- **Security** — Code Analyzer is a primary control for enforcing CRUD/FLS, SOQL injection prevention, XSS prevention in LWC, and dependency vulnerability scanning. Graph Engine's taint analysis surfaces security vulnerabilities that manual review and simpler static analysis miss. AppExchange submissions require scan results as evidence of security due diligence.

- **Operational Excellence** — Integrating Code Analyzer into CI pipelines as a hard gate enforces consistent quality standards across all contributors. Configuration via `code-analyzer.yml` makes the quality bar explicit, version-controlled, and reproducible. Archived scan artifacts create an audit trail for security review and incident response.

- **Reliability** — Static analysis catches classes of defects (null pointer patterns, resource leaks, unreachable code) before they reach production. PMD's Apex rule set includes reliability-oriented rules beyond security, such as complexity thresholds that correlate with defect density.

- **Performance** — PMD includes performance-oriented Apex rules (e.g., SOQL in loops, DML inside loops) that identify patterns likely to cause governor limit violations under load. Running these rules in CI prevents performance regressions from reaching production.

## ApexGuru Remote Analysis Boundary

ApexGuru extends Code Analyzer with remote AI-driven Apex performance analysis. It requires an authenticated org and scans `.cls`/`.trigger` source. Treat connected-org access as a prerequisite, not automatic proof of production runtime telemetry. Preserve explicit analysis-mode fields when present and use separate runtime evidence to validate impact. The repository-specific MCP server exposes this skill and the specialized ApexGuru skill as knowledge resources; it does not misrepresent the retired Salesforce Code Analyzer MCP integration as an execution path.

## Architectural Tradeoffs

**Full scan on every push vs. staged scanning:** Running all engines including Graph Engine on every push provides maximum coverage but adds significant pipeline time. The recommended tradeoff is to run fast engines (PMD, ESLint, RetireJS, Regex) on every push with a tight severity threshold, and run Graph Engine on a scheduled nightly job or on branch merges to the release branch. This maintains fast developer feedback cycles while ensuring security-critical taint analysis is performed before release.

**Severity threshold strictness:** Setting the threshold to 1 (Critical only) misses High severity violations that are commonly exploitable. Setting it to 5 (every violation, including Info) creates an unworkable gate for brownfield codebases. The recommended default is 2 (Critical and High) for greenfield projects and 3 (Critical, High, and Moderate) for security-sensitive packages targeting AppExchange. Ratcheting from 2 to 3 as the violation backlog is resolved is more operationally sustainable than imposing 3 on day one.

**Rule selector scope:** `all` maximizes finding coverage but produces noise that obscures real violations. `Security` provides a focused, actionable set. For Partner Security submissions, the documented combination is `--rule-selector AppExchange --rule-selector Recommended:Security`, with the resulting reports attached in the Security Review Wizard. Using a broader selector than needed reduces signal-to-noise ratio and risks "alert fatigue" where developers learn to dismiss all findings.

**Custom rule mechanism choice:** Team standards can be codified three ways, in increasing order of power and maintenance cost. Regex custom rules (`engines.regex.custom_rules`) are pure configuration — no build step, but pattern-matching only. XPath-based PMD rules live in a ruleset XML registered via `engines.pmd.custom_rulesets` and query the AST without any Java compilation. Java-based PMD rules are the most expressive but require compiling a JAR, registering it in `engines.pmd.java_classpath_entries`, and maintaining a build for the rules themselves. Prefer the cheapest mechanism that can express the check; escalate to Java rules only when XPath over the AST cannot capture the semantics. Because every custom PMD rule is auto-tagged `Custom`, custom-rule findings stay separately selectable and auditable in CI regardless of mechanism.

## Anti-Patterns

1. **Advisory-only scans with no CI gate** — Running Code Analyzer and archiving results without a `--severity-threshold` exit code gate means violations never block delivery. Static analysis findings accumulate without remediation. The correct approach is to tie process exit code to CI step failure from the first pipeline integration, even if the initial threshold is lenient (1, Critical-only).

2. **Suppressing violations at the file or class level without justification** — Using `@SuppressWarnings` at the class declaration level or with blanket rule names silences all future violations of that category. This creates invisible technical debt. Every suppression must name the specific rule and include a comment explaining why the suppression is intentional and safe.

3. **Treating the AppExchange scan as a one-time pre-submission activity** — Running Code Analyzer only immediately before submission means violations accumulate across the entire development cycle and require a large remediation sprint. Integrating the AppExchange rule selector into CI from the start of package development means the security baseline is maintained continuously.

## Official Sources Used

- Overview of Salesforce Code Analyzer — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/code-analyzer.html
- `sf code-analyzer run` Command Reference (flags, engine list, severity scale, output-file formats) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/analyze.html
- Salesforce Graph Engine (`sfge` engine name, disable_engine, Java heap settings) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/engine-sfge.html
- Graph Engine Rules Reference (`--rule-selector sfge`) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/rules-sfge.html
- Produce Code Analyzer Reports for AppExchange Security Review (selectors, HTML report) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/appexchange.html
- Customize Code Analyzer Configuration (rules overrides, regex custom rules, ESLint config, ignores) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/config-custom.html
- PMD Engine (custom_rulesets, java_classpath_entries, XPath vs Java rules, automatic Custom tag) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/engine-pmd.html
- Regex Engine (custom_rules fields, severity values, global modifier requirement) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/engine-regex.html
- ESLint Engine (eslint_config_file, auto_discover_eslint_config, base-config toggles) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/engine-eslint.html
- ApexGuru engine (target org, Apex-only coverage, JSON output, timeout/backoff) — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/engine-apexguru.html
- Code Analyzer MCP lifecycle and engine limitations — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/mcp.html
- Migrate from Code Analyzer v4 to v5 — confirms the August 2025 v4 retirement sentence, the `scanner` → `code-analyzer` topic move and full command mapping (including the two commands with no v5 equivalent), the `--category`/`--engine` → `--rule-selector`, `--projectdir` → `--workspace` and `--pmdconfig`/`--eslintconfig` → `code-analyzer.yml` flag mappings, and the inversion of PMD custom-ruleset semantics from restrictive to additive — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/migrate.html (verified 2026-08-13)
