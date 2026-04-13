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

## MFA Configuration

**Org MFA enforcement status:** [ ] Not enforced  [ ] Enforced

If enforced:
- [ ] MFA waiver configured via permission set
- [ ] OR JWT bearer flow used (inherently MFA-resistant, preferred)

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
- [ ] MFA challenge does not appear during authentication

## Monitoring

- [ ] LoginHistory monitoring configured
- [ ] Periodic review scheduled (quarterly recommended)
- [ ] Alert configured for failed login attempts from unexpected IPs

## Documentation

- [ ] Integration user details documented in runbook
- [ ] Permission set contents documented with justification for each permission
- [ ] MFA waiver status documented
- [ ] Quarterly access review date set

## Notes

(Record any deviations and justifications.)
