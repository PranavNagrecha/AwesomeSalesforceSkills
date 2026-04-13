# Well-Architected Notes — Cross-Cloud Deployment Patterns

## Relevant Pillars

- **Operational Excellence** — Cross-cloud deployments are a core operational challenge. The foundation-first split-batch sequence is the operationally correct pattern because it makes deployment order explicit, repeatable, and auditable. Teams that rely on single-transaction ordering assumptions accumulate operational risk that compounds across release cycles.
- **Reliability** — Cascading reference failures during cross-cloud deployments are a reliability risk. The split-batch pattern reduces the blast radius of a failed deployment: if the network layer fails, the experience layer never executes, making the failure state predictable and rollback straightforward.
- **Security** — Permission sets that grant Experience Cloud site access must land in the foundation batch alongside the objects they reference. Misplacing permission sets in the experience batch creates a window where objects exist but access grants are absent, which can temporarily expose data to the wrong profiles or leave site users locked out post-deployment.

## Architectural Tradeoffs

**Split batches vs. single transaction:** A three-batch deployment is slower (three separate deploy transactions, each with validation overhead) than a single-package deploy. The tradeoff is correctness: single-transaction cross-cloud deployments are not guaranteed to resolve cross-layer references in the right order. The operational overhead of a split deploy is small compared to the cost of a failed production deployment of an Experience Cloud site.

**Wildcard retrieval vs. explicit manifest:** Using wildcard `*` retrieval for Experience Cloud metadata is convenient but pulls in SiteDotCom and other non-deployable artifacts. The correct tradeoff is to use explicit member lists in `package.xml` for any retrieve that will feed directly into a deployment pipeline. Wildcard retrieval is appropriate only for exploration or local development, not for release engineering.

**API version alignment:** Enforcing that target orgs be at the same API version as source orgs before deploying Experience Cloud metadata is a reliability constraint that has a real cost: it sometimes blocks a deployment until a sandbox is refreshed or an org upgrade completes. The tradeoff is accepting that upgrade timing must be coordinated across environments, rather than discovering version incompatibility during a live deploy window.

## Anti-Patterns

1. **Monolithic multi-cloud package** — Deploying all foundation, network, and experience metadata in a single package and relying on the Metadata API's internal ordering. This pattern works in simple cases but produces `no Network named X found` errors in complex or large deployments where intra-transaction ordering is not guaranteed for cross-type references. The correct approach is always an explicit split-batch sequence.

2. **Deploying without version alignment check** — Skipping API version verification before a cross-cloud deploy that includes DigitalExperienceBundle. This produces opaque errors at deploy time that are difficult to attribute to the version mismatch. The correct approach is to enforce a pre-flight API version check as a mandatory gate in the deployment pipeline.

3. **Including SiteDotCom in deployment packages** — Staging all retrieved metadata without filtering out SiteDotCom, then including it in package.xml because it was returned during retrieval. SiteDotCom is never deployable. It should be in `.forceignore` permanently and reviewed out of every deployment manifest before execution.

## Official Sources Used

- B2B Commerce Developer Guide — Deploy Experience Metadata — https://developer.salesforce.com/docs/commerce/salesforce-commerce/guide/b2b-d2c-comm-deploy-experience-metadata.html
- Salesforce Developer Blog — Master Metadata API Deployments Best Practices — https://developer.salesforce.com/blogs/2025/10/master-metadata-api-deployments-with-best-practices
- Experience Cloud Developer Guide — Migrate to ExperienceBundle for Experience Builder Sites — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_migrate_expbundle.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — sf project deploy start — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference_project_commands_unified.htm#cli_reference_project_deploy_start
- Metadata Coverage Report — https://developer.salesforce.com/docs/metadata-coverage
