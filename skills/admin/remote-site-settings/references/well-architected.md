# Well-Architected Notes — Remote Site Settings and CSP Trusted Sites

## Relevant Pillars

- **Security** — Remote Site Settings and CSP Trusted Sites are platform-enforced security boundaries. Remote Site Settings prevent Apex from calling arbitrary external URLs, limiting the blast radius of compromised code. CSP prevents Lightning components from loading external scripts that could enable XSS attacks.
- **Reliability** — Including Remote Site Settings in every Change Set or deployment package that includes the dependent Apex code prevents the most common deployment-related callout failures.

## Architectural Tradeoffs

**Remote Site Settings vs. Named Credentials:** Remote Site Settings require managing credentials separately (in the Apex code or a Custom Setting). Named Credentials combine the URL allowlist with credential storage in a single, Salesforce-managed configuration. For any integration requiring authentication, Named Credentials are the preferred approach — they move credentials out of code and support certificate-based authentication. Remote Site Settings are appropriate when the external service requires no authentication or when Named Credentials are not supported for the authentication scheme.

**Broad domain vs. specific URL:** A Remote Site Setting for `https://api.example.com` covers all paths under that domain. This is convenient but over-permissive if the Apex code only calls one specific path. Specific URL entries reduce surface area but require updates when new paths are added. For external services where the full URL surface is known and stable, specific entries are preferred. For services with many endpoints, the domain-level entry is practical.

## Anti-Patterns

1. **Adding endpoint to CSP Trusted Sites to fix Apex callout** — The most common misdirection in integration troubleshooting. CSP controls browser-side resource loading; Apex callouts are server-side. This action is harmless (the CSP entry doesn't hurt) but does not fix the callout failure. The fix is always Remote Site Settings for Apex callouts.

2. **Omitting Remote Site Settings from Change Sets** — Deploying Apex callout code without including the dependent Remote Site Settings in the Change Set. Apex deploys successfully; callouts immediately fail in production. Always verify Remote Site Settings are in the Change Set.

3. **Using Remote Site Settings instead of Named Credentials for authenticated callouts** — Storing credentials in Apex code or Custom Settings when Named Credentials would centralize and secure credential management. Named Credentials manage the URL allowlist internally — the associated Remote Site Setting is not required when using Named Credentials.

## Official Sources Used

- Adding Remote Site Settings — Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_remote_site_settings.htm
- RemoteSiteSetting — Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_remotesitesetting.htm
- Content Security Policy (CSP) — Security for Lightning Components — https://developer.salesforce.com/docs/atlas.en-us.lightning.meta/lightning/security_csp.htm
- Manage CSP Trusted Sites — Salesforce Help — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm&type=5
