# Well-Architected Notes — Remote Site Settings and CSP Trusted Sites

## Relevant Pillars

- **Security** — Remote Site Settings and CSP Trusted Sites are platform-enforced security boundaries. Remote Site Settings prevent Apex from calling arbitrary external URLs, limiting the blast radius of compromised code. CSP prevents Lightning components from loading external scripts that could enable XSS attacks.
- **Reliability** — Including Remote Site Settings in every Change Set or deployment package that includes the dependent Apex code prevents the most common deployment-related callout failures.

## Architectural Tradeoffs

**Remote Site Settings vs. Named Credentials:** Remote Site Settings require managing credentials separately (in the Apex code or a Custom Setting). Named Credentials combine the URL allowlist with credential storage in a single, Salesforce-managed configuration. For any integration requiring authentication, Named Credentials are the preferred approach — they move credentials out of code (a named credential "specifies the URL of a callout endpoint and its required authentication parameters in one definition", apexdev 264 L34761-34762); the legacy `certificate` field supplies a client certificate for two-way SSL but is deprecated in API 56.0 (api_meta 264 L92742-92749). Remote Site Settings are appropriate when the external service requires no authentication or when Named Credentials are not supported for the authentication scheme.

**Broad domain vs. specific URL:** UNVERIFIED (2026-10-21): that a Remote Site Setting for `https://api.example.com` covers all paths under that domain — the corpus does not describe URL matching, though its sample registers a URL with a path (api_meta 264 L106556). A domain entry is convenient but over-permissive if the Apex code only calls one specific path. Specific URL entries reduce surface area but require updates when new paths are added. For external services where the full URL surface is known and stable, specific entries are preferred. For services with many endpoints, the domain-level entry is practical.

## Anti-Patterns

1. **Adding endpoint to CSP Trusted Sites to fix Apex callout** — CSP controls browser-side resource loading; Apex callouts are server-side. The Trusted URL entry does not fix the callout failure. The fix is a Remote Site Setting, or a named credential endpoint (apexdev 264 L34758-34762).

2. **Omitting Remote Site Settings from Change Sets** — Deploying Apex callout code without including the dependent Remote Site Settings in the Change Set. Apex deploys successfully; callouts fail in production because the site is not registered there. Always verify Remote Site Settings are in the Change Set (auto-inclusion UNVERIFIED (2026-10-21), Help-only).

3. **Using Remote Site Settings instead of Named Credentials for authenticated callouts** — Storing credentials in Apex code or Custom Settings when Named Credentials would centralize and secure credential management. Named Credentials manage the URL allowlist internally — the associated Remote Site Setting is not required when using Named Credentials.

## Official Sources Used

- Adding Remote Site Settings — Apex Developer Guide: registration required before any Apex callout (apexdev 264 L34758-34759), Quick Find path (L34765), named credential exemption (L34761) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_remote_site_settings.htm
- RemoteSiteSetting — Metadata API Developer Guide: scope incl. Visualforce and s-controls (api_meta 264 L106497-106498), `.remoteSite` file (L106503-106504), `disableProtocolSecurity` meaning (L106516-106521), Required `disableProtocolSecurity`/`isActive`/`url` (L106516, L106542-106545) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_remotesitesetting.htm
- CspTrustedSite — Metadata API Developer Guide: Trusted URL, formerly CSP Trusted Sites (api_meta 264 L41578-41582); `isApplicableTo…` flags with no script-src (L41687-41727).
- Content Security Policy (CSP) — Security for Lightning Components — https://developer.salesforce.com/docs/atlas.en-us.lightning.meta/lightning/security_csp.htm
- Second-Generation Managed Packages: Remote Site Setting not updated on upgrade; Remote Site Name not editable (pkg2 264 L14550, L14572).
- Manage CSP Trusted Sites — Salesforce Help (not corpus) — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm&type=5
