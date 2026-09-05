# Metadata Examples — Experience Cloud Member Management

Deployable shapes for site membership, the external member permission set, external-user creation, offboarding, and login-failure diagnosis. Element names, enum values and field properties below come from the Metadata API Developer Guide (`Network`, `PermissionSet`), the Object Reference (`NetworkMemberGroup`, `NetworkMember`, `User`, `UserLicense`, `LoginHistory`) and the Apex Reference Guide (`Site` class); the worked examples extend the guides' own sample definitions to a realistic two-audience site. Validate the metadata with:

```bash
python3 skills/admin/experience-cloud-member-management/scripts/check_experience_cloud_member_management.py --manifest-dir force-app/main/default
```

## Where the files live

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Site settings + membership | `Network` (`<members>Acme_Partners</members>`) | `networks/Acme_Partners.network-meta.xml` | 28.0+ |
| External member permission set | `PermissionSet` | `permissionsets/Partner_Site_Member.permissionset-meta.xml` | 22.0+ |
| External profile | `Profile` | `profiles/Partner Community Login User.profile-meta.xml` | — |
| Site URL container | `CustomSite` | `sites/Acme_Partners.site-meta.xml` | — |
| Self-reg handler | `ApexClass` | `classes/AcmeSelfRegHandler.cls` | — |

Network components live in the `networks` directory, the file name matches the site name and the extension is `.network` (Metadata API Developer Guide, `Network` § Declarative Metadata File Suffix and Directory Location, api_meta.txt L90679–90682).

## Network: the membership and registration block

`networkMemberGroups` is the whole of site membership. There is no other declarative way to make a user a member.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Network xmlns="http://soap.sforce.com/2006/04/metadata">
    <!-- Required fields: emailSenderAddress, emailSenderName, forgotPasswordTemplate,
         site, status, tabs (api_meta.txt L90745, L90767, L90923, L91180, L91188, L91213) -->
    <description>Acme partner and customer portal</description>
    <emailSenderAddress>portal@acme.example.com</emailSenderAddress>
    <emailSenderName>Acme Portal</emailSenderName>
    <forgotPasswordTemplate>unfiled$public/CommunityForgotPasswordEmailTemplate</forgotPasswordTemplate>
    <changePasswordTemplate>unfiled$public/CommunityChangePasswordEmailTemplate</changePasswordTemplate>
    <welcomeTemplate>unfiled$public/CommunityWelcomeEmailTemplate</welcomeTemplate>
    <site>Acme_Partners</site>
    <urlPathPrefix>partners</urlPathPrefix>
    <status>UnderConstruction</status>

    <!-- MEMBERSHIP. Every profile and permission set named here makes its
         assigned users members of the site. -->
    <networkMemberGroups>
        <profile>Partner Community Login User</profile>
        <profile>Customer Community Plus User</profile>
        <permissionSet>Partner_Site_Member</permissionSet>
        <permissionSet>Customer_Site_Member</permissionSet>
    </networkMemberGroups>

    <!-- SELF-REGISTRATION. selfRegProfile is read only when selfRegistration is true. -->
    <selfRegistration>true</selfRegistration>
    <selfRegProfile>Customer Community Plus User</selfRegProfile>
    <selfRegMicroBatchSubErrorEmailTemplate>unfiled$public/SelfRegMicroBatchError</selfRegMicroBatchSubErrorEmailTemplate>
    <sendWelcomeEmail>true</sendWelcomeEmail>

    <!-- INTERNAL USERS. Internal users are legitimate site members; this flag governs
         whether they may use their internal credentials on the site login page. -->
    <allowInternalUserLogin>true</allowInternalUserLogin>

    <!-- MEMBER VISIBILITY. Two independent switches: authenticated members seeing
         each other, and unauthenticated guests seeing authenticated members. -->
    <enableMemberVisibility>true</enableMemberVisibility>
    <enableGuestMemberVisibility>false</enableGuestMemberVisibility>
    <enableNicknameDisplay>true</enableNicknameDisplay>
    <enableInvitation>false</enableInvitation>

    <!-- REPUTATION. Only read when enableReputation is true. -->
    <enableReputation>true</enableReputation>
    <disableReputationRecordConversations>true</disableReputationRecordConversations>

    <tabs>
        <defaultTab>Home</defaultTab>
        <standardTab>Case</standardTab>
        <standardTab>Contact</standardTab>
    </tabs>
</Network>
```

### How to read it

- **`networkMemberGroups` takes `<profile>` and `<permissionSet>` children only** — the guide's own sample definition shows exactly those two element names repeated (api_meta.txt L91837–91844). "The profiles and permission sets that have access to the site. Users with these profiles or permission sets are members of the site." (api_meta.txt L90963–90965). A user with neither a listed profile nor a listed permission set is not a member, whatever else you configure.
- **The permission-set route has one documented exclusion:** "If a Chatter customer (from a customer group) is assigned a permission set that is also associated with a site, the Chatter customer isn't added to the site." (api_meta.txt L90967–90970; repeated in the Object Reference, `NetworkMemberGroup`, object_reference.txt L188599–188601).
- **`selfRegProfile` is conditional:** "The profile assigned to users who self-register. This value is used only if `selfRegistration` is enabled for the site." (api_meta.txt L91163–91165). Setting `selfRegProfile` with `selfRegistration` false is inert, not an error — the checker flags the reverse (self-reg on, no profile).
- **The self-registration *default account* is not a `Network` field.** The `Network` field table has no default-account element; the account is supplied at runtime as the `accountId` argument to `Auth.ConfigurableSelfRegHandler.createUser` and passed on to `Site.createExternalUser(user, accountId, password)` (apexrefguide.txt L6580–6598, L231089–231095). UNVERIFIED (2026-09-05): the extracted guides do not name the Setup field or the Metadata API element that stores the site's configured default new-user account, so treat that value as UI/Tooling-managed and assert it in a post-deploy check rather than in the `Network` file.
- **`allowInternalUserLogin`** — "Determines whether internal users can log in with their internal credentials on the site login page. Available in API version 40.0 and later." (api_meta.txt L90687–90689). It governs *credentials*, not membership.
- **`enableMemberVisibility`** — "Controls user visibility on a per-site basis. If true, the *See other members of this site* preference is enabled for the selected site. Available in API version 45.0 and later." (api_meta.txt L90873–90876). `enableGuestMemberVisibility` is the separate guest-facing switch: "Determines if unauthenticated guest users can see the authenticated members" (api_meta.txt L90858–90860).
- **`enableNicknameDisplay`** — "Determines if user nicknames display instead of their first and last names in most places in the site. Set to false by default." (api_meta.txt L90878–90881). `User.CommunityNickname` is the "Unique name used to identify this user in the Experience Cloud site" (object_reference.txt L295064–295069), and the Apex `Site` class requires it: "The nickname field is required for the User sObject when using the createExternalUser method." (apexrefguide.txt L231081).
- **`disableReputationRecordConversations`** — "When reputation levels are enabled for the site, determines whether to exclude contributions to records when counting points toward reputation levels." (api_meta.txt L90738–90742). It is read only when `enableReputation` is true.
- **`status`** — `Live`, `DownForMaintenance`, `UnderConstruction`. "After a site is published, it can never be in this status again" applies to `UnderConstruction` (api_meta.txt L91188–91212). Deploy new sites as `UnderConstruction`, flip to `Live` in a follow-up deploy once membership is verified.
- **`emailSenderAddress` cannot be updated by Metadata API.** "You can add the sender email address via the `emailSenderAddress` field only when you deploy `Network` for the first time... If you attempt to update this field via Metadata API, your changes are ignored and Salesforce doesn't show an error." (api_meta.txt L90750–90763).

## PermissionSet: an external member group

A permission set named in `networkMemberGroups` grants membership to everyone assigned it, so this file is a membership boundary as much as an access boundary. Element names follow the guide's `PermissionSet` sample definition (api_meta.txt L95195–95235).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Partner Site Member</label>
    <description>Site membership + deal registration access for Acme partner users.</description>
    <hasActivationRequired>false</hasActivationRequired>

    <!-- Documented user permissions only. ApiEnabled and ViewRoles both appear
         verbatim in the guide's PermissionSet samples (api_meta.txt L95216, L95388). -->
    <userPermissions>
        <enabled>true</enabled>
        <name>ApiEnabled</name>
    </userPermissions>

    <objectPermissions>
        <allowCreate>true</allowCreate>
        <allowDelete>false</allowDelete>
        <allowEdit>true</allowEdit>
        <allowRead>true</allowRead>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllFields>false</viewAllFields>
        <viewAllRecords>false</viewAllRecords>
        <object>Deal_Registration__c</object>
    </objectPermissions>

    <fieldPermissions>
        <editable>true</editable>
        <field>Deal_Registration__c.Estimated_Value__c</field>
        <readable>true</readable>
    </fieldPermissions>

    <tabSettings>
        <tab>Deal_Registration__c</tab>
        <visibility>Available</visibility>
    </tabSettings>
</PermissionSet>
```

How to read it:

- **`label` is the only element the field table marks Required** (api_meta.txt L94824). `license` is optional: "Either the related permission set license or the user license associated with this permission set... Use this field instead of `userLicense`, which is deprecated and only available up to API Version 37.0." (api_meta.txt L94825–94830). UNVERIFIED (2026-09-05): the guides do not state whether omitting `license` lets one permission set be assigned across two different external user licenses — verify in a sandbox before using a single member permission set for both a Customer Community and a Partner Community audience.
- **`userPermissions` is deploy-destructive from API 40.0:** "In API Version 40.0 and later, if a permission isn't specified for a deployment, it's disabled." (api_meta.txt L94863–94869). Retrieve the live permission set before editing; a partial file silently strips permissions.
- **Retrieve dependencies with the permission set.** "When you retrieve permission sets, also retrieve the related components with assigned permissions. For example, to retrieve `objectPermissions` and `fieldPermissions` for a custom object, you must also retrieve the `CustomObject` component." (api_meta.txt L95250–95253).

## Creating external users

### The Apex path (`Site.createExternalUser`)

`Site` exposes three `createExternalUser` overloads plus the older `createPortalUser` (apexrefguide.txt L231052, L231095, L231141, L231258):

```apex
public static Id createExternalUser(SObject user, String accountId)
public static Id createExternalUser(SObject user, String accountId, String password)
public static Id createExternalUser(SObject user, String accountId, String password,
                                    Boolean sendEmailConfirmation)
public static ID createPortalUser(sObject user, String accountId, String password,
                                  Boolean sendEmailConfirmation)   // legacy
```

"If you're using API version 34.0 or later, we recommend using the `createExternalUser()` methods because they offer better error handling than this method." (apexrefguide.txt L231282–231283). All four require `CommunityNickname` and all four are "only valid when a site is associated with a Customer Portal" (apexrefguide.txt L231081, L231085, L231284).

The contact-matching rule is documented per overload and decides whether a contact is created or reused:

> "The email address of the user is used to look for matching contacts associated with the specified `accountId`. If a matching contact is found and is already used by an external user, self-registration isn't successful. If a matching contact is found but isn't used by an external user, it is used for the new external user. If there is no matching contact, a new contact is created for the new external user." (apexrefguide.txt L231074–231077)

Bulk-enable already-vetted contacts under one account:

```apex
public with sharing class ExternalUserProvisioner {

    // Site.createExternalUser throws Site.ExternalUserCreateException on failure
    // (apexrefguide.txt L231079) and does NOT auto-commit in API 30.0+
    // (apexrefguide.txt L231085-231087), so a Savepoint is meaningful here.
    public static List<Id> enableContacts(List<Contact> contacts, Id accountId, Id profileId) {
        List<Id> created = new List<Id>();
        for (Contact c : contacts) {
            Savepoint sp = Database.setSavepoint();
            try {
                User u = new User(
                    ProfileId         = profileId,
                    ContactId         = c.Id,          // contact MUST have an AccountId
                    FirstName         = c.FirstName,
                    LastName          = c.LastName,
                    Email             = c.Email,
                    Username          = c.Email + '.acmeptr',
                    Alias             = buildAlias(c),
                    CommunityNickname = buildNickname(c),
                    TimeZoneSidKey    = 'Europe/London',
                    LocaleSidKey      = 'en_GB',
                    LanguageLocaleKey = 'en_US',
                    EmailEncodingKey  = 'UTF-8',
                    IsActive          = true
                );
                // password null => Salesforce emails a set-password link
                created.add(Site.createExternalUser(u, accountId, null, true));
            } catch (Site.ExternalUserCreateException e) {
                Database.rollback(sp);
                ApplicationLogger.error('ExternalUserProvisioner', c.Id, e);
            }
        }
        return created;
    }

    private static String buildAlias(Contact c)    { return c.LastName.left(8); }
    private static String buildNickname(Contact c) { return (c.LastName + c.Id).right(40); }
}
```

`ContactId` is createable and updateable, and "The contact must have a value in the `AccountId` field or an error occurs." (object_reference.txt L295089–295096). `User.AccountId` itself is read-only — its properties are Filter, Group, Nillable, Sort with no Create or Update (object_reference.txt L294996–294999) — so you link a user to an account through the contact, never directly.

### The Data Loader path

```csv
ContactId,ProfileId,Username,Email,Alias,CommunityNickname,FirstName,LastName,TimeZoneSidKey,LocaleSidKey,LanguageLocaleKey,EmailEncodingKey,IsActive
003XX000004TmiQ,00eXX0000015SxT,rgarcia@northwind.example.com.acmeptr,rgarcia@northwind.example.com,rgarcia,rgarcia_nw_01,Rosa,Garcia,America/Los_Angeles,en_US,en_US,UTF-8,TRUE
003XX000004TmiR,00eXX0000015SxT,tokafor@northwind.example.com.acmeptr,tokafor@northwind.example.com,tokafor,tokafor_nw_02,Tunde,Okafor,America/New_York,en_US,en_US,UTF-8,TRUE
```

Column rules, all from the Object Reference `User` field table:

| Column | Why it is in the file |
|---|---|
| `ContactId` | The only way to bind the user to an account; the contact must already have an `AccountId` (L295089–295096) |
| `ProfileId` | Required. "If you change the user's profile, the user's license also changes, because every profile belongs to exactly one user license type." (L295686–295693) |
| `Username` | Required, must be an email-form value in all lowercase, unique across **all** Salesforce orgs (L295865–295872) |
| `Email`, `Alias`, `LastName` | `Email` and `Alias` are marked Required (L295216–295222, L295019–295024) |
| `CommunityNickname` | "Unique name used to identify this user in the Experience Cloud site" (L295064–295069) |
| `TimeZoneSidKey`, `LocaleSidKey`, `LanguageLocaleKey`, `EmailEncodingKey` | Required restricted picklists (L295837, L295525, L295460, L295223) |

**`UserType` is deliberately absent.** Its properties are Filter, Group, Nillable, Sort, Restricted picklist — no Create and no Update (object_reference.txt L297100–297104). You cannot set it on insert; it is derived from the profile's user license, and the `Profile` object adds "In API version 53.0 and later, you can't set the value of `UserType` using Apex." (object_reference.txt L232482). Verify it after the load instead:

```sql
SELECT Id, Username, UserType, Profile.Name, Profile.UserLicense.Name, ContactId, Contact.AccountId
FROM User
WHERE ContactId != null AND CreatedDate = TODAY
```

Expect `PowerPartner` for Partner Community profiles, `CspLitePortal` for High Volume Portal, `CustomerSuccess`/`PowerCustomerSuccess` for Customer Portal profiles (object_reference.txt L297106–297122). A row that comes back `Standard` means the CSV pointed at an internal profile.

Set Data Loader's **Import batch size** to 200 or less for a SOAP insert — "The maximum import batch size is 200 records for SOAP API and 10000 records for Bulk API" (salesforce_data_loader.txt L351–L353).

## Offboarding an external user

Users are never deleted: "You can't delete a user in the user interface or the API. You can deactivate a user in the user interface; and you can deactivate or disable a Customer Portal or partner portal user in the user interface or the API." (object_reference.txt L297169–297172).

```apex
// 1. Reassign owned records BEFORE deactivating.
List<Case> owned = [SELECT Id FROM Case WHERE OwnerId = :leaverId];
for (Case c : owned) { c.OwnerId = fallbackQueueId; }
update owned;

// 2. Deactivate. This is the offboarding action - there is no delete.
update new User(Id = leaverId, IsActive = false);
```

Verify the seat came back:

```sql
SELECT Name, MasterLabel, TotalLicenses, UsedLicenses, MonthlyLoginsEntitlement, MonthlyLoginsUsed
FROM UserLicense
WHERE Name IN ('PID_Partner_Community', 'PID_Partner_Community_Login',
               'PID_Customer_Community', 'PID_Customer_Community_Login')
```

- `UsedLicenses` is "The number of user licenses that are assigned to **active** users in the organization." (object_reference.txt L299669–299672) — so deactivation does reduce it.
- `MonthlyLoginsEntitlement` is "The maximum number of customer or partner portal logins allowed per month. A **null** value in this field means the user license is charged according to the number of users rather than the number of logins." (object_reference.txt L299611–299616). Both login fields need Digital Experiences enabled and the View Setup and Configuration permission to be visible and queryable.
- `UsedLicenses` "isn't filterable in API version 64.0 or later when using it in a WHERE clause in a SOQL query. Instead, you have to process the data after fetching all the records." (object_reference.txt L299672–299675) — filter on `Name`, sort in your client.

### The offboarding checklist artifact

The checker validates any `*offboard*.json` under the manifest directory against this shape (one object, or an array of them). It exists because two of the steps have no undo: records must move before `IsActive = false`, and the username is burned for good.

```json
[
  {
    "username": "rgarcia@northwind.example.com.acmeptr",
    "contactId": "003XX000004TmiQ",
    "recordsReassignedTo": "00GXX0000012abc",
    "deactivated": true,
    "membershipGroupsReviewed": true,
    "usernameRetired": true
  }
]
```

| Key | What it records |
|---|---|
| `username` | Which user; also the key that can never be reused (object_reference.txt L295865–295872) |
| `contactId` | The contact the external user hangs off — deactivating the user does not touch the Contact |
| `recordsReassignedTo` | The queue or user that owned records moved to, captured **before** deactivation |
| `deactivated` | The `IsActive = false` step itself; there is no delete (object_reference.txt L297169–297170) |
| `membershipGroupsReviewed` | Whether the site still needs this person's profile or permission set in `networkMemberGroups` — one leaver rarely justifies a group removal, but the question must be asked |
| `usernameRetired` | Explicit acknowledgement that a returning person needs a new username |

The checker errors when `deactivated` is true and `recordsReassignedTo` is absent, which is the ordering mistake this artifact exists to prevent.

### Membership rows

`NetworkMember` supports only `describeSObjects()`, `query()`, `retrieve()`, `update()` (object_reference.txt L188302–188303). There is no create and no delete: you cannot add or remove one member. Audit who is a member of what:

```sql
SELECT NetworkId, MemberId, Member.Username, Member.IsActive, LastChatterActivityDate
FROM NetworkMember
WHERE NetworkId = '0DBXX0000004CAa'
```

Membership itself is changed through `NetworkMemberGroup`, which supports `create()`, `describeSObjects()`, `query()`, `retrieve()`, `update()` — "the `upsert()` call is not supported for this object" and there is no `delete()` (object_reference.txt L188608–188612):

```sql
SELECT Id, NetworkId, ParentId, AssignmentStatus FROM NetworkMemberGroup
WHERE NetworkId = '0DBXX0000004CAa'
```

To detach a profile or permission set from a site you **update** the row rather than deleting it, setting `AssignmentStatus` to the remove status — the Object Reference's own sample sets `WaitingForRemove` (object_reference.txt L188689–188691). The picklist values are `Add Calculated`, `Added`, `Failed Add`, `Failed Remove`, `Remove Calculated`, `Waiting for Add`, `Waiting for Remove`; "Profiles and permission sets are added and removed asynchronously, so you can also check the status" (object_reference.txt L188625–188648, L188673–188675). A site that looks half-configured after a deploy is usually sitting on `Waiting for Add`.

## Diagnosing external login failures

```sql
SELECT UserId, LoginTime, LoginType, Status, Application, Browser,
       SourceIp, CountryIso, LoginUrl, TlsProtocol
FROM LoginHistory
WHERE NetworkId = '0DBXX0000004CAa'
  AND LoginTime > LAST_N_DAYS:7
ORDER BY LoginTime DESC
```

- `NetworkId` is "The ID of the Experience Cloud site that the user is logging in to. This field is available in API version 31.0 and later, if Salesforce Experience Cloud sites are enabled for your org." (object_reference.txt L176984–176989) — it is the only reliable way to scope login history to one site.
- **`Status` is not filterable.** The guide lists the filterable fields exactly: `AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`, `LoginTime`, `LoginType`, `LoginUrl`, `NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol`, `UserId` (object_reference.txt L177041–177054). `Status` — "either success or a reason for failure" (object_reference.txt L176981–176983) — must be filtered client-side. `WHERE Status = 'Invalid Password'` fails to compile.
- **Read `LoginType` to see which door the user came through** (object_reference.txt L176863–176899). The site-relevant values are `ChatterCommunityPortalUnPwd` (Chatter Communities External User), `ChatterCommunityThirdPartySso`, `SamlChatterNetworks` (SAML Chatter Communities External User SSO), `EmployeeLoginToCommunity` (Employee Login to Community), `NetworksPortalApiOnly`, `PasswordlessLogin`, plus the legacy portal values `Portal`, `PortalThirdPartySso`, `PrmPortal`, `PrmPortalThirdPartySso`, `SamlCspPortal`, `SamlPrmPortal`, `SamlSite`. Rows arriving as `Application` or `Oauth2` are not site logins at all.
- Access is restricted: "only users with Manage Users or Monitor Login History permissions can access this object", except that "in API version 37.0 and later, all users can retrieve their own login history records" (object_reference.txt L176634–176638).

`EmployeeLoginToCommunity` rows against your site are the fastest confirmation that internal users really are members — see gotcha 6.

## package.xml and deploy order

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Partner Community Login User</members>
        <members>Customer Community Plus User</members>
        <name>Profile</name>
    </types>
    <types>
        <members>Partner_Site_Member</members>
        <members>Customer_Site_Member</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>AcmeSelfRegHandler</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Acme_Partners</members>
        <name>CustomSite</name>
    </types>
    <types>
        <members>Acme_Partners</members>
        <name>Network</name>
    </types>
    <version>62.0</version>
</Package>
```

Order matters because `networkMemberGroups` and `selfRegProfile` are references: every profile and permission set the `Network` file names must already exist in the target org or be in the same deployment.

1. `Profile`, `PermissionSet`, `ApexClass` (the self-reg handler compiles independently).
2. `CustomSite` — `Network.site` is a required reference to it (api_meta.txt L91180–91181).
3. `Network` with `status` `UnderConstruction`.
4. Verify (below), then a second deploy flipping `status` to `Live`.

```bash
# retrieve what is live before editing - permission sets deploy destructively
sf project retrieve start -m "Network:Acme_Partners" -m "PermissionSet:Partner_Site_Member" -o prod

# validate only
sf project deploy start -x manifest/package.xml -o prod --dry-run

sf project deploy start -x manifest/package.xml -o prod
```

## Verification

Run all three after the first deploy, before flipping `status` to `Live`:

```bash
sf data query -o prod -q "SELECT Id, ParentId, AssignmentStatus FROM NetworkMemberGroup WHERE NetworkId = '0DBXX0000004CAa'"
```

1. Every row reads `Added` — not `Waiting for Add`, not `Failed Add`. Membership is applied asynchronously, so a run immediately after the deploy will legitimately show `Waiting for Add`; re-run until it settles.
2. `SELECT Name, TotalLicenses, UsedLicenses FROM UserLicense` shows enough headroom for the planned user volume. Exceeding it is a hard failure, not a warning: "Each inserted User also counts as a license. Every organization has a maximum number of licenses. If you attempt to exceed the maximum number of licenses by inserting User records, the create request is rejected." (object_reference.txt L295872–295875).
3. Setup > Digital Experiences > *[site]* > Administration > Members lists the same profiles and permission sets that appear in `networkMemberGroups`. A profile in the file but not in Setup means the async add failed.
