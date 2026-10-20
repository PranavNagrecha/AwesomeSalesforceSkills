# Well-Architected Notes -- Pre-Deployment Checklist

## Relevant Pillars

- **Reliability** -- The pre-deployment checklist is fundamentally a reliability practice. Validation deploys confirm that the deployment will succeed before the production window opens. Pre-release backups provide a tested rollback path. Dependency checks prevent partial failures that leave metadata in an inconsistent state.
- **Operational Excellence** -- A standardized checklist reduces human error during releases. Automation of validation deploys and backup retrieval makes the process repeatable across teams and releases. Quick-deploy windows minimize production downtime.
- **Security** -- Pre-deployment review should include confirming that permission sets and profiles in the package do not inadvertently grant elevated access. Sharing rule changes must be reviewed for data exposure risk before deploying.

## Architectural Tradeoffs

**Speed vs. Safety:** Quick deploys skip test execution (api_meta 264 L4967-4968), which shortens the production window ("hours to minutes" is UNVERIFIED, 2026-10-20). The tradeoff is that a code change made after the validation means the changed package needs a fresh validation (the guide requires the components to be validated within the last 10 days, api_meta 264 L3579; "invalidates the quick-deploy ID" is UNVERIFIED, 2026-10-20). Teams must resist the temptation to make last-minute changes after validation.

**Monolithic vs. Staged Deploys:** A single deployment package is simpler to manage but harder to debug and roll back. Staged deploys (schema, then logic, then presentation, then access) isolate failures but require more coordination and multiple deployment windows. The right choice depends on the release size: under 20 components, monolithic is fine; over 50, staged is safer.

**Backup Granularity:** Backing up only the components being deployed is fast and targeted. Backing up the entire org is comprehensive but slow and storage-intensive. The targeted approach is sufficient for rollback in nearly all cases, since the deployment only overwrites the components in the manifest.

## Anti-Patterns

1. **Deploying without validating against production** -- Teams that rely on sandbox test results alone discover production-specific failures during the release window, extending outages and forcing emergency rollbacks. Validation deploys are safe (they write nothing) and should always precede production deployments.

2. **No pre-release backup** -- Without a backup, rollback requires reconstructing the prior state from source control history, which is slow and error-prone (especially for declarative metadata that may not be fully version-controlled). Retrieving the current production state before deploying takes minutes and provides a one-command rollback path.

3. **Ignoring the deployment status queue** -- Only one deployment runs at a time and queued ones are not necessarily run in submitted order (api_meta 264 L4246-4249); "lock contention failures" is UNVERIFIED (2026-10-20). Teams that do not check the Deployment Status page lose track of which deploy ran first.

## Official Sources Used

- Metadata API Developer Guide -- https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm -- quick-deploy conditions api_meta 264 L4967-4974, test levels L4423-4443, deployment queue L4246-4249, destructive manifests L4749-4758.
- Salesforce CLI Reference -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm -- `sf project deploy validate` and `quick --job-id` at sfdx_dev 264 L14359-14370, 10-day window L14372.
- Salesforce Help: Deployment Best Practices -- https://help.salesforce.com/s/articleView?id=sf.platform.deploy_best_practices.htm
- Salesforce Developer Blog: Master Metadata API Deployments with Best Practices (Oct 2025)
- Salesforce Trust Site -- https://trust.salesforce.com -- "real-time information on system performance" (secguide 262 L127-129); per-instance maintenance listings UNVERIFIED (2026-10-20)
