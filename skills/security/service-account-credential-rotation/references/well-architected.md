# Well-Architected Notes — Service Account Credential Rotation

## Relevant Pillars

- **Security** — rotation bounds the blast radius of any credential leak.
- **Reliability** — zero-downtime patterns prevent rotation-induced outages.
- **Operational Excellence** — detector + runbook + cadence make rotation predictable.

## Architectural Tradeoffs

- **Aggressive cadence vs operational cost:** short cadences raise cost; long cadences widen leak exposure. Tie cadence to the credential's blast radius.
- **Dual-credential grace window vs coordinated cutover:** dual-credential is always safer but not every credential type supports it.
- **Vault-first vs platform-first storage:** vault-first enables rotation without consumer code change but requires a vault; platform-first is simpler for smaller orgs.

## Anti-Patterns

1. `PasswordNeverExpires = true` on service accounts.
2. Rotating without a verification step; silently broken integrations discovered days later.
3. No inventory — relying on "we'll know when it breaks."

## Official Sources Used

- Connected App management — https://help.salesforce.com/s/articleView?id=sf.connected_app_manage.htm
- JWT Bearer Flow — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm
- Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Salesforce Well-Architected Security — https://architect.salesforce.com/docs/architect/well-architected/trusted/secure
