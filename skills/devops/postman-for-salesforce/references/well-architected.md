# Well-Architected Notes — Postman for Salesforce

## Relevant Pillars

- **Security** — Postman setups handle long-lived OAuth credentials, JWT private keys, and access tokens that grant broad API access. Mishandled, they become an attack surface: leaked client secrets in shared workspaces, JWT keys committed to source control, access tokens exposed in screenshots. The Vault-vs-environment-variable distinction is the central security primitive.
- **Operational Excellence** — A team-shared Postman collection is part of the operational toolchain. Drift between developers' local copies, undocumented setup steps, and unstable variable references all degrade incident-response velocity. Source-controlled collection JSON, a setup runbook in the collection itself, and explicit environment-per-org separation are the levers.
- **Reliability** — Pre-request scripts that re-auth on every request hit per-user login limits during normal use. Hard-coded URLs break on sandbox refresh. Multi-step chained flows that don't handle terminal-state polling correctly hang or report success on a still-running job.

## Architectural Tradeoffs

**Personal workspace vs shared workspace vs source-controlled JSON.** Personal is fastest to start. Shared eliminates onboarding friction. Source-controlled is the only auditable form. Most mature teams use both shared workspace (live editing) *and* source-controlled exports (audit trail) — exporting on a regular ritual (post-merge, weekly).

**Web Server flow vs JWT bearer for developer use.** Web Server flow is one-click in Postman's OAuth helper but requires manual token refresh when the token expires (Postman's helper doesn't refresh transparently). JWT bearer is one-time setup of the private key + Connected App, then the pre-request script refreshes silently. JWT wins for any team that uses Postman more than weekly.

**Vault per-user vs synced environment secrets.** Vault keeps each developer's credentials local — required for least-privilege models where each developer authenticates with their own Connected App or service account. Synced secrets are simpler for one-shared-credential teams but every workspace member has the same access. Don't mix the two within one collection.

**Collection runner with delay vs explicit poll loops.** The runner's delay setting paces the whole collection; explicit `postman.setNextRequest(pm.info.requestName)` paces just the polling step. Explicit is preferred when one step needs to poll for minutes while others run in seconds; delay is fine for lightweight collections.

**Postman vs `sf api request rest` vs curl/HTTPie.** Postman wins on visibility (response body inspection, response visualizers, history). CLI tools win on scriptability and CI integration. Don't try to make Postman work as a CI tool — use Newman (the Postman CLI runner) for that, but accept that maintaining Newman runs in CI plus interactive Postman use creates two surfaces to keep aligned.

## Anti-Patterns

1. **Re-authenticating on every request.** Multiplies request count, exhausts per-user login limits, and slows down every interactive use. Cache the token by expiry; refresh only when nearing expiration.
2. **Hard-coded `instanceUrl` and `apiVersion`.** Sandbox refreshes, My Domain rebrands, and API version drift all break hard-coded URLs. Always use environment variables.
3. **Synced environment secrets for per-developer credentials.** Putting a JWT private key into a "secret" environment variable in a shared workspace exposes it to every workspace member. Use Vault for per-developer keys; synced env vars are for shared-config items only.
4. **Skipping `pm.test` assertions.** A 200 response body with a malformed payload looks like success in Postman's UI. Without assertions, schema drift goes unnoticed for days.
5. **Letting collections drift from source control.** Postman auto-syncs to the user's account. Without a regular export-and-commit ritual, the source-controlled JSON ages and divergence accumulates. Bake the export into the team's PR-merge or weekly checklist.
6. **Mixing collection-level Auth and manual `Authorization` header in pre-request script.** Two auth-injection paths compete; bug surface is the merge of both. Centralize on one.
7. **Using Postman as a deployment tool.** Postman is for *exercising* APIs. Deploying metadata, running tests, or executing user-managed releases belongs in `sf` CLI, DevOps Center, or a CI pipeline — Postman has no audit trail or rollback story for those use cases.

## Official Sources Used

- Salesforce Developers — Postman Quick Start (links to the official Salesforce Postman collection): https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/postman.htm
- REST API Developer Guide (composite, sObjects, query) — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
- OAuth 2.0 JWT Bearer Flow — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm
- OAuth 2.0 Web Server Flow — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_web_server_flow.htm
- OAuth 2.0 Client Credentials Flow — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_client_credentials_flow.htm
- Connected App Authentication Settings (IP Relaxation, callback URLs) — https://help.salesforce.com/s/articleView?id=sf.connected_app_continuous_ip.htm
- Salesforce Well-Architected — Trusted (security pillar) — https://architect.salesforce.com/well-architected/trusted/secure
