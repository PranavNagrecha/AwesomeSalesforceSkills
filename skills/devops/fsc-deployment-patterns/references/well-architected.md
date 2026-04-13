# Well-Architected Notes — FSC Deployment Patterns

## Relevant Pillars

- **Security** — Compliant Data Sharing is the primary row-level security mechanism for regulated financial data in FSC. Deployment sequencing errors (wrong OWD settings, missing sharing recalculation, broken Participant Role references) directly result in data exposure or data lockout. Every deployment step in the CDS activation sequence has a security consequence. The deployment process itself is a security control.
- **Reliability** — FSC has hard sequential dependencies (Person Accounts before household record types, record types before Participant Role custom metadata) that make deployment ordering a reliability concern. A deployment that lands components out of order leaves the org in a partially functional state that may not be detectable until runtime. Phased deployments with explicit validation gates between phases are the reliable pattern.
- **Operational Excellence** — The namespace incompatibility between managed-package and platform-native Core FSC models is an operational risk that surfaces only when a pipeline is run against an incompatible target. Embedding a pre-flight namespace audit in every pipeline run eliminates this class of failure. Runbooks must explicitly document which FSC model each environment uses.

## Architectural Tradeoffs

**Phased deployment vs. single-wave deployment:** FSC's dependency chain (Person Accounts → record types → IndustriesSettings → custom metadata) forces at least four distinct deployment phases. Single-wave deployments that include all components in one batch will either fail (if Person Accounts are not yet enabled) or succeed with silent misconfiguration (if CDS is activated before OWDs are correctly set). The tradeoff is deployment complexity vs. correctness — phased deployment is always more complex but is the only approach that produces a verifiable, correctly sequenced state.

**Managed-package FSC vs. platform-native Core FSC:** The managed-package model provides a contained, versioned artifact that can be installed and upgraded as a unit, but all customizations must use the `FinServ__` namespace, making the metadata non-portable. Platform-native Core FSC provides standard-object semantics and namespace-free metadata, but requires careful migration planning when moving from managed-package orgs. Teams should pick one model per pipeline and enforce it — mixed-model pipelines are the primary source of namespace-related deployment failures.

**CDS share-table recalculation timing:** Running the recalculation batch synchronously after every deployment that touches CDS configuration ensures correctness but adds deployment time. Deferring recalculation to a scheduled off-hours job reduces deployment window duration but creates a period where pre-existing records have incorrect access. For regulated financial data under compliance requirements (SOX, MiFID II, GLBA), the synchronous recalculation is the required choice.

## Anti-Patterns

1. **Deploying FSC metadata in a single wave without pre-flight prerequisite checks** — Skipping the Person Account and OWD pre-flight checks and deploying all FSC components in one batch creates a deployment that either fails mid-run (on missing Person Accounts) or silently misconfigures CDS (if OWDs are wrong). Both outcomes require manual remediation that is riskier than the pre-flight checks would have been. The correct pattern is: check prerequisites, gate on results, then deploy in phases.

2. **Building pipelines without documenting the FSC model per environment** — When pipeline documentation does not explicitly state whether each environment (dev sandbox, UAT sandbox, production) uses managed-package FSC or platform-native Core FSC, pipeline maintainers will eventually deploy a package built for the wrong model. This error is silent at deploy time (the sf CLI does not flag namespace model incompatibility), expensive to diagnose, and easily prevented by adding a single `fsc_model: managed_package | platform_native` field to each environment's configuration.

3. **Treating CDS activation as a one-step toggle rather than a four-step sequence** — The assumption that enabling the CDS flag in `IndustriesSettings` is sufficient to make CDS functional leads to all four of the major CDS deployment gotchas: wrong OWDs, missing recalculation, broken Participant Role references, and missing share-table rows for existing records. CDS activation is a four-step sequence (OWDs → IndustriesSettings deploy → Participant Role custom metadata → sharing recalculation) and each step must be validated before the next begins.

## Official Sources Used

- FSC Admin Guide: Compliant Data Sharing Considerations — https://help.salesforce.com/s/articleView?id=ind.fsc_admin_cds_considerations.htm
- IndustriesSettings Metadata API Reference — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_industriessettings.htm
- FSC Developer Guide: Custom Metadata Types — https://developer.salesforce.com/docs/atlas.en-us.fsc_dev.meta/fsc_dev/fsc_api_custom_metadata_usage.htm
- Salesforce Architects: Compliant Data Sharing in FSC — https://medium.com/salesforce-architects
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
