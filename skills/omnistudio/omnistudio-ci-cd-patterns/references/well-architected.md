# Well-Architected Notes — OmniStudio CI/CD Patterns

## Relevant Pillars

- **Operational Excellence** — Structured DataPack pipelines with job files in version control, post-deploy verification, and explicit activation gates create repeatable, auditable deployment processes that reduce manual error and deployment rollback frequency.
- **Reliability** — The --activate verification step after every DataPack deploy prevents silent "deployed but not live" failures from reaching production users. Environment-gated promotion (dev → UAT → production) with manual sign-off reduces regression risk.
- **Security** — CI/CD service accounts authenticating to Salesforce orgs must use connected apps with JWT bearer flow (not username/password), and the service account should be an API-only integration user with the minimum required permissions. Connected app credentials must be stored as CI/CD secrets, not in job files committed to source control.

## Architectural Tradeoffs

**DataPack (Package Runtime) vs. Metadata API (Standard Runtime):** DataPack deployments are more complex to set up and maintain (separate tooling, job files, activation step) but are required for Package Runtime orgs. Standard Runtime orgs benefit from simpler SFDX-based pipelines aligned with the rest of the Salesforce metadata toolchain. Teams planning a runtime migration from Package to Standard should plan for a pipeline migration as part of the runtime cutover.

**Monorepo vs. separate repos for OmniStudio components:** Storing DataPack JSON alongside standard metadata in a monorepo simplifies change tracking but requires disciplined pipeline stage separation (DataPack deploy and metadata deploy are separate steps). Separate repos make pipeline logic cleaner but add overhead for cross-component changes.

**Manual activation gate vs. automated activation:** Including `--activate` in the automated pipeline step ensures speed but leaves no human review gate between import and live activation. For high-traffic production components, consider a two-step pipeline: import without activate (review), then activate as a manual approval step.

## Anti-Patterns

1. **Omitting --activate from DataPack deploy** — The single most common OmniStudio CI/CD mistake. The pipeline appears to succeed, engineers verify the export JSON was imported, but production users see no change. Always include `--activate` and verify the active version post-deploy.

2. **Using DataPack tooling on Standard Runtime orgs** — Running `sf omnistudio datapack deploy` against a Standard/Core Runtime org either fails with an unhelpful error or silently does nothing, depending on the CLI version. Standard Runtime components must use standard Salesforce metadata deployment. Confirm runtime type before selecting tooling.

3. **Storing CI/CD service account credentials in the job file** — OmniStudio Build Tool job files support inline credentials for convenience. Committing these credentials to source control (even in private repos) is a security violation. Store all org credentials as encrypted CI/CD secrets and reference them via environment variables at runtime.

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Deploy OmniStudio for Managed Package Components — https://help.salesforce.com/s/articleView?id=sf.os_deploy_managed_package_components.htm&type=5
- OmniStudio DataPacks Developer Guide — https://help.salesforce.com/s/articleView?id=sf.os_datapacks_developer_guide.htm&type=5
- Export and Deploy by Using the OmniStudio Build Tool Job File — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_build_tool_job_file.htm&type=5
- OmniStudio Integration Procedures — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm&type=5
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
