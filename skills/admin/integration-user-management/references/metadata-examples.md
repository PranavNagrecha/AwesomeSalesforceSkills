# Metadata Examples — Integration User Management

Deployable shapes for the metadata that actually defines an integration user's access: the `Profile` it is anchored to, the `PermissionSet` that carries its object/field grants, the `ProfileSessionSetting` and `ProfilePasswordPolicy` that govern its session, the `ConnectedApp` OAuth policy that names it as the client-credentials execution user, and the REST payload that creates the User record.

Element names, enum values, file suffixes and API-version floors below come from the Metadata API Developer Guide (v62/262 PDF, sections `PermissionSet`, `Profile`, `ProfileLoginHours`, `ProfileLoginIpRange`, `ProfilePasswordPolicy`, `ProfileSessionSetting`, `ConnectedApp`) and the Object Reference (`User`, `UserLicense`, `LoginHistory`). The worked examples extend the guide's own sample definitions to a realistic single-integration setup.

Validate the result with:

```bash
python3 skills/admin/integration-user-management/scripts/check_integration_user_management.py \
  --manifest-dir force-app/main/default
```

## How to read it

- **The Profile is the anchor, the Permission Set is the grant.** Anchor the integration user to a profile that carries no object permissions, then layer every object and field grant on a permission set. `Profile.userLicense` is available in API v17.0 and later; `Profile.userPermissions` in v29.0 and later (`api_meta.txt` L97772–97782).
- **`license`, not `userLicense`, on a Permission Set.** `PermissionSet.userLicense` is deprecated and available only up to API v37.0; from v38.0 use `license` (`api_meta.txt` L94826–94830). The guide's own sample still shows the deprecated element — do not copy it forward.
- **Unspecified user permissions are disabled on deploy.** "In API Version 40.0 and later, if a permission isn't specified for a deployment, it's disabled" (`api_meta.txt` L94867–94873). Omitting `ModifyAllData` from the permission set is an active grant of *no* Modify All Data, not a silent no-op.
- **Deploy the whole permission set or lose parts of it.** "when you deploy a permission set, you must include all of its metadata to avoid accidentally overwriting the permission set's contents" (`api_meta.txt` L94712–94717).
- **A Profile deploy overlays; it does not replace.** Disabled permissions are not exported, so a permission you turned off in source stays on in the target unless you write it out explicitly as `false` (`api_meta.txt` L97623–97627).
- **Login-hour minutes are minutes since midnight, divisible by 60.** `300` is 5:00 AM, `1020` is 5:00 PM; a start requires a matching end for the same day and start cannot exceed end (`api_meta.txt` L98071–98092).
- **`sessionTimeout` is a fixed value set**, not a free integer: `0`, `15`, `30`, `60`, `90`, `120`, `240`, `480`, `720`, `1440` (`api_meta.txt` L98840–98853).
- **`oauthClientCredentialUser` must be an API-only user.** The Metadata API guide states outright: "The execution user for the OAuth 2.0 client credentials flow. Salesforce returns access tokens on behalf of this user. This user must have the API Only permission." (`api_meta.txt` L35443–35448).

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Profile | `Profile` | `profiles/SVC_Integration_API_Only.profile-meta.xml` | 10.0+ (`api_meta.txt` L97600) |
| Permission Set | `PermissionSet` | `permissionsets/MuleSoft_Order_Sync.permissionset-meta.xml` | 22.0+ (`api_meta.txt` L94733) |
| Profile session settings | `ProfileSessionSetting` | `profileSessionSettings/SVC_Integration_API_Only.profileSessionSetting-meta.xml` | 40.0+ (`api_meta.txt` L98826) |
| Profile password policy | `ProfilePasswordPolicy` | `profilePasswordPolicies/SVC_Integration_API_Only.profilePasswordPolicy-meta.xml` | 40.0+ (`api_meta.txt` L98714) |
| Connected app | `ConnectedApp` | `connectedApps/MuleSoft_Order_Sync.connectedApp-meta.xml` | 56.0+ for `isClientCredentialEnabled` (`api_meta.txt` L35332–35337) |

`PermissionSet` and both profile-policy types support the `*` wildcard in package.xml (`api_meta.txt` L95290, L98805, L98898). The User record itself is data, not metadata — create it over REST (below), never in a package.

## 1. Custom API-only Profile for the integration user

Use this shape when the integration user sits on a standard Salesforce or Salesforce Platform license rather than the dedicated integration license. It grants no object permissions, restricts the source IPs, and closes login hours outside the ETL window.

> UNVERIFIED (2026-09-05): the standard profile name "Minimum Access - API Only Integrations" and the "Salesforce Integration" user license name (asserted in `SKILL.md`) do not appear in the Metadata API guide, Object Reference, or App Limits cheat sheet extracts available offline; `UserLicense.LicenseDefinitionKey` in `object_reference.txt` L299548–299600 lists `AUL`, `SFDC`, `FDC_ONE` and portal keys but no integration key. Confirm the exact license and profile labels in your own org's Setup > Company Information before deploying.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <description>API-only anchor profile for middleware service accounts. Grants no object access; all grants live on permission sets.</description>
    <userLicense>Salesforce</userLicense>

    <!-- Explicitly false: a Profile deploy overlays the target, so a permission
         you want OFF must be written out. See api_meta.txt L97623-97627. -->
    <userPermissions>
        <enabled>true</enabled>
        <name>ApiEnabled</name>
    </userPermissions>
    <userPermissions>
        <enabled>false</enabled>
        <name>ModifyAllData</name>
    </userPermissions>
    <userPermissions>
        <enabled>false</enabled>
        <name>ViewAllData</name>
    </userPermissions>
    <userPermissions>
        <enabled>false</enabled>
        <name>AuthorApex</name>
    </userPermissions>
    <userPermissions>
        <enabled>false</enabled>
        <name>ManageUsers</name>
    </userPermissions>

    <!-- ProfileLoginIpRange: startAddress and endAddress are both required.
         description is available in API v31.0+. api_meta.txt L98109-98122. -->
    <loginIpRanges>
        <description>MuleSoft CloudHub dedicated egress, eu-west-1</description>
        <startAddress>52.30.0.10</startAddress>
        <endAddress>52.30.0.14</endAddress>
    </loginIpRanges>
    <loginIpRanges>
        <description>MuleSoft CloudHub retry cluster, eu-west-1</description>
        <startAddress>52.30.0.20</startAddress>
        <endAddress>52.30.0.22</endAddress>
    </loginIpRanges>

    <!-- ProfileLoginHours: minutes since midnight, evenly divisible by 60.
         1260 = 21:00, 1440 = 24:00. Every day that has a Start must have an End.
         api_meta.txt L98071-98092. -->
    <loginHours>
        <mondayStart>1260</mondayStart>
        <mondayEnd>1440</mondayEnd>
        <tuesdayStart>1260</tuesdayStart>
        <tuesdayEnd>1440</tuesdayEnd>
        <wednesdayStart>1260</wednesdayStart>
        <wednesdayEnd>1440</wednesdayEnd>
        <thursdayStart>1260</thursdayStart>
        <thursdayEnd>1440</thursdayEnd>
        <fridayStart>1260</fridayStart>
        <fridayEnd>1440</fridayEnd>
        <saturdayStart>1260</saturdayStart>
        <saturdayEnd>1440</saturdayEnd>
        <sundayStart>1260</sundayStart>
        <sundayEnd>1440</sundayEnd>
    </loginHours>
</Profile>
```

Login hours are a real availability control, not a formality: a retry that fires at 03:00 against a profile whose window closes at 24:00 is rejected as a login failure, not as a permission error. If you decide the integration must be reachable around the clock, delete the `loginHours` block by deploying an **empty** `<loginHours/>` element — the guide is explicit that removing prior restrictions requires the empty tag, not the absence of the tag (`api_meta.txt` L98105–98107).

## 2. Permission Set: the actual grant

The skeleton follows the guide's own `PermissionSet` sample definition (`api_meta.txt` L95194–95238), narrowed to a least-privilege integration scope and switched from the deprecated `userLicense` element to `license`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>MuleSoft Order Sync</label>
    <description>Order sync integration: read Account, read/write Order and Order Product. No View All / Modify All.</description>

    <!-- license replaces the deprecated userLicense element from API v38.0.
         api_meta.txt L94826-94830. -->
    <license>Salesforce</license>

    <!-- hasActivationRequired MUST stay false (or be omitted) for an integration
         user: a session-activated permission set grants nothing to a headless
         client credentials or JWT flow. api_meta.txt L94820-94822. -->
    <hasActivationRequired>false</hasActivationRequired>

    <userPermissions>
        <enabled>true</enabled>
        <name>ApiEnabled</name>
    </userPermissions>

    <objectPermissions>
        <allowCreate>false</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>false</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Account</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>Order</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>
    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>true</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <object>OrderItem</object>
        <viewAllRecords>false</viewAllRecords>
    </objectPermissions>

    <!-- fieldPermissions: available API v23.0+. Permissions for REQUIRED fields
         cannot be retrieved or deployed from API v30.0 onward, so Order.AccountId
         and OrderItem.Quantity are deliberately absent here.
         api_meta.txt L95019-95022. -->
    <fieldPermissions>
        <editable>false</editable>
        <field>Account.External_Customer_Id__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Order.External_Order_Id__c</field>
        <readable>true</readable>
    </fieldPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Order.Sync_Status__c</field>
        <readable>true</readable>
    </fieldPermissions>
</PermissionSet>
```

Two element choices carry weight. `viewAllFields` on `objectPermissions` (API v63.0+) is omitted on purpose: enabling it suppresses the individual `fieldPermissions` entries from retrieve, so your source stops describing the field grants it is supposed to describe (`api_meta.txt` L95027–95030, L95104–95110). And `hasActivationRequired` is stated explicitly rather than left out, because a permission set that "requires an associated active session" (`api_meta.txt` L94820–94822) is invisible to a headless flow that never establishes a UI session.

## 3. Session and password policy for the integration profile

Both types key off the profile by name, and both are available from API v40.0.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProfileSessionSetting xmlns="http://soap.sforce.com/2006/04/metadata">
    <profile>SVC_Integration_API_Only</profile>
    <requiredSessionLevel>STANDARD</requiredSessionLevel>
    <sessionTimeout>120</sessionTimeout>
</ProfileSessionSetting>
```

`STANDARD` here is the load-bearing value. `HIGH_ASSURANCE` on this profile combined with a connected app whose `ConnectedAppSessionPolicy` raises the session level will *block* the integration outright: "All other flows, such as the JSON Web Token (JWT) bearer token flow, don't include a user approval step. For flows without a user approval step, API logins with the High Assurance session security level are blocked." (`api_meta.txt` L35826–35836). Do not set `LOW` either — the guide warns that "users assigned to this level experience unpredictable and reduced functionality" (`api_meta.txt` L98880–98883).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProfilePasswordPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <profile>SVC_Integration_API_Only</profile>
    <forgotPasswordRedirect>false</forgotPasswordRedirect>
    <lockoutInterval>30</lockoutInterval>
    <maxLoginAttempts>10</maxLoginAttempts>
    <minimumPasswordLength>15</minimumPasswordLength>
    <minimumPasswordLifetime>false</minimumPasswordLifetime>
    <obscure>false</obscure>
    <passwordComplexity>4</passwordComplexity>
    <passwordExpiration>0</passwordExpiration>
    <passwordHistory>0</passwordHistory>
    <passwordQuestion>1</passwordQuestion>
</ProfilePasswordPolicy>
```

`passwordExpiration` is `0` — never expires — because a rotating password breaks an unattended integration at an unpredictable hour. That forces `passwordHistory` to `0`: the guide states that if `passwordHistory` is `0`, `passwordExpiration` must be set to `0` (`api_meta.txt` L98773–98777). Valid `passwordExpiration` values are `0`, `30`, `60`, `90`, `180`, `365`; valid `lockoutInterval` values are `0`, `15`, `30`, `60`; valid `maxLoginAttempts` values are `0`, `3`, `5`, `10` (`api_meta.txt` L98724–98760).

## 4. Connected app naming the integration user as the client-credentials principal

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>MuleSoft Order Sync</label>
    <contactEmail>integration-platform@example.com</contactEmail>
    <oauthConfig>
        <callbackUrl>https://login.salesforce.com/services/oauth2/success</callbackUrl>
        <isClientCredentialEnabled>true</isClientCredentialEnabled>
        <oauthClientCredentialUser>svc.mulesoft.ordersync@example.com</oauthClientCredentialUser>
        <scopes>Api</scopes>
        <scopes>RefreshToken</scopes>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE</ipRelaxation>
    </oauthPolicy>
</ConnectedApp>
```

The element shape follows the guide's own `ConnectedApp` sample definition (`api_meta.txt` L36006–36037). `ipRelaxation` is `ENFORCE` — the default — which is what makes the profile's `loginIpRanges` above actually apply to app traffic: "Enforces the IP restrictions configured for the org, such as the IP ranges assigned to a user profile" (`api_meta.txt` L35655–35661). Setting `BYPASS` here quietly discards the entire IP allowlist you just deployed.

## 5. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SVC_Integration_API_Only</members>
        <name>Profile</name>
    </types>
    <types>
        <members>SVC_Integration_API_Only</members>
        <name>ProfileSessionSetting</name>
    </types>
    <types>
        <members>SVC_Integration_API_Only</members>
        <name>ProfilePasswordPolicy</name>
    </types>
    <types>
        <members>MuleSoft_Order_Sync</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>MuleSoft_Order_Sync</members>
        <name>ConnectedApp</name>
    </types>
    <!-- Retrieve the objects too: object and field permissions only come back
         when the related CustomObject is in the same package.
         api_meta.txt L95251-95254. -->
    <types>
        <members>Order</members>
        <members>OrderItem</members>
        <name>CustomObject</name>
    </types>
    <version>62.0</version>
</Package>
```

## 6. Retrieve and deploy

```bash
# Pull the current state before you change anything.
sf project retrieve start --manifest manifest/integration-user.xml --target-org prod

# Validate only — no metadata is written.
sf project deploy validate --manifest manifest/integration-user.xml --target-org prod

# Deploy for real once validation is clean.
sf project deploy start --manifest manifest/integration-user.xml --target-org prod
```

## 7. Create the User record over REST

The User record is data. Required fields on `User` are `Alias`, `Email`, `EmailEncodingKey`, `LanguageLocaleKey`, `LastName`, `LocaleSidKey`, `ProfileId`, `TimeZoneSidKey` and `Username` (`object_reference.txt` L295024–295872). `Username` "must be in the form of an email address, using all lowercase characters. It must also be unique across all organizations" (`object_reference.txt` L295869–295871).

```bash
curl https://MyDomainName.my.salesforce.com/services/data/v62.0/sobjects/User/ \
  -H "Authorization: Bearer ${SF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @integration-user.json
```

```json
{
  "Username": "svc.mulesoft.ordersync@example.com.prod",
  "LastName": "MuleSoft Order Sync (Service Account)",
  "Alias": "svcmoq",
  "Email": "integration-platform@example.com",
  "ProfileId": "00e5f000000XXXXAAA",
  "TimeZoneSidKey": "GMT",
  "LocaleSidKey": "en_GB",
  "EmailEncodingKey": "UTF-8",
  "LanguageLocaleKey": "en_US",
  "IsActive": true,
  "FederationIdentifier": "mulesoft-order-sync"
}
```

`Email` points at a monitored team alias while `Username` carries the org suffix, so a sandbox refresh cannot collide with the production username and password-reset mail still reaches a human. Note that `UserType` is not settable in this payload — it is a restricted picklist derived from the license (`object_reference.txt` L297100–297127), so the profile you name in `ProfileId` is what actually decides the user's category.

## 8. Verify the result

Three checks, in order. First, confirm the user landed on the intended profile and license — `ProfileId` is the lever, because "If you change the user's profile, the user's license also changes, because every profile belongs to exactly one user license type" (`object_reference.txt` L295693–295696):

```soql
SELECT Id, Username, IsActive, Profile.Name, Profile.UserLicense.Name,
       Profile.UserType, LastLoginDate
FROM User
WHERE Username = 'svc.mulesoft.ordersync@example.com.prod'
```

Second, confirm the permission set assignment and that no elevated permission arrived with it:

```soql
SELECT PermissionSet.Name, PermissionSet.IsOwnedByProfile,
       PermissionSet.PermissionsModifyAllData, PermissionSet.PermissionsViewAllData,
       PermissionSet.PermissionsApiEnabled, PermissionSet.HasActivationRequired
FROM PermissionSetAssignment
WHERE Assignee.Username = 'svc.mulesoft.ordersync@example.com.prod'
```

Third, confirm the integration is authenticating the way you configured it. `LoginType` and `LoginSubType` are the fields that prove the flow — `Oauth2` with subtype `OauthClientCredentials` for a client-credentials app, `Certificate` for a JWT bearer flow (`object_reference.txt` L176798–176812, L176849–176905):

```soql
SELECT LoginTime, LoginType, LoginSubType, Status, SourceIp, Application,
       ApiType, ApiVersion, TlsProtocol
FROM LoginHistory
WHERE UserId = '0055f00000XXXXXAAA'
  AND LoginTime = LAST_N_DAYS:7
ORDER BY LoginTime DESC
```

Read `Status` and `SourceIp` from the returned rows, never from a `WHERE` clause. `LoginHistory` is filterable only on `AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`, `LoginTime`, `LoginType`, `LoginUrl`, `NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol` and `UserId` (`object_reference.txt` L177012–177025) — a filter on `Status` or `SourceIp` fails, and `SourceIp` additionally rejects `LIKE` (`object_reference.txt` L176979).

In Setup, the equivalent visual check is Setup > Users > *the integration user*, confirming the Profile row, the Permission Set Assignments related list, and the Login History related list all agree with the three queries above.
