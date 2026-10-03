# Well-Architected Notes: Release Management

## Relevant Pillars

- **Operational Excellence**: Release management is the primary operational excellence discipline for Salesforce deployments. Structured release plans, go/no-go criteria, and post-deploy checklists reduce deployment failures and mean time to recovery.
- **Reliability**: Rollback strategy and quick deploy validation directly serve reliability. A release that can be reversed in minutes recovers faster from defects than one with no rollback plan.

## Architectural Tradeoffs

**Version numbering complexity vs traceability:** Org-based projects have no native version concept. Simple git tags are easy but require discipline; a version-tracking custom object provides richer history but adds overhead. Teams with quarterly releases can use git tags. Teams with weekly releases benefit from a custom object or JIRA integration.

**Full test run vs Quick Deploy speed:** Quick Deploy skips tests and is much faster on release night. The validation must have succeeded within the last 10 days, so teams with long approval cycles may find the window expires before they can deploy. UNVERIFIED (2026-10-03): whether org changes made after the validation (for example new Apex classes) invalidate a pending quick deploy is not stated in the Metadata API guide; re-validate after any production change to be safe.

**Sandbox preview adoption vs stability:** Preview sandboxes receive the new Salesforce release early, allowing advance testing. However, running preview may expose your development work to platform changes before they are fully stable. Teams building near platform upgrade boundaries should weigh early testing against potential instability.

## Anti-Patterns

1. **No rollback archive before deployment**: deploying to production without first archiving the current metadata state means rollback requires manual reconstruction of the previous version. Always retrieve and store a backup before deploying.
2. **Activating sandbox preview for all sandboxes**: opting every sandbox into preview creates a situation where the full development team is running on an unstable preview release. Reserve preview for one dedicated regression sandbox; keep development sandboxes on the stable release.
3. **No documented go/no-go criteria**: without predefined criteria, go/no-go decisions become subjective and pressure-driven. Unambiguous criteria (zero Sev-1 defects, >75% test coverage, validation deploy passed) remove ambiguity and protect against rushed deployments.

## Official Sources Used

- Metadata API Developer Guide, Summer '26 (release 262): `deployRecentValidation()`, "Running Tests in a Deployment", DeployOptions `testLevel` and `rollbackOnError`, "Slow Deployments", Flow type limitations, FlowSettings `enableFlowDeployAsActiveEnabled` - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce DX Developer Guide, Summer '26: Unlocked Packaging Keywords (`NEXT`), version numbering after promote, "Upgrade a Version of an Unlocked Package" (lower-version install is not a rollback) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_dev.pdf
- Second-Generation Managed Packaging Developer Guide, Summer '26: comparison of 1GP and 2GP (no patch orgs), Patch Versions, package ancestry table (downgrade not allowed) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/pkg2_dev.pdf
- Salesforce CLI Command Reference, Summer '26: `project deploy validate`, `project deploy quick` - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/sfdx_cli_reference.pdf
- Salesforce CLI 2.151.7 local `--help` output for `project deploy validate`, `project deploy quick` (`--job-id` 10-day validity, `--use-most-recent` 3-day lookback), `project deploy start` (`--ignore-conflicts`, `--ignore-errors`, `--metadata-dir`, `--single-package`), `project retrieve start`, `package version create`, `package install`
- Salesforce Trust (instance maintenance calendar) - https://trust.salesforce.com
