# Well-Architected Notes — Destructive Changes Deployment

## Relevant Pillars

- **Reliability** — Destructive deployments are irreversible. A deletion that removes a field containing production data is permanent; Salesforce does not retain field values after a CustomField deletion. Reliability practice demands that dependency checks, dry runs (checkOnly), and rollback planning are built into the deployment process before any destructive manifest is executed against a production org.
- **Operational Excellence** — Destructive changes must be tracked in version control alongside the companion `package.xml` so the full deletion history is auditable. Deployment pipelines should enforce ordering (pre vs post manifest selection) as a code-reviewed, tested artifact rather than a runtime decision made by an individual developer.

## Architectural Tradeoffs

**Atomic deletion vs. staged deletion:** Combining a deletion with an update to the referencing component in a single deployment (using the post variant) is convenient but couples two separate concerns. If the updated component has a bug, rolling back the deployment restores the reference removal and the deletion simultaneously — the component you wanted to delete may be back in the org. A staged approach (deploy the reference removal first in one deployment, then the deletion in a subsequent deployment) is slower but creates a clean audit trail and simpler rollback surface.

**Destructive manifests vs. manual deletion:** For one-off field removals with no dependencies, manual deletion in Setup is often lower risk than authoring a deployment manifest. Metadata API deployment errors can leave an org in a partially-applied state in edge cases. Reserve manifest-driven deletion for bulk operations, CI/CD pipelines, or situations requiring audit trails.

## Anti-Patterns

1. **Deleting without dependency verification** — Deploying a destructive manifest without first confirming that no active component references the target component is the most common cause of failed releases. Always use Setup dependency tooling or local source inspection before authoring the manifest. Skipping this step leads to "component in use" deployment failures that block the entire release.

2. **Treating destructive manifests as reversible** — Unlike an Apex class deployment that can be reverted by re-deploying a prior version, a field deletion destroys the field and all its data permanently. Practitioners sometimes treat destructive deployments with the same casualness as code deployments. Every destructive manifest targeting production should require explicit sign-off and a data export if the field holds live data.

3. **Using undocumented manual deletions instead of manifest-driven deletion** — Making deletions directly in a sandbox UI without capturing them in a destructive manifest means the change is invisible to version control. When the sandbox is refreshed or a new org is spun up, the deleted component re-appears because no deployment artifact records the deletion intent.

## Official Sources Used

- Metadata API Developer Guide — Deploying Destructive Changes: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_deleting_files.htm
- Salesforce CLI sf project deploy start Command Reference: https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm#cli_reference_project_deploy_start
- Salesforce DX Developer Guide — Deleting Source from an Org: https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_develop_delete_source.htm
- Metadata API Developer Guide — Package.xml Schema: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/manifest_files.htm
