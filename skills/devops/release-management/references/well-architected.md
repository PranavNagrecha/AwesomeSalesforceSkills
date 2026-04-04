# Well-Architected Notes — Release Management

## Relevant Pillars

- **Operational Excellence** — Release management is the primary operational excellence discipline for Salesforce deployments. Structured release plans, go/no-go criteria, and post-deploy checklists reduce deployment failures and mean time to recovery.
- **Reliability** — Rollback strategy and quick deploy validation directly serve reliability. A release that can be reversed in minutes recovers faster from defects than one with no rollback plan.

## Architectural Tradeoffs

**Version numbering complexity vs traceability:** Org-based projects have no native version concept. Simple git tags are easy but require discipline; a version-tracking custom object provides richer history but adds overhead. Teams with quarterly releases can use git tags. Teams with weekly releases benefit from a custom object or JIRA integration.

**Full test run vs Quick Deploy speed:** Quick Deploy skips tests and is dramatically faster on deployment night, but the 10-day validation window means any org changes after validation (e.g., new Apex classes) may cause the quick deploy to fail. Teams with high-velocity orgs may find the validation window expires before they can deploy.

**Sandbox preview adoption vs stability:** Preview sandboxes receive the new Salesforce release early, allowing advance testing. However, running preview may expose your development work to platform changes before they are fully stable. Teams building near platform upgrade boundaries should weigh early testing against potential instability.

## Anti-Patterns

1. **No rollback archive before deployment** — deploying to production without first archiving the current metadata state means rollback requires manual reconstruction of the previous version. Always retrieve and store a backup before deploying.
2. **Activating sandbox preview for all sandboxes** — opting every sandbox into preview creates a situation where the full development team is running on an unstable preview release. Reserve preview for one dedicated regression sandbox; keep development sandboxes on the stable release.
3. **No documented go/no-go criteria** — without predefined criteria, go/no-go decisions become subjective and pressure-driven. Unambiguous criteria (zero Sev-1 defects, >75% test coverage, validation deploy passed) remove ambiguity and protect against rushed deployments.

## Official Sources Used

- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Metadata API Developer Guide (deployRecentValidation) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference (project deploy validate, quick, start) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce Trust and Release Schedule — https://trust.salesforce.com
