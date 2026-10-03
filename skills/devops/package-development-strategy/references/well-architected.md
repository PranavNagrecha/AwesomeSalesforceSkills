# Well-Architected Notes: Package Development Strategy

## Relevant Pillars

### Operational Excellence
Package-based development provides modular, versioned deployment units that improve release management. Each package has an independent version history and dependency graph. Teams can release independently without shared deployment lock contention.

### Security
Managed packages (1GP and 2GP) compile Apex and hide source from subscribers, providing IP protection. Unlocked packages expose source to the subscriber org admin. The package type selection is a security decision as well as an architectural one.

### Reliability
Reproducibility depends on which package type you picked, because deletion rules differ. Released 2GP managed versions cannot be deleted, so a subscriber can always reinstall a specific version. Released *unlocked* versions can be deleted, deletion is permanent, and installs of a deleted version fail afterwards, version-pinned CI/CD against unlocked packages is only as reproducible as your retention discipline, so gate the Delete Second-Generation Packages user permission accordingly. Rollback is limited by package type: managed 2GP can't be downgraded, and installing a lower unlocked version is possible but "is not the same as a rollback, which isn't possible" (Salesforce DX Developer Guide). Plan to roll forward with a new version.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Modularity | Unlocked packages for internal org modularity; managed packages for ISV IP protection |
| Versioning | Use released versions for production deployments; beta versions for internal testing. Released unlocked versions are deletable and deletion is permanent, treat retention as a controlled decision |
| Namespace Strategy | Treat namespace selection as permanent; choose brand-stable string before registering |
| ISV Readiness | 2GP is Salesforce-recommended for all new ISV development; supports AppExchange listing |

## Cross-Skill References

- `architect/ci-cd-pipeline-architecture`: CI/CD pipeline design for package-based development
- `devops/managed-package-development`: Detailed 2GP managed package development workflow
- `devops/scratch-org-management`: Scratch org definition files, Org Shape, and scratch org lifecycle
- `devops/salesforce-dx-project-structure`: SFDX project structure and source-format layout

## Official Sources Used

- Salesforce DX Developer Guide, Summer '26: What's an Unlocked Package (modifiable in production, AppExchange guidance), Unlocked Packaging Keywords, Create Org-Dependent Unlocked Packages, Skip Validation, Code Coverage for Unlocked Packages, Upgrade a Version of an Unlocked Package, Delete an Unlocked Package or Package Version, Project Configuration File (`definitionFile`) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_dev.pdf
- Second-Generation Managed Packaging Developer Guide, Summer '26: Why Switch to 2GP, Comparison of 1GP and 2GP, Link a Namespace to a Dev Hub Org, Namespaces for 2GP, Apex obfuscation in managed packages, Get Ready to Promote (beta install rules), Package Ancestors, Patch Versions, Transfer a 2GP Package to a Different Dev Hub - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/pkg2_dev.pdf
- Salesforce CLI Command Reference, Summer '26: package commands - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_cli_reference.pdf
- Salesforce CLI 2.151.7 local `--help` output for `package create` (`--path` required, `--no-namespace`, `--org-dependent`), `package version create` (`--package`, `--skip-validation`, `--code-coverage`), `package version promote`, `package version report`, `package install` (`--upgrade-type`), `package list`
- Metadata API Developer Guide, Summer '26: InstalledPackage (managed 1GP only, must deploy alone, `activateRSS`) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
