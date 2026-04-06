# Well-Architected Notes — Salesforce DX Project Structure

## Relevant Pillars

- **Operational Excellence** — Project structure directly determines developer ergonomics, CI/CD pipeline simplicity, and deployment reliability. A well-structured project reduces friction in daily development workflows and makes onboarding faster.
- **Reliability** — Correct `sourceApiVersion` alignment and validated packageDirectory paths prevent deployment failures. Misconfigured projects cause silent metadata omission or outright deploy rejection.
- **Scalability** — Multi-package directory layouts enable teams to scale from one workstream to many without restructuring the repo. Package dependencies enforce build order and prevent circular references.

## Architectural Tradeoffs

1. **Single directory vs. multi-package:** Single directory is simpler to maintain but creates merge conflicts and unclear ownership at scale. Multi-package adds configuration complexity but enables independent versioning, team ownership boundaries, and selective deployment. Choose multi-package only when you have two or more teams or need independent deployment lifecycles.

2. **Pinning sourceApiVersion vs. tracking latest:** Pinning to a lower version ensures all target orgs accept the deploy but may exclude newer metadata types from retrieves. Tracking the latest enables new features but risks deployment failures to orgs that have not received the release yet. Pin to the lowest common denominator across your org fleet.

3. **Namespace vs. no namespace:** Adding a namespace enables managed packaging and intellectual property protection but makes the metadata less portable and harder to test in scratch orgs. Use a namespace only for ISV managed packages; prefer unlocked packages (no namespace) for internal development.

## Anti-Patterns

1. **Monolithic force-app with implicit ownership** — Stuffing all metadata from multiple teams into a single `force-app/` directory with no package boundaries. This creates merge hell, makes it impossible to deploy one team's changes without the other, and provides no version lineage. Use multi-package directories with explicit ownership.

2. **Credentials in sfdx-project.json** — Storing `sfdxAuthUrl`, sandbox usernames, or tokens in the project config file. This file is committed to version control and visible to everyone with repo access. Move auth to CI secrets, environment variables, or `sf org login` commands that store credentials in the local `.sfdx/` directory (which must be gitignored).

3. **Ignoring dependency order in multi-package projects** — Creating packages that reference each other without declaring `dependencies` in `sfdx-project.json`. This works locally because all metadata is present, but fails during `sf package version create` because the packaging engine resolves each package in isolation. Always declare dependencies explicitly with minimum version constraints.

## Official Sources Used

- Salesforce DX Developer Guide — Project Configuration (sfdx-project.json)
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ws_config.htm
- Salesforce DX Developer Guide — Multiple Package Directories
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_ws_mpd.htm
- Salesforce DX Developer Guide — Unlocked Packages
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_unlocked_pkg_intro.htm
- Salesforce CLI Command Reference — sf project deploy start
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm
- Metadata API Developer Guide — Source Format
  URL: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
