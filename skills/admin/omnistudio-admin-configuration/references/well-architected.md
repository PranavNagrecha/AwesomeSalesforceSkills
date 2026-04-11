# Well-Architected Notes — OmniStudio Admin Configuration

## Relevant Pillars

- **Security** — Permission set and PSL assignment directly controls who can author and consume OmniStudio components. Over-provisioning `OmniStudio Admin` to non-builder users violates least privilege and creates an unnecessary authoring attack surface. Community user access requires an explicitly enabled custom permission, not just a standard permission set assignment.
- **Reliability** — The Runtime Namespace field and Standard Runtime toggle are org-level settings with no automatic validation on save. An incorrect or blank namespace value silently blocks component activation. Post-refresh runbooks and deployment checklists must explicitly verify these settings to prevent reliability failures in development and production environments.
- **Operational Excellence** — OmniStudio Settings are not automatically replicated across sandbox refreshes. Documenting the configuration in a runbook and including namespace verification in every org provisioning checklist reduces operator error and enables repeatable, auditable deployments.

## Architectural Tradeoffs

**Standard Runtime vs. Managed Package Runtime:** Standard (native) Runtime eliminates the managed package dependency and is the direction Salesforce is investing in. However, enabling it per-component is irreversible, and orgs with existing Vlocity-built components face a real migration cost. Mixed-mode states (some components native, some managed) are transitional only and should not be treated as a long-term architecture.

**Centralized vs. delegated permission management:** Assigning OmniStudio permissions through profiles (legacy) versus permission sets (recommended) versus permission set groups (best practice for complex orgs) has operational tradeoffs. Permission set groups allow bundling the PSL and permission sets into a single assignable unit, reducing provisioning errors. However, they require careful governance so that the community consumer permission is not inadvertently bundled into groups assigned to internal users.

## Anti-Patterns

1. **Enabling Standard Runtime without a component migration plan** — Toggling Standard OmniStudio Runtime in Setup before auditing existing managed-package components permanently converts the first component any developer opens. In large orgs with hundreds of components, this can create a chaotic mixed-state that is difficult and expensive to resolve. Always plan the migration before enabling the toggle.

2. **Treating permission set assignment as sufficient without PSL provisioning** — PSL consumption is the licensing control; the permission set is the access control. Operating without confirming PSL assignment results in users who appear correctly permissioned but cannot access any OmniStudio functionality, leading to confusing support escalations.

3. **Hardcoding namespace assumptions in org configuration scripts** — Scripts or deployment tools that assume a fixed namespace (e.g., always writing `vlocity_cmt`) will break when deployed to an org using a different Vlocity namespace or a native OmniStudio org. Namespace must be read from the actual org configuration or explicitly parameterized.

## Official Sources Used

- Salesforce Help: OmniStudio Settings — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_settings.htm
- Salesforce Help: OmniStudio Permission Sets and Licenses — https://help.salesforce.com/s/articleView?id=sf.os_permission_sets_and_licenses.htm
- Salesforce Help: Standard OmniStudio Content and Runtime — https://help.salesforce.com/s/articleView?id=sf.os_standard_content_and_runtime.htm
- Salesforce Help: Disable Managed Package Runtime — https://help.salesforce.com/s/articleView?id=sf.os_disable_managed_package_runtime.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
