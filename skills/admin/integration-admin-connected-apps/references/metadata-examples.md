# Metadata Examples — Operating an Integration's Connected App

Everything here is an **operations** artefact: the policy block you edit on an app that already
exists, the permission set that pre-authorizes it, the queries that prove it, the revoke and rotate
procedures, and the review checklist the skill checker lints.

**The full deployable file is not here.** `admin/connected-apps-and-auth` →
`references/metadata-examples.md` owns the complete `connectedApp-meta.xml`, the four-file External
Client App set, and the Named Credential + External Credential pair. The excerpts below are
fragments of that file, marked as such, so you can diff a policy change without re-authoring the app.

Element names, enum values and defaults come from the Metadata API Developer Guide
(https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — `ConnectedApp`,
`ConnectedAppOauthPolicy`, `ConnectedAppSessionPolicy`, `ConnectedAppSettings`, `PermissionSet` —
and the Object Reference
(https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) —
`ConnectedApplication`, `OauthToken`, `LoginHistory`, `SetupAuditTrail`, `PermissionSetAssignment`.

---

## 1. The hardened policy block for a server-to-server app

This is an **excerpt**, not a whole file — the `<ConnectedApp>` root is shown only so the fragment is
well-formed XML you can validate locally. Merge these four children into the existing
`force-app/main/default/connectedApps/Billing_Sync_JWT.connectedApp-meta.xml`; a file containing only
what is below is missing `label` and `contactEmail`, which the guide marks **Required**.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- EXCERPT: oauthPolicy / sessionPolicy / grantee children only.
     The complete file lives in admin/connected-apps-and-auth. -->
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <oauthConfig>
        <isAdminApproved>true</isAdminApproved>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE</ipRelaxation>
        <refreshTokenPolicy>specific_inactivity:7:DAYS</refreshTokenPolicy>
    </oauthPolicy>
    <sessionPolicy>
        <sessionTimeout>120</sessionTimeout>
    </sessionPolicy>
    <permissionSetName>Billing_Sync_Integration</permissionSetName>
    <ipRanges>
        <description>Billing platform egress</description>
        <start>203.0.113.10</start>
        <end>203.0.113.20</end>
    </ipRanges>
</ConnectedApp>
```

**How to read it**

- `ipRelaxation` is **Required** on `ConnectedAppOauthPolicy`. `ENFORCE` is the default and
  "enforces the IP restrictions configured for the org, such as the IP ranges assigned to a user
  profile." It is a *pointer* to a list maintained elsewhere — see `references/gotchas.md`.
- `refreshTokenPolicy` is **Required**, and its default is `infinite` — "the refresh token is used
  indefinitely, unless revoked by the user or Salesforce admin." `specific_inactivity:7:DAYS` means
  the token dies if it is not exchanged within seven days, and each exchange resets the window.
  The other forms are `zero`, `specific_lifetime:number:HOURS|DAYS|MONTHS`, and
  `specific_inactivity:number:HOURS|DAYS|MONTHS`.
- Tightening this value is not a cut-off: "The Refresh Token policy is evaluated only during usage
  of the issued refresh token and doesn't affect a user's current session." The mechanics of that
  are in `admin/connected-apps-and-auth`; the operational consequence is in `references/gotchas.md`.
- `isAdminApproved` `true` means "only users with the appropriate profile or permission set can
  access the app. These users don't have to approve the app before they can access it." Both
  `permissionSetName` and `profileName` carry "To use this field, the `isAdminApproved` field on the
  `ConnectedAppOauthConfig` subtype must be set to true."
- `permissionSetName` takes one name per line and is a *sibling* of `oauthConfig`, not a child of it.
  Deploying `<permissionSetName></permissionSetName>` removes every permission set from the app.
- `sessionPolicy/sessionTimeout` is the app's own session length; "If you don't set a value,
  Salesforce uses the timeout value in the connected app user's profile."
- `sessionPolicy` also carries the kill switch: `policyAction` `Block` "Makes the connected app
  inaccessible to your org's users. Blocking an app ends all current user sessions with the
  connected app and prevents all new sessions." Its sibling value `RaiseSessionLevel` (with
  `sessionLevel` `HIGH_ASSURANCE`) applies only to flows with a user approval step — "All other
  flows, such as the JSON Web Token (JWT) bearer token flow, don't include a user approval step. For
  flows without a user approval step, API logins with the High Assurance session security level are
  blocked." Do not put `RaiseSessionLevel` on a headless integration.
- `ipRanges` needs `start` and `end` (both Required); `description` is optional. These are the app's
  own allowed ranges, distinct from the org trusted-IP list `ENFORCE` consults.

### Org-wide switch above every app

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedAppSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAdminApprovedAppsOnly>true</enableAdminApprovedAppsOnly>
    <enableAdminApprovedAppsOnlyForExternalUser>true</enableAdminApprovedAppsOnlyForExternalUser>
</ConnectedAppSettings>
```

Stored as `settings/ConnectedApp.settings-meta.xml`. `enableAdminApprovedAppsOnly`: "If `false`
(default), any connected app can call the Salesforce API. If `true`, only apps that have been
approved or installed by the admin can call the Salesforce API." Both fields carry "To access this
field, you must contact Salesforce Customer Support to enable API Access Control" — so this is a
support request, not a same-day deploy. Inventory before flipping it.

---

## 2. The pre-authorization permission set

The permission set itself grants the *platform* access the integration needs. The connected-app
grant is **not** in this file — it lives in `permissionSetName` on the app above. A permission-set
diff will therefore never show you that the app was pre-authorized.

`force-app/main/default/permissionsets/Billing_Sync_Integration.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing Sync Integration</label>
    <description>Pre-authorizes the Billing Sync JWT connected app and grants its minimum object access.</description>
    <hasActivationRequired>false</hasActivationRequired>
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
        <object>Invoice__c</object>
    </objectPermissions>
    <fieldPermissions>
        <editable>true</editable>
        <field>Invoice__c.External_Id__c</field>
        <readable>true</readable>
    </fieldPermissions>
</PermissionSet>
```

**How to read it**

- The app's grantee list is one-directional: the guide says to "Manage permission sets for the app
  by editing each permission set's **Assigned Connected App** list", but the deployable
  representation of that link is `permissionSetName` on `ConnectedApp`. Deploy both files together
  or the pairing is half-applied.
- `ApiEnabled` is the platform permission the integration user needs regardless of the connected app.
- `modifyAllRecords`, `viewAllRecords` and `viewAllFields` are all `false` on purpose. Anything that
  pulls the principal toward admin-shaped permissions is covered by `security/api-only-user-hardening`.
- This permission set is the pre-authorization *and* the data grant. Splitting them into two
  permission sets is fine — only the one named in `permissionSetName` pre-authorizes.

---

## 3. Pairing the permission set to the integration user

The connected app is pre-authorized to a permission set; the permission set reaches the integration
user through a `PermissionSetAssignment`. That object supports `create()`, `delete()`,
`describeSObjects()`, `query()`, `retrieve()` and `update()`, and "only users who have one of these
permissions can access this object: View Setup and Configuration, Assign Permission Sets, Manage User."

Verify the pairing (run in the Developer Console or `sf data query`):

```sql
SELECT Assignee.Username, Assignee.IsActive, Assignee.Profile.Name,
       PermissionSet.Name, ExpirationDate, IsActive
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'Billing_Sync_Integration'
ORDER BY Assignee.Username
```

A non-null `ExpirationDate` is the finding. It is "the date that the assignment of the permission set
or permission set group expires for the specified user" — when it passes, the integration user is no
longer in the app's pre-authorized population and OAuth begins failing with no metadata change.

Create the assignment without an expiry:

```apex
// Run in anonymous Apex as a user with Assign Permission Sets.
PermissionSet ps = [SELECT Id FROM PermissionSet WHERE Name = 'Billing_Sync_Integration' LIMIT 1];
User integrationUser = [SELECT Id FROM User WHERE Username = 'billing.sync@example.com.prod' LIMIT 1];

PermissionSetAssignment psa = new PermissionSetAssignment(
    PermissionSetId = ps.Id,
    AssigneeId      = integrationUser.Id
    // ExpirationDate deliberately omitted — a dated grant silently de-authorizes the integration.
);
insert psa;
```

Confirm the principal itself is shaped correctly before you rely on it:

```sql
SELECT Username, IsActive, UserType, Profile.Name, Profile.UserLicense.Name, LastLoginDate
FROM User
WHERE Username = 'billing.sync@example.com.prod'
```

`UserType` is "the category of user license", a restricted picklist whose values include `Standard`
("This user type also includes Salesforce Platform and Salesforce Platform One user licenses"),
`PowerPartner`, `CspLitePortal`, `CustomerSuccess`, `PowerCustomerSuccess`, `CsnOnly` and `Guest`.
Read `Profile.UserLicense.Name` rather than inferring the licence from `UserType`. Which licence and
profile an integration user *should* hold is `admin/integration-user-management` and
`security/api-only-user-hardening`.

---

## 4. The monitoring query set

Four objects, four different questions. Run all of them as a user holding **Customize Application**.

### 4a. What policy actually landed — `ConnectedApplication`

"Represents a connected app and its details; all fields are read-only." Supports
`describeSObjects()`, `query()`, `retrieve()`.

```sql
SELECT Name, OptionsAllowAdminApprovedUsersOnly, OptionsHasSessionLevelPolicy,
       RefreshTokenValidityPeriod, OptionsRefreshTokenValidityMetric,
       StartUrl, MobileStartUrl, PinLength
FROM ConnectedApplication
ORDER BY Name
```

- `OptionsAllowAdminApprovedUsersOnly` "Indicates whether access is limited to users granted approval
  to use the connected app by an administrator." It must be `true` on every app you deployed with
  `isAdminApproved`.
- `RefreshTokenValidityPeriod` is "the duration of an authorization token until it expires in hours,
  months, or days as set in the connected app management page." The unit is not in the field —
  `OptionsRefreshTokenValidityMetric` disambiguates the *kind*: "If `true`, the token validity is
  measured based on the last use of the token; otherwise, it's based on the token duration." A row
  with a period and a false metric is a hard lifetime, not an inactivity window.
- `OptionsHasSessionLevelPolicy` "Specifies whether the connected app requires a High Assurance level
  session" — expect `false` on a headless integration.

### 4b. Who holds a grant — `OauthToken`

"Represents an OAuth access token for connected app authentication", API 32.0+, supports only
`describeSObjects()` and `query()`.

```sql
SELECT AppName, UserId, LastUsedDate, UseCount, DeleteToken
FROM OauthToken
WHERE AppName = 'Billing Sync JWT'
ORDER BY LastUsedDate DESC
```

Before trusting the result, get the true size — the object caps out at 2,500 rows over `query()` plus
`queryMore()`:

```sql
SELECT COUNT() FROM OauthToken
```

If that count exceeds 2,500, split by `UserId` or page with `OFFSET`, which the guide caps at 2,000:

```sql
SELECT AppName, UserId, LastUsedDate, UseCount FROM OauthToken LIMIT 2000 OFFSET 0
SELECT AppName, UserId, LastUsedDate, UseCount FROM OauthToken LIMIT 2000 OFFSET 2000
```

Do not select `Id` as a key — on this object "`Id` … Reserved for future use. Currently, the value is
always null." Key rows on `UserId` + `AppName`.

### 4c. Which sessions the app produced — `LoginHistory`

Only twelve fields are filterable: `AuthenticationServiceId`, `CipherSuite`, `CountryIso`, `Id`,
`LoginTime`, `LoginType`, `LoginUrl`, `NetworkId`, `OptionsIsGet`, `OptionsIsPost`, `TlsProtocol`,
`UserId`. `Application`, `SourceIp` and `Status` are **not** among them, so aggregate on them instead
of filtering:

```sql
SELECT Application, LoginType, Status, COUNT(Id) Logins
FROM LoginHistory
WHERE LoginTime = LAST_N_DAYS:7
  AND LoginType IN ('Application', 'Oauth, Remote Access Client', 'Oauth2, Remote Access 2.0')
GROUP BY Application, LoginType, Status
ORDER BY COUNT(Id) DESC
```

Two of those three picklist values contain a comma *inside the value*. Then pivot to the one
filterable identifier you have — the integration user:

```sql
SELECT LoginTime, LoginType, Application, SourceIp, Status, TlsProtocol, ApiType, ApiVersion
FROM LoginHistory
WHERE UserId = '005XXXXXXXXXXXXXXX'
  AND LoginTime = LAST_N_DAYS:7
ORDER BY LoginTime DESC
```

Access is gated: "only users with Manage Users or Monitor Login History permissions can access this
object", except that "in API version 37.0 and later, all users can retrieve their own login history
records."

### 4d. Who changed a policy — `SetupAuditTrail`

"Represents changes you or other admins made in your org's Setup area for at least the last 180
days." Supports `query()` and `retrieve()` only.

```sql
SELECT CreatedDate, CreatedBy.Name, DelegateUser, Action, Section, Display
FROM SetupAuditTrail
WHERE Section = 'Connected Apps'
ORDER BY CreatedDate DESC
LIMIT 200
```

`Action` is "the category of the change made in Setup"; `Display` is "the full description of changes
made in Setup"; `DelegateUser` is "the Login-As user who executed the action in Setup." Note the
aggregate restriction: "`SELECT count() FROM SetupAuditTrail` works but `SELECT count(Id) FROM
SetupAuditTrail` fails."

### 4e. Token-level events — `EventLogFile` (add-on)

```
GET /services/data/v64.0/query?q=SELECT+Id,EventType,LogDate,LogFileLength+FROM+EventLogFile
+WHERE+EventType+IN+('ConnectedApp','ConnectedAppOAuth')+AND+LogDate=LAST_N_DAYS:7
```

Requires the Event Monitoring add-on. Everything in 4a–4d works without it.

---

## 5. Revoking a grant

`OauthToken` supports only `describeSObjects()` and `query()` — **there is no `delete()`**, so no
Flow, Apex trigger or Data Loader operation can revoke a token. The documented path uses the token's
own `DeleteToken` value, which is "a token that can be used at the revoke OAuth token endpoint to
remove this token":

```bash
# 1. Find the grant to revoke. Run as a user with Customize Application.
sf data query -o prod -q "SELECT AppName, UserId, LastUsedDate, DeleteToken \
  FROM OauthToken WHERE AppName = 'Billing Sync JWT' ORDER BY LastUsedDate DESC"

# 2. Revoke exactly that grant. The guide's own form of the URL:
#    https://MyDomainName.my.salesforce.com/services/oauth2/revoke?token=(the Delete Token)
curl -s -o /dev/null -w '%{http_code}\n' \
  "https://mycompany.my.salesforce.com/services/oauth2/revoke?token=REPLACE_WITH_DELETE_TOKEN"

# 3. Re-run the query from step 1 and confirm the row is gone.
```

If you do not have the `DeleteToken` — or need to stop an app for everyone at once — the Setup path
is **Connected Apps OAuth Usage → Block** on the app's row, or a deploy setting
`sessionPolicy/policyAction` to `Block`, which "ends all current user sessions with the connected app
and prevents all new sessions." That is org-wide and immediate; per-user revocation is the
`DeleteToken` route above.

Revoking a single grant is not the same as ending a session. The guide describes that boundary for
the adjacent case, `refreshTokenPolicy` `zero`: "The refresh token is invalid immediately. The user
can use the current session (access token) already issued, but can't obtain a new session when the
access token expires." Only `Block` is documented as ending current sessions.

---

## 6. Rotating the consumer key or secret

There is no rotation field on `ConnectedApp`. `consumerKey`: "In API version 32.0 and later, you can
set this field's value only during creation. After you define and save the value, it can't be
edited," and `consumerSecret`: "After you save the value, it can't be edited. When set, the value
isn't returned in Metadata API requests." Rotation for a connected app therefore means a replacement
app plus a caller cutover.

An **External Client App** has the fields, and both carry the same deploy requirement — "To maintain
security, if this field is set to `true`, you must include the ignore warnings attribute in the
deploy command":

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- EXCERPT: rotation flags only. The full ExtlClntAppGlobalOauthSettings file
     "can't be packaged and must not be added to source control" — see
     admin/connected-apps-and-auth for the complete four-file ECA set. -->
<ExtlClntAppGlobalOauthSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing Sync ECA Global OAuth</label>
    <externalClientApplication>Billing_Sync_ECA</externalClientApplication>
    <shouldRotateConsumerKey>true</shouldRotateConsumerKey>
    <shouldRotateConsumerSecret>true</shouldRotateConsumerSecret>
</ExtlClntAppGlobalOauthSettings>
```

```bash
# The ignore-warnings attribute is mandatory when either rotation flag is true.
sf project deploy start \
  -m "ExtlClntAppGlobalOauthSettings:Billing_Sync_ECA_glbl" \
  -o prod --ignore-warnings
```

Set both flags back to `false` after the rotation deploy, or the next deploy of the same file
regenerates the credentials again.

---

## 7. The periodic review checklist

Ships as `templates/connected-app-review-checklist.yaml`. The skill checker lints it: every entry
under `apps:` must carry `owner`, `last-reviewed`, and `token-count-query-run`.

```yaml
# connected-app-review-checklist.yaml
review:
  cycle: quarterly
  # Keep the cycle inside 180 days: SetupAuditTrail holds Setup changes for
  # "at least the last 180 days", so a longer gap leaves the previous review
  # with no corroborating evidence.
  last-completed: 2026-09-01
  reviewer-permission: Customize Application

apps:
  - name: Billing Sync JWT
    owner: platform-integrations@example.com
    last-reviewed: 2026-09-01
    token-count-query-run: 2026-09-01
    token-count: 3
    permitted-users: AdminApprovedUsers
    pre-auth-permission-set: Billing_Sync_Integration
    assignment-expires: none
    ip-relaxation: ENFORCE
    refresh-token-policy: specific_inactivity:7:DAYS
    notes: JWT bearer, no interactive login.

  - name: Partner Portal Web
    owner: partner-experience@example.com
    last-reviewed: 2026-08-28
    token-count-query-run: 2026-08-28
    token-count: 412
    permitted-users: AdminApprovedUsers
    pre-auth-permission-set: Partner_Portal_Access
    assignment-expires: none
    ip-relaxation: ENFORCE_RELAXREFRESH
    refresh-token-policy: specific_lifetime:90:DAYS
    notes: Web server flow; ENFORCE_RELAXREFRESH justified by partner egress churn.
```

`token-count-query-run` is a separate field from `last-reviewed` on purpose: reading the policy off
`ConnectedApplication` is not the same as proving who holds tokens, and only the second one requires
Customize Application.

---

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Billing_Sync_JWT</members>
        <name>ConnectedApp</name>
    </types>
    <types>
        <members>Billing_Sync_Integration</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>ConnectedApp</members>
        <name>Settings</name>
    </types>
    <version>64.0</version>
</Package>
```

`ConnectedAppSettings` values are "stored in a single file named `ConnectedApp.settings` in the
`settings` directory", and the type is available in API version 47.0 and later.

---

## Retrieve, check, deploy

```bash
# 1. Retrieve the live app before touching its policy — you are editing, not authoring.
sf project retrieve start -m "ConnectedApp:Billing_Sync_JWT" -o prod

# 2. Lint the policy XML and the review checklist.
python3 scripts/check_integration_admin_connected_apps.py --manifest-dir force-app/main/default
python3 scripts/check_integration_admin_connected_apps.py --manifest-dir templates

# 3. Validate without committing.
sf project deploy start -x manifest/package.xml -o prod --dry-run

# 4. Deploy.
sf project deploy start -x manifest/package.xml -o prod
```

A retrieved `connectedApp-meta.xml` has no `consumerSecret` in it — "When set, the value isn't
returned in Metadata API requests" — so never treat the retrieved file as a complete backup of the
app.

---

## Verify after deploy

One query, run as a user with Customize Application, answers whether the policy landed *and* whether
the pre-authorization reaches the integration user:

```sql
SELECT Name, OptionsAllowAdminApprovedUsersOnly,
       RefreshTokenValidityPeriod, OptionsRefreshTokenValidityMetric
FROM ConnectedApplication
WHERE Name = 'Billing Sync JWT'
```

Expected: `OptionsAllowAdminApprovedUsersOnly` = `true`, `RefreshTokenValidityPeriod` = `7`,
`OptionsRefreshTokenValidityMetric` = `true` (inactivity, not lifetime). Then:

```sql
SELECT Assignee.Username, ExpirationDate
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'Billing_Sync_Integration'
```

Expected: the integration user present, `ExpirationDate` null. If the first query is right and the
second is empty, the app is pre-authorized to a permission set nobody holds — the deploy succeeded
and the integration is still locked out.

---

## Related reading

| Question | Skill |
|---|---|
| Author the whole `connectedApp` / ECA / Named Credential file, or choose the artefact | `admin/connected-apps-and-auth` |
| An OAuth error code is already on screen | `admin/connected-app-troubleshooting` |
| Who the integration user should be, and which licence | `admin/integration-user-management`, `security/api-only-user-hardening` |
| The org trusted-IP list that `ENFORCE` consults | `admin/org-setup-and-configuration`, `security/network-security-and-trusted-ips` |
| Permission-set assignment expiry as a model | `admin/permission-set-expiration` |
| Secret rotation and PKCE as a security programme | `security/connected-app-security-policies` |
| Token issue, refresh, rotation, introspection mechanics | `security/oauth-token-management` |
| The EventLogFile pipeline itself | `security/event-monitoring` |
