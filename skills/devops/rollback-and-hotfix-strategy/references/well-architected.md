# Well-Architected Notes — Rollback And Hotfix Strategy

## Relevant Pillars

- **Reliability** — Rollback capability is a core reliability mechanism. Systems that can recover quickly from failed deployments minimize downtime and user impact. The pre-deploy archive pattern ensures recoverability is built into the deployment process rather than improvised during an incident. Quick deploy reduces the mean time to recovery (MTTR) by eliminating the test execution wait during emergency fixes.

- **Operational Excellence** — A documented rollback and hotfix process transforms incident response from ad-hoc firefighting into a repeatable, practiced procedure. Operational excellence requires that rollback plans exist before every production deployment, not after something goes wrong. The hotfix branch isolation pattern keeps emergency changes traceable and auditable.

## Architectural Tradeoffs

**Rollback vs. Roll Forward** — Rolling back restores stability immediately but may discard valid changes that were bundled with the broken component. Rolling forward preserves all changes but keeps production in a degraded state until the fix is ready. The correct default is to roll back first (restore stability) and then re-deploy the valid changes in a subsequent release, unless the rollback itself would cause data integrity issues (e.g., after a data migration).

**Quick Deploy Speed vs. Test Coverage** — Quick deploy skips test execution by relying on a prior validation run. This is safe when the validated package has not changed, but introduces risk if the org state has changed between validation and promotion (e.g., another deployment landed in between, or data-dependent tests would now fail). Teams must weigh the speed benefit against the staleness risk of the validation.

**Pre-Deploy Archive Storage Cost vs. Recovery Speed** — Maintaining archives of production state before every deployment consumes storage and adds pipeline complexity. The alternative (reconstructing from Git history) is free but slow and error-prone during an incident. For production orgs with high availability requirements, the storage cost is justified.

**Hotfix Isolation vs. Pipeline Bypass Risk** — Hotfix branches bypass the normal release pipeline to reach production faster. This is necessary for emergencies but creates risk if the hotfix is not merged back into the development branch or if the minimal change introduces its own regression. Strict post-hotfix merge policies mitigate this risk.

## Anti-Patterns

1. **No pre-deploy archive and no rollback plan** — Deploying to production without capturing the current state first. When something goes wrong, the team scrambles to reconstruct the previous state from Git history while production is down. This turns a 5-minute rollback into a multi-hour incident.

2. **Hotfix on the development branch instead of a production-based branch** — Creating the hotfix from the development branch, which may contain unreleased features. The hotfix deployment accidentally promotes untested changes to production alongside the fix.

3. **Treating all components as rollbackable** — Building a rollback plan that assumes every component can be reverted via deployment, ignoring Record Types, Picklist values, and active Flow versions. The rollback deployment fails partway through, leaving production in a partially-reverted state that is worse than the original regression.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
