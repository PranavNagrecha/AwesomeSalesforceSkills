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
- Sibling skill — `skills/security/oauth-flows-and-connected-apps/SKILL.md` (when one exists)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
