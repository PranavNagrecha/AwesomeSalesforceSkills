# Metadata Examples: MFA Enforcement Strategy

Deployable settings and readiness queries for an MFA rollout. Element names come from the Metadata API Developer Guide (Summer '26, API 67.0) for SecuritySettings and ProfileSessionSetting, and field names from the Object Reference for TwoFactorMethodsInfo.

## 1. Readiness query: who has no verification method yet

Run as a user with the "Manage MFA in API" permission. Do not run it in the same Apex call as DML (UncommittedWork error).

```soql
SELECT UserId, HasSalesforceAuthenticator, HasTotp, HasSecurityKey, HasBuiltInAuthenticator, HasU2F, HasTempCode
FROM TwoFactorMethodsInfo
WHERE HasSalesforceAuthenticator = false
  AND HasTotp = false
  AND HasSecurityKey = false
  AND HasBuiltInAuthenticator = false
  AND HasU2F = false
```

```soql
-- Phase-1 readiness: privileged users and the methods they registered
SELECT UserId, HasSecurityKey, HasBuiltInAuthenticator, HasSalesforceAuthenticator, HasTotp
FROM TwoFactorMethodsInfo
WHERE UserId IN (SELECT AssigneeId FROM PermissionSetAssignment WHERE PermissionSet.PermissionsModifyAllData = true)
```

UNVERIFIED (2026-10-03): the second query assumes `PermissionSet.PermissionsModifyAllData` is filterable through the `PermissionSetAssignment` relationship in a semi-join on `TwoFactorMethodsInfo`; if the platform rejects the semi-join, run the `PermissionSetAssignment` query first and filter by the returned user IDs.

## 2. Org settings for the rollout

Deploy this only after the pilot. It omits `networkAccess` on purpose, because deploying that element replaces every trusted IP range.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/Security.settings-meta.xml (MFA-related fields only) -->
<SecuritySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <sessionSettings>
        <enableBuiltInAuthenticator>true</enableBuiltInAuthenticator>
        <enableLightningLogin>true</enableLightningLogin>
        <enableMFADirectUILoginOptIn>true</enableMFADirectUILoginOptIn>
        <enableU2F>true</enableU2F>
        <identityConfirmationOnTwoFactorRegistrationEnabled>true</identityConfirmationOnTwoFactorRegistrationEnabled>
        <skipSFAWhenMFADirectUILogin>true</skipSFAWhenMFADirectUILogin>
    </sessionSettings>
    <singleSignOnSettings>
        <enableSamlLogin>true</enableSamlLogin>
        <isLoginWithSalesforceCredentialsDisabled>false</isLoginWithSalesforceCredentialsDisabled>
    </singleSignOnSettings>
</SecuritySettings>
```

Field meanings (all from SecuritySettings in the Metadata API guide):

| Field | Effect |
|---|---|
| `enableMFADirectUILoginOptIn` | Requires a verification method for direct UI logins with username and password; the waiver permission overrides it (per the Summer '26 guide) |
| `skipSFAWhenMFADirectUILogin` | Registration screen lists all supported methods instead of only Salesforce Authenticator |
| `enableBuiltInAuthenticator` | Allows Touch ID, Windows Hello, and similar built-in authenticators |
| `enableU2F` | Allows U2F-compatible security keys |
| `enableLightningLogin` | Allows Salesforce Authenticator passwordless login |
| `identityConfirmationOnTwoFactorRegistrationEnabled` | Users confirm their identity when adding a verification method, instead of logging in again |
| `isLoginWithSalesforceCredentialsDisabled` | When true, users are redirected to the identity provider; set it per org only after the SSO-only population and break-glass path are confirmed |

## 3. High-assurance session for a privileged profile

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/profileSessionSettings/Security_Admin.profileSessionSetting-meta.xml -->
<ProfileSessionSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <profile>Security Admin</profile>
    <requiredSessionLevel>HIGH_ASSURANCE</requiredSessionLevel>
    <sessionTimeout>60</sessionTimeout>
</ProfileSessionSetting>
```

The SessionSecurityLevel section of the guide says MFA "requires HIGH_ASSURANCE", so users of this profile must complete MFA to get a session.

## 4. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/mfa-rollout.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Security</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Security_Admin</members>
        <name>ProfileSessionSetting</name>
    </types>
    <version>67.0</version>
</Package>
```

## 5. Rollout commands and verification

```bash
sf project retrieve start --metadata "Settings:Security" ProfileSessionSetting --target-org prod --output-dir baseline/prod
python3 skills/security/mfa-enforcement-strategy/scripts/check_mfa_enforcement_strategy.py --skip-skill --manifest-dir baseline/prod
sf project deploy start --manifest manifest/mfa-rollout.xml --target-org uat --wait 30
```

| Phase | Step | Verify |
|---|---|---|
| 0 | Readiness query | Count of users with no method, per population |
| 1 | Enable methods and `skipSFAWhenMFADirectUILogin` | Pilot users can register a key or built-in authenticator |
| 2 | `enableMFADirectUILoginOptIn` in a sandbox, then production | Login history shows MFA for direct UI logins |
| 3 | High-assurance profile session settings | Privileged users are prompted for MFA at login |
