# Well-Architected Alignment -- Metadata API Coverage Gaps

## Relevant Pillars

- **Reliability** -- Metadata coverage gaps directly impact deployment reliability. When unsupported types are not accounted for, deployments succeed technically but deliver incomplete configurations, leading to runtime failures that erode trust in the CI/CD pipeline. A well-architected approach ensures every deployment produces a fully functional org regardless of metadata type support status.

- **Operational Excellence** -- Release runbooks, post-deploy scripts, and coverage gap tables are operational artifacts that reduce toil and prevent human error during deployments. Without them, teams rely on tribal knowledge ("someone remembers to toggle that setting in Setup"), which is fragile and does not scale.

- **Adaptability** -- Metadata type support changes across Salesforce releases. A well-architected DevOps practice treats the coverage gap table as a living document that is reviewed each release cycle, ensuring the pipeline adapts to new support additions and deprecations without emergency rework.

## Architectural Tradeoffs

### Automation vs. Documentation

Post-deploy scripts using the Tooling API automate workarounds for coverage gaps but introduce maintenance burden -- the scripts must be updated when Salesforce changes the Tooling API object model. Release runbooks with manual steps are easier to maintain but depend on human discipline. The right balance depends on deployment frequency: high-frequency pipelines (daily or more) should automate aggressively; quarterly release cycles can tolerate well-documented manual steps.

### API Version Pinning vs. Latest

Pinning `sourceApiVersion` ensures consistent behavior across the team and across time, but delays access to newly supported metadata types. Using the latest API version gives access to the newest coverage improvements but risks breaking existing deployments when types are deprecated. Pin by default and upgrade deliberately.

### Exclusion vs. Conditional Deployment

Excluding unsupported types from `package.xml` is the simplest approach but loses the ability to deploy them when targeting an org where they are supported. Conditional deployment (using environment-specific manifests) preserves flexibility but adds pipeline complexity. Use exclusion for types that are universally unsupported; use conditional deployment for types whose support varies by org edition.

## Anti-Patterns

1. **"Deploy and hope" without a coverage audit** -- Deploying without checking the Metadata Coverage Report and discovering gaps only when production users report missing functionality. This violates the Reliability pillar by introducing unknown failure modes into every deployment.

2. **Tribal knowledge instead of runbooks** -- Relying on one team member who "knows" which settings to configure manually after each deployment. When that person is unavailable, deployments are incomplete. This violates Operational Excellence by creating single points of failure in the release process.

3. **Over-broad .forceignore patterns** -- Adding sweeping exclusion patterns to suppress deployment errors without understanding which components are being excluded. This masks real problems and causes silent configuration drift, violating both Reliability and Adaptability.

## Official Sources Used

- Metadata API Developer Guide -- https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Metadata Coverage Report -- https://developer.salesforce.com/docs/metadata-coverage
- Unsupported Metadata Types -- https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_unsupported_types.htm
- Salesforce DX Developer Guide -- https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Well-Architected Framework Overview -- https://architect.salesforce.com/well-architected/overview
