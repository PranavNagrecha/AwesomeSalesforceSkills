# Well-Architected Notes — Package Development Strategy

## Relevant Pillars

### Operational Excellence
Package-based development provides modular, versioned deployment units that improve release management. Each package has an independent version history and dependency graph. Teams can release independently without shared deployment lock contention.

### Security
Managed packages (1GP and 2GP) compile Apex and hide source from subscribers, providing IP protection. Unlocked packages expose source to the subscriber org admin. The package type selection is a security decision as well as an architectural one.

### Reliability
Reproducibility depends on which package type you picked, because deletion rules differ. Released 2GP managed versions cannot be deleted, so a subscriber can always reinstall a specific version. Released *unlocked* versions can be deleted, deletion is permanent, and installs of a deleted version fail afterwards — version-pinned CI/CD against unlocked packages is only as reproducible as your retention discipline, so gate the Delete Second-Generation Packages user permission accordingly. Rollback works by installing a prior released version that still exists.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Modularity | Unlocked packages for internal org modularity; managed packages for ISV IP protection |
| Versioning | Use released versions for production deployments; beta versions for internal testing. Released unlocked versions are deletable and deletion is permanent — treat retention as a controlled decision |
| Namespace Strategy | Treat namespace selection as permanent; choose brand-stable string before registering |
| ISV Readiness | 2GP is Salesforce-recommended for all new ISV development; supports AppExchange listing |

## Cross-Skill References

- `devops/deployment-pipeline-design` — CI/CD pipeline design for package-based development
- `devops/managed-package-development` — Detailed 2GP managed package development workflow
- `devops/scratch-org-strategy` — Scratch org configuration and source-format development

## Official Sources Used

- Salesforce Developer Docs — Second-Generation Managed Packages: https://developer.salesforce.com/docs/atlas.en-us.pkg2_dev.meta/pkg2_dev/pkg2_dev_intro.htm
- Salesforce Developer Docs — Unlocked Packages: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_intro.htm
- Salesforce DX Developer Guide — Delete an Unlocked Package or Package Version: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_package_deletion.htm
- Salesforce Developer Docs — First-Generation Managed Packages: https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/packaging_intro.htm
- AppExchange Security Review — Package Types Accepted: https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/security_review_overview.htm
- Salesforce CLI Reference — sf package version create: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_package_commands_unified.htm
