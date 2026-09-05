# Integration Admin: Connected Apps — Work Template

Use this template when configuring or auditing a Connected App for an integration.

## Scope

**Skill:** `integration-admin-connected-apps`

**Connected App name:** (fill in)

**Integration type:** [ ] Server-to-server (JWT/OAuth Client Credentials)  [ ] User-context (OAuth Web Server)  [ ] Legacy (username/password)

**Integration user:** (fill in username)

## OAuth Policy Configuration

| Setting | Current Value | Required Value |
|---|---|---|
| Permitted Users | | [ ] AllUsers / [ ] AdminApprovedUsers |
| IP Relaxation | | [ ] Enforce / [ ] Relax / [ ] Relax with second factor |
| Refresh Token Policy | | [ ] Immediate / [ ] N days / [ ] Inactivity |

## Pre-Authorization Assignment (if AdminApprovedUsers)

- [ ] Connected app assigned to Profile: ___
- [ ] Connected app assigned to Permission Set: ___
- [ ] Tested authentication as integration user — SUCCEEDS

## Scope Review

| Scope | Granted? | Required? | Notes |
|---|---|---|---|
| api | | | |
| refresh_token | | | |
| offline_access | | | |
| full | | Should be NO for integrations | Overly broad |

## IP Configuration

**Integration server IP range:** ___

- [ ] Integration user's profile trusted IP ranges include the integration server IPs
- [ ] OR IP Relaxation set to Relax (document justification)

## Monitoring Setup

- [ ] EventLogFile monitoring configured (requires Event Monitoring add-on)
- [ ] Monitoring schedule: (daily / weekly)
- [ ] Alert configured for authentication failures

## Post-Configuration Testing

- [ ] OAuth token issuance succeeds as integration user
- [ ] API calls succeed with issued token
- [ ] Token refresh succeeds (if refresh tokens used)
- [ ] IP restrictions verified (if enforced)

## Quarterly Audit Items

- [ ] Review Connected App OAuth Usage for orphaned/inactive sessions
- [ ] Review uninstalled apps still in use (September 2025 blocking policy)
- [ ] Confirm no integration depends on "Use Any API Client" to self-authorize an uninstalled app (blocked since the week of December 8, 2025 when API Access Control is enabled)
- [ ] Review Refresh Token Policy — tokens older than policy window should be revoked

## Revoke and Rotate Runbook

**Revoke one grant** (there is no DML delete on `OauthToken` — supported calls are
`describeSObjects()` and `query()` only):

1. As a user with **Customize Application**: `SELECT AppName, UserId, LastUsedDate, DeleteToken FROM OauthToken WHERE AppName = '___'`
2. Call `https://<MyDomain>.my.salesforce.com/services/oauth2/revoke?token=<DeleteToken>`
3. Re-run step 1 and confirm the row is gone.

- [ ] Rehearsed once in a sandbox on: ______  (the integration recovered: Y / N)

**Org-wide stop** (ends current sessions): Connected Apps OAuth Usage -> **Block**, or deploy
`sessionPolicy/policyAction` = `Block`.

**Rotate the key/secret** — pick one and record it:

- [ ] Connected app: `consumerKey` cannot be edited after save -> replacement app + caller cutover. Change window owner: ______
- [ ] External Client App: set `shouldRotateConsumerKey` / `shouldRotateConsumerSecret` to `true` and deploy with the ignore-warnings attribute, then set both back to `false`.

**Key/secret custody:** which system holds the pair, and who owns it? ______

## Periodic Review

- [ ] App added to `templates/connected-app-review-checklist.yaml` with `owner`, `last-reviewed`, `token-count-query-run`
- [ ] Review cadence set inside 180 days (SetupAuditTrail retains Setup changes for at least that long)
- [ ] `python3 scripts/check_integration_admin_connected_apps.py --manifest-dir <dir>` exits 0

## Notes

(Record any deviations from standard configuration and justification.)
