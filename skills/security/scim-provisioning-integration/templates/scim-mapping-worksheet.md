# SCIM Mapping Worksheet

## Source Of Truth

- IdP:
- Directory upstream (HR? IT?):
- Mixed workforce? (separate tenants for contractors/partners):

## Attribute Mapping

| SCIM Attribute | Salesforce User Field | Transform |
|---|---|---|
| `userName` | `Username` |   |
| `emails[primary].value` | `Email` |   |
| `name.givenName` | `FirstName` |   |
| `name.familyName` | `LastName` |   |
|   |   |   |

## Group → Entitlement Mapping

| IdP Group | Maps To | Requires PSL? | Owner |
|---|---|---|---|
|   |   |   |   |

## Profile Strategy

- Default profile:
- Rationale (why not map profile per group):

## Deprovisioning Runbook

- [ ] Freeze user (instant).
- [ ] Revoke OAuth tokens for connected apps.
- [ ] Reassign ownership: cases / opps / accounts / queues / scheduled jobs.
- [ ] SCIM `active=false`.
- [ ] Confirm license released.

## SLA

- Deactivation SLA:
- Monitoring dashboard:
- Alerting thresholds:
