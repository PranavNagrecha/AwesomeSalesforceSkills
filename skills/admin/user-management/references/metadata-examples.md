# Metadata Examples — User Management

## Start here: users are data, not metadata

There is no `User` metadata type. The Object Reference is explicit that User records are not
configuration: "Unlike other objects, the records in the User table represent actual
users—not data owned by users" (Object Reference, User → Usage). That single fact decides the whole
toolchain for this skill:

| Artefact | Deployable via Metadata API? | How you actually move it |
|---|---|---|
| The user themselves (`User`) | No | CSV + Data Loader / Bulk API 2.0, `composite/sobjects`, or Apex in a test |
| Freeze state (`UserLogin.IsFrozen`) | No | **update** only — `UserLogin` supports `describeSObjects()`, `query()`, `retrieve()`, `update()` and nothing else |
| Permission set assignment (`PermissionSetAssignment`) | No | `create()` / `delete()` / `update()` |
| Permission set licence assignment (`PermissionSetLicenseAssign`) | No | `create()` / `delete()` only — there is no `update()` |
| The role the user sits in (`Role`) | **Yes** — `.role` files in the `roles/` directory | `sf project deploy start` |
| The profile that carries the licence, login hours, IP ranges (`Profile`) | **Yes** | `sf project deploy start` |

So a "user management change" is normally two deploys and a data load, in that order: deploy the
`Role` and `Profile` metadata, then load the `User` rows that point at them, then assign permission
sets. The rest of this file gives one artefact per step.

---

## 1. The user CSV

Nine columns are non-negotiable. Every one of these is marked **Required** in the Object Reference's
User field table: `Username`, `LastName`, `Email`, `Alias`, `TimeZoneSidKey`, `LocaleSidKey`,
`EmailEncodingKey`, `LanguageLocaleKey`, `ProfileId`. `UserPermissionsMarketingUser` is also
documented as Required, so include it explicitly rather than letting it default.

```csv
Username,LastName,FirstName,Email,Alias,TimeZoneSidKey,LocaleSidKey,EmailEncodingKey,LanguageLocaleKey,ProfileId,UserRoleId,ManagerId,FederationIdentifier,UserPermissionsMarketingUser,IsActive
avargas@northwind.com,Vargas,Ana,ana.vargas@northwind.com,avargas,America/Los_Angeles,en_US,UTF-8,en_US,00e5g000001AbCdAAK,00E5g000000XyZaEAK,0055g00000QqRstAAO,ana.vargas@northwind.com,false,true
tokafor@northwind.com,Okafor,Tunde,tunde.okafor@northwind.com,tokafor,Europe/London,en_GB,UTF-8,en_US,00e5g000001AbCdAAK,00E5g000000XyZbEAK,0055g00000QqRstAAO,tunde.okafor@northwind.com,false,true
lchen@northwind.com,Chen,Lian,lian.chen@northwind.com,lchen,Asia/Singapore,en_SG,UTF-8,en_US,00e5g000001AbCeAAK,,0055g00000QqRstAAO,lian.chen@northwind.com,false,true
```

**How to read it**

- `Username` "must be in the form of an email address, using all lowercase characters. It must also
  be unique across all organizations." It is deliberately *not* the same string as `Email` here —
  `Email` is where password resets and notifications land, `Username` is only a login key. Keeping
  them different is what lets you suffix sandbox usernames without breaking anyone's mail.
- `TimeZoneSidKey`, `LocaleSidKey`, `LanguageLocaleKey` and `EmailEncodingKey` are all **restricted
  picklists**. A typo is a row-level failure, not a silent default. The Object Reference's own advice
  is to "manually set one User time zone in the user interface, and then use that value for creating
  or updating other User records via the API" — copy a known-good value rather than guessing the
  ISO spelling.
- `LocaleSidKey` "affects formatting and parsing of values, especially numeric values, in the user
  interface. It doesn't affect the API." Row 3 differs from row 2 in locale but not language: Lian
  reads English and sees Singapore number and date formats.
- `UserRoleId` is blank on row 3 on purpose. It is `Nillable`; the other two are not blank because
  those users need role-hierarchy visibility. See `references/gotchas.md` on what "no role" costs.
- `FederationIdentifier` only does anything when the SAML User ID Type is *Assertion contains
  Federation ID from the User record*; the Object Reference says that otherwise "this field can't be
  edited." Populate it during the load anyway if SSO is on the roadmap — retro-fitting it across
  hundreds of rows later is a second load.
- `IsActive` is `Defaulted on create`. Setting it explicitly documents intent and makes the row
  reusable as an update later.

### Resolving `ProfileId` and `UserRoleId` from names

Do not hand-type 18-character IDs. Export them first and join. Both `Profile.Name` and
`UserRole.Name` carry the `idLookup` property, which the Object Reference defines as "can be used to
specify a record in an upsert call" — the same property that makes them safe, stable join keys.

```sql
SELECT Id, Name, UserType, UserLicenseId
FROM Profile
WHERE Name IN ('Northwind Sales User', 'Northwind Service User')

SELECT Id, Name, DeveloperName, ParentRoleId
FROM UserRole
ORDER BY DeveloperName
```

### Loading it

`User` supports `create()`, `update()` **and `upsert()`**, and `Username` is `idLookup` — so the
second run of a provisioning job can be an upsert keyed on `Username` instead of a create that
fails on every existing row.

```bash
# Insert: 200/batch on SOAP, 10,000/batch on Bulk API; Bulk API 2.0 sizes batches itself
sf data import bulk --sobject User --file users.csv --target-org prod --wait 10

# Re-runnable provisioning: upsert on the idLookup field
sf data upsert bulk --sobject User --external-id Username --file users.csv --target-org prod --wait 10
```

> **Blank cells do not clear fields under Bulk API.** The Data Loader guide states that "empty field
> values are ignored when you update records using either API. To set a field value to null when
> either API option is selected, use a field value of `#N/A` in the import CSV file." Leaving
> `UserRoleId` empty on an *update* leaves the old role in place. Write `#N/A` to actually remove it.

---

## 2. The `Role` metadata file

`Role` components have the `.role` suffix and live in the `roles` directory. The shape below is the
guide's own sample definition extended with `parentRole` — the field that actually builds the
hierarchy, and the one the sample omits.

`force-app/main/default/roles/Northwind_Sales_AMER.role-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Role xmlns="http://soap.sforce.com/2006/04/metadata">
    <caseAccessLevel>None</caseAccessLevel>
    <contactAccessLevel>Edit</contactAccessLevel>
    <description>AMER field sales reps. Reports into Northwind_Sales_Global.</description>
    <mayForecastManagerShare>false</mayForecastManagerShare>
    <name>Sales — AMER</name>
    <opportunityAccessLevel>Read</opportunityAccessLevel>
    <parentRole>Northwind_Sales_Global</parentRole>
</Role>
```

**How to read it**

- The file name *is* `fullName`. `Northwind_Sales_AMER.role-meta.xml` produces the API name; `<name>`
  is the human label ("Required. The name of the role or territory"). They are allowed to differ and
  usually should — labels get renamed, API names should not.
- `parentRole` is "the role above this role in the hierarchy." Omit it and the role lands at the top
  level. Deploy parents before children, or in the same deploy.
- `caseAccessLevel`, `contactAccessLevel` and `opportunityAccessLevel` govern access to *other users'*
  records "that are associated with accounts the user owns" — valid values `Read`, `Edit`, `None`.
  The guide notes each field "is not visible if your organization's sharing model" for that object is
  Public Read/Write, so setting `caseAccessLevel` in an org with Public Read/Write Cases is inert.
- `Role` supports the `*` wildcard in `package.xml`.

---

## 3. Profile: the licence, the login window, the IP allowlist

Only the three user-management-relevant sections are shown. The root element and namespace are real,
so this parses on its own, but a deployed profile carries far more.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: force-app/main/default/profiles/Northwind Sales User.profile-meta.xml
     Only userLicense, loginHours and loginIpRanges are shown. A real retrieved profile
     also contains objectPermissions, fieldPermissions, layoutAssignments and more. -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>
    <userLicense>Salesforce</userLicense>
    <loginHours>
        <mondayStart>420</mondayStart>
        <mondayEnd>1320</mondayEnd>
        <tuesdayStart>420</tuesdayStart>
        <tuesdayEnd>1320</tuesdayEnd>
        <wednesdayStart>420</wednesdayStart>
        <wednesdayEnd>1320</wednesdayEnd>
        <thursdayStart>420</thursdayStart>
        <thursdayEnd>1320</thursdayEnd>
        <fridayStart>420</fridayStart>
        <fridayEnd>1320</fridayEnd>
    </loginHours>
    <loginIpRanges>
        <description>Northwind HQ egress</description>
        <startAddress>203.0.113.0</startAddress>
        <endAddress>203.0.113.255</endAddress>
    </loginIpRanges>
    <loginIpRanges>
        <description>Northwind VPN concentrator</description>
        <startAddress>198.51.100.10</startAddress>
        <endAddress>198.51.100.20</endAddress>
    </loginIpRanges>
</Profile>
```

**How to read it**

- `userLicense` is "The User License for the profile. A user license determines the baseline of
  features that the user can access. Every user must have exactly one user license." It is the field
  that couples profile and licence — which is why the User field table warns that "if you change the
  user's profile, the user's license also changes, because every profile belongs to exactly one user
  license type."
- Login-hour values are **minutes since midnight** and "must be evenly divisible by 60 (full hours)."
  `420` = 07:00, `1320` = 22:00. `825` is rejected. If a day's start is given its end must be too,
  and start can't exceed end.
- Saturday and Sunday are simply absent, which blocks weekend login for this profile.
- `loginIpRanges` repeats; `startAddress` and `endAddress` are both Required, `description` is
  optional and available in API version 31.0 and later.
- **To remove login hours you must deploy an empty `<loginHours/>` element.** The guide: "To delete
  login hour restrictions from a profile that previously had them, you must explicitly include an
  empty `loginHours` tag without any start or end times." Omitting the element leaves the existing
  restriction in place.

Login restrictions live on the profile and therefore apply to every user who shares it. If you need
per-user or risk-based control instead, that is `security/ip-range-and-login-flow-strategy` and
`security/mfa-enforcement-patterns`, not this skill.

---

## 4. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Northwind_Sales_Global</members>
        <members>Northwind_Sales_AMER</members>
        <members>Northwind_Sales_EMEA</members>
        <name>Role</name>
    </types>
    <types>
        <members>Northwind Sales User</members>
        <members>Northwind Service User</members>
        <name>Profile</name>
    </types>
    <version>62.0</version>
</Package>
```

`Role` supports `<members>*</members>`. Prefer the explicit list anyway: a wildcard retrieve of
`Role` in a large org pulls every portal role too, and portal roles cannot be updated
("You can't update any field for a portal role").

```bash
# Pull current state into source before editing
sf project retrieve start --manifest manifest/package.xml --target-org my-sandbox

# Validate without deploying — roles and profiles both trigger sharing work
sf project deploy validate --manifest manifest/package.xml --target-org my-sandbox

sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

---

## 5. Creating a user in Apex (test context)

`User` is a setup sObject. Inserting one alongside an ordinary sObject in the same transaction raises
the mixed-DML error. The Apex Developer Guide's own framing: the `System.runAs` block "creates a test
user with a role and a test account, which is a mixed DML operation" — and wrapping it in `runAs` is
what makes it legal.

```apex
@IsTest
private class UserProvisioningTest {

    @IsTest
    static void reassignsOpenWorkOnDeactivation() {
        User me = [SELECT Id FROM User WHERE Id = :UserInfo.getUserId()];

        User departing;
        Account book;

        // Setup + non-setup DML together is only legal inside runAs.
        System.runAs(me) {
            Profile p = [SELECT Id FROM Profile WHERE Name = 'Standard User' WITH USER_MODE];
            UserRole r = [SELECT Id FROM UserRole WHERE DeveloperName = 'Northwind_Sales_AMER' WITH USER_MODE];

            // Unique username: it must be globally unique across ALL orgs, sandboxes included.
            String uniqueUserName = 'nwleaver' + DateTime.now().getTime() + '@northwind.test';

            departing = new User(
                Alias             = 'nwleave',
                Email             = 'leaver@northwind.test',
                EmailEncodingKey  = 'UTF-8',
                LastName          = 'Leaver',
                LanguageLocaleKey = 'en_US',
                LocaleSidKey      = 'en_US',
                ProfileId         = p.Id,
                UserRoleId        = r.Id,
                TimeZoneSidKey    = 'America/Los_Angeles',
                UserName          = uniqueUserName
            );
            insert departing;

            book = new Account(Name = 'Northwind Retail');
            insert book;
        }

        System.runAs(departing) {
            Test.startTest();
            OffboardingService.reassignOpenWork(departing.Id, me.Id);
            Test.stopTest();
        }

        Assert.areEqual(
            me.Id,
            [SELECT OwnerId FROM Account WHERE Id = :book.Id].OwnerId,
            'Open account should have moved to the surviving owner'
        );
    }
}
```

**How to read it**

- The username is built from `DateTime.now().getTime()` because global uniqueness spans sandboxes,
  and a hard-coded test username collides the moment the org is cloned.
- `runAs` "ignores user license limits. You can create users with `runAs` even if your organization
  has no additional user licenses." A green test proves nothing about production licence headroom —
  check `UserLicense` for that (section 7).
- "Every call to `runAs` counts against the total number of DML statements issued in the process,"
  so a loop of `runAs` calls burns the DML governor.
- `WITH USER_MODE` on the Profile and UserRole queries keeps the setup lookups honest about
  permissions; see `apex/soql-security` territory rather than freestyling `without sharing`.

---

## 6. Provisioning over REST (`composite/sobjects`)

```http
POST /services/data/v62.0/composite/sobjects
Authorization: Bearer <token>
Content-Type: application/json

{
  "allOrNone" : true,
  "records" : [
    {
      "attributes"        : { "type" : "User" },
      "Username"          : "avargas@northwind.com",
      "LastName"          : "Vargas",
      "FirstName"         : "Ana",
      "Email"             : "ana.vargas@northwind.com",
      "Alias"             : "avargas",
      "TimeZoneSidKey"    : "America/Los_Angeles",
      "LocaleSidKey"      : "en_US",
      "EmailEncodingKey"  : "UTF-8",
      "LanguageLocaleKey" : "en_US",
      "ProfileId"         : "00e5g000001AbCdAAK",
      "UserRoleId"        : "00E5g000000XyZaEAK",
      "UserPermissionsMarketingUser" : false
    },
    {
      "attributes"        : { "type" : "User" },
      "Username"          : "tokafor@northwind.com",
      "LastName"          : "Okafor",
      "Email"             : "tunde.okafor@northwind.com",
      "Alias"             : "tokafor",
      "TimeZoneSidKey"    : "Europe/London",
      "LocaleSidKey"      : "en_GB",
      "EmailEncodingKey"  : "UTF-8",
      "LanguageLocaleKey" : "en_US",
      "ProfileId"         : "00e5g000001AbCdAAK",
      "UserPermissionsMarketingUser" : false
    }
  ]
}
```

**How to read it**

- Cap is 200 records per call, and "objects are created in the order they're listed."
- **Every record in this payload is a `User` on purpose.** The REST guide states: "You can't create
  records for multiple object types in one call when one of the types is related to a feature in the
  Salesforce Setup area." That is mixed DML wearing a REST hat — you cannot batch Users together
  with Accounts, and you cannot batch Users together with their `PermissionSetAssignment` rows.
  Permission sets are a second call, after the User IDs come back.
- `allOrNone: true` is the right default for a provisioning batch. With `false`, a partial success
  leaves you reconciling which of 200 usernames landed — and usernames are globally unique, so the
  retry of a "failed" row that actually succeeded fails again on duplicate username.
- To make the call re-runnable, `PATCH /composite/sobjects/User/Username` upserts on the `idLookup`
  field instead (also capped at 200).

---

## 7. Verifying licences before you load

Run these *before* the CSV, not after the error. "Each inserted User also counts as a license. Every
organization has a maximum number of licenses. If you attempt to exceed the maximum number of
licenses by inserting User records, the create request is rejected."

```sql
-- User licences: UsedLicenses counts licences "assigned to ACTIVE users"
SELECT Name, MasterLabel, LicenseDefinitionKey, Status, TotalLicenses, UsedLicenses
FROM UserLicense
WHERE Status = 'Active'
ORDER BY MasterLabel

-- Permission set licences: UsedLicenses counts licences "currently assigned to users"
-- (no active-user qualifier -- a deactivated user still holds a PSL)
SELECT MasterLabel, DeveloperName, ExpirationDate, TotalLicenses, UsedLicenses
FROM PermissionSetLicense
ORDER BY MasterLabel

-- Who holds a scarce PSL, and are they still active?
SELECT Assignee.Username, Assignee.IsActive, PermissionSetLicense.MasterLabel
FROM PermissionSetLicenseAssign
WHERE PermissionSetLicense.DeveloperName = 'EinsteinAnalyticsPlusPsl'
ORDER BY Assignee.IsActive, Assignee.Username
```

> Do not write `WHERE UsedLicenses >= TotalLicenses`. `UserLicense.UsedLicenses` "isn't filterable in
> API version 64.0 or later when using it in a `WHERE` clause in a SOQL query. Instead, you have to
> process the data after fetching all the records." Fetch all rows and compare in your client.

Reading `PermissionSetLicense` needs *View Setup and Configuration*; reading
`PermissionSetLicenseAssign` needs *View Setup and Configuration* or *Assign Permission Sets*
(Summer '20 and later). A delegated admin without one of those gets an empty result, not an error.

---

## 8. Freeze, then deactivate

Two different objects, in this order.

```sql
-- Step 1. Find the UserLogin row. You cannot address it by UserId --
-- UserLogin.UserId is documented as "This field can't be updated", and
-- UserLogin supports only describeSObjects/query/retrieve/UPDATE. No insert.
SELECT Id, UserId, IsFrozen, IsPasswordLocked
FROM UserLogin
WHERE UserId = '0055g00000QqRstAAO'

-- Sanity check: everyone currently frozen (the guide's own query)
SELECT Id, UserId FROM UserLogin WHERE IsFrozen = true
```

`freeze.csv` — the Id column is the **UserLogin** Id (`05D…`), not the User Id:

```csv
Id,IsFrozen
05D5g000000TfRzEAK,true
```

```bash
# Step 1 — freeze. Instant, reversible, licence still consumed.
sf data update bulk --sobject UserLogin --file freeze.csv --target-org prod --wait 10

# Step 2 — reassign records, queue membership, approvals (section 9), THEN:
sf data update bulk --sobject User --file deactivate.csv --target-org prod --wait 10
```

`deactivate.csv` — this one keys on the **User** Id (`005…`):

```csv
Id,IsActive
0055g00000QqRstAAO,false
```

**Constraints the guides state outright**

- "You can't delete a user in the user interface or the API." Deactivation is the terminal state.
  "Because users can never be deleted, we recommend that you exercise caution when creating them."
- "The user interface provides options to auto-remove a user from teams, but the removal isn't
  supported in API." A Data Loader deactivation therefore leaves team memberships behind that the
  Setup UI would have cleared.
- On deactivation, every `EntitySubscription` where the user is the `ParentId` or `SubscriberId` is
  **soft** deleted and "if the user is reactivated, the subscriptions are restored." But if you
  deactivate multiple mutually-following users at once, "their subscriptions are hard deleted…
  Such subscriptions can't be restored upon user reactivation."
- `UserLogin.IsPasswordLocked`: "From the API, you can set this field to false, but not true."
  You can unlock over the API; you cannot lock.

UNVERIFIED (2026-09-04): the Object Reference points to a help topic — "Be aware of the expected
behaviors when deactivating users. See Considerations for Deactivating Users" — that is not
reproduced in any of the developer PDFs, and help.salesforce.com is not fetchable. The commonly
cited blockers (user is the default workflow user, a default case or lead owner, or a designated
approver) are therefore **not** grounded here. Section 9 finds those references by query instead of
relying on the platform to refuse the save.

---

## 9. The offboarding checklist, as SOQL

Deactivation does not clean up after itself. Run every one of these against the departing user's Id
and drive the reassignment from the results.

```sql
-- 1. Records they own. Repeat per object that matters; there is no global "everything I own" query.
SELECT COUNT(Id) FROM Account      WHERE OwnerId = '0055g00000QqRstAAO'
SELECT COUNT(Id) FROM Opportunity  WHERE OwnerId = '0055g00000QqRstAAO' AND IsClosed = false
SELECT COUNT(Id) FROM Case         WHERE OwnerId = '0055g00000QqRstAAO' AND IsClosed = false
SELECT COUNT(Id) FROM Lead         WHERE OwnerId = '0055g00000QqRstAAO' AND IsConverted = false

-- 2. Queue AND public-group membership in one query. Group.Type distinguishes them:
--    'Queue' = queue membership, 'Regular' = standard public group.
SELECT Id, Group.Name, Group.Type
FROM GroupMember
WHERE UserOrGroupId = '0055g00000QqRstAAO'
ORDER BY Group.Type, Group.Name

-- 3. Pending approvals where they are the actor.
SELECT Id, ProcessInstance.TargetObjectId, ActorId, ProcessInstance.Status
FROM ProcessInstanceWorkitem
WHERE ActorId = '0055g00000QqRstAAO'

-- 4. Permission sets and permission set groups.
SELECT PermissionSet.Name, PermissionSet.Label, PermissionSetGroupId, ExpirationDate
FROM PermissionSetAssignment
WHERE AssigneeId = '0055g00000QqRstAAO'

-- 5. Permission set LICENCES -- these keep consuming after deactivation. Delete them.
SELECT Id, PermissionSetLicense.MasterLabel
FROM PermissionSetLicenseAssign
WHERE AssigneeId = '0055g00000QqRstAAO'

-- 6. Anyone who reports to them. Orphaned ManagerId breaks manager-group sharing and approvals.
SELECT Id, Username, Name FROM User
WHERE ManagerId = '0055g00000QqRstAAO' AND IsActive = true

-- 7. Does their role have children? A role with no active occupant breaks hierarchy visibility.
SELECT Id, Name, DeveloperName FROM UserRole
WHERE ParentRoleId IN (SELECT UserRoleId FROM User WHERE Id = '0055g00000QqRstAAO')
```

Query 2 catches **direct** membership only. The Object Reference is explicit: "User records that are
indirect members of Regular public groups aren't listed as group members. A User can be an indirect
member of a group if he or she is in a `UserRole` above the direct group member in the hierarchy, or
if he or she is a member of a group that is included as a subgroup in that group." Access that
arrives via the role hierarchy will not appear here — that is what `admin/sharing-and-visibility`
and the `/diff-users` agent are for.

Two more references live in **metadata**, not in any record, so no query finds them: `CaseSettings`
carries `defaultCaseOwner` ("the default owner of a case when assignment rules fail to locate an
owner") and `defaultCaseUser` ("the user listed in the Case History related list for automated case
changes"). Retrieve `CaseSettings` and grep for the departing username before you deactivate.

Bulk reassignment of the records found by query 1 is `admin/mass-transfer-ownership`, not this skill.

---

## 10. Last login, and the dormant-account sweep

```sql
-- Never logged in, or not for 90 days. LastLoginDate is on the User record.
SELECT Id, Username, Name, Profile.Name, LastLoginDate, IsActive
FROM User
WHERE IsActive = true
  AND (LastLoginDate = null OR LastLoginDate < LAST_N_DAYS:90)
ORDER BY LastLoginDate NULLS FIRST

-- Forensic detail for one user. LoginHistory carries LoginType, Status, SourceIp, Browser, Platform.
SELECT UserId, LoginTime, LoginType, Status, SourceIp, Browser, Application
FROM LoginHistory
WHERE UserId = '0055g00000QqRstAAO'
  AND LoginTime > 2026-06-01T00:00:00.000Z
ORDER BY LoginTime DESC
```

**How to read it**

- `User.LastLoginDate` "is updated if 60 seconds elapses since the user's last login" — it is not a
  live session indicator, and a user who logged in 30 seconds ago may not show yet.
- `LoginHistory` has a **closed filterable-field list**: `AuthenticationServiceId`, `CipherSuite`,
  `CountryIso`, `Id`, `LoginTime`, `LoginType`, `LoginUrl`, `NetworkId`, `OptionsIsGet`,
  `OptionsIsPost`, `TlsProtocol`, `UserId`. `Status` and `SourceIp` are selectable but **not**
  filterable. `WHERE Status = 'Success'` fails; filter in your client instead.
- Access needs *Manage Users* or *Monitor Login History*, "except that, in API version 37.0 and
  later, all users can retrieve their own login history records."

Deeper login analysis — failed-login clustering, geography, session anomalies — is
`security/login-forensics`.

---

## Verification step

After the role/profile deploy and the user load, confirm all three layers in one pass:

```sql
SELECT Id, Username, Name, IsActive,
       Profile.Name, Profile.UserLicense.MasterLabel,
       UserRole.Name, UserRole.ParentRoleId,
       ManagerId, TimeZoneSidKey, LocaleSidKey, FederationIdentifier,
       (SELECT PermissionSet.Label FROM PermissionSetAssignments)
FROM User
WHERE Username IN ('avargas@northwind.com','tokafor@northwind.com','lchen@northwind.com')
```

Then run the linter against the CSV and the retrieved metadata:

```bash
python3 skills/admin/user-management/scripts/check_user_management.py \
    --manifest-dir force-app/main/default --csv users.csv
```

A green result means: no duplicate usernames in the file, every required column present, no profile
silently missing login restrictions, and no unexplained `ModifyAllData` on a profile you are about
to hand to three new hires.
