# Well-Architected Notes — Service Account Credential Rotation

## Relevant Pillars

- **Security** — rotation bounds the blast radius of any credential leak.
- **Reliability** — zero-downtime patterns prevent rotation-induced outages.
- **Operational Excellence** — detector + runbook + cadence make rotation predictable.

## Architectural Tradeoffs

- **Aggressive cadence vs operational cost:** short cadences raise cost; long cadences widen leak exposure. Tie cadence to the credential's blast radius.
- **Dual-credential grace window vs coordinated cutover:** dual-credential is safer where it exists, but a connected app has one `certificate` (api_meta 264 L37419) and its metadata `consumerSecret` can't be edited after save (L37441-37443), so cutover is the default for those.
- **Vault-first vs platform-first storage:** vault-first enables rotation without consumer code change but requires a vault; platform-first is simpler for smaller orgs.

## Anti-Patterns

1. The Password Never Expires permission on a service account's profile or permission set (secguide 262 L6398).
2. Rotating without a verification step; silently broken integrations discovered days later.
3. No inventory — relying on "we'll know when it breaks."

## Official Sources Used

- Metadata API Developer Guide (264) — `ConnectedAppOauthConfig.certificate` single PEM string (api_meta 264 L37419) and `consumerSecret` not editable after save (L37429-37449); `refreshTokenPolicy` values and default (L37818-37842); `isRefreshTokenRotationEnabled` (L37538-37552).
- Metadata API Developer Guide (264) — External Client App `certificate` enables JWT bearer (api_meta 264 L67151-67155) and `shouldRotateConsumerSecret` replaces the secret on deploy (L67305-67311); external credential refresh on 401 and `AdditionalRefreshStatusCode` (L66295-66298).
- Metadata API Developer Guide (264) — password policy `expiration` values and default (api_meta 264 L129594-129601); profile `passwordExpiration` 0 = never (L101392-101394).
- Salesforce Security Guide (262) — Password Never Expires as a user permission a policy can block in a permission set or profile (secguide 262 L6383, L6398); Object Reference (264) — `User.PasswordExpirationDate` (obj 264 L298549-298555); Platform Events (264) — `PasswordNeverExpires` permission API name (platform_events 264 L25315).
- Not corpus, used only for claims marked UNVERIFIED: Connected App management — https://help.salesforce.com/s/articleView?id=sf.connected_app_manage.htm ; JWT Bearer Flow — https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_jwt_flow.htm ; Named Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
