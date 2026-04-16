# Well-Architected Notes — Package Development Strategy

## Relevant Pillars

### Operational Excellence
Package-based development provides modular, versioned deployment units that improve release management. Each package has an independent version history and dependency graph. Teams can release independently without shared deployment lock contention.

### Security
Managed packages (1GP and 2GP) compile Apex and hide source from subscribers, providing IP protection. Unlocked packages expose source to the subscriber org admin. The package type selection is a security decision as well as an architectural one.

### Reliability
Immutable package versions (released versions cannot be deleted) ensure reproducible deployments. A subscriber can always reinstall a specific package version. Package version rollback is possible by installing a prior released version.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Modularity | Unlocked packages for internal org modularity; managed packages for ISV IP protection |
| Versioning | Use released versions for production deployments; beta versions for internal testing |
| Namespace Strategy | Treat namespace selection as permanent; choose brand-stable string before registering |
| ISV Readiness | 2GP is Salesforce-recommended for all new ISV development; supports AppExchange listing |

## Cross-Skill References

- `devops/deployment-pipeline-design` — CI/CD pipeline design for package-based development
- `devops/managed-package-development` — Detailed 2GP managed package development workflow
- `devops/scratch-org-strategy` — Scratch org configuration and source-format development

## Official Sources Used

- Salesforce Developer Docs — Second-Generation Managed Packages: https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/pkg2_dev_intro.htm
- Salesforce Developer Docs — Unlocked Packages: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_intro.htm
- Salesforce Developer Docs — First-Generation Managed Packages: https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/packaging_intro.htm
- AppExchange Security Review — Package Types Accepted: https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/security_review_overview.htm
- Salesforce CLI Reference — sf package version create: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_package_commands_unified.htm
