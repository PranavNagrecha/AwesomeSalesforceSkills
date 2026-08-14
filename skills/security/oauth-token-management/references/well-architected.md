# Well-Architected Notes — OAuth Token Management

## Relevant Pillars

- **Security** — OAuth tokens are bearer credentials. Shortening access token exposure, narrowing scopes, rotating refresh tokens, and using precise revocation reduce blast radius when clients or secrets leak.
- **Reliability** — Integrations that mishandle refresh rotation or session timeout interactions generate intermittent `invalid_grant` and partial data sync failures that are hard to replay-debug without a token lifecycle model.
- **Performance** — Not the primary pillar here; avoid chatty “ping” APIs used as pseudo health checks for tokens; prefer bounded refresh scheduling driven by real expiry data.
- **Scalability** — Central token services and vaults scale better when each Connected App has explicit refresh policy and rotation semantics documented per consumer.
- **Operational Excellence** — Runbooks should name token types, expected invalidation effects, and verification steps; token incidents are common enough to automate detection of `invalid_grant` spikes per Connected App.

## Architectural Tradeoffs

Long-lived refresh tokens simplify operations but extend compromise windows. Immediate refresh expiry improves credential hygiene but pushes complexity into re-authentication UX or alternate grants such as JWT bearer for headless cases. Refresh token rotation improves replay resistance but demands idempotent, transactional client persistence—middleware must never drop the newest refresh string.

This trade-off is only yours to make for **internal** Connected Apps. For partner-distributed Connected Apps and External Client Apps, Salesforce set a May 11, 2026 compliance deadline for PKCE, Refresh Token Rotation, a 30-day idle refresh token TTL, and a refresh token IP allowlist; PKCE and RTR cannot be disabled once enabled. Design ISV token handling as if rotation and a 30-day idle ceiling are givens, and treat the sequencing as the real decision—an irreversible control enabled before the client persists rotated tokens leaves no way back.

## Anti-Patterns

1. **Bearer token logging** — Logging access or refresh tokens in application logs defeats the purpose of short-lived access tokens and rotation; use correlation IDs instead.
2. **Global Connected App loosening “to fix” one client** — Widening IP relaxation or session timeouts for token symptoms masks the underlying grant or persistence bug.
3. **Skipping sandbox rehearsal for policy changes** — Changing refresh or session policies without a dry run strands production integrations without a tested re-auth path.

## Official Sources Used

- [Manage OAuth Access Policies for a Connected App](https://help.salesforce.com/s/articleView?id=sf.connected_app_manage_oauth.htm&type=5) — session and refresh behavior configured on the app
- [OAuth 2.0 Refresh Token Flow](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_refresh_token_flow.htm&type=5) — how refresh exchanges work at the token endpoint
- [Revoke OAuth Tokens](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_revoke_token.htm&type=5) — programmatic revocation semantics
- [Rotate Refresh Tokens (release notes)](https://help.salesforce.com/s/articleView?id=sf.rn_security_refresh_token_rotation.htm&release=248.0&type=5) — rotation expectations for clients
- [OpenID Connect Token Introspection Endpoint](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oidc_token_introspection_endpoint.htm&type=5) — validating token active state where supported
- [Salesforce Security Guide](https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5) — broader security context for credentials and sessions
- [Integration Patterns — Salesforce Architects](https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html) — how token-heavy integrations fit larger integration topologies
- [Preventing Connections from Anonymizing VPNs, Proxies and High-Risk IP Addresses](https://help.salesforce.com/s/articleView?id=005318944&language=en_US&type=1) — confirms Salesforce-side containment (account frozen, all OAuth refresh tokens revoked, admin email), the November 20, 2025 and April 24, 2026 dates, expansion to all Connected App and API traffic, and that no opt-out or allowlist is documented (verified 2026-08-13)
- [Secure Your Connected Apps and External Client Apps](https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/secure_code_ac_eca.htm) — confirms the May 11, 2026 ISV deadline for PKCE, RTR, 30-day idle refresh token TTL and refresh token IP allowlist; that PKCE and RTR cannot be disabled once enabled; the 256-IP-address cap; and the callback-URL exclusions (verified 2026-08-13)
