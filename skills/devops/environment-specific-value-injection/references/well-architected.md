# Well-Architected Notes — Environment-Specific Value Injection

## Relevant Pillars

- **Security** — This is the primary pillar. Secrets (OAuth tokens, passwords, client secrets) must never enter source control, Custom Metadata records, or CI logs. The recommended patterns keep secrets in org-bound credential stores or CI secret managers, inject them post-deploy via authenticated API calls, and ensure the only path to read a secret at runtime is through Named Credentials or External Credentials — never via SOQL or Apex string literals.
- **Operational Excellence** — Environment injection must be deterministic and automated. Manual steps (e.g., "remember to update the Named Credential password after each sandbox refresh") are deployment risks. Well-Architected orgs automate credential population, validate callouts post-deploy, and fail CI early if environment variables are missing.
- **Reliability** — Configuration drift between environments (sandbox pointing to production endpoint, wrong threshold in UAT) is one of the most common sources of unreliable Salesforce integrations. Deployable Custom Metadata and string replacement eliminate the class of bugs caused by environment-specific values diverging silently over time.

## Architectural Tradeoffs

**Named Credentials vs. hardcoded Apex:** Named Credentials add a layer of indirection — Apex never sees the raw URL or credential. This is the correct tradeoff. The cost is that credential population must be automated and tested separately from the metadata deploy. Teams that skip the post-deploy population step and rely on manual Setup entry pay for it in every environment they provision.

**Custom Metadata vs. Custom Settings for non-secret config:** Custom Metadata records are deployable metadata — they travel with the release, are source-controlled, and arrive in a new scratch org or sandbox on first deploy. Custom Settings are org-specific data — they require a post-refresh script or manual entry in every new environment. For values that should behave consistently across environments (feature flags, routing keys), Custom Metadata is the right choice even though it is less convenient to update without a deployment. The correct tradeoff: accept slower config change cycles in exchange for reliable, source-controlled configuration.

**sfdx string replacement vs. post-deploy API calls:** String replacement is simpler and requires no post-deploy network call — but it only works for non-secret values (the substituted value appears in the deployed metadata and can be retrieved from the org). Post-deploy API calls are required for actual secrets, but they add a second failure point (the API call must succeed, the credentials must be valid, the org must be accessible). Both mechanisms should be combined: string replacement for URLs and non-sensitive config, post-deploy API calls for credentials only.

## Anti-Patterns

1. **Storing secrets in Custom Metadata records** — A team uses `OrgSettings__mdt` to store API keys and OAuth client secrets because "it's deployable and easy." The CMT records appear in Setup, are visible to system admins, and are deployed in source control where any repository contributor can read them. This is not secret management — it is secret leakage with extra steps. Named Credentials and External Credentials exist specifically to hold secrets in an org-bound, non-queryable store.

2. **Hardcoding per-environment values in Apex constants or static resources** — Teams use `if (URL.getSalesforceBaseUrl().toExternalForm().contains('sandbox'))` to branch behavior, then hardcode the sandbox-specific values in the same Apex file. This creates a maintenance burden, embeds environment logic in business logic, and breaks silently when sandbox names change or new environments are added. The correct model is to externalize all environment-specific values into Named Credentials or Custom Metadata and keep Apex environment-agnostic.

3. **Using sfdx string replacement as a general-purpose secret injection mechanism** — A team injects an API password directly into a Named Credential XML using `replaceWithEnv`. The substituted value is now written into the deployed metadata record in the org. Any admin who retrieves the Named Credential from the org can read the password in the retrieved XML. String replacement is appropriate for non-sensitive URLs and config values, not for secrets that must remain confidential in the org.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide (String Replacements) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Named Credentials Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm
- Custom Metadata Types Help — https://help.salesforce.com/s/articleView?id=sf.custommetadatatypes_overview.htm
- Salesforce Well-Architected — https://architect.salesforce.com/well-architected/overview
