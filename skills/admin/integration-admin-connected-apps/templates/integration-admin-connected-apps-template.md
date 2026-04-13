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
- [ ] Review Refresh Token Policy — tokens older than policy window should be revoked

## Notes

(Record any deviations from standard configuration and justification.)
