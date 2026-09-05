# Auth Integration Template

Fill this before enabling any new connected app, External Client App, or outbound authenticated
integration. Every row maps to a field in `references/metadata-examples.md` or to a question in
`SKILL.md`. Replace the bracketed guidance with real values; a bracket left in place is an
unanswered design question, not a formatting artefact.

The worked example in each row is a headless billing sync — replace it, don't copy it.

---

## Integration Summary

| Property | Value |
|----------|-------|
| Integration name | `Billing_Sync_JWT` — the metadata `fullName`, not a prose label |
| Direction | Into Salesforce / Out of Salesforce / User-delegated — pick one; two directions means two artefacts |
| Owner | Named person and team accountable for revoke and rotate |
| Business purpose | One sentence a non-admin can read a year from now |
| Data classification | Public / Internal / Confidential / Restricted — drives IP and session policy |
| Systems and environments | Which external system, which orgs (DEV / UAT / PROD) |

## Auth Design

| Item | Value |
|------|-------|
| Auth flow | JWT bearer / Client credentials / Web server (auth code + PKCE) / Named Credential outbound |
| Container | Connected app (existing / package-delivered) or External Client App (net-new in Spring '26+) |
| Metadata files | e.g. `connectedApps/Billing_Sync_JWT.connectedApp-meta.xml`, or the four-file ECA set |
| Named Credential / External Credential | Only for outbound; name both, or write "n/a — inbound only" |
| Integration user or principal | Dedicated user; for client credentials it must hold **API Only** |
| Required scopes | The minimum enum values, e.g. `Api`, `RefreshToken`. Justify any use of `Full` |
| Pre-authorization | `isAdminApproved` true plus the exact `permissionSetName` / `profileName` that ships in the same deploy |
| Certificate | For JWT bearer: which certificate, issued by whom, expiring when |

## Environment and Security Controls

| Control | Decision |
|---------|----------|
| DEV endpoint/auth config | Endpoint and app name in DEV; note that consumer keys are per-org |
| UAT endpoint/auth config | Same for UAT |
| PROD endpoint/auth config | Same for PROD |
| Consumer key / secret custody | Which vault or secret store holds each org's pair, and who can read it |
| IP relaxation | `ENFORCE` / `ENFORCE_RELAXREFRESH` / `BYPASS_2FACTOR` / `BYPASS` — with the reason |
| Allowed IP ranges | Start–end pairs the caller actually egresses from, or "caller cannot enumerate" |
| Refresh token policy | Explicit value, e.g. `specific_inactivity:7:DAYS`. `infinite` needs a written justification |
| Session policy | `sessionTimeout`, and whether High Assurance applies |
| Secret or certificate rotation owner | Person, cadence, and the calendar entry that triggers it |
| Revoke runbook location | Link to the runbook, and the date it was last executed for real |

## Monitoring

| Signal | Decision |
|---|---|
| Auth failure alerting | Where failures surface and who is paged |
| Token or certificate expiry monitoring | What watches the certificate expiry date and how far ahead it warns |
| Usage review cadence | How often `ConnectedApplication` / `OauthToken` are reviewed, and by whom |
| Incident escalation path | First responder, then owner, then vendor contact |

## Pre-Deploy Checklist

- [ ] `python3 scripts/check_connected_auth.py --manifest-dir force-app/main/default` — zero ERRORs, every WARN justified above
- [ ] `isAdminApproved` is paired with a real `permissionSetName` or `profileName` in the same file
- [ ] Every `callbackUrl` value is `https://`
- [ ] `refreshTokenPolicy` (or `refreshTokenPolicyType` + period + unit) is set deliberately, not left at the default
- [ ] Consumer key and secret recorded against the target org, outside source control
- [ ] `ExtlClntAppGlobalOauthSettings` (if ECA) is excluded from the repo
- [ ] `sf project deploy start -x manifest/package.xml --dry-run` passes

## Post-Deploy Verification

- [ ] `ConnectedApplication` query returns `OptionsAllowAdminApprovedUsersOnly = true` for this app
- [ ] `RefreshTokenValidityPeriod` and `OptionsRefreshTokenValidityMetric` match the intended policy
- [ ] `OauthToken` query (run as a user with Customize Application) shows only expected principals
- [ ] Revoke tested and the integration recovered
- [ ] Rotation rehearsed, or a dated ticket exists to rehearse it
