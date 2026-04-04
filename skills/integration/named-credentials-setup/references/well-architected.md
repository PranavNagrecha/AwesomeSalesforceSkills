# Well-Architected Notes — Named Credentials Setup

## Relevant Pillars

- **Security** — Named Credentials are Salesforce's primary mechanism for securing outbound integration credentials. They prevent secrets from being stored in Apex, Custom Settings, or Custom Metadata where they are readable via SOQL or exportable via packages. The credential vault provides encryption at rest and enforces a one-way write model (secrets are not readable back). Per User principal type enforces user-level access boundaries on external systems. Permission Set assignments on External Credential principals enforce least-privilege access at the org user level.

- **Operational Excellence** — Separating endpoint configuration (Named Credential URL) from authentication configuration (External Credential) reduces the blast radius of credential rotation. Rotating a client secret or password requires only a Setup UI update to the External Credential vault value — no code change, no deployment. Enhanced Named Credentials also enable one External Credential to back multiple Named Credentials, reducing duplication across many endpoint paths on the same service.

## Architectural Tradeoffs

**Named Principal vs Per User:** Named Principal is operationally simpler — one credential, one rotation event, no user onboarding overhead. Per User adds operational complexity (each user must authorize, re-authorize on token expiry, and be trained to use User Settings) but is the correct choice when the external service enforces user-level data scoping or audit trails.

**Enhanced vs Legacy:** Enhanced Named Credentials require more configuration steps (two records instead of one) but unlock Per User principals, formula-based custom headers, and reusable External Credentials across multiple endpoints. For any net-new integration, always use the enhanced model. For legacy migrations, the operational risk is in formula namespaces and callback URL changes — plan carefully.

**Deployment boundaries:** The clean separation between deployable metadata structure and vault-stored secrets is a security feature, not a limitation. It forces a deliberate post-deployment credential entry step that can be gated on change management approval in regulated industries.

## Anti-Patterns

1. **Storing credentials in Custom Settings or Custom Metadata** — Secrets stored in platform-queryable fields are readable by anyone with object access or a query tool. SOQL access to credentials is a critical security exposure. Custom Metadata values appear in managed packages and version control. Always use Named Credentials + External Credentials for outbound auth secrets.

2. **Using Per User principals for async Apex callouts** — Per User principals require a Salesforce user to have completed an OAuth authorization flow. Headless async contexts (batch, scheduled, future methods) run without an interactive user who has completed that flow, causing callouts to fail. Use Named Principal for all async integration patterns.

3. **Hardcoding Named Credential names as string literals scattered across Apex classes** — `callout:MyNC` references spread across the codebase make credential renames or environment-specific overrides brittle. Centralize Named Credential names as constants in a dedicated integration utility class so changes require a single edit point.

4. **Deploying Named Credentials without a post-deployment credential-entry runbook** — Assuming deployment alone is sufficient causes integrations to fail silently in target environments. Every deployment pipeline involving Named Credentials must document and enforce the manual vault re-entry step.

## Official Sources Used

- Named Credentials Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_namedcredential.htm (metadata types, deployment behavior, ExternalCredential metadata shape)
- Apex Developer Guide: Named Credentials — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm (callout syntax, merge field behavior in Apex)
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm (REST API integration context)
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html (outbound integration pattern selection, synchronous vs async tradeoffs)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Security and Operational Excellence pillar framing)
