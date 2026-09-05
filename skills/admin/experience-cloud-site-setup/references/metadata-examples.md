# Metadata Examples — Experience Cloud Site Setup

Deployable source for a customer support site: the `Network`, the `CustomSite` it
must point at, the `NavigationMenu`, and the Experience Builder content bundle.
Every field name and enum value below is from the Metadata API Developer Guide
(v62 / Summer '26 text extract) at the line numbers cited.

Sibling scope: guest profile permissions and public-page access belong to
`admin/experience-cloud-guest-access`; membership provisioning and licence
allocation belong to `admin/experience-cloud-member-management` and
`admin/portal-requirements-gathering`; moving a finished site between orgs
belongs to `devops/experience-cloud-deployment-admin`.

---

## Where the files live

```text
force-app/main/default/
├── networks/
│   └── Customer_Support.network-meta.xml          # Network       (api_meta.txt L90680–L90681)
├── sites/
│   └── Customer_Support.site-meta.xml             # CustomSite    (api_meta.txt L46759–L46760)
├── navigationMenus/
│   └── Customer_Support_Primary.navigationMenu-meta.xml   # NavigationMenu (api_meta.txt L90455)
├── experiences/                                   # ExperienceBundle — Aura + non-enhanced LWR
│   └── Customer_Support1/
│       ├── Customer_Support1.site-meta.xml
│       ├── brandingSets/
│       ├── config/
│       ├── routes/
│       ├── themes/
│       ├── variations/
│       └── views/
└── digitalExperiences/                            # DigitalExperienceBundle — enhanced LWR only
    └── site/
        └── Customer_Support1/
            ├── Customer_Support1.digitalExperience-meta.xml
            └── sfdc_cms__view/
                └── home/
                    ├── _meta.json
                    └── content.json
```

**How to read it**

- One Experience Cloud site is **two** metadata records, not one. Creating a Lightning
  site creates a `CustomSite` of type `ChatterNetwork` named `<site_name>` and a
  SiteDotCom of type `ChatterNetworkPicasso` named `<site_name>1` — the trailing `1`
  keeps the names unique (api_meta.txt L130582–L130585). The Experience Builder
  content folder inherits that `1` suffix, which is why the bundle folder above is
  `Customer_Support1` while the network file is `Customer_Support`.
- `Network.site` is **Required** and holds the `CustomSite` name (api_meta.txt L91045).
  A `Network` deployed without its `CustomSite` present in the target org has nothing
  to bind to.
- `experiences/` (ExperienceBundle) and `digitalExperiences/` (DigitalExperienceBundle)
  are **alternatives, not layers**. Use `DigitalExperienceBundle` only for enhanced LWR
  sites created in Winter '23 or later; for Aura sites and other LWR sites use
  `ExperienceBundle` (recommended) or `SiteDotCom` (api_meta.txt L51234–L51236).
- `NavigationMenu` replaced the `navigationLinkSet` subtype on `Network` in API 47.0;
  `navigationLinkSet` is only valid in API 37.0–46.0 (api_meta.txt L90951–L90954).
  Writing menu items inside the `.network-meta.xml` on a modern API version is the
  most common shape error in this domain.

---

## `networks/Customer_Support.network-meta.xml`

Status starts at `UnderConstruction` (the Setup label is **Preview**) so the site is
reachable only by users who hold Create and Set Up Experiences and whose profile is
associated with the site (object_reference.txt L187370–L187373). Flip to `Live` in a
second deploy once the content bundle and guest permissions are in place.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Network xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowInternalUserLogin>true</allowInternalUserLogin>
    <allowMembersToFlag>true</allowMembersToFlag>
    <allowedExtensions>jpg,png,pdf,docx,csv</allowedExtensions>
    <changePasswordTemplate>unfiled$public/CommunityChangePasswordEmailTemplate</changePasswordTemplate>
    <description>Authenticated self-service support portal for retail customers</description>
    <emailSenderAddress>support-portal@example.com</emailSenderAddress>
    <emailSenderName>Example Support</emailSenderName>
    <enableGuestChatter>false</enableGuestChatter>
    <enableGuestFileAccess>false</enableGuestFileAccess>
    <enableInvitation>false</enableInvitation>
    <enableKnowledgeable>false</enableKnowledgeable>
    <enableNicknameDisplay>false</enableNicknameDisplay>
    <enablePrivateMessages>false</enablePrivateMessages>
    <enableReputation>false</enableReputation>
    <enableSiteAsContainer>true</enableSiteAsContainer>
    <forgotPasswordTemplate>unfiled$public/CommunityForgotPasswordEmailTemplate</forgotPasswordTemplate>
    <lockoutTemplate>unfiled$public/CommunityLockoutEmailTemplate</lockoutTemplate>
    <logoutUrl>https://www.example.com/goodbye</logoutUrl>
    <maxFileSizeKb>10240</maxFileSizeKb>
    <networkMemberGroups>
        <permissionSet>Support_Portal_Member</permissionSet>
        <permissionSet>Support_Portal_Power_User</permissionSet>
    </networkMemberGroups>
    <selfRegistration>false</selfRegistration>
    <sendWelcomeEmail>true</sendWelcomeEmail>
    <site>Customer_Support</site>
    <status>UnderConstruction</status>
    <tabs>
        <defaultTab>home</defaultTab>
        <standardTab>home</standardTab>
        <standardTab>Case</standardTab>
        <standardTab>Contact</standardTab>
    </tabs>
    <urlPathPrefix>support</urlPathPrefix>
    <welcomeTemplate>unfiled$public/CommunityWelcomeEmailTemplate</welcomeTemplate>
</Network>
```

**How to read it**

- Required fields on `Network`: `emailSenderAddress`, `emailSenderName`,
  `forgotPasswordTemplate`, `site`, `status`, `tabs` (api_meta.txt L90782, L90797,
  L90917, L91045, L91054, L91081). A file missing any of them fails the deploy.
- `emailSenderAddress` is **write-once through the API**: it can be supplied only on the
  first deploy that creates the site, the address must already be verified, and later
  Metadata API updates to it "are ignored and Salesforce doesn't show an error"
  (api_meta.txt L90784–L90795). Changing it afterwards is a Setup action in the site's
  Administration workspace → Emails. Template selection itself belongs to
  `admin/email-templates-and-alerts`.
- The email-template fields take a **folder-qualified developer name**
  (`unfiled$public/Name`), matching the guide's own sample (api_meta.txt L91835).
  The guide adds that Lightning email templates aren't packageable and recommends
  Classic templates for these fields (api_meta.txt L90919–L90920).
- `networkMemberGroups` accepts `<profile>` and `<permissionSet>` children
  (api_meta.txt L90963, sample at L91837–L91843). Permission-set membership is the
  maintainable shape, but note the platform carve-out: a Chatter customer already in a
  customer group is *not* added to the site by a permission set that is associated with
  it (api_meta.txt L90967–L90970).
- `urlPathPrefix` `support` produces `MyDomainName.my.site.com/support`
  (api_meta.txt L91084–L91089).
- `maxFileSizeKb` accepts a number between 3072 KB and the org's maximum file size;
  leave it empty to inherit the 2 GB default (api_meta.txt L90936–L90941).
- Deliberately omitted: `reputationLevels`, `reputationPointsRules`,
  `recommendationDefinition`. They only apply when `enableReputation` is `true`, and
  the guide notes that omitting them while reputation is enabled falls back to default
  values (api_meta.txt L90863–L90869) — an unwanted default set is harder to spot than
  a missing feature.

---

## `sites/Customer_Support.site-meta.xml`

The `CustomSite` that `Network.site` points at.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <active>true</active>
    <allowHomePage>false</allowHomePage>
    <allowStandardAnswersPages>false</allowStandardAnswersPages>
    <allowStandardIdeasPages>false</allowStandardIdeasPages>
    <allowStandardLookups>false</allowStandardLookups>
    <allowStandardPortalPages>false</allowStandardPortalPages>
    <allowStandardSearch>false</allowStandardSearch>
    <browserXssProtection>true</browserXssProtection>
    <clickjackProtectionLevel>SameOriginOnly</clickjackProtectionLevel>
    <contentSniffingProtection>true</contentSniffingProtection>
    <description>Customer support portal</description>
    <enableAuraRequests>true</enableAuraRequests>
    <indexPage>UnderConstruction</indexPage>
    <masterLabel>Customer Support</masterLabel>
    <redirectToCustomDomain>true</redirectToCustomDomain>
    <referrerPolicyOriginWhenCrossOrigin>true</referrerPolicyOriginWhenCrossOrigin>
    <siteAdmin>portal.admin@example.com</siteAdmin>
    <siteGuestRecordDefaultOwner>portal.admin@example.com</siteGuestRecordDefaultOwner>
    <siteType>ChatterNetwork</siteType>
    <urlPathPrefix>support</urlPathPrefix>
</CustomSite>
```

**How to read it**

- `siteType` for an Experience Cloud site's `CustomSite` is `ChatterNetwork`; the paired
  SiteDotCom record is `ChatterNetworkPicasso` (api_meta.txt L130582–L130585).
  `Siteforce` — the value in the guide's own generic sample — is a Site.com site
  (api_meta.txt L130607–L130609) and is the wrong value here.
- `clickjackProtectionLevel` is **Required** and takes `AllowAllFraming`, `External`,
  `SameOriginOnly`, or `NoFraming`; the guide marks `SameOriginOnly` "(recommended)"
  and `AllowAllFraming` "(no protection)" (api_meta.txt L46876–L46888).
- There is no `requireHttps` element to set. It was **removed in API version 52.0 and
  later**, and in 51.0 and earlier the value is ignored (api_meta.txt L47015–L47017).
  HTTPS redirection is governed by `redirectToCustomDomain`, which defaults to `false`
  in Experience Cloud sites and routes system-managed `*.my.site.com` URLs to the HTTPS
  custom domain when set to `true` (api_meta.txt L46982–L46989).
- `allowStandardPortalPages` is a real access control: when disabled, authenticated
  members cannot reach standard Salesforce pages "even if their access controls allow
  it" (api_meta.txt L46796–L46804). Leave it `false` for a Builder-only portal.
- `guestProfile` and `subdomain` are **Read only** (api_meta.txt L46959, L47059) —
  writing them into source produces drift you can never reconcile. Guest profile design
  lives in `admin/experience-cloud-guest-access`.
- `enableAuraRequests` set to `false` stops Lightning features loading for guest users
  (api_meta.txt L46919–L46922); keep it `true` for any Experience Builder site.

---

## `navigationMenus/Customer_Support_Primary.navigationMenu-meta.xml`

Four items: an internal link, a Salesforce object, a Knowledge object, and an external
link opened in a new tab.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NavigationMenu xmlns="http://soap.sforce.com/2006/04/metadata">
    <container>Customer_Support</container>
    <containerType>Network</containerType>
    <label>Support Primary</label>
    <navigationMenuItem>
        <label>Home</label>
        <position>1</position>
        <publiclyAvailable>true</publiclyAvailable>
        <target>/</target>
        <type>InternalLink</type>
    </navigationMenuItem>
    <navigationMenuItem>
        <label>My Cases</label>
        <position>2</position>
        <publiclyAvailable>false</publiclyAvailable>
        <target>Case</target>
        <type>SalesforceObject</type>
    </navigationMenuItem>
    <navigationMenuItem>
        <label>Knowledge</label>
        <position>3</position>
        <publiclyAvailable>true</publiclyAvailable>
        <target>Knowledge__kav</target>
        <type>SalesforceObject</type>
    </navigationMenuItem>
    <navigationMenuItem>
        <label>Status Page</label>
        <position>4</position>
        <publiclyAvailable>true</publiclyAvailable>
        <target>https://status.example.com</target>
        <targetPreference>OpenInExternalTab</targetPreference>
        <type>ExternalLink</type>
    </navigationMenuItem>
</NavigationMenu>
```

**How to read it**

- `containerType` is `Network` or `CommunityTemplateDefinition`; `container` names the
  site (api_meta.txt L90468–L90471). `label`, `position` and `type` are the required
  fields per item (api_meta.txt L90500, L90506, L90546).
- Valid `type` values are exactly `SalesforceObject`, `ExternalLink`, `InternalLink`,
  `MenuLabel`, `NavigationalTopic` (api_meta.txt L90546–L90564). There is no
  "Knowledge" or "Article" type — a Knowledge entry is a `SalesforceObject` item whose
  `target` is the Knowledge object, `Knowledge__kav` (object_reference.txt L160685).
- `target` is required for `ExternalLink`, `InternalLink` and `SalesforceObject`, and
  unused for `MenuLabel` and `NavigationalTopic`; internal targets are relative URLs
  such as `/contactsupport`, external targets are absolute (api_meta.txt L90515–L90527).
- `targetPreference` takes `None` or `OpenInExternalTab` (api_meta.txt L90528–L90543).
  The guide's own NavigationMenu sample uses `OpenExternalLinkInSameTab`
  (api_meta.txt L90627), a value the field table does not list — prefer the field table.
- Menu items **do not create pages.** The guide is explicit that Help Center and the LWR
  templates (Build Your Own, Microsites) ship no generic record pages, so an object menu
  item without a matching object page shows the end user nothing when clicked
  (api_meta.txt L90449–L90452). The `My Cases` and `Knowledge` items above each need a
  route in the content bundle.
- `publiclyAvailable` `true` exposes the item to guest users (api_meta.txt L90509–L90510).
  It controls the *menu entry only* — it grants no record access; that is
  `admin/experience-cloud-guest-access`.
- Nesting: only `MenuLabel` items can hold a `subMenu`, and `MenuLabel` /
  `NavigationalTopic` cannot be nested under a `MenuLabel` (api_meta.txt L90583–L90584,
  L90565–L90569).

---

## The content bundle

The site's pages, branding sets, themes and routes live in the bundle, not in `Network`.
Pick exactly one type.

`experiences/Customer_Support1/Customer_Support1.site-meta.xml` — ExperienceBundle,
shaped from the guide's sample (api_meta.txt L59938–L59945):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExperienceBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Customer_Support1</label>
    <type>ChatterNetworkPicasso</type>
    <urlPathPrefix>support</urlPathPrefix>
</ExperienceBundle>
```

`digitalExperiences/site/Customer_Support1/Customer_Support1.digitalExperience-meta.xml`
— DigitalExperienceBundle for an enhanced LWR site (api_meta.txt L51346–L51350):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DigitalExperienceBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Customer_Support1</label>
</DigitalExperienceBundle>
```

An enhanced LWR site also needs its `DigitalExperienceConfig`, which is where the URL
path prefix lives for that type (api_meta.txt L54019–L54026):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DigitalExperienceConfig xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Customer_Support</label>
    <site>
        <urlPathPrefix>support</urlPathPrefix>
    </site>
    <space>site/Customer_Support1</space>
</DigitalExperienceConfig>
```

**Excerpt only — one branding-set file inside the bundle.** This is JSON, not XML, and it
is a trimmed excerpt of one file from `experiences/Customer_Support1/brandingSets/`;
the real file carries the full `values` map (api_meta.txt L60042–L60070):

```json
{
  "brandingSetType": "APP",
  "definitionName": "starter:branding-starter",
  "label": "Support Brand",
  "type": "brandingSet",
  "values": {
    "ActionColor": "#0176D3",
    "PageBackgroundColor": "#F3F3F3",
    "TextColor": "#181818",
    "PrimaryFont": "Salesforce Sans"
  }
}
```

**How to read it**

- `ExperienceBundle.type` has one legal value, `ChatterNetworkPicasso`
  (api_meta.txt L59915–L59916); `label` and `type` are required, `urlPathPrefix` is not.
- `ExperienceBundle.urlPathPrefix` must agree with the `Network`: for Aura sites and
  authenticated LWR sites created before Winter '23 the bundle path ends in `/s` and the
  part without `/s` must match the Network's URL; for unauthenticated LWR sites and
  authenticated LWR sites created after Winter '23 there is no `/s`
  (api_meta.txt L59918–L59937). Copy whichever shape the retrieve gave you rather than
  inventing one.
- `brandingSetType` is required in LWR sites, not applicable to Aura, and **cannot be
  changed from one type to another**; `APP` applies to the whole site and there can be
  only one of them (api_meta.txt L59996–L60003).
- `definitionName` is `theme:branding-theme` and the standard templates have fixed
  values — `starter:branding-starter` for Build Your Own, `cpt:branding-cpt` for
  Customer Account Portal, `prm:branding-prm` for Partner Central,
  `service:branding-service` for Customer Service, `helpCenter:branding-helpCenter`
  for Help Center (api_meta.txt L60005–L60019). `definitionName` + `label` must be
  unique in the org.
- Aura sites need **Enable ExperienceBundle Metadata API** switched on in Setup →
  Digital Experiences → Settings before this type can be used; LWR sites use
  ExperienceBundle by default (api_meta.txt L59901–L59904).

---

## `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Customer_Support</members>
        <name>CustomSite</name>
    </types>
    <types>
        <members>Customer_Support</members>
        <name>Network</name>
    </types>
    <types>
        <members>Customer_Support_Primary</members>
        <name>NavigationMenu</name>
    </types>
    <types>
        <members>Customer_Support1</members>
        <name>ExperienceBundle</name>
    </types>
    <version>62.0</version>
</Package>
```

Wildcards: `Network`, `CustomSite`, `NavigationMenu`, `ExperienceBundle`,
`DigitalExperienceBundle` and `DigitalExperienceConfig` all document wildcard support in
the manifest (api_meta.txt L92032, L47232, L90666, L61118, L51372, L54050). `DigitalExperienceBundle` members are addressed
workspace-qualified, `site/<name>`, not by bare name (api_meta.txt L51357–L51360).

Do **not** add `SiteDotCom` to a manifest that carries `ExperienceBundle`: the guide
says to ensure the `SiteDotCom` type isn't included when deploying an Experience Builder
site with `ExperienceBundle` (api_meta.txt L61110).

---

## Retrieve, check, deploy

```bash
# 1. Pull the org's current site into source before editing anything
sf project retrieve start \
  --metadata CustomSite:Customer_Support Network:Customer_Support \
             NavigationMenu:Customer_Support_Primary ExperienceBundle:Customer_Support1 \
  --target-org my-sandbox

# 2. Lint the retrieved source
python3 skills/admin/experience-cloud-site-setup/scripts/check_experience_cloud_site_setup.py \
  --manifest-dir force-app/main/default

# 3. Validate without committing
sf project deploy validate --manifest manifest/package.xml --target-org my-sandbox

# 4. Deploy the container first: CustomSite before Network, because Network.site
#    is a required reference to it (api_meta.txt L91045).
sf project deploy start --source-dir force-app/main/default/sites --target-org my-sandbox
sf project deploy start --source-dir force-app/main/default/networks --target-org my-sandbox

# 5. Then the menu and the content bundle
sf project deploy start --source-dir force-app/main/default/navigationMenus --target-org my-sandbox
sf project deploy start --source-dir force-app/main/default/experiences --target-org my-sandbox
```

Ordering note: the guide states the dependency (`Network.site` is a Required reference to
the `CustomSite`, api_meta.txt L91045) but does not publish a prescriptive deploy
sequence for these types. UNVERIFIED (2026-09-04): splitting the deploy into the five
steps above is the ordering implied by that required reference, not an ordering the
Metadata API Developer Guide states; a single combined deploy of all directories also
resolves the reference within one request.

**Publishing.** `status` moves `UnderConstruction` → `Live` (Setup labels **Preview** →
**Published**) and that transition is one-way: "After a site is published, it can never
be in this status again" (object_reference.txt L187370–L187373). Change the element and
redeploy the `Network` to publish the site itself.
UNVERIFIED (2026-09-04): whether deploying an `ExperienceBundle` or
`DigitalExperienceBundle` also publishes the Builder content, or leaves it in draft
pending a Publish click in Experience Builder, is not stated in the Metadata API
Developer Guide sections for either type — treat a post-deploy Publish in Experience
Builder as required until verified in the target org.

Cross-org promotion, ExperienceBundle API-version pinning and sandbox refresh handling
are `devops/experience-cloud-deployment-admin`.

---

## Verification

After the deploy, confirm the site is in the state you intended rather than trusting the
deploy result:

```sql
-- Site status and URL. Status labels: Live = Published, DownForMaintenance = Offline,
-- UnderConstruction = Preview (object_reference.txt L187347–L187373).
SELECT Id, Name, Status, UrlPathPrefix, OptionsSelfRegistrationEnabled, SelfRegProfileId
FROM Network
WHERE Name = 'Customer_Support'

-- Membership actually resolved from the permission sets in networkMemberGroups.
SELECT COUNT(Id)
FROM NetworkMember
WHERE Network.Name = 'Customer_Support'

-- Who the members are, newest first, when the count looks wrong.
SELECT MemberId, Member.Name, NetworkId
FROM NetworkMember
WHERE Network.Name = 'Customer_Support'
LIMIT 50
```

`Network` supports `query()` and `update()` but not `create()` or `delete()`
(object_reference.txt L186636–L186637) — a site cannot be created from SOQL/DML, only
inspected and adjusted. `NetworkMember` likewise supports `query()`, `retrieve()` and
`update()` only (object_reference.txt L188301–L188302), so membership is a consequence of
profile and permission-set assignment, never a row you insert.

Setup check for the same facts: Setup → Digital Experiences → All Sites shows Status and
URL; the site's Administration workspace → Emails shows the sender address that
`emailSenderAddress` set on first deploy and that the API will not update afterwards.
