# Well-Architected Notes — Named Credentials Setup

## Relevant Pillars

- **Security** — Named Credentials are Salesforce's primary mechanism for securing outbound integration credentials. They prevent secrets from being stored in Apex, Custom Settings, or Custom Metadata where they are readable via SOQL or exportable via packages (UNVERIFIED 2026-10-20: who can read custom settings or metadata values is not stated in the corpus). Credentials are encrypted under org-specific keys (meta 264 L92625-92627); the one-way write model (secrets are not readable back) is UNVERIFIED (2026-10-20). Per User principal type enforces user-level access boundaries on external systems. Permission Set assignments on External Credential principals enforce least-privilege access at the org user level.

- **Operational Excellence** — Separating endpoint configuration (Named Credential URL) from authentication configuration (External Credential) reduces the blast radius of credential rotation. Rotating a client secret or password requires only a Setup UI update to the External Credential vault value — no code change, no deployment. Enhanced Named Credentials also enable one External Credential to back multiple Named Credentials, reducing duplication across many endpoint paths on the same service.

## Architectural Tradeoffs

**Named Principal vs Per User:** Named Principal is operationally simpler — one credential, one rotation event, no user onboarding overhead. Per User adds operational complexity (each user must authorize, re-authorize on token expiry, and be trained to use the per-user authentication page) but is the correct choice when the external service enforces user-level data scoping or audit trails.

**Enhanced vs Legacy:** Enhanced Named Credentials require more configuration steps (two records instead of one) but add the External Credential parameter schema (`AuthHeader`, `HttpHeader`, JWT claims, additional refresh status codes) and reuse of an External Credential across endpoints (UNVERIFIED 2026-10-20). Legacy credentials already support Per User (`principalType` PerUser, meta 264 L92936-92945). For any net-new integration, always use the enhanced model. For legacy migrations, the operational risk is in formula namespaces and callback URL changes — plan carefully.

**Deployment boundaries:** The clean separation between deployable metadata structure and vault-stored secrets is a security feature, not a limitation. It forces a deliberate post-deployment credential entry step that can be gated on change management approval in regulated industries.

## Anti-Patterns

1. **Storing credentials in Custom Settings or Custom Metadata** — Secrets stored in platform-queryable fields are readable by anyone with object access or a query tool (UNVERIFIED 2026-10-20: not stated in the corpus). SOQL access to credentials is a critical security exposure. Custom Metadata values appear in managed packages and version control. Always use Named Credentials + External Credentials for outbound auth secrets.

2. **Using Per User principals for async Apex callouts** — Per User principals require a Salesforce user to have completed an OAuth authorization flow. Headless async contexts (batch, scheduled, future methods) run without an interactive user who has completed that flow, causing callouts to fail (UNVERIFIED 2026-10-20: not in the corpus, see gotchas.md Gotcha 5). Use Named Principal for all async integration patterns.

3. **Hardcoding Named Credential names as string literals scattered across Apex classes** — `callout:MyNC` references spread across the codebase make credential renames or environment-specific overrides brittle. Centralize Named Credential names as constants in a dedicated integration utility class so changes require a single edit point.

4. **Deploying Named Credentials without a post-deployment credential-entry runbook** — Assuming deployment alone is sufficient causes integrations to fail in target environments ("silently" is UNVERIFIED 2026-10-20). Every deployment pipeline involving Named Credentials must document and enforce the manual vault re-entry step.

## Official Sources Used

- Named Credentials Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_namedcredential.htm (metadata types, deployment behavior, ExternalCredential metadata shape)
- Metadata API Developer Guide 264 — `NamedCredential` L92621-93145 (type, fields, parameters, example), `ExternalCredential` L66149-66416, `ExternalAuthIdentityProvider` L65793-65955, `PermissionSetExternalCredentialPrincipalAccess` L97687-97704; Second-Generation Managed Packaging Guide 264 L9543-9574 (packaging, post-install steps); Apex Developer Guide 264 L34727-34831, L34926-34960 (callout:, remote sites, merge fields)
- Apex Developer Guide: Named Credentials — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm (callout syntax, merge field behavior in Apex)
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm (REST API integration context)
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html (outbound integration pattern selection, synchronous vs async tradeoffs)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (Security and Operational Excellence pillar framing)
