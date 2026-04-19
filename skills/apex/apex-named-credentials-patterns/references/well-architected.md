# Well-Architected Notes — Apex Named Credentials Patterns

## Relevant Pillars

- **Security** — Named Credentials are the primary Security pillar control for outbound Apex callouts. Credentials (OAuth tokens, passwords, API keys) stored in the platform's Protected credential vault are encrypted at rest and not accessible to Apex code, Setup UI export, or data export tools. Using Named Credentials instead of Custom Labels, Custom Settings, or hardcoded strings directly satisfies the Salesforce Well-Architected principle of not storing secrets in accessible org data layers.
- **Reliability** — Named Credentials participate in the platform's OAuth token refresh flow, reducing callout failures due to expired tokens in long-running integrations. Per-user token checks via `UserExternalCredential` let applications fail fast with a meaningful prompt rather than producing an opaque HTTP 401. Setting an explicit callout timeout (rather than relying on the 10-second default) is a Reliability control.
- **Operational Excellence** — Named Credentials are environment-aware: different endpoint URLs and auth configs can be deployed per sandbox and production. This avoids hardcoded environment-switching logic in Apex and makes deployment pipelines simpler. Named Credentials are deployable via Metadata API and Salesforce CLI.

## Architectural Tradeoffs

**Legacy model vs. enhanced model:** The legacy model is simpler to configure but couples endpoint and auth in one record — changing the auth type requires replacing the Named Credential and updating all Apex references to any changed API name. The enhanced model's separation of External Credential and Named Credential allows multiple Named Credentials (for different endpoints) to share one External Credential (one auth config). For integrations with multiple related API endpoints sharing the same OAuth app, the enhanced model is the correct long-term architecture despite the additional setup complexity.

**Per-user vs. named principal auth:** Per-user auth (each Salesforce user authenticates individually) provides stronger data isolation and audit trails but requires per-user OAuth flows, more complex UI handling for the auth prompt, and `UserExternalCredential` queries before callouts. Named principal auth (all users share one credential) is operationally simpler but means all API activity in the external system appears under one identity — data access controls in the external system cannot distinguish Salesforce users.

## Anti-Patterns

1. **Storing credentials in Custom Labels or Custom Settings** — These fields are visible in the Setup UI, included in data exports, and not encrypted by the credential vault. Any Apex security scan will flag these. Named Credentials exist specifically to replace this pattern. The Well-Architected Security pillar explicitly calls out credential storage in accessible fields as a risk.

2. **Bypassing Named Credentials for "simpler" one-off callouts** — Developers occasionally hardcode the endpoint URL and set the `Authorization` header manually in Apex for what they assume is a temporary integration. These "temporary" callouts frequently remain in production indefinitely, accumulating technical security debt. Every outbound callout should use a Named Credential from day one.

3. **Using Named Credentials with the Continuation framework** — The `callout:` prefix is incompatible with Continuation. Developers who discover this limitation sometimes refactor to hardcode the endpoint URL in the Continuation setup, bypassing the Named Credential and all its security controls. The correct architectural fix is to move the callout to a Queueable job, not to abandon Named Credentials.

## Official Sources Used

- Apex Developer Guide — Named Credentials as callout endpoints: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm
- Named Credentials Developer Guide — enhanced model, External Credentials, principal types, UserExternalCredential: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_namedcredential.htm
- Apex Developer Guide — callout limits and timeout: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_timeouts.htm
- Salesforce Well-Architected Overview — Security pillar: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
