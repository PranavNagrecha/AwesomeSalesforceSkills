# Well-Architected Notes — Integration User Management

## Relevant Pillars

- **Security** — Dedicated integration users with API-only profiles and least-privilege permission sets limit the blast radius of compromised credentials. The Minimum Access - API Only Integrations profile ensures that even with valid credentials, an attacker cannot access the Salesforce UI.
- **Operational Excellence** — Named, documented integration users per integration system enable rapid incident response (disable a single user to cut off a compromised integration without affecting others), clear access audit trails, and predictable quarterly access reviews.

## Architectural Tradeoffs

**One integration user vs. one per integration system:** A single "integration user" shared across all integrations creates a single point of failure (disabling it affects all integrations), makes audit logs uninterpretable (all API calls look the same), and makes least-privilege impossible (the user needs all permissions any integration needs). One integration user per system is the minimum; one per integration function is preferred for complex deployments.

**Username-password OAuth vs. JWT bearer flow:** Username-password flows are simpler to set up but send credentials over the network and remain subject to the profile's password policy, so a password expiry setting can lock an unattended integration out on a schedule nobody is watching. JWT bearer flow uses a certificate pair (private key on the integration server, public key in the connected app) and never sends credentials — there is nothing to rotate, expire, or leak. For all production integrations, JWT bearer flow is the recommended authentication pattern, with one condition attached: it has no user approval step, so a `HIGH_ASSURANCE` session level on the profile or a `RaiseSessionLevel` connected-app policy blocks it outright (`api_meta.txt` L35826–35836).

## Anti-Patterns

1. **Admin profile for integration users** — Granting System Administrator or cloned admin profiles to avoid permission configuration. Creates severe least-privilege violations and enables UI login capability for service accounts.

2. **Shared integration user across multiple systems** — Using a single "IntegrationUser@org.com" for all integrations. Disabling it breaks all integrations simultaneously; audit logs are uninterpretable; permission sets must cover all integration needs.

3. **Blaming org-wide MFA for a blocked integration user** — org-wide MFA enforcement is scoped to direct UI logins (`api_meta.txt` L126248–126252) and an API-only user has no UI login to challenge, so the waiver is not part of a working setup. Time spent granting it is time not spent on the four gates that do block API logins: profile IP ranges, login hours, `requiredSessionLevel`, and the connected app's session policy.

## Official Sources Used

- Metadata API Developer Guide — `PermissionSet` (`license` supersedes the deprecated `userLicense` from API v38.0; `hasActivationRequired`; "if a permission isn't specified for a deployment, it's disabled" from v40.0) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `Profile`, `ProfileLoginHours`, `ProfileLoginIpRange` (profile deploys overlay rather than replace, so disabled permissions must be written out explicitly; login-hour minutes must be divisible by 60; an empty `loginHours` tag is required to remove prior restrictions) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `ProfileSessionSetting`, `SessionSecurityLevel`, `ConnectedAppSessionPolicy` (High Assurance blocks API logins on flows without a user approval step, which is why an integration profile stays at `STANDARD`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `ConnectedApp` and `SecuritySettings` (`oauthClientCredentialUser` "must have the API Only permission"; `ipRelaxation` `ENFORCE` is what makes profile IP ranges apply to app traffic; `enableMFADirectUILoginOptIn` is scoped to direct UI logins) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference for the Salesforce Platform — `LoginHistory` (the filterable-field list that excludes `Status` and `SourceIp`; the `LoginType` and `LoginSubType` picklist values used for monitoring) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference for the Salesforce Platform — `User`, `UserLicense`, `PermissionSet`, `SetupAuditTrail`, `EventLogFile` (profile change implies license change; `LastLoginDate` 60-second throttle; username uniqueness across all orgs; `UsedLicenses` not filterable from v64.0) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce Developer Limits and Allocations Quick Reference — API Request Limits and Allocations ("Limits and allocations are not on a per-user basis"; 25 concurrent long-running inbound requests for production orgs and sandboxes) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- REST API Developer Guide — Limit Info Header and status codes (`Sforce-Limit-Info: api-usage` reports org-level usage; HTTP 403 with `REQUEST_LIMIT_EXCEEDED`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
- Give Integration Users API Only Access (the API-only access model for integration users) — https://help.salesforce.com/s/articleView?id=sf.integration_user_api_only_access.htm&type=5
- Platform Integration User (the dedicated integration user license and its base profile) — https://help.salesforce.com/s/articleView?id=sf.sf_platform_integration_user.htm&type=5
- Invoke REST APIs with the Salesforce Integration User and OAuth Client Credentials (client-credentials execution user pattern) — https://developer.salesforce.com/docs/apis/rest/en/invoke-rest-apis-integration-user.html
- Salesforce Security Guide — Monitor Login History (Setup-side login monitoring for integration users) — https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/salesforce_security_guide_login_history.htm
