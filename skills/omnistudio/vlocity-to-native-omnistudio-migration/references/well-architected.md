# Well-Architected Notes — Vlocity to Native OmniStudio Migration

## Relevant Pillars

- **Operational Excellence** — This migration is fundamentally an operational project. The risk of downtime, data loss, and regression is proportional to the quality of the migration runbook, the completeness of the pre-migration audit, and the discipline of the phased cutover approach. A well-executed migration follows a documented sequence, validates each step before proceeding, and maintains rollback options throughout. Ad-hoc migration without a checklist is the primary source of production incidents in this domain.
- **Adaptability** — Moving from a managed package dependency to native platform metadata is a structural improvement in long-term maintainability. Native OmniStudio components are managed with standard Salesforce tooling (SFDX, Metadata API, change sets) rather than Vlocity-specific DataPacks and the Vlocity Build Tool. This reduces external toolchain dependencies and aligns the org with the standard Salesforce development lifecycle. Rebuilding the CI/CD pipeline as part of the migration is not optional work — it is the adaptability payoff of the migration.
- **Security** — The migration is an opportunity to review and improve OmniStudio component security posture. Vlocity managed package Integration Procedures may have been invoked via direct REST endpoints that bypass Apex sharing rules. In the native runtime, enforcing that all Integration Procedure invocations from LWC go through `@AuraEnabled` Apex preserves sharing enforcement. DataRaptor operations should be reviewed for CRUD/FLS compliance during the field reference audit.

## Architectural Tradeoffs

**Phased migration vs. big-bang cutover.** A phased, domain-by-domain migration reduces risk and allows teams to build migration expertise progressively. The cost is a longer transition period during which both runtimes must be maintained. A big-bang cutover is faster and eliminates the dual-maintenance window, but requires comprehensive pre-testing and carries higher rollback complexity. Large orgs (100+ components, multiple business domains) should always prefer phased migration.

**Activated native components vs. deactivated Vlocity components during testing.** The safest side-by-side testing approach keeps Vlocity components active for production users while native components are tested in parallel in a sandbox. However, this requires careful control of which runtime is active in which environment. The risk of accidentally activating a native component in production before it is tested is real and must be controlled through sandbox-only activation gates.

**DataPack pipeline retention vs. early replacement.** Some teams retain the Vlocity Build Tool pipeline alongside the new SFDX pipeline during the transition to avoid disrupting ongoing development. This creates short-term operational complexity but avoids blocking active development teams. The better practice is to build and validate the SFDX pipeline first in a feature sandbox, then cut over the CI/CD pipeline before beginning component migration in shared environments.

## Anti-Patterns

1. **Skipping the pre-migration namespace audit** — Running the Migration Tool without first auditing custom code for Vlocity namespace references creates a false sense of completion. The tool only migrates component definitions; it cannot update LWC markup or Apex classes. Teams that skip the audit discover the scope of custom code changes after the migration window, under pressure, with users impacted.

2. **Treating the Migration Tool run as the final step** — The Migration Tool is step 4 of a 7-step process. Orgs that consider the migration complete after the tool finishes neglect to activate native components, update code, replace CI/CD pipelines, and validate behavior. This leaves the org in a partially migrated state that is fragile — the managed package is still a dependency, and the native components are inactive and untested.

3. **Uninstalling the managed package before all Apex references are removed** — The Salesforce platform blocks managed package uninstall if any Apex code in the org references the package's namespace types. Attempting an early uninstall to "clean up" before all Apex has been updated results in a failed uninstall and a confusing error message. The uninstall must be the last step, after all code changes are deployed and verified.

## Official Sources Used

- OmniStudio Help: Migrate from Vlocity to OmniStudio — https://help.salesforce.com/s/articleView?id=sf.os_migrate_vlocity_to_omnistudio.htm
- OmniStudio Developer Guide (Industries Reference) — https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/omnistudio_overview.htm
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
