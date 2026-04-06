# Well-Architected Notes — Migration From Change Sets To SFDX

## Relevant Pillars

- **Operational Excellence** — This migration directly improves operational maturity. Change sets have no version history, no rollback mechanism, and no automation hooks. Moving to source-driven development introduces git-based change tracking, repeatable CLI deployments, CI/CD pipeline integration, and code review workflows. The migration itself is an operational project that must be planned, phased, and validated incrementally to avoid disrupting in-flight releases.

- **Reliability** — Source-driven development improves deployment reliability. Every deploy is repeatable from a known git commit. Validation can run in CI before a human approves the release. Failed deploys can be traced to a specific commit rather than an opaque change set. The migration must be validated with round-trip deploys at each phase to confirm conversion fidelity — deploying unconverted or partially converted metadata is a reliability risk.

- **Security** — The migration must preserve existing security configurations. Profiles and permission sets retrieved from the org contain the full security model. Carelessly deploying converted profiles can remove production-only permissions. Teams should exclude profiles from the migration and manage access through permission sets, ensuring the security model is not degraded during the transition.

## Architectural Tradeoffs

**Incremental vs. Big-Bang Migration:** Incremental migration (Pattern 1 in SKILL.md) trades speed for safety. Each batch is independently validated, but the migration spans multiple sprints. Big-bang migration is faster but carries higher risk: a single conversion error can block the entire project, and one massive commit destroys git history value.

**Manifest-Based vs. Package-Based End State:** Manifest-based deploys (`sf project deploy start --manifest package.xml`) are the simplest change-set replacement and require no Dev Hub or packaging infrastructure. Unlocked packages add versioning, dependency management, and installation governance but require more upfront design. The right choice depends on org complexity, team size, and whether modular architecture already exists.

**Shadow Period vs. Hard Cutover:** Running change sets and CLI deploys in parallel (Pattern 2) doubles the deployment effort temporarily but eliminates the risk of a production incident during the learning curve. Hard cutover saves time but assumes the team is already proficient with the CLI.

## Anti-Patterns

1. **Converting everything at once without validation** — Retrieving the entire org's metadata with wildcards and committing it in one pass. This produces an unmanageable repository, includes managed-package and standard metadata the team cannot deploy, and makes it impossible to isolate conversion issues. Always migrate in targeted batches with round-trip validation.

2. **Treating source-format deploy as additive like change sets** — Assuming that deploying a subset of metadata only affects those components. In reality, deploying a profile replaces the entire profile; deploying an object definition replaces all fields and validation rules in that definition unless source format decomposition is used correctly. Teams must understand that CLI deploys are declarative (the deployed state becomes the org state for those components), not incremental.

3. **Skipping .forceignore configuration** — Failing to exclude managed-package components, standard objects, and profiles from the source project. This leads to deploy failures ("Cannot modify managed component"), unintended permission overwrites, and a bloated repository full of metadata the team does not own.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce DX Developer Guide: Source Format — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_source_file_format.htm
- Salesforce DX Developer Guide: Migrate Existing Source — https://developer.salesforce.com/docs/platform/sfcli/guide/project-convert-mdapi.html
