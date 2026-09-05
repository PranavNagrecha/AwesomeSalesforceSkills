# Well-Architected Notes — Connected App Troubleshooting

## Relevant Pillars

- **Security** — Refresh Token Policy "Valid until revoked"
  paired with credential rotation is the standard server-to-server
  pattern; alternatives produce silent failures or excessive
  re-authorization friction.
- **Reliability** — `invalid_grant` is the most-overloaded OAuth
  error; Login History is the disambiguation source. Triage
  always starts there.
- **Operational Excellence** — Connected App settings are
  metadata; deploy them, but verify per-environment Consumer
  Keys and re-fetch after deploy.

## Architectural Tradeoffs

- **Refresh Token Policy "Valid until revoked" vs sliding /
  hard expiry.** Valid-until-revoked is operationally simpler;
  expiry policies force periodic re-authorization at the cost
  of integration uptime.
- **IP Relaxation: Enforce vs Relax.** Enforce is tighter but
  cloud-incompatible. Relax + tight user permissions is the
  standard cloud pattern.
- **Permitted Users: Self-authorize vs Admin-approved.**
  Self-authorize is friction-free for users; admin-approved
  controls who can access. Server-to-server should always be
  admin-approved with a dedicated integration user.

## Anti-Patterns

1. **Default Refresh Token Policy** for server-to-server.
2. **`username-password` OAuth flow** for new integrations
   (deprecated).
3. **Hardcoded Consumer Key / Secret / Refresh Token** in source.
4. **Missing user assignment** to admin-approved Connected App.
5. **`redirect_uri` near-misses** (trailing slash differences).
6. **JWT `sub` = Email instead of Username**.

## Official Sources Used

- Connected App OAuth Settings — https://help.salesforce.com/s/articleView?id=sf.connected_app_overview.htm&type=5
- Refresh Token Policies — https://help.salesforce.com/s/articleView?id=sf.connected_app_create_api_integration.htm&type=5
- IP Relaxation in Connected Apps — https://help.salesforce.com/s/articleView?id=sf.connected_app_continuous_ip.htm&type=5
- OAuth Authorization Flows — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_flows.htm&type=5
- LoginHistory Object — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_loginhistory.htm
- JWT Bearer Flow — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm&type=5
- Sibling skill — `skills/integration/oauth-flows-and-connected-apps/SKILL.md`
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Metadata API Developer Guide, `ConnectedAppOauthPolicy` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the four `refreshTokenPolicy` values and the four `ipRelaxation` values, both Required; the `zero` semantics behind gotcha 1 and runbook row 4)
- Metadata API Developer Guide, `ConnectedAppOauthConfig` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`isAdminApproved` and its profile/permission-set precondition; `isConsumerSecretOptional` vs `isSecretRequiredForRefreshToken` behind gotcha 14; `isRefreshTokenRotationEnabled` behind runbook row 6; `consumerSecret` not returned in Metadata API requests)
- Metadata API Developer Guide, `ConnectedApp` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`permissionSetName` one-per-line, and that an empty string on deployment removes every assignment)
- Object Reference, `LoginHistory` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (the twelve filterable fields; the `LoginSubType` OAuth value list; `Status` documented only as "success or a reason for failure"; `SourceIp` recording the first proxy and not supporting `LIKE`; `ForwardedForIp` not populated for OAuth or SSO logins — gotchas 11 and 12)
- Object Reference, `OauthToken` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (Customize Application gates org-wide visibility, so an empty evidence result from a least-privileged runner proves nothing; `LastUsedDate` and `UseCount` as the "grant existed and was used once" signature)
- Object Reference, `SetupAuditTrail` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (retention of "at least the last 180 days"; `Action` and `DelegateUser` filterable while `Section` and `Display` are not — gotcha 13)
- REST API Developer Guide, Status Codes and Error Responses — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf (401 as an expired or invalid session/OAuth token; 403 as a refusal to check permissions against — the grounding for runbook row 11, and the reason every token-endpoint `error` string in the runbook is marked UNVERIFIED)
- Data Loader Guide, connection configuration — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf (production and test endpoints default to `login.salesforce.com` / `test.salesforce.com` and the recommendation to use My Domain URLs — the sandbox reproduction step)
- Sibling skill — `skills/admin/connected-apps-and-auth/SKILL.md` (artefact choice and the full connected app / ECA file)
- Sibling skill — `skills/admin/integration-admin-connected-apps/SKILL.md` (revocation, rotation, monitoring and the periodic review that follow a diagnosis)
- Sibling skill — `skills/admin/org-setup-and-configuration/SKILL.md` (My Domain sequencing and trusted IP ranges, which the login host and IP branch depend on)
