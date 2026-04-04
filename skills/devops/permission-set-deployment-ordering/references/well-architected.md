# Well-Architected Notes — Permission Set Deployment Ordering

## Relevant Pillars

- **Security** — Permission set deployments directly control what data and features users can access. Silent permission wipeout is a security event: it can inadvertently revoke access for large user populations or leave access gaps. Correct deployment ordering ensures the principle of least privilege is maintained intentionally, not accidentally degraded by deployment mechanics.
- **Reliability** — A deployment that silently removes field-level access creates a production incident with no immediate error signal. Reliable deployment processes require explicit retrieve-then-deploy patterns that preserve the existing security state.
- **Operational Excellence** — Sequential, well-ordered deployment pipelines with explicit stage dependencies (PSets before PSGs, ConnectedApps before PSets referencing them) are self-documenting and repeatable. Ad-hoc single-batch deployments are fragile and environment-dependent.

## Architectural Tradeoffs

**Retrieve-first vs. construct-from-scratch:** Retrieve-first is safer but adds a pipeline step (the retrieve must run against the target org, which requires an authenticated connection). Construct-from-scratch is faster in CI but catastrophically wrong if the permission set already has permissions in the target. The tradeoff always favors retrieve-first for production deployments.

**Single-batch vs. multi-stage deploy:** A single batch is simpler to reason about but cannot handle ConnectedApp + PS conflicts or reliable PSG sequencing. Multi-stage is more complex to configure in CI but eliminates the class of ordering errors entirely.

## Anti-Patterns

1. **Deploying permission sets constructed only from the changes being added** — This is the single most common cause of silent permission loss. The developer only adds the new permissions to the package XML without including existing permissions from the target org. Fix: always retrieve-then-merge.
2. **Including ConnectedApp and referencing PermissionSet in the same deploy batch** — Triggers a known cross-reference error. Fix: split into two sequential deploys, ConnectedApp first.
3. **Deploying PSGs without pre-verifying constituent PSets exist in target** — Causes PSG validation failure. Fix: use multi-stage pipeline where PSets are a prerequisite stage.

## Official Sources Used

- Metadata API Developer Guide — PermissionSet metadata type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Metadata API Developer Guide — Deploy Components in the Correct Order — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_order.htm
- Salesforce CLI Reference — sf project deploy start — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Help — Permission Set Group — https://help.salesforce.com/s/articleView?id=sf.perm_sets_groups.htm
