# Well-Architected Notes — Salesforce Code Analyzer

## Relevant Pillars

- **Security** — Code Analyzer is a primary control for enforcing CRUD/FLS, SOQL injection prevention, XSS prevention in LWC, and dependency vulnerability scanning. Graph Engine's taint analysis surfaces security vulnerabilities that manual review and simpler static analysis miss. AppExchange submissions require scan results as evidence of security due diligence.

- **Operational Excellence** — Integrating Code Analyzer into CI pipelines as a hard gate enforces consistent quality standards across all contributors. Configuration via `code-analyzer.yml` makes the quality bar explicit, version-controlled, and reproducible. Archived scan artifacts create an audit trail for security review and incident response.

- **Reliability** — Static analysis catches classes of defects (null pointer patterns, resource leaks, unreachable code) before they reach production. PMD's Apex rule set includes reliability-oriented rules beyond security, such as complexity thresholds that correlate with defect density.

- **Performance** — PMD includes performance-oriented Apex rules (e.g., SOQL in loops, DML inside loops) that identify patterns likely to cause governor limit violations under load. Running these rules in CI prevents performance regressions from reaching production.

## Architectural Tradeoffs

**Full scan on every push vs. staged scanning:** Running all engines including Graph Engine on every push provides maximum coverage but adds significant pipeline time. The recommended tradeoff is to run fast engines (PMD, ESLint, RetireJS, Regex) on every push with a tight severity threshold, and run Graph Engine on a scheduled nightly job or on branch merges to the release branch. This maintains fast developer feedback cycles while ensuring security-critical taint analysis is performed before release.

**Severity threshold strictness:** Setting threshold to 1 (Critical only) misses High severity violations that are commonly exploitable. Setting to 4 (all violations) creates an unworkable gate for brownfield codebases. The recommended default is 2 (Critical and High) for greenfield projects and 3 (Critical, High, and Moderate) for security-sensitive packages targeting AppExchange. Ratcheting from 3 to 2 as the violation backlog is resolved is more operationally sustainable than imposing 2 on day one.

**Rule selector scope:** `all` maximizes finding coverage but produces noise that obscures real violations. `Security` provides a focused, actionable set. `AppExchange` is the required selector for Partner Security submissions. Using a broader selector than needed reduces signal-to-noise ratio and risks "alert fatigue" where developers learn to dismiss all findings.

## Anti-Patterns

1. **Advisory-only scans with no CI gate** — Running Code Analyzer and archiving results without a `--severity-threshold` exit code gate means violations never block delivery. Static analysis findings accumulate without remediation. The correct approach is to tie process exit code to CI step failure from the first pipeline integration, even if the initial threshold is lenient (severity 4).

2. **Suppressing violations at the file or class level without justification** — Using `@SuppressWarnings` at the class declaration level or with blanket rule names silences all future violations of that category. This creates invisible technical debt. Every suppression must name the specific rule and include a comment explaining why the suppression is intentional and safe.

3. **Treating the AppExchange scan as a one-time pre-submission activity** — Running Code Analyzer only immediately before submission means violations accumulate across the entire development cycle and require a large remediation sprint. Integrating the AppExchange rule selector into CI from the start of package development means the security baseline is maintained continuously.

## Official Sources Used

- Salesforce Code Analyzer v5 Overview — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/ca-overview.html
- `sf code-analyzer run` Command Reference — https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/run-command.html
