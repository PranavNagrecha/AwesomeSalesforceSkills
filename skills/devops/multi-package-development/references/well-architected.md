# Well-Architected Notes — Multi-Package Development

## Relevant Pillars

- **Scalability** — Multi-package decomposition allows independent teams to develop and release packages on separate cadences. As the org grows, new domain packages can be added without modifying existing ones, enabling horizontal scaling of development effort.
- **Reliability** — A well-structured dependency DAG ensures that packages can be upgraded independently. Isolating changes to a single package reduces the blast radius of regressions and makes rollback possible at the package level rather than the entire org.
- **Operational Excellence** — Topological build and install ordering, combined with CI/CD automation, makes deployments repeatable and auditable. Each package version is immutable and traceable to a specific commit, supporting change management and compliance requirements.
- **Security** — Package boundaries create natural trust boundaries. Managed packages enforce namespace isolation, and even unlocked packages can use `@namespaceAccessible` selectively. Cross-package Apex access is governed by the consuming package's explicit dependency declaration.

## Architectural Tradeoffs

### Granularity vs. Complexity

More packages provide finer-grained deployment control and team independence, but increase dependency management overhead. Each additional package adds a node to the DAG, a build step to the pipeline, and a version to track. Start with 2-4 packages and add more only when team boundaries or release cadence differences justify the overhead.

### Mono-Repo vs. Multi-Repo

Mono-repo keeps the full DAG visible in a single `sfdx-project.json` and simplifies atomic cross-package refactoring, but couples all teams to a shared branch and CI/CD pipeline. Multi-repo gives teams full autonomy but requires explicit version pinning and cross-repo coordination for breaking changes.

### LATEST vs. Pinned Dependencies

`LATEST` provides development convenience but introduces non-determinism. Pinned 04t IDs provide reproducible builds but require manual updates when upstream packages release new versions. Most teams use `LATEST` in feature branches and pin in release branches.

## Anti-Patterns

1. **God Package** — Putting all shared metadata in a single massive Base package that every other package depends on. This creates a bottleneck: any change to Base forces all downstream packages to rebuild and retest. Instead, decompose the base layer into focused packages (e.g., Base-Objects, Base-Utilities) so that downstream packages depend only on what they actually use.

2. **Circular Dependency via Lateral References** — Two domain packages referencing each other's objects or fields. This is architecturally and technically illegal in SFDX. Extract shared components into a lower-layer package that both depend on. Never work around this by duplicating metadata.

3. **Skipping Topological Order in CI/CD** — Building or installing packages in alphabetical or arbitrary order instead of dependency order. This causes intermittent failures that are hard to diagnose because they depend on timing and caching. Always compute and enforce topological sort in the pipeline.

4. **Treating Package Boundaries as Optional** — Allowing metadata to "leak" across package directories by referencing components that are not in the declared dependency chain. This works in scratch orgs (where all source is deployed together) but fails in production installs where each package is installed independently.

5. **Version Coupling Across All Packages** — Requiring all packages to be at the same version number or released simultaneously. This defeats the purpose of multi-package architecture. Each package should have its own independent semantic version and release cadence.

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce DX Developer Guide: Package Dependencies — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_dev2gp_config_file.htm
- Salesforce CLI Reference: sf package commands — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_package_commands_unified.htm
- Salesforce Architects: Modular Development — https://architect.salesforce.com/deliver/release-management/modular-development
- Salesforce Architects: Unlocked Packages for Customers — https://architect.salesforce.com/deliver/release-management/unlocked-packages
- Trailhead: Organize Your Metadata — https://trailhead.salesforce.com/content/learn/modules/unlocked-packages-for-customers
