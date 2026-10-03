# Metadata Examples: Org Hardening And Baseline Config

A deployable hardening baseline. Every element name below appears in the Metadata API Developer Guide (Summer '26, API 67.0) for SecuritySettings, CspTrustedSite, CorsWhitelistOrigin, or ProfileSessionSetting. Paths are Salesforce DX source format.

## 1. Org security settings baseline

This file deliberately omits `networkAccess`. Deploying `networkAccess` replaces every trusted IP range, so manage IP ranges in a separate, fully retrieved file.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/Security.settings-meta.xml -->
<SecuritySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <canUsersGrantLoginAccess>false</canUsersGrantLoginAccess>
    <enableAdminLoginAsAnyUser>false</enableAdminLoginAsAnyUser>
    <enableCoopHeader>true</enableCoopHeader>
    <enablePermissionsPolicy>true</enablePermissionsPolicy>
    <grantCameraAccess>TrustedUrls</grantCameraAccess>
    <grantMicrophoneAccess>TrustedUrls</grantMicrophoneAccess>
    <passwordPolicies>
        <complexity>UpperLowerCaseNumericSpecialCharacters</complexity>
        <expiration>NinetyDays</expiration>
        <historyRestriction>12</historyRestriction>
        <lockoutInterval>ThirtyMinutes</lockoutInterval>
        <maxLoginAttempts>FiveAttempts</maxLoginAttempts>
        <minimumPasswordLength>12</minimumPasswordLength>
        <minimumPasswordLifetime>true</minimumPasswordLifetime>
        <obscureSecretAnswer>true</obscureSecretAnswer>
        <questionRestriction>DoesNotContainPassword</questionRestriction>
    </passwordPolicies>
    <sessionSettings>
        <enableCSRFOnGet>true</enableCSRFOnGet>
        <enableCSRFOnPost>true</enableCSRFOnPost>
        <enableClickjackNonsetupSFDC>true</enableClickjackNonsetupSFDC>
        <enableClickjackNonsetupUser>true</enableClickjackNonsetupUser>
        <enableClickjackNonsetupUserHeaderless>true</enableClickjackNonsetupUserHeaderless>
        <enableClickjackSetup>true</enableClickjackSetup>
        <enforceIpRangesEveryRequest>true</enforceIpRangesEveryRequest>
        <forceLogoutOnSessionTimeout>true</forceLogoutOnSessionTimeout>
        <forceRelogin>true</forceRelogin>
        <hstsOnForcecomSites>true</hstsOnForcecomSites>
        <lockSessionsToDomain>true</lockSessionsToDomain>
        <referrerPolicy>true</referrerPolicy>
        <referrerPolicyDirective>strict-origin-when-cross-origin</referrerPolicyDirective>
        <requireHttpOnly>true</requireHttpOnly>
        <sessionTimeout>TwoHours</sessionTimeout>
        <terminateUserSessionsWhenAdminResetsPassword>true</terminateUserSessionsWhenAdminResetsPassword>
    </sessionSettings>
</SecuritySettings>
```

Test before production: `enableClickjackNonsetupUser` and `enableClickjackNonsetupUserHeaderless` block framing of customer Visualforce pages, and `requireHttpOnly` breaks JavaScript that reads the session cookie.

## 2. A governed CSP Trusted Site

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/cspTrustedSites/Maps_Vendor_Tiles.cspTrustedSite-meta.xml -->
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <context>LEX</context>
    <description>Owner: Field Ops (J. Rivera). Map tiles for the Route Planner LWC. Review 2027-01-15.</description>
    <endpointUrl>https://tiles.maps-vendor.example.com</endpointUrl>
    <isActive>true</isActive>
    <isApplicableToConnectSrc>false</isApplicableToConnectSrc>
    <isApplicableToFontSrc>false</isApplicableToFontSrc>
    <isApplicableToFrameSrc>false</isApplicableToFrameSrc>
    <isApplicableToImgSrc>true</isApplicableToImgSrc>
    <isApplicableToMediaSrc>false</isApplicableToMediaSrc>
    <isApplicableToStyleSrc>false</isApplicableToStyleSrc>
</CspTrustedSite>
```

Only the image directive is open, the context is Lightning Experience only, and the description carries owner, purpose, and review date.

## 3. A CORS allowlist entry

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/corsWhitelistOrigins/Partner_Portal.corsWhitelistOrigin-meta.xml -->
<CorsWhitelistOrigin xmlns="http://soap.sforce.com/2006/04/metadata">
    <urlPattern>https://portal.partner.example.com</urlPattern>
</CorsWhitelistOrigin>
```

## 4. A profile session override (made explicit and reviewed)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/profileSessionSettings/Integration_Admin.profileSessionSetting-meta.xml -->
<ProfileSessionSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <profile>Integration Admin</profile>
    <requiredSessionLevel>HIGH_ASSURANCE</requiredSessionLevel>
    <sessionTimeout>30</sessionTimeout>
</ProfileSessionSetting>
```

`sessionTimeout` here overrides the org-wide value for users of this profile. UNVERIFIED (2026-10-03): the file name convention for ProfileSessionSetting components comes from the Salesforce CLI metadata registry (directory `profileSessionSettings`, suffix `profileSessionSetting`); the Metadata API guide gives the suffix and folder but not the member naming rule.

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- manifest/hardening-package.xml -->
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Security</members>
        <name>Settings</name>
    </types>
    <types>
        <members>Maps_Vendor_Tiles</members>
        <name>CspTrustedSite</name>
    </types>
    <types>
        <members>Partner_Portal</members>
        <name>CorsWhitelistOrigin</name>
    </types>
    <types>
        <members>Integration_Admin</members>
        <name>ProfileSessionSetting</name>
    </types>
    <version>67.0</version>
</Package>
```

## 6. Deploy order and verification

```bash
sf project deploy validate --manifest manifest/hardening-package.xml --target-org uat --wait 30
sf project deploy start --manifest manifest/hardening-package.xml --target-org uat --wait 30
python3 skills/security/org-hardening-and-baseline-config/scripts/check_org_hardening_and_baseline_config.py --manifest-dir force-app
```

| Order | Step | Verify |
|---|---|---|
| 1 | Deploy to a sandbox | Embedded Visualforce, integrations, and custom JavaScript still work |
| 2 | Re-run Health Check in the sandbox | Score against the chosen baseline improved; remaining items listed |
| 3 | Deploy to production in a change window | Health Check matches the sandbox result |
| 4 | Record exceptions | Every CSP and CORS entry has an owner and review date |
