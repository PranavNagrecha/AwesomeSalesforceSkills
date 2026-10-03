# Well-Architected Notes: MFA Enforcement Strategy

## Relevant Pillars

- **Security**: MFA enforcement is a foundational **Trusted** control: it reduces credential theft impact, supports least-privilege session establishment, and pairs with SSO and session policies for defense in depth. Official Salesforce security guidance frames MFA as part of the broader identity and access model, not an isolated checkbox.
- **Performance**: Poorly staged rollouts can spike help desk volume and IdP load during registration waves. Spread cutovers and cache IdP capacity assumptions in peak windows (month-end, retail peaks).
- **Scalability**: At large user counts, **operational scalability** matters: standard verification methods, automated provisioning for security keys, and repeatable runbooks scale better than bespoke per-team exceptions.
- **Reliability**: Authentication is on the critical path for every business process that touches Salesforce. Treat MFA changes like a release: canary populations, measurable SLOs on login success rate, and rollback owners.
- **Operational Excellence**: Runbooks, training, metrics on registration completion, and post-incident reviews when lockouts occur are core to **Easy** and **Adaptable** operations, teams should improve the program each cycle without emergency heroics.

## Architectural Tradeoffs

- **Central IdP MFA versus Salesforce-native factors:** Centralizing MFA at the IdP simplifies employee experience and audit evidence for SSO-only populations, but requires discipline on bypass channels. Salesforce-native enforcement is essential where Salesforce passwords remain in use.
- **Phased rollout versus speed to baseline:** Phasing trades calendar time for lower incident volume; big-bang trades short calendar time for higher operational risk. Regulated environments often still require phased evidence collection even when policy deadlines are aggressive.
- **Security keys versus mobile TOTP:** Keys reduce SIM-swap and OTP phishing risk but add procurement and replacement logistics. Many orgs standardize on keys for privileged roles and allow TOTP more broadly.

## Anti-Patterns

1. **MFA theater**: Announcing enforcement without closing SSO bypass or shared credentials. Auditors and attackers both focus on the weakest path.
2. **Unbounded exemptions**: Treating exemptions as permanent configuration rather than time-bound risk acceptance. Creates untestable security posture.
3. **Ignoring integration blast radius**: Assuming “users will figure it out” for automation accounts. Data pipelines are often less visible than UI lockouts but more expensive when broken.

## Related skill navigation

Cross-check these when MFA work touches adjacent controls (from repository skill graph):

- `security/session-management-and-timeout`: session lifetime and reauthentication complement MFA
- `security/oauth-token-management` and `security/connected-app-security-policies`, OAuth clients in the same identity story
- `security/login-forensics`: evidence when diagnosing login failures after MFA changes
- `admin/integration-user-management`: integration users and MFA-resistant OAuth patterns

## Official Sources Used

- Salesforce Security Guide, Summer '26 (release 262): Multi-Factor Authentication (contractual requirement for direct and SSO logins; MFA default for direct login in production), Device Activation, Transaction Security (MFA action unavailable in Lightning Experience, mobile, and API) - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_security_impl_guide.pdf
- Metadata API Developer Guide, Summer '26: SecuritySettings > SessionSettings (`enableMFADirectUILoginOptIn` and the waiver override, `skipSFAWhenMFADirectUILogin`, `enableBuiltInAuthenticator`, `enableU2F`, `enableLightningLogin`, `identityConfirmationOnTwoFactorRegistrationEnabled`), SingleSignOnSettings (`isLoginWithSalesforceCredentialsDisabled`), NetworkAccess, ProfileSessionSetting and SessionSecurityLevel - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference, Summer '26: TwoFactorMethodsInfo (registered methods, Manage MFA in API, UncommittedWork note), PermissionSetAssignment `ExpirationDate` - https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

### Cited but not fetchable (UNVERIFIED (2026-10-03))

These Salesforce Help articles back the 2026 enforcement statements in `SKILL.md`. An unauthenticated fetch returns only a script shell, so their content was not read for this revision:

- Salesforce Help: Enable MFA for Your Entire Org - https://help.salesforce.com/s/articleView?id=xcloud.security_mfa_org_wide_setting.htm&type=5
- Salesforce Help: Exclude Exempt Users from MFA - https://help.salesforce.com/s/articleView?id=xcloud.security_mfa_exclude_exempt_users.htm&type=5
- Salesforce Help: Prepare for MFA Enforcement for All Employee Users - https://help.salesforce.com/s/articleView?id=005321561&language=en_US&type=1
- Salesforce Help: Prepare for Phishing-Resistant MFA Enforcement for Privileged Users including Admins - https://help.salesforce.com/s/articleView?id=005321563&language=en_US&type=1
- Salesforce Help: Security-Related Product Updates to the Salesforce Platform - https://help.salesforce.com/s/articleView?id=005317465&language=en_US&type=1
