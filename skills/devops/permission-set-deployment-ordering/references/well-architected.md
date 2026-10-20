# Well-Architected Notes — Permission Set Deployment Ordering

## Relevant Pillars

- **Security** — Permission set deployments directly control what data and features users can access. Permission loss on deploy is a security event: it can inadvertently revoke access for large user populations or leave access gaps. Correct deployment ordering ensures the principle of least privilege is maintained intentionally, not accidentally degraded by deployment mechanics.
- **Reliability** — A deployment that removes field-level access creates a production incident; UNVERIFIED (2026-10-20): that there is no immediate error signal. Reliable deployment processes require explicit retrieve-then-deploy patterns that preserve the existing security state.
- **Operational Excellence** — Sequential, well-ordered deployment pipelines with explicit stage dependencies (PSets before PSGs, ConnectedApps before PSets referencing them) are self-documenting and repeatable. Ad-hoc single-batch deployments are fragile and environment-dependent.

## Architectural Tradeoffs

**Retrieve-first vs. construct-from-scratch:** Retrieve-first is safer but adds a pipeline step (the retrieve must run against the target org, which requires an authenticated connection). Construct-from-scratch is faster in CI but catastrophically wrong if the permission set already has permissions in the target. The tradeoff always favors retrieve-first for production deployments.

**Single-batch vs. multi-stage deploy:** A single batch is simpler to reason about but gives no ordering guarantee (api_meta 264 L4246-4249); the ConnectedApp + PS conflict is UNVERIFIED (2026-10-20). Multi-stage is more complex to configure in CI but eliminates the class of ordering errors entirely.

## Anti-Patterns

1. **Deploying permission sets constructed only from the changes being added** — This is the single most common cause of permission loss. UNVERIFIED (2026-10-20): "most common" is the package's assertion, not a corpus figure. The developer only adds the new permissions to the package XML without including existing permissions from the target org. Fix: always retrieve-then-merge.
2. **Including ConnectedApp and referencing PermissionSet in the same deploy batch** — UNVERIFIED (2026-10-20): "triggers a known cross-reference error"; neither corpus holds it. Fix as a precaution: split into two sequential deploys, ConnectedApp first.
3. **Deploying PSGs without pre-verifying constituent PSets exist in target** — UNVERIFIED (2026-10-20): "causes PSG validation failure". Fix: use a multi-stage pipeline where PSets are a prerequisite stage (ordered deploys run one at a time, api_meta 264 L4246-4249).

## Official Sources Used

- Metadata API Developer Guide — PermissionSet metadata type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm — supports the include-all-metadata rule from API 40.0 (api_meta 264 L97416-97418), PSG fields and versions (L98009, L98039-98043) and ConnectedApp `permissionSetName` (L37225-37226).
- Metadata API Developer Guide — Deploy Components in the Correct Order — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_order.htm — the one-at-a-time ordering rule is api_meta 264 L4246-4249; the page's own text is not in the corpus.
- Salesforce CLI Reference — sf project deploy start — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Help — Permission Set Group — https://help.salesforce.com/s/articleView?id=sf.perm_sets_groups.htm — Help-only, UNVERIFIED (2026-10-20): not fetchable and not in the corpus.
