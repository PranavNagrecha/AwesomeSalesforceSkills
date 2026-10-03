# Well-Architected Mapping

| Pillar | ApexGuru analysis behavior |
|---|---|
| Trusted | Preserve target identity, source revision, evidence attribution, and security/correctness during fixes |
| Easy | Normalize line-level findings into reviewable dispositions with owners and rationale |
| Adaptable | Detect scale-sensitive source patterns, validate against volume, and keep configuration reproducible in CI |

The six frontmatter dimensions are internal repository mappings.

## Official Sources Used

- ApexGuru engine: https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/engine-apexguru.html
- Code Analyzer run command: https://developer.salesforce.com/docs/platform/salesforce-cli-reference/guide/cli_reference_code-analyzer_run.html
- Code Analyzer JSON output schema: https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/output-schemas-json.html
- Code Analyzer CLI workflow: https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/analyze.html
- Code Analyzer VS Code integration: https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/analyze-vscode.html

The current official `forcedotcom/sf-skills` ApexGuru workflow was used as feature-discovery input. This package is independently written against the product documentation and repository contracts.
