# Well-Architected Notes — Experience Cloud Deployment Dev

## Relevant Pillars

- **Reliability** — The primary pillar for this skill. Silent deployment failures (empty retrieves, CMS content exclusion, wrong metadata type) cause production incidents that are hard to trace back to the deployment. Reliable Experience Cloud deployment requires explicit validation at every stage: non-empty retrieves, CMS content verification, and post-deployment smoke tests. The deployment pipeline must not trust exit code 0 as a sufficient success signal.
- **Operational Excellence** — Post-deployment manual steps (domain, SSO, CDN, site activation) are unavoidable due to platform gaps. Operational excellence means these steps are documented in a runbook, owned by named individuals, and verified after every deployment — never left as tribal knowledge.
- **Security** — Guest user profile assignments and SSO configurations are not deployed by any metadata type. Deploying a site without re-configuring authentication and guest access settings can leave the target org site open to unintended guest access or broken SSO login flows.
- **Performance** — CDN configuration is not captured in metadata. If the source org site uses a CDN-backed URL for asset delivery, the target org site will fall back to uncached origin serving until CDN is manually reconfigured. This causes visible performance degradation in the target org that does not appear in pre-deployment testing.

## Architectural Tradeoffs

**ExperienceBundle vs. DigitalExperienceBundle selection is a one-time architectural commitment.** The choice of runtime at site creation cannot be changed without rebuilding the site. Aura-based sites use ExperienceBundle; enhanced LWR sites use DigitalExperienceBundle. Deploying with the wrong type leaves no trace of the error — the metadata simply does not match the site structure. Document the runtime type for every site in the project and enforce it in the CI pipeline.

**Metadata-only deployment vs. full-stack deployment.** A pure metadata deployment (CLI deploy) covers site structure, page layouts, component configuration, and custom LWC. It does not cover CMS managed content, domain settings, SSO, or CDN. Teams that treat metadata deployment as a complete deployment will encounter missing content and misconfigured access in every target org. The complete deployment model requires a metadata layer, a CMS content layer, and a manual configuration layer — all three must be planned and executed.

**Scratch org development vs. sandbox-first development for LWR sites.** DigitalExperienceBundle has known scratch org support gaps. Teams building enhanced LWR sites should use a sandbox (Developer or Developer Pro) as the primary integration environment and reserve scratch orgs for component-level development. This is a deviation from the standard Salesforce DX recommended workflow and must be explicitly documented in the team's DevOps process.

## Anti-Patterns

1. **Trusting exit code 0 as deployment success** — Both ExperienceBundle and DigitalExperienceBundle deployments can succeed (exit 0) while producing an incomplete or functionally broken site. CMS content is silently excluded, domain config is absent, and the site may be inactive. Every post-deployment runbook must include explicit verification steps that check site accessibility, content rendering, and authentication before marking the deployment complete.

2. **Using a single-step deployment for all Experience Cloud components** — Running `sf project deploy start --manifest package.xml` with all Experience Cloud components in one step does not enforce the correct deployment order (ExperienceBundleSettings > Network > site bundle) and can leave the target org in a partially deployed state if any step fails mid-way. Use sequential, ordered deployment steps with validation gates between each stage.

3. **Omitting CMS content from the deployment plan** — Teams that scope Experience Cloud deployments as "just metadata" routinely discover CMS content gaps after the deployment reaches production. CMS content must be explicitly scoped into the deployment plan from the start, with a separate migration strategy documented before the deployment begins.

## Official Sources Used

- ExperienceBundle for Experience Builder Sites (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_experiencebundle.htm
- Deploy Experience Cloud Site with Metadata API — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/networks_migrating_from_sandbox.htm
- DigitalExperienceBundle (Metadata API Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_digitalexperiencebundle.htm
- Migrate an Experience Builder Site to Another Org — https://developer.salesforce.com/docs/atlas.en-us.communities_dev.meta/communities_dev/communities_dev_migrate_expbundle.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Command Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
