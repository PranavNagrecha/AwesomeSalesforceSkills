# Well-Architected Notes — Experience Cloud Deployment Admin

## Relevant Pillars

- **Reliability** — Experience Cloud site deployments fail silently in surprising ways (wrong metadata order, missing flag, SiteDotCom inclusion). Reliable deployments require a validated, sequenced process with explicit success checks at each stage and a post-deployment smoke test confirming the site is Published and accessible.
- **Operational Excellence** — The mandatory manual Publish step and the org-specific Enable Experience Bundle Metadata API flag are the two most common sources of release incidents. Encoding both into automated pipelines (Connect REST API publish, post-provision scripts) converts ad hoc runbook steps into repeatable, auditable operations.
- **Security** — The Guest User Profile controls what unauthenticated visitors can access on the site. Because this profile is not bundled in ExperienceBundle, its permissions can silently diverge between source and target orgs after deployment. A Well-Architected deployment process includes an explicit Guest User Profile review step to prevent unintended data exposure to anonymous users.
- **Performance** — ExperienceBundle deployments for large LWR sites with many pages can be time-consuming. Splitting dependencies from the bundle (as recommended in the workflow) reduces the blast radius of a failed deploy and allows dependency components to be verified before the longer bundle deploy is attempted.
- **Scalability** — Sites that grow to many pages, CMS workspaces, or multi-language configurations increase the complexity of ExperienceBundle. Using source-tracked SFDX projects and split manifests scales better than monolithic change sets as site complexity grows.

## Architectural Tradeoffs

**Single change set vs. split change sets:** A single change set is simpler to create and track but does not guarantee dependency-aware ordering within the set. For Experience Cloud sites, this means ExperienceBundle can fail because Network is not yet committed when ExperienceBundle is processed. Split change sets add operational overhead (two deployments instead of one) but guarantee the required ordering. For any non-trivial site, split deployment is the correct choice.

**Manual Publish vs. Connect REST API Publish:** Manual publish via Experience Builder requires human access to the target org after deployment and is error-prone in time-pressured releases. The Connect REST API publish endpoint enables fully automated, pipeline-driven releases but requires a valid access token and knowledge of the Community Id. For production releases, API-driven publish is strongly preferred because it is auditable and removes dependency on human intervention post-deployment.

**Monolithic package.xml vs. manifest-per-layer:** Deploying all site metadata in a single manifest introduces ordering risk and makes partial retries difficult. A layered manifest approach (deps → site bundle) makes each step independently retrievable, verifiable, and retriable. The operational overhead of maintaining two manifests is outweighed by the reliability gain for anything deployed more than once.

## Anti-Patterns

1. **Deploying ExperienceBundle before Network and CustomSite** — This is the most frequent cause of Experience Cloud deployment failures. ExperienceBundle requires its parent Network record to exist in the target org. Teams that deploy all components in a single unordered package or change set regularly hit this failure. The correct pattern is always to confirm Network and CustomSite are present in the target before initiating the ExperienceBundle deploy step.

2. **Assuming a successful deployment means the site is live** — Deployment success and site availability are two separate outcomes. A deployed-but-unpublished site shows a "Site Under Construction" page to all visitors. Teams that treat deployment completion as release completion miss this step, leading to avoidable production incidents. The publish step must be explicitly included in the deployment runbook and verified as a post-deployment acceptance criterion.

3. **Omitting Guest User Profile from the deployment package** — Treating ExperienceBundle as the complete representation of an Experience Cloud site leads to permission drift between source and target orgs. The Guest User Profile must be explicitly retrieved, reviewed, and deployed as a separate component to ensure the security posture of the site matches the source.

## Official Sources Used

- ExperienceBundle for Experience Builder Sites — https://help.salesforce.com/s/articleView?id=sf.communities_dev_migrate_expbundle.htm
- Deploy Experience Cloud Site with Change Sets — https://help.salesforce.com/s/articleView?id=sf.networks_migrate_changesets.htm
- Metadata API Developer Guide: ExperienceBundle — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_experiencebundle.htm
- Metadata API Developer Guide (general) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Connect REST API: Publish Community — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_communities.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
