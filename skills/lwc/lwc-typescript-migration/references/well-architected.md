# Well-Architected Mapping

| Pillar | Migration behavior |
|---|---|
| Trusted | Preserve public contracts, avoid assertion-based false safety, and validate external data boundaries |
| Easy | Improve editor feedback and maintain one unambiguous source/build workflow |
| Adaptable | Migrate incrementally, use generated Salesforce configs, keep rollback possible, and separate language change from behavior refactoring |

The frontmatter's six dimensions are internal repository mappings.

## Official Sources Used

- Salesforce Spring '26 developer guide, TypeScript support for base components: https://developer.salesforce.com/blogs/2026/01/developers-guide-to-the-spring-26-release
- Salesforce Extensions for VS Code TypeScript LWC support guide: https://github.com/forcedotcom/salesforcedx-vscode/blob/develop/docs/TYPESCRIPT_LWC_SUPPORT.md
- Salesforce Extensions for VS Code repository: https://github.com/forcedotcom/salesforcedx-vscode
- Salesforce Code Analyzer ESLint engine: https://developer.salesforce.com/docs/platform/salesforce-code-analyzer/guide/engine-eslint.html

Because the first two sources describe different deployment stages, the skill requires installed-tool and target-org validation rather than asserting one universal strategy.
