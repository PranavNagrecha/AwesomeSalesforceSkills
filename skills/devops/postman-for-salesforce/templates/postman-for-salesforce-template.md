# Postman for Salesforce — Work Template

Use this template when designing or auditing a Postman setup for Salesforce APIs.

## Scope

**Skill:** `postman-for-salesforce`

**Request summary:** (one line — what Postman setup is being built/audited and why)

## OAuth Flow

Pick one (drives the rest of this template):

- [ ] Web Server (interactive developer use, browser available)
- [ ] JWT bearer (unattended, server-side private key)
- [ ] Username-Password (legacy; only for existing setups, not new)
- [ ] Client Credentials (Spring '23+, server-to-server, "Run As" user)

## Connected App Configuration

- App Name: ____
- Consumer Key (clientId): ____
- Callback URL (Web Server only): ____ (`https://oauth.pstmn.io/v1/callback` is the Postman default)
- IP Relaxation: Relax IP restrictions / Enforce IP restrictions
- Run As user (Client Credentials only): ____
- Scopes enabled: api / refresh_token / openid / offline_access / ____

## Environment Plan

One environment per Salesforce org. List each:

| Environment | loginUrl | apiVersion | Run As / sub user | Notes |
|---|---|---|---|---|
| DevSandbox | https://test.salesforce.com | v59.0 |   |   |
| UAT |   |   |   |   |
| Prod | https://login.salesforce.com |   |   |   |

## Vault Keys (per-developer)

For shared workspaces, declare the Vault keys each developer must populate locally:

- [ ] `clientSecret`
- [ ] `jwtPrivateKey` (JWT bearer only; PEM format with literal `\n` line breaks)
- [ ] `password+token` (Username-Password legacy only)

## Pre-Request Script

- [ ] Lives at **collection level**, not duplicated per request
- [ ] Reads `accessToken` and `accessTokenExpiry` from environment first
- [ ] Skips refresh when `Date.now() < accessTokenExpiry - 60000`
- [ ] Sets `accessToken`, `instanceUrl`, `accessTokenExpiry` after refresh
- [ ] Logs failures to `console.error` and rethrows so collection runner reports red
- [ ] (JWT only) `aud` claim is the login URL — NOT the token endpoint

## Collection Structure

Folder per API surface:

- [ ] `Data API` — CRUD on sObjects, SOQL queries
- [ ] `Tooling API` — metadata-shape operations (route through `/tooling/`)
- [ ] `Bulk API 2.0` — chained job lifecycle folder
- [ ] `Connect API` — feeds, communities, social
- [ ] `Composite REST` — composite-graph batched workflows
- [ ] (other): ____

## Per-Request Hygiene

For every request:

- [ ] URL uses `{{instanceUrl}}/services/data/{{apiVersion}}/...` — no hard-coded host or version
- [ ] At least one `pm.test` assertion (status code minimum, body shape ideally)
- [ ] Multi-step chain state uses `pm.collectionVariables.set` (not `pm.variables.set`)
- [ ] Bulk API 2.0 upload step uses `PUT`, not POST/PATCH
- [ ] JSON body uses Raw editor when variables are inside arrays/nested objects

## Setup Runbook

- [ ] "00 — Setup" markdown request at top of collection
- [ ] Lists required environment variables (which are synced, which from Vault)
- [ ] Lists required Connected App configuration
- [ ] Includes a smoke-test request the new joiner runs first

## Source-Controlled Export

- [ ] Collection JSON exported as `.postman_collection.json`
- [ ] Committed to repo
- [ ] Export ritual documented (when it runs — pre-commit, post-merge, weekly)

## Validation

- [ ] `python3 scripts/check_postman_for_salesforce.py --collection <path>` returns 0
- [ ] Full collection run via Postman runner against sandbox passes
- [ ] If used in CI: Newman command works with secrets injected via `--env-var`

## Notes

(Record deviations from the standard patterns and why.)
