# Well-Architected Notes — Salesforce DX Project Structure

## Relevant Pillars

- **Operational Excellence** — Project structure directly determines developer ergonomics, CI/CD pipeline simplicity, and deployment reliability. A well-structured project reduces friction in daily development workflows and makes onboarding faster.
- **Reliability** — Correct `sourceApiVersion` alignment and validated packageDirectory paths prevent deployment failures. Misconfigured projects cause missing fields on retrieve (sfdx_dev 264 L2430-2434) or deploy rejection (UNVERIFIED, 2026-10-20: the rejection mechanics are not in the corpus).
- **Scalability** — Multi-package directory layouts enable teams to scale from one workstream to many without restructuring the repo. Package dependencies are declared in installation order (sfdx_dev 264 L14813-14814); UNVERIFIED (2026-10-20): that they enforce build order and prevent circular references.

## Architectural Tradeoffs

1. **Single directory vs. multi-package:** Single directory is simpler to maintain but creates merge conflicts and unclear ownership at scale. Multi-package adds configuration complexity but enables independent versioning, team ownership boundaries, and selective deployment. Choose multi-package only when you have two or more teams or need independent deployment lifecycles.

2. **Pinning sourceApiVersion vs. tracking latest:** Pinning to a lower version means retrieves return only the fields that version has (sfdx_dev 264 L2430-2434); UNVERIFIED (2026-10-20): that it "ensures all target orgs accept the deploy" or excludes whole types. Tracking the latest enables new features; that it fails deploys to orgs that have not received the release yet is UNVERIFIED (2026-10-20), so pinning to the lowest common version across your org fleet is a convention, not a documented rule.

3. **Namespace vs. no namespace:** Adding a namespace prefixes every component added to the package (pkg2_dev 264 L946-948). UNVERIFIED (2026-10-20): "intellectual property protection", "harder to test in scratch orgs" and the advice to prefer unlocked packages for internal development.

## Anti-Patterns

1. **Monolithic force-app with implicit ownership** — Stuffing all metadata from multiple teams into a single `force-app/` directory with no package boundaries. This creates merge hell, makes it impossible to deploy one team's changes without the other, and provides no version lineage. Use multi-package directories with explicit ownership.

2. **Credentials in sfdx-project.json** — Storing `sfdxAuthUrl`, sandbox usernames, or tokens in the project config file. This file is committed to version control and visible to everyone with repo access. Move auth to CI secrets, environment variables, or `sf org login` commands that store credentials in the local `.sfdx/` directory (which must be gitignored).

3. **Ignoring dependency order in multi-package projects** — Creating packages that reference each other without declaring `dependencies` in `sfdx-project.json`. UNVERIFIED (2026-10-20): that this fails in `sf package version create` because the engine resolves each package in isolation. Declare dependencies explicitly, with a version, in installation order (sfdx_dev 264 L14804-14814).

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
- Salesforce Developers Blog — The Salesforce Developer's Guide to the Winter '26 Release
  URL: https://developer.salesforce.com/blogs/2025/09/winter26-developers
  Confirms source mobility ships in Winter '26 and that `SF_DISABLE_SOURCE_MOBILITY` (default `false`) is the opt-out — moving files inside a DX project no longer registers as a delete plus recreate. (verified 2026-08-13)
- Salesforce CLI Setup Guide — Salesforce CLI Environment Variables
  URL: https://developer.salesforce.com/docs/atlas.en-us.sfdx_setup.meta/sfdx_setup/sfdx_dev_cli_env_variables.htm
  Confirms the `SF_DISABLE_SOURCE_MOBILITY` description and that its default of `false` means source mobility is enabled by default. (verified 2026-08-13)
