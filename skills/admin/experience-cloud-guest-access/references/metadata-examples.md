# Metadata Examples: Experience Cloud Guest Access

One public Help Center site, `Help_Center`, expressed as the deployable metadata that actually governs unauthenticated access: the route that makes a page public, the guest profile that grants object and field read, the guest sharing rule that releases specific records, the `CustomSite` that names the owner of anything a guest creates, the `Network` flags that switch on files and Chatter for guests, and the org preference that makes all of it necessary in the first place.

Six files, one gate each. All six must agree before a public page renders data. A deploy that touches only one of them changes nothing a visitor can see — that is the single most common failure in this domain.

For the record-access model around the guest rule (OWD strategy, role hierarchy, sharing sets for *authenticated* external users) read `admin/sharing-and-visibility`. For the full `SharingRules` container reference and a second guest-rule worked example on a different object read `admin/sharing-rules`. For hardening the Apex that these pages call, and for auditing an already-live site, read `security/guest-user-security` and `security/guest-user-security-audit`.

---

## The six gates, in deploy order

| # | Gate | File | Element that decides |
|---|---|---|---|
| 0 | Org preference | `settings/Sharing.settings-meta.xml` | `enableSecureGuestAccess` — read-only in practice; see gate 0 below |
| 1 | Object baseline | `objects/FAQ_Article__c/FAQ_Article__c.object-meta.xml` | `externalSharingModel` |
| 2 | Page reachability | `experiences/Help_Center1/routes/<Route>.json` | `pageAccess` |
| 3 | Object + field permission | `profiles/Help Center Profile.profile-meta.xml` | `objectPermissions`, `fieldPermissions` |
| 4 | Record release | `sharingRules/FAQ_Article__c.sharingRules-meta.xml` | `sharingGuestRules` |
| 5 | Guest-created record ownership | `sites/Help_Center.site-meta.xml` | `siteGuestRecordDefaultOwner` |
| 6 | Site-level guest switches | `networks/Help_Center.network-meta.xml` | `enableGuestChatter`, `enableGuestFileAccess`, `enableGuestMemberVisibility` |

---

## Gate 0 — the org preference that forces the whole design

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/settings/Sharing.settings-meta.xml -->
<SharingSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableExternalSharingModel>true</enableExternalSharingModel>
    <enableSecureGuestAccess>true</enableSecureGuestAccess>
    <enableManualUserRecordSharing>true</enableManualUserRecordSharing>
</SharingSettings>
```

**How to read it**

- `enableSecureGuestAccess`: "When true, guest users have org-wide defaults set to Private. To share records with them, you must use guest user sharing rules." That sentence is the whole reason gate 4 exists.
- It is not a decision you get to make. "As of API version 50.0, this field's value is always true, regardless of the value that you set. Changing its value has no effect on Salesforce, even if it reads `false`. This change applies retroactively back to API version 47.0." A deploy that sets it to `false` succeeds and does nothing. Do not put it in a package as a lever; include it, if at all, as documentation of the constraint.
- `enableExternalSharingModel` is what makes `externalSharingModel` (gate 1) exist as a separate column at all. Without the external sharing model enabled there is no separate external OWD to set.
- Package member name is `Sharing`, type `Settings` — not `Security`. The guest-related settings are spread across four different settings files, not one: `Sharing.settings` (this one), `Communities.settings` (`enableGuvSecurityOptOutPref`, `enablePreventBadgeGuestAccess`), `Content.settings` (`enableSiteGuestUserToUploadFiles`), and `Apex.settings` (`enableAuraApexCtrlGuestUserAccessCheckPref`, `enableRestrictCommunityExecAnon`).

---

## Gate 1 — external OWD on the object

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/objects/FAQ_Article__c/FAQ_Article__c.object-meta.xml -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>Public FAQ content. Private to guests by default; released record-by-record via a guest sharing rule.</description>
    <enableActivities>false</enableActivities>
    <enableHistory>true</enableHistory>
    <label>FAQ Article</label>
    <nameField>
        <label>FAQ Article Name</label>
        <type>Text</type>
    </nameField>
    <pluralLabel>FAQ Articles</pluralLabel>
    <sharingModel>ReadWrite</sharingModel>
    <externalSharingModel>Private</externalSharingModel>
</CustomObject>
```

**How to read it**

- `externalSharingModel` is the one guests obey. `sharingModel` (internal) can be as wide as you like and changes nothing for an unauthenticated visitor.
- Keep `externalSharingModel` at `Private` and release records with gate 4. `Read` here would publish every current *and future* `FAQ_Article__c` record to every guest of every site in the org — including the draft somebody creates next quarter.
- `Read` is the API name for Public Read Only. There is no `PublicReadOnly` enumeration value.
- Read `admin/sharing-and-visibility` for the OWD decision itself; this file is included here only because gate 4 is meaningless without it.

---

## Gate 2 — page access, as a route file

Experience Builder's Page Properties → Page Access is a single JSON property inside the site's `ExperienceBundle`. There is one route file per page.

```json
{
  "id": "c7263124-7bc4-4147-a39a-25fe7e305b98",
  "type": "route",
  "label": "FAQ",
  "devName": "FAQ",
  "urlPrefix": "faq",
  "routeType": "standard",
  "appPageId": "b5fe94e2-071f-47b2-b76d-427a624cb407",
  "activeViewId": "1f0a2c55-8d24-42b6-93b7-6e2c1c0d8a11",
  "pageAccess": "Public"
}
```

**How to read it**

- `pageAccess` is required and takes exactly three values: `UseParent`, `Public`, `RequiresLogin`. It "identifies the status of a route as public or private."
- `UseParent` is the default, and it is the dangerous one: "When set to the default value `UseParent`, the status of the site determines the status of the route." Every route left at `UseParent` flips the moment the site's own guest setting flips. Set `Public` and `RequiresLogin` explicitly on every route you care about; treat a `UseParent` route as unclassified, not as private.
- The site-level status this inherits from lives in `config/<sitename>.json` — `authenticationType` for LWR sites (`AUTHENTICATED`, `AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED`, `UNAUTHENTICATED`) and `isAvailableToGuests` (boolean, default `false`) for Aura sites. They are not interchangeable: "For Aura sites, use `isAvailableToGuests` instead", "For LWR sites, use `authenticationType` instead."
- `UNAUTHENTICATED` "isn't supported for LWR sites created after Winter '23 through Experience Builder or Connect API. To allow guest user access, we recommend using `AUTHENTICATED_WITH_PUBLIC_ACCESS_ENABLED`." A new LWR site's public mode is an authenticated site with the public checkbox on, not a genuinely login-less site.
- For an **Aura** site this file only exists in a retrieve after you enable it: "To use the ExperienceBundle metadata type for Aura-based Experience Builder sites, from Setup, enter `Digital Experiences` in the Quick Find box, and then select Settings. Select Enable ExperienceBundle Metadata API… LWR sites use ExperienceBundle by default." Retrieving an Aura site without that preference gives you a `SiteDotCom` binary blob and no `pageAccess` to review.
- **Enhanced LWR sites retrieve as a different type.** They come back as `DigitalExperienceBundle` — suffix `.digitalExperience`, stored under `digitalExperiences/`, where "all routes in an enhanced LWR site are stored under a content type folder called `sfdc_cms__route`" and each route is one content item. `pageAccess` there carries the same three values and the same `UseParent` inheritance, plus one extra constraint the `ExperienceBundle` copy does not state: "You can change the `pageAccess` value only if the site is authenticated." Its site content item holds `authenticationType`, where `UNAUTHENTICATED` is now called out as "a legacy value." Check which of `experiences/` and `digitalExperiences/` your retrieve produced before editing anything.
- `configurationTags` also appears on routes and is documented as internal — "This is an internal property and must not be edited." Leave whatever the retrieve produced.

---

## Gate 3 — the guest user profile

The guest profile is an ordinary `Profile` file. Nothing in its XML marks it as a guest profile; only the org knows that, from the site it is bound to.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/profiles/Help Center Profile.profile-meta.xml -->
<Profile xmlns="http://soap.sforce.com/2006/04/metadata">
    <custom>true</custom>

    <!-- Read-only on the object the public FAQ page renders. -->
    <objectPermissions>
        <object>FAQ_Article__c</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllFields>false</viewAllFields>
    </objectPermissions>

    <!-- Create-only on Case: the "Contact us" screen flow inserts, nothing reads back. -->
    <objectPermissions>
        <object>Case</object>
        <allowRead>false</allowRead>
        <allowCreate>true</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
        <viewAllFields>false</viewAllFields>
    </objectPermissions>

    <!-- Every field the page renders, enumerated. readable=true, editable=false. -->
    <fieldPermissions>
        <field>FAQ_Article__c.Question__c</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>
    <fieldPermissions>
        <field>FAQ_Article__c.Answer__c</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>
    <fieldPermissions>
        <field>FAQ_Article__c.Publication_Status__c</field>
        <readable>true</readable>
        <editable>false</editable>
    </fieldPermissions>
    <!-- Deliberately absent: FAQ_Article__c.Internal_Notes__c, FAQ_Article__c.Reviewer__c -->

    <!-- Case fields the form writes. editable=true is required for a guest insert. -->
    <fieldPermissions>
        <field>Case.SuppliedEmail</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>
    <fieldPermissions>
        <field>Case.Subject</field>
        <readable>true</readable>
        <editable>true</editable>
    </fieldPermissions>

    <userPermissions>
        <name>ApiEnabled</name>
        <enabled>false</enabled>
    </userPermissions>
</Profile>
```

**How to read it**

- The five object flags are `allowRead`, `allowCreate`, `allowEdit`, `allowDelete`, plus the three escalation flags `viewAllRecords`, `modifyAllRecords`, and `viewAllFields` (the last "available in API version 63.0 and later"). `viewAllRecords` and `modifyAllRecords` are the object-scoped equivalents of View All Data and Modify All Data and both bypass sharing "regardless of the sharing settings for the object" — which means they bypass gate 4 entirely. On a guest profile they are the difference between publishing three FAQ articles and publishing the table.
- Write the negatives explicitly rather than omitting them. Omission is not the same as `false` in a partial deploy against an existing profile, and an explicit `false` is what makes `scripts/check_experience_cloud_guest_access.py` able to tell "reviewed and denied" from "never considered".
- `fieldPermissions` uses `readable` and `editable`. `readable` "replaces the `hidden` field" from API 23.0. Two defaults matter here: "In API version 30.0 and later, when deploying a new custom field, this field is `false` by default" and "For portal profiles, this field is set to `false` by default." So a newly deployed field is invisible to guests until you add an entry — which is the behaviour you want, and the reason a guest-facing object needs a profile edit in the same release as every new field.
- "In API version 30.0 and later, permissions for required fields can't be retrieved or deployed." A required custom field on a guest-writable object cannot have its FLS expressed here at all.
- Guest profile naming (`<Site Name> Profile`) is a convention of the site-creation wizard. UNVERIFIED (2026-09-04): the Metadata API guide documents neither the guest profile's generated name nor its user license label; the checker therefore matches on `guest` appearing in the file name or in a `userLicense` element, and you may need to point it at the real file name in your project.

---

## Gate 4 — the guest user sharing rule

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/sharingRules/FAQ_Article__c.sharingRules-meta.xml -->
<SharingRules xmlns="http://soap.sforce.com/2006/04/metadata">
    <sharingGuestRules>
        <fullName>Published_FAQ_To_Help_Center_Guest</fullName>
        <label>Published FAQ to Help Center Guest</label>
        <description>Releases only Published FAQ articles to the Help Center site guest user. Read only by platform rule.</description>
        <accessLevel>Read</accessLevel>
        <sharedTo>
            <guestUser>Help_Center</guestUser>
        </sharedTo>
        <criteriaItems>
            <field>Publication_Status__c</field>
            <operation>equals</operation>
            <value>Published</value>
        </criteriaItems>
        <includeHVUOwnedRecords>false</includeHVUOwnedRecords>
    </sharingGuestRules>
</SharingRules>
```

**How to read it**

- `accessLevel` is required and inherited from `SharingBaseRule`, but for this rule type the platform pins it: "For `SharingGuestRule`, the `accessLevel` field can be set only to `Read`." There is no supported write path to a guest through sharing. `Edit` here is a deploy failure, not a wider grant.
- `sharedTo/guestUser` is "a list of guest user nicknames with sharing access. This field can be used only with `SharingGuestRule`." It is a *nickname*, not a username or an Id, and it names one site's guest user — which is why cloning a site does not carry its guest rules across.
- `sharingGuestRules` arrived in API version 47.0; `criteriaItems` and `booleanFilter` on this rule type arrived in 48.0. A project pinned below 48.0 can create the rule but cannot filter it, so it must discriminate by ownership instead.
- `includeHVUOwnedRecords` (API 52.0+, default `false`): "By default, only records owned by authenticated users, guest users, and queues are included in sharing rules." If your published FAQ articles happen to be owned by a high-volume Experience Cloud user, they are silently outside this rule until you set it `true`. And: "You can't edit this field after the sharing rule is created."
- `operation` takes a `FilterOperation` value: `equals`, `notEqual`, `lessThan`, `greaterThan`, `lessOrEqual`, `greaterOrEqual`, `contains`, `notContain`, `startsWith`, `includes`, `excludes`, `within`.
- All four rule types for an object share one file: "Criteria-based, owner-based, territory-based, and guest user sharing rules are all contained in a `object.sharingRule` file." A partial deploy of this file replaces the object's rule set; retrieve before you edit.
- The declarative rule is the only mechanism. Apex managed sharing cannot substitute: on the `__Share` object's `UserOrGroupId`, "You can't grant access to unauthenticated guest users using Apex."

---

## Gate 5 — the site, and who owns what a guest creates

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/sites/Help_Center.site-meta.xml -->
<CustomSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <masterLabel>Help Center</masterLabel>
    <description>Public help center. FAQ read + Contact Us case create.</description>
    <siteType>ChatterNetwork</siteType>
    <urlPathPrefix>help</urlPathPrefix>
    <siteAdmin>site.admin@example.com</siteAdmin>

    <!-- Records a guest creates are reassigned to this user on insert. -->
    <siteGuestRecordDefaultOwner>site.integration@example.com</siteGuestRecordDefaultOwner>

    <clickjackProtectionLevel>SameOriginOnly</clickjackProtectionLevel>
    <browserXssProtection>true</browserXssProtection>
    <contentSniffingProtection>true</contentSniffingProtection>
    <referrerPolicyOriginWhenCrossOrigin>true</referrerPolicyOriginWhenCrossOrigin>
    <redirectToCustomDomain>true</redirectToCustomDomain>
    <enableAuraRequests>true</enableAuraRequests>
    <allowHomePage>false</allowHomePage>
    <allowStandardIdeasPages>false</allowStandardIdeasPages>
    <allowStandardLookups>false</allowStandardLookups>
    <allowStandardPortalPages>false</allowStandardPortalPages>
    <allowStandardSearch>false</allowStandardSearch>
    <indexPage>Home</indexPage>
    <authorizationRequiredPage>Unauthorized</authorizationRequiredPage>
    <fileNotFoundPage>FileNotFound</fileNotFoundPage>
</CustomSite>
```

**How to read it**

- `siteGuestRecordDefaultOwner` (API 51.0+) is "the username of the user who owns all new records that unauthenticated guest users create." Pair it with gate 3's `allowCreate`: any object a guest can insert produces records the guest does not own. Omit it and you get the org-preference behaviour instead — `enableSitesRecordReassignOrgPref` in `Sites.settings`, "when `false`, the guest user remains the owner of the record", which is now deprecated in API version 63.0 and later. Set it on the site.
- `guestProfile` appears in the guide's own sample `CustomSite` definition, but the field table marks it **"Read only. The name of the profile associated with the guest user."** Do not try to bind a profile to a site by deploying this element — it is not the wiring mechanism, and this example omits it deliberately.
- `requireHttps` is also absent deliberately: on `CustomSite`, "this field is removed in API version 52.0 and later. In API version 51.0 and earlier, the value in the field is ignored." The identically named field in `SessionSettings` is inert for a different reason — "enabled by default for security reasons and can't be disabled" — and is itself only "available in API version 40.0 to 60.0". Neither one is a lever you can pull from a package. HTTPS on the site comes from the domain and certificate on `customWebAddresses` plus `redirectToCustomDomain`, which "indicates whether requests for this site's system-managed URLs are redirected to the HTTPS custom domain serving this site."
- `clickjackProtectionLevel` is required. Values, with the guide's own annotations: `AllowAllFraming` (no protection), `External` (good protection), `SameOriginOnly` (recommended), `NoFraming` (most protection).
- `enableAuraRequests` "determines whether guest users can view features available only in Lightning (`true`). If set to `false`, Lightning features don't load." On an LWR or Aura Experience Cloud site this is not optional — `false` is a blank page for guests.
- The `allowStandard*` family is guest-facing surface you are not designing: `allowStandardPortalPages` off means "authenticated users in this site can't access standard Salesforce pages, even if their access controls allow it… disabling this setting helps add a layer of access protection to your site."
- The guide's headline note on this type — "This Metadata API Type applies only to Salesforce sites and Visualforce sites. For Digital Experiences, also known as Experience Cloud sites, see `Network`" — reads as if `CustomSite` is irrelevant here. It is not: `Network.site` is "Required. The `CustomSite` associated with the Experience Cloud site." Every Experience Cloud site has a `CustomSite` record behind it, and that is where `siteGuestRecordDefaultOwner` lives.

---

## Gate 6 — the Network guest switches

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- force-app/main/default/networks/Help_Center.network-meta.xml -->
<Network xmlns="http://soap.sforce.com/2006/04/metadata">
    <site>Help_Center</site>
    <status>Live</status>
    <urlPathPrefix>help</urlPathPrefix>
    <description>Public help center.</description>
    <emailSenderAddress>help@example.com</emailSenderAddress>
    <emailSenderName>Example Help Center</emailSenderName>

    <enableGuestChatter>false</enableGuestChatter>
    <enableGuestFileAccess>false</enableGuestFileAccess>
    <enableGuestMemberVisibility>false</enableGuestMemberVisibility>

    <selfRegistration>false</selfRegistration>
    <allowInternalUserLogin>false</allowInternalUserLogin>
    <allowMembersToFlag>true</allowMembersToFlag>
    <enableInvitation>false</enableInvitation>
    <networkMemberGroups>
        <profile>Help Center Login User</profile>
    </networkMemberGroups>
</Network>
```

**How to read it**

- These three are independent of the guest profile and of every sharing rule. They are site-level switches:
  - `enableGuestChatter` — "whether guest users can access public Chatter groups in the site without logging in."
  - `enableGuestFileAccess` (API 41.0+) — "whether guest users view asset files shared with the site on publicly accessible pages and login pages."
  - `enableGuestMemberVisibility` (API 47.0+) — "if unauthenticated guest users can see the authenticated members."
- `enableGuestFileAccess` carries a trap in its own description: "**If public access is enabled in Experience Builder at the page or site level, this property is automatically enabled.**" Setting a single route to `Public` in gate 2 turns guest file access on for you. `false` in this file is a statement of intent that the platform may overwrite — re-retrieve after publishing and check what it actually says.
- `site` is required and points at gate 5's `CustomSite`. `status` is required: `Live`, `DownForMaintenance`, or `UnderConstruction`.
- `networkMemberGroups` lists the profiles and permission sets with access. The guest profile is not a member group; it is bound to the site by creation, not by this list.
- Two more guest switches live outside this file: `enableSiteGuestUserToUploadFiles` in `Content.settings` ("when `true`, site guest users can upload files") and `enablePreventBadgeGuestAccess` in `Communities.settings` (API 53.0+, "hides badges from guest users in Experience Builder sites").

---

## package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>FAQ_Article__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Help Center Profile</members>
        <name>Profile</name>
    </types>
    <types>
        <members>FAQ_Article__c</members>
        <name>SharingRules</name>
    </types>
    <types>
        <members>Help_Center</members>
        <name>CustomSite</name>
    </types>
    <types>
        <members>Help_Center</members>
        <name>Network</name>
    </types>
    <types>
        <members>Help_Center1</members>
        <name>ExperienceBundle</name>
    </types>
    <types>
        <members>Sharing</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

**How to read it**

- `CustomObject` and `Profile` must be in the *same* retrieve. The guide is explicit: "the returned `.profile` files only include security settings for the other metadata types referenced in the retrieve request." Retrieve the guest profile on its own and you get user permissions and login hours and essentially no `objectPermissions` — you will conclude the guest profile grants nothing, and be wrong.
- The wildcard on `CustomObject` "doesn't match standard objects", so `Case` object permissions on the guest profile do not come back from a `*` retrieve either. Name `Case` as a `CustomObject` member when you need its guest FLS.
- `SharingRules` supports the wildcard; `SharingBaseRule` and `Profile` do not. And "you can't retrieve, delete, or deploy manual sharing rules or sharing rules by their type (owner, criteria-based, territory, or guest user)" — you take the object's whole rule file or none of it.
- `ExperienceBundle` members are the *site folder* names under `experiences/`, which are not always the `Network`/`CustomSite` name — LWR and Aura sites commonly get a numeric suffix. Read the folder name from a retrieve rather than guessing it.

---

## Retrieve and deploy

```bash
# 1. Pull the current state of all six gates before changing anything.
sf project retrieve start \
  --metadata "CustomObject:FAQ_Article__c" \
  --metadata "CustomObject:Case" \
  --metadata "Profile:Help Center Profile" \
  --metadata "SharingRules:FAQ_Article__c" \
  --metadata "CustomSite:Help_Center" \
  --metadata "Network:Help_Center" \
  --metadata "ExperienceBundle:Help_Center1" \
  --metadata "Settings:Sharing" \
  --target-org uat

# 2. Static review of what you are about to publish.
python3 skills/admin/experience-cloud-guest-access/scripts/check_experience_cloud_guest_access.py \
  --manifest-dir force-app/main/default

# 3. Validate against the target org without committing (check-only).
sf project deploy start --manifest manifest/package.xml --dry-run --target-org uat

# 4. Deploy.
sf project deploy start --manifest manifest/package.xml --target-org uat
```

Deploy the object (gate 1) before the sharing rule (gate 4): the rule's `criteriaItems` reference `Publication_Status__c`, and a rule cannot be created against a field that does not exist yet. Everything else in the package is order-independent.

---

## Verification

Configuration that deployed is not configuration that works. Three checks, in the order that isolates the failing gate.

**1. Confirm the guest user exists and find its Id.** `UserType` is a restricted picklist whose `Guest` value means "user whose access is limited because they're an unauthenticated user without login credentials."

```sql
SELECT Id, Name, Username, UserType, ProfileId, Profile.Name, IsActive
FROM User
WHERE UserType = 'Guest'
ORDER BY Name
```

**2. Confirm gate 3 (the profile) and gate 4 (the rule) separately.** Object permissions come from `ObjectPermissions`; released records show up as share rows with `RowCause = 'GuestRule'` — "the user or group has access via a … guest user sharing rule."

```sql
-- Gate 3: what the guest profile actually grants. Expect PermissionsRead only.
SELECT SobjectType, PermissionsRead, PermissionsCreate, PermissionsEdit,
       PermissionsDelete, PermissionsViewAllRecords, PermissionsModifyAllRecords
FROM ObjectPermissions
WHERE ParentId IN (
    SELECT Id FROM PermissionSet WHERE ProfileId = '00eXXXXXXXXXXXXXXX'
)
AND SobjectType IN ('FAQ_Article__c', 'Case')

-- Gate 4: which records the rule actually released, and at what level.
SELECT Id, ParentId, UserOrGroupId, AccessLevel, RowCause
FROM FAQ_Article__Share
WHERE RowCause = 'GuestRule'
```

A non-empty gate-3 result with an empty gate-4 result is the classic "page renders, list is empty" symptom. The reverse — share rows present, no `ObjectPermissions` row — is "the records are released but the guest cannot see the object at all."

**3. Confirm gate 2 from outside the org.** No session, no cookie, no Salesforce client:

```bash
# A route with pageAccess=Public returns the page.
curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' \
  'https://example.my.site.com/help/faq'

# A route with pageAccess=RequiresLogin must redirect to login, not render.
curl -sS -o /dev/null -w '%{http_code} %{redirect_url}\n' \
  'https://example.my.site.com/help/my-cases'
```

Run these from a machine that has never authenticated to the org. A browser that is logged in as an admin will render both, which is why "I checked it and it looked fine" is not evidence about guest access.

---

## Source lines used

Every claim above traces to `api_meta.txt` / `object_reference.txt` / `apexdev.txt` from the Summer '26 (v62) PDF set:

| Claim | File:line |
|---|---|
| `enableSecureGuestAccess` always true as of API 50.0, retroactive to 47.0 | `api_meta.txt:127101–127110` |
| `SharingSettings` sample + `Sharing` package member | `api_meta.txt:127127–127147`, `:127225` |
| `pageAccess` values and `UseParent` inheriting site status | `api_meta.txt:60561–60567` |
| `authenticationType` / `isAvailableToGuests`, `UNAUTHENTICATED` unsupported post-Winter '23 | `api_meta.txt:60098–60125` |
| ExperienceBundle must be enabled for Aura sites | `api_meta.txt:59901–59905` |
| `DigitalExperienceBundle` for enhanced LWR: suffix, folders, `pageAccess` authenticated-only, `UNAUTHENTICATED` legacy | `api_meta.txt:51115–51128`, `:52695–52708`, `:52797–52812` |
| `ProfileObjectPermissions` flags incl. `viewAllFields` (API 63.0+) | `api_meta.txt:98123–98189` |
| `ProfileFieldLevelSecurity` `readable`/`editable` defaults, portal default `false` | `api_meta.txt:98004–98027` |
| Profile retrieve returns only co-retrieved types; `*` excludes standard objects | `api_meta.txt:98477–98479`, `:98503` |
| `SharingGuestRule` `accessLevel` Read only; API 47.0/48.0/52.0 versions | `api_meta.txt:129291–129292`, `:129322–129334`, `:129344–129350` |
| `sharedTo/guestUser` is a nickname list, `SharingGuestRule` only | `api_meta.txt:129069–129072` |
| All four rule types in one `.sharingRules` file; no per-type deploy | `api_meta.txt:129249–129256` |
| `FilterOperation` enumeration | `api_meta.txt:43902–43917` |
| `CustomSite.siteGuestRecordDefaultOwner` (API 51.0+) | `api_meta.txt:47040–47042` |
| `CustomSite.guestProfile` read only | `api_meta.txt:46959–46960` |
| `requireHttps` removed API 52.0+, ignored earlier | `api_meta.txt:47015–47019` (and the second, inert `requireHttps` in `SessionSettings` at `:126529–126533`) |
| `clickjackProtectionLevel` enumeration | `api_meta.txt:46876–46887` |
| `enableAuraRequests`, `allowStandardPortalPages` | `api_meta.txt:46919–46923`, `:46796–46804` |
| CustomSite scope note vs `Network.site` required | `api_meta.txt:46749–46751`, `:91045–91046` |
| `enableGuestChatter` / `enableGuestFileAccess` auto-enable / `enableGuestMemberVisibility` | `api_meta.txt:90829–90841` |
| `enableSiteGuestUserToUploadFiles`, `enablePreventBadgeGuestAccess` | `api_meta.txt:113131`, `:112867` |
| `enableSitesRecordReassignOrgPref` deprecated API 63.0+ | `api_meta.txt:127224–127229` |
| Apex managed sharing cannot target guests | `apexdev.txt:12564` |
| `User.UserType = 'Guest'` | `object_reference.txt:232430–232460` |
| `RowCause = 'GuestRule'` | `object_reference.txt:17742` |
