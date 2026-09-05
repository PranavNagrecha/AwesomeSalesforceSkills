# Metadata Examples — Org Setup and Configuration

Deployable shapes for the org-wide settings this skill owns. Element names, enum values and API-version notes come from the Metadata API Developer Guide (v66 / Summer '26 PDF: `Settings`, `SecuritySettings`, `MyDomainSettings`, `CompanySettings`, `LanguageSettings`, `CspTrustedSite`); the worked files below extend the guide's own sample definitions to a realistic new-org baseline. Verification fields come from the Object Reference (`Organization`).

Validate a retrieved settings tree with:

```bash
python3 skills/admin/org-setup-and-configuration/scripts/check_org_setup_and_configuration.py --manifest-dir force-app/main/default
```

The checker reports `ERROR` (the deploy will fail), `WARN` (the deploy succeeds and weakens something) and `INFO` (a posture decision worth confirming), and exits non-zero if it reports anything at all. The files on this page are deliberately not silent: the `MyDomain.settings` example trips the `canOnlyLoginWithMyDomainUrl` advisory, because that value is correct for production and wrong for a sandbox. Read the findings; do not tune them away.

## How to read it

- **One file per settings component.** "Each settings component gets stored in a single file in the `settings` directory of the corresponding package directory. The filename uses the format `Setting feature.settings`." (Metadata API Guide, `Settings`). In an SFDX source-format project the file is `settings/Security.settings-meta.xml`.
- **The manifest name is always `Settings`.** "The member format when used in the package manifest is the component metadata type name without the 'Settings' suffix" — `SecuritySettings` is retrieved as `<members>Security</members>` / `<name>Settings</name>`.
- **The wildcard is all-or-nothing.** "The wildcard character `*` … doesn't apply to metadata types for feature settings. The wildcard applies only when retrieving all settings, not for an individual setting."
- **`networkAccess` is replace-in-place, not merge.** "To add an IP range, deploy all existing IP ranges, including the one you want to add. Otherwise, the existing IP ranges are replaced with the ones you deploy. To remove all the IP ranges, leave the `networkAccess` field blank (`<networkAccess></networkAccess>`)." Retrieve before you edit — always.
- **Some fields are read-only in the API.** In `MyDomainSettings`, `myDomainName`, `myDomainSuffix`, `domainPartition`, `edgeRoutingMethod` and `useEdge` are all documented "read-only in the API." You cannot register or rename a My Domain by deploying this file; you change the name on the My Domain Setup page and deploy the *behaviour* fields around it.
- **Not everything in Setup is in the Metadata API.** "Not all feature settings are available in Metadata API" (`Settings`), and for unsupported types "These metadata types can't be retrieved or deployed with Metadata API. To make changes to these types, you must do it manually in each of your organizations." Check the Metadata Coverage report before promising a setting will travel in a package.
- **Elements are emitted in the guide's field order** (alphabetical within each container). Keep that order when hand-editing; re-retrieve after deploying and diff rather than assuming your ordering survived.

## Where the files live

| What | package.xml `<name>` | `<members>` | File in a DX project | API |
|---|---|---|---|---|
| Session, password, IP, SSO, login-as | `Settings` | `Security` | `settings/Security.settings-meta.xml` | 27.0+ |
| My Domain behaviour and redirects | `Settings` | `MyDomain` | `settings/MyDomain.settings-meta.xml` | 47.0+ |
| Fiscal year | `Settings` | `Company` | `settings/Company.settings-meta.xml` | 27.0+ |
| Locale/ICU formats, translation | `Settings` | `Language` | `settings/Language.settings-meta.xml` | 47.0+ |
| CSP Trusted Sites (Trusted URLs) | `CspTrustedSite` | site name or `*` | `cspTrustedSites/<Name>.cspTrustedSite-meta.xml` | 39.0+ |

`OrgPreferenceSettings` is **not** on this list on purpose: the guide records it as "Removed in API version 48.0 … most of the settings supported in the `preferences` field were made available in the form of Boolean fields on other Settings types." If an agent proposes an `OrgPreference.settings` file, that file cannot deploy on any current API version.

## Security.settings — new-org baseline

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: settings/Security.settings-meta.xml. Shown with the four containers
     an org stand-up actually touches; a retrieved file has more fields. -->
<SecuritySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- false = only an admin with Manage Users can grant login access to Support -->
    <canUsersGrantLoginAccess>false</canUsersGrantLoginAccess>
    <!-- "Administrators Can Log in as Any User". Default is false. -->
    <enableAdminLoginAsAnyUser>false</enableAdminLoginAsAnyUser>

    <networkAccess>
        <!-- REPLACE semantics: this list IS the org's trusted-IP list after deploy.
             Every range you want to keep must appear here. -->
        <ipRanges>
            <description>London office egress</description>
            <start>203.0.113.0</start>
            <end>203.0.113.255</end>
        </ipRanges>
        <ipRanges>
            <description>Corporate VPN concentrator</description>
            <start>198.51.100.10</start>
            <end>198.51.100.20</end>
        </ipRanges>
    </networkAccess>

    <passwordPolicies>
        <!-- Valid: NoRestriction | AlphaNumeric (default) | SpecialCharacters |
             UpperLowerCaseNumeric | UpperLowerCaseNumericSpecialCharacters |
             Any3UpperLowerCaseNumericSpecialCharacters (46.0+) -->
        <complexity>UpperLowerCaseNumericSpecialCharacters</complexity>
        <!-- Valid: Never | ThirtyDays | SixtyDays | NinetyDays (default) | SixMonths | OneYear -->
        <expiration>NinetyDays</expiration>
        <!-- 0-24 passwords remembered (24 max applies to API 31.0+); default 3 -->
        <historyRestriction>10</historyRestriction>
        <!-- Valid: FifteenMinutes (default) | ThirtyMinutes | SixtyMinutes | Forever -->
        <lockoutInterval>ThirtyMinutes</lockoutInterval>
        <!-- ENUM, not a number. Valid: NoLimit | ThreeAttempts | FiveAttempts | TenAttempts (default) -->
        <maxLoginAttempts>FiveAttempts</maxLoginAttempts>
        <!-- String, 5-50 characters, default 8 (API 35.0+) -->
        <minimumPasswordLength>12</minimumPasswordLength>
        <minimumPasswordLifetime>false</minimumPasswordLifetime>
        <obscureSecretAnswer>true</obscureSecretAnswer>
        <!-- Valid: None | DoesNotContainPassword (default) -->
        <questionRestriction>DoesNotContainPassword</questionRestriction>
    </passwordPolicies>

    <sessionSettings>
        <!-- Warning popup before timeout. true DISABLES the warning. -->
        <disableTimeoutWarning>false</disableTimeoutWarning>
        <enableCSRFOnGet>true</enableCSRFOnGet>
        <enableCSRFOnPost>true</enableCSRFOnPost>
        <enableCacheAndAutocomplete>false</enableCacheAndAutocomplete>
        <enableClickjackNonsetupSFDC>true</enableClickjackNonsetupSFDC>
        <enableClickjackNonsetupUser>true</enableClickjackNonsetupUser>
        <enableClickjackNonsetupUserHeaderless>true</enableClickjackNonsetupUserHeaderless>
        <enableClickjackSetup>true</enableClickjackSetup>
        <!-- The org-wide MFA switch. The "Multi-Factor Authentication for User Interface
             Logins" user permission and the "Waive Multi-Factor Authentication for Exempt
             Users" user permission both interact with it - see gotchas.md. -->
        <enableMFADirectUILoginOptIn>true</enableMFADirectUILoginOptIn>
        <!-- true = Login IP Ranges enforced on EVERY request, not just at login (34.0+) -->
        <enforceIpRangesEveryRequest>false</enforceIpRangesEveryRequest>
        <forceLogoutOnSessionTimeout>true</forceLogoutOnSessionTimeout>
        <forceRelogin>true</forceRelogin>
        <lockSessionsToDomain>true</lockSessionsToDomain>
        <!-- Breaks cellular/VPN users. See gotchas.md before setting true. -->
        <lockSessionsToIp>false</lockSessionsToIp>
        <requireHttpOnly>true</requireHttpOnly>
        <!-- Valid: FifteenMinutes | ThirtyMinutes | SixtyMinutes | NinetyMinutes (58.0+) |
             TwoHours | FourHours | EightHours | TwelveHours | TwentyFourHours (38.0+) -->
        <sessionTimeout>TwoHours</sessionTimeout>
        <terminateUserSessionsWhenAdminResetsPassword>true</terminateUserSessionsWhenAdminResetsPassword>
    </sessionSettings>

    <singleSignOnSettings>
        <enableCaseInsensitiveFederationID>false</enableCaseInsensitiveFederationID>
        <enableMultipleSamlConfigs>true</enableMultipleSamlConfigs>
    </singleSignOnSettings>
</SecuritySettings>
```

Two fields an agent is likely to reach for and should not:

| Field | Why not |
|---|---|
| `requireHttps` | "This option is enabled by default for security reasons and can't be disabled. To change to HTTP, contact Salesforce Customer Support." Available in API version 40.0 **to 60.0** — it is not a v61+ lever. |
| `enableRequireHttpsConnection` | "Deprecated in API version 47.0 and later." |

Per-profile **login IP ranges** are not in this file. They live on the `Profile` type as `loginIpRanges` (`ProfileLoginIpRange`: `startAddress`, `endAddress`, `description`; API 17.0+), alongside `loginHours`. Those are a different control with different semantics — see `admin/permission-sets-vs-profiles` and `admin/user-management`. The `Profile` metadata type's field table contains **no** password-policy fields at all, so a profile-level password override configured in Setup does not travel in a `Profile` deploy.

## MyDomain.settings — behaviour after the domain exists

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: settings/MyDomain.settings-meta.xml. myDomainName and myDomainSuffix
     are READ-ONLY in the API; they are shown here only because a retrieve emits them. -->
<MyDomainSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- true = users MUST use the My Domain login URL. Note: an admin can use the
         Log In action on the Sandboxes Setup page only when this is false in the sandbox. -->
    <canOnlyLoginWithMyDomainUrl>true</canOnlyLoginWithMyDomainUrl>
    <!-- true = API access must also use the My Domain login URL -->
    <doesApiLoginRequireOrgDomain>false</doesApiLoginRequireOrgDomain>
    <doesWarnOnForceComRedirect>true</doesWarnOnForceComRedirect>
    <doesWarnOnRedirect>true</doesWarnOnRedirect>
    <!-- Valid: Redirect | WarnOnRedirect | NoRedirect (59.0+).
         The guide's own sample definition prints "false" here; the field table is
         the authority - use one of the three enum values. -->
    <instancedUrlRedirectHandling>Redirect</instancedUrlRedirectHandling>
    <isFirstPartyCookieUseRequired>true</isFirstPartyCookieUseRequired>
    <!-- true = Hostname Redirects event log is produced daily (56.0+) -->
    <logRedirections>true</logRedirections>
    <myDomainName>mycompany</myDomainName>
    <!-- MySalesforce = my.salesforce.com WITH enhanced domains.
         MySalesforceLimited = my.salesforce.com WITHOUT enhanced domains. -->
    <myDomainSuffix>MySalesforce</myDomainSuffix>
    <redirectForceComSitesUrls>true</redirectForceComSitesUrls>
    <!-- Resets to its default (true) whenever you deploy a NEW My Domain -->
    <redirectPriorMyDomain>true</redirectPriorMyDomain>
    <useStabilizedMyDomainHostnames>true</useStabilizedMyDomainHostnames>
</MyDomainSettings>
```

`myDomainSuffix` is the only field in this file that tells you whether **enhanced domains** are on: `MySalesforce` means enhanced, `MySalesforceLimited` means not. There is no `enhancedDomains` boolean in `MyDomainSettings`. Partitioned domains (`domainPartition` — `sandbox`, `scratch`, `develop`, `patch`, `none`) "require enhanced domains," and "Production orgs always have a value of `none`."

## Company.settings and Language.settings — the rest of the stand-up

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: settings/Company.settings-meta.xml. This type carries the fiscal year
     and nothing else in the guide's field table - locale, time zone and currency
     defaults are NOT here. -->
<CompanySettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCustomFiscalYear>false</enableCustomFiscalYear>
    <fiscalYear>
        <!-- endingMonth or startingMonth -->
        <fiscalYearNameBasedOn>endingMonth</fiscalYearNameBasedOn>
        <startMonth>February</startMonth>
    </fiscalYear>
</CompanySettings>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: settings/Language.settings-meta.xml -->
<LanguageSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- ICU date/currency formats. Default true for orgs created in API 47.0+. -->
    <enableICULocaleDateFormat>true</enableICULocaleDateFormat>
    <enableCanadaIcuFormat>true</enableCanadaIcuFormat>
    <enableEndUserLanguages>true</enableEndUserLanguages>
    <!-- Setting enablePlatformLanguages true also forces enableEndUserLanguages true -->
    <enablePlatformLanguages>false</enablePlatformLanguages>
    <enableTranslationWorkbench>true</enableTranslationWorkbench>
    <useLanguageFallback>true</useLanguageFallback>
</LanguageSettings>
```

The org's **default locale, default time zone and default currency** are not settings metadata: they are updatable fields on the `Organization` standard object (`DefaultLocaleSidKey`, `TimeZoneSidKey`, `LanguageLocaleKey` — all "Filter, Group, Restricted picklist, Sort, **Update**" in the Object Reference). Set them in Setup > Company Information, or by an `update` on the single `Organization` row; do not expect them in a settings deploy. `LanguageSettings` governs the *format engine* (ICU) and which languages are selectable, not the org's chosen default.

## CspTrustedSite — one file per trusted URL

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- cspTrustedSites/ThirdPartyAnalytics.cspTrustedSite-meta.xml -->
<CspTrustedSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <canAccessCamera>false</canAccessCamera>
    <canAccessMicrophone>false</canAccessMicrophone>
    <!-- All | Communities | FieldServiceMobileExtension | LEX | VisualForce -->
    <context>LEX</context>
    <description>Embedded revenue dashboard on the Account record page (ticket ARCH-2291)</description>
    <endpointUrl>https://analytics.thirdparty.example.com</endpointUrl>
    <isActive>true</isActive>
    <!-- Grant ONLY the directive the console error named. In API 59.0+ at least one
         isApplicable*/canAccess* field must be true or the component is invalid. -->
    <isApplicableToConnectSrc>false</isApplicableToConnectSrc>
    <isApplicableToFontSrc>false</isApplicableToFontSrc>
    <isApplicableToFrameSrc>true</isApplicableToFrameSrc>
    <isApplicableToImgSrc>false</isApplicableToImgSrc>
    <isApplicableToMediaSrc>false</isApplicableToMediaSrc>
    <isApplicableToStyleSrc>false</isApplicableToStyleSrc>
</CspTrustedSite>
```

There is no `script-src` field in this type's field table — the six `isApplicableTo*` directives plus the two `canAccess*` permissions-policy flags are the whole surface. `endpointUrl` accepts a wildcard (`*.example.com`) and requires `https://` for a third-party API or `wss://` for a WebSocket; a malformed URL such as `https://{subdomain}.example.com` fails the syntax check, and pre-February-2025 malformed entries "are excluded from generated CSP HTTP headers." Keep the whole header under 12 KB — "Salesforce customers report issues when the header size approaches 16 KB."

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Company</members>
        <members>Language</members>
        <members>MyDomain</members>
        <members>Security</members>
        <name>Settings</name>
    </types>
    <types>
        <members>*</members>
        <name>CspTrustedSite</name>
    </types>
    <version>66.0</version>
</Package>
```

`CspTrustedSite` supports the `*` wildcard. `Settings` does not, per member — `<members>*</members>` under `<name>Settings</name>` means *every* settings component in the org, which is a very large retrieve and almost never what you want in a deploy package.

## Retrieve, validate, deploy

```bash
# 1. ALWAYS retrieve first - Security.settings networkAccess is replace-in-place
sf project retrieve start \
  --metadata "Settings:Security" "Settings:MyDomain" "Settings:Company" "Settings:Language" \
  --target-org my-sandbox

# 2. Edit settings/*.settings-meta.xml, then lint before you deploy
python3 skills/admin/org-setup-and-configuration/scripts/check_org_setup_and_configuration.py \
  --manifest-dir force-app/main/default

# 3. Check-only against the sandbox
sf project deploy validate --source-dir force-app/main/default/settings --target-org my-sandbox

# 4. Deploy to the sandbox, verify logins, then promote
sf project deploy start --source-dir force-app/main/default/settings --target-org my-sandbox
sf project deploy start --source-dir force-app/main/default/settings --target-org production
```

Settings components have no `fullName` you can target individually — there is exactly one `Security.settings` per org, so a deploy of this file is a full replacement of the containers it contains. That is why step 1 is not optional.

## Verification

After the deploy, confirm the org identity and the locale defaults that settings metadata does *not* carry:

```sql
SELECT Id, Name, InstanceName, IsSandbox, OrganizationType,
       DefaultLocaleSidKey, LanguageLocaleKey, TimeZoneSidKey,
       TrialExpirationDate
FROM Organization
```

```bash
sf data query --query "SELECT Id, Name, InstanceName, IsSandbox, OrganizationType, DefaultLocaleSidKey, LanguageLocaleKey, TimeZoneSidKey, TrialExpirationDate FROM Organization" --target-org my-sandbox
```

`IsSandbox` is the check that stops a "which org am I in?" mistake before a production settings deploy — it is read-only and `true` only in sandboxes (API 31.0+). `InstanceName` is read-only (API 31.0+). `TrialExpirationDate` is non-null only while a trial licence is running.

Then re-retrieve and diff — the deployed file is the only proof the enum you wrote is the enum the org stored:

```bash
sf project retrieve start --metadata "Settings:Security" --target-org my-sandbox
git diff -- force-app/main/default/settings/Security.settings-meta.xml
```

## Setup checklist after the deploy

| # | Check | Where |
|---|---|---|
| 1 | Trusted IP list matches the deployed `ipRanges` exactly — nothing silently dropped | Setup > Security > Network Access |
| 2 | Session timeout and the timeout-warning behaviour match `sessionTimeout` / `disableTimeoutWarning` | Setup > Security > Session Settings |
| 3 | MFA prompt appears for a direct UI login by a test user with no waiver | private browser, `https://<mydomain>.my.salesforce.com` |
| 4 | An SSO test user is *not* double-prompted | IdP-initiated login |
| 5 | Password policy shows the deployed `complexity` / `minimumPasswordLength` | Setup > Security > Password Policies |
| 6 | Every Connected App callback URL resolves against the current My Domain | Setup > App Manager |
| 7 | Each CSP trusted site loads its resource with no console violation | Lightning page + DevTools Console |
| 8 | `Organization.IsSandbox` reads `false` before you call the production deploy done | the SOQL above |
