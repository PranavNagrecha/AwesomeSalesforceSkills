# Integration User Management — Work Template

Use this template when setting up or auditing a Salesforce integration user.

## Scope

**Skill:** `integration-user-management`

**Integration system name:** (e.g., MuleSoft, Informatica, Custom ETL)

**Integration user username:** ___@___.com

## Integration User Configuration

| Setting | Required Value | Configured? |
|---|---|---|
| License | Salesforce Integration | [ ] |
| Profile | Minimum Access - API Only Integrations | [ ] |
| Email | Team alias (not individual) | [ ] |
| Active | true | [ ] |

## Login Gates (the four things that actually block an API login)

**Org MFA enforcement status:** [ ] Not enforced  [ ] Enforced — note: this setting is scoped to direct UI logins, so it does not challenge this user's API logins. Do not record an MFA waiver as a setup step.

| Gate | Value recorded | Verified? |
|---|---|---|
| Profile `loginIpRanges` | | [ ] |
| Connected app `ipRelaxation` (`ENFORCE` for the ranges above to apply) | | [ ] |
| Profile `loginHours` (all seven days, or absent) | | [ ] |
| Profile `requiredSessionLevel` (`STANDARD`) | | [ ] |
| Connected-app session policy (`RaiseSessionLevel` must be off) | | [ ] |

**MFA waiver:** [ ] Not applicable — API-only account  [ ] Granted, because this account genuinely logs in through the UI: ___

## Session and Network Restrictions

| Setting | Value recorded | Checked? |
|---|---|---|
| `ProfileSessionSetting.requiredSessionLevel` | must be `STANDARD` — `HIGH_ASSURANCE` blocks JWT and client-credentials logins | [ ] |
| `ProfileSessionSetting.sessionTimeout` | one of 0/15/30/60/90/120/240/480/720/1440 | [ ] |
| `ProfilePasswordPolicy.passwordExpiration` | `0` (never) so an unattended integration is not broken by rotation; forces `passwordHistory` `0` | [ ] |
| Profile `loginIpRanges` | middleware egress range(s), including retry cluster | [ ] |
| Profile `loginHours` | all seven days covered, or absent entirely | [ ] |
| Connected app `ipRelaxation` | `ENFORCE` so the profile IP ranges actually apply | [ ] |

**Checker run:** `python3 skills/admin/integration-user-management/scripts/check_integration_user_management.py --manifest-dir <path>` — exit code: ___

## Permission Set Configuration

| Permission Set Name | Object Permissions Granted | Field Permissions | Assigned? |
|---|---|---|---|
| | | | [ ] |
| | | | [ ] |

**Guiding principle:** Grant only what this specific integration needs. No `Modify All Data` or `View All Data` unless technically required with documented justification.

## Connected App Assignment

- **Connected app name:** ___
- **Permitted Users setting:** [ ] Admin approved users are pre-authorized
- [ ] Connected app assigned to integration user's permission set or profile

## Authentication Configuration

**Authentication flow:** [ ] JWT Bearer (preferred)  [ ] OAuth Client Credentials  [ ] Username-Password (avoid)

For JWT Bearer:
- [ ] Digital certificate uploaded to connected app
- [ ] Private key stored securely (never in code/config files)

## Testing

- [ ] Authentication succeeds via selected flow
- [ ] API call to required objects succeeds
- [ ] UI login is blocked (API-only profile enforced)
- [ ] `LoginHistory.Status` for the test login reads success, and `LoginType` / `LoginSubType` match the configured flow

## Monitoring

- [ ] LoginHistory monitoring configured
- [ ] Periodic review scheduled (quarterly recommended)
- [ ] Alert configured for failed login attempts from unexpected IPs
- [ ] Monitoring query filters only on `UserId` and `LoginTime`; `Status` and `SourceIp` are evaluated client-side
- [ ] Expected `LoginType` / `LoginSubType` for this flow recorded here: ___

## Documentation

- [ ] Integration user details documented in runbook
- [ ] Permission set contents documented with justification for each permission
- [ ] Login gates documented: IP ranges, `ipRelaxation`, login hours, session level
- [ ] Quarterly access review date set

## Notes

(Record any deviations and justifications.)
