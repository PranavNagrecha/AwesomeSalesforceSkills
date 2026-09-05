# Gotchas — Experience Cloud Guest Access

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Each Site Has Exactly One Guest Profile — Shared Across All Public Pages

**What happens:** An admin adds Read access to a new object on the guest user profile to support a newly launched public page. Unknown to the admin, other public pages on the same site have components that query the same object. Those components now return data they were never intended to show publicly, because the guest profile permission applies site-wide.

**When it occurs:** Any time the guest profile is modified to support one new page without auditing all other public pages on the same site for unintended side effects.

**How to avoid:** Before adding any object or field to the guest user profile, list all public pages on the site and check whether any existing component queries that object. Use the guest profile edit page alongside Experience Builder's page inventory. Treat the guest profile as a site-wide setting, not a per-page setting.

---

## Gotcha 2: FLS on the Guest Profile Applies to All Guest Apex Calls, Not Just the Page You Changed

**What happens:** A developer removes field-level Read access from the guest profile for a field deemed too sensitive for public display. The targeted public page no longer shows the field — which is correct. However, an Apex controller on a different public page queries the same field. That Apex call now either returns null for the field or throws a FLS exception in system mode, breaking the second page unexpectedly.

**When it occurs:** When multiple public pages share Apex controllers that query overlapping fields, and FLS changes on the guest profile are made with only one page in mind.

**How to avoid:** Before removing field-level access from the guest profile, search for all @AuraEnabled and @InvocableMethod Apex classes reachable from guest context and check whether they reference the affected field. Coordinate FLS changes with a full review of guest-accessible Apex, not just the immediate page trigger. See `security/guest-user-security` for Apex review guidance.

---

## Gotcha 3: External OWD Controls Guest Record Visibility — Internal OWD Does Not

**What happens:** An admin sets the internal OWD for a custom object to Public Read Only so internal users can see all records. They expect this also makes records visible to guest users on a public page. The public page still shows empty results because the external OWD for that object is Private.

**When it occurs:** Whenever internal OWD and external OWD are confused. Experience Cloud introduced a split OWD model where guest users and external authenticated users follow external OWD, not internal OWD.

**How to avoid:** Always check external OWD separately from internal OWD (Setup > Sharing Settings — external OWD is the second column in the OWD table). For any object that must be visible on a public page, the external OWD must be set to Public Read Only, OR a Guest User Sharing Rule for the site must grant Read access to the specific records.

---

## Gotcha 4: Guest User Sharing Rules Are Site-Specific and Do Not Transfer Between Sites

**What happens:** An admin copies or clones a site and expects the Guest User Sharing Rules from the original site to carry over to the new site. The new site's public pages show empty results because sharing rules are associated with the original site's guest user (a distinct system user) and do not apply to the new site's guest user.

**When it occurs:** During site cloning, template changes, or when a second site is created to serve a different audience with similar public content.

**How to avoid:** After any site clone or creation, navigate to Setup > Sharing Settings > Guest User Sharing Rules and confirm rules are present and correctly configured for the new site's guest user. Do not assume sharing rules from the original site are inherited.

---

## Gotcha 5: Page Access = Public Does Not Override Missing Guest Profile Permissions

**What happens:** An admin sets a page to Public in Experience Builder and publishes the site. The page is accessible without login but displays blank components. They assume the content is published incorrectly. The actual issue is that the guest user profile has no Read access on the object the page components are querying.

**When it occurs:** When admins configure page access and profile permissions as separate steps and one step is missed — common during initial site setup or when adding a new page type to an existing site.

**How to avoid:** After setting any page to Public, immediately verify the guest user profile has the required object Read access, relevant field permissions, and appropriate sharing visibility. Use a checklist (see the template in templates/) to ensure all three gates are checked together rather than in isolation.

---

## Gotcha 6: View All Fields Is Not a Guest FLS Shortcut

**What happens:** An admin finds the Spring '25 **View All Fields** object permission (`PermissionsViewAllFields`, API 63.0+) and tries to grant it on the guest profile so every field on a public object stays readable as new fields are added.

**When it occurs:** Any time a guest-readable object keeps gaining fields and someone looks for a permission that covers them all at once. `viewAllFields` is a real `objectPermissions` element (`api_meta.txt:98183–98185`, API 63.0+), so it deploys onto a guest profile file without a syntax error.

**Why it fails:** View All Fields auto-grants read on all current and future fields for one object — useful on internal permission sets, but **View All Data, Modify All Data, and View All Fields for a given object can't be assigned to external users**, and guest profiles allow only read/create at the object level anyway.

**How to avoid:** Enumerate guest field permissions explicitly. Treat each new field on a guest-readable object as a deliberate public-exposure decision.

---

## Gotcha 7: A Route Left at `pageAccess: UseParent` Is Not Private — It Is Undecided

**What happens:** An admin classifies the site's pages, sets three of them to Public in Experience Builder, and leaves the rest alone assuming untouched means login-required. Later someone turns on public access at the site level. Every page that was never explicitly classified becomes public in the same moment, including internal-facing ones.

**When it occurs:** On any Experience Builder site where page access was set page-by-page rather than for every route. The metadata makes this visible in a way the Builder UI does not: in `experiences/<site>/routes/<page>.json`, `pageAccess` is required and takes `UseParent`, `Public`, or `RequiresLogin`, and the guide states that with the default value `UseParent`, "the status of the site determines the status of the route" (`api_meta.txt:60561–60567`).

**How to avoid:** Retrieve the site's `ExperienceBundle` and grep the `routes` folder for `"pageAccess"`. Treat every `UseParent` hit as unclassified and resolve it to `Public` or `RequiresLogin` explicitly. For an Aura site the folder does not exist in a retrieve until you enable ExperienceBundle Metadata API in Setup → Digital Experiences → Settings (`api_meta.txt:59901–59905`); LWR sites use it by default. `scripts/check_experience_cloud_guest_access.py` does not read route JSON — this one is a grep, not a checker rule.

---

## Gotcha 8: Making One Page Public Silently Turns On Guest File Access For the Whole Site

**What happens:** An admin sets a single FAQ route to Public. They never touch file settings. Asset files shared with the site become viewable by unauthenticated visitors on every public page and on the login page.

**When it occurs:** Every time public access is enabled. `Network.enableGuestFileAccess` (API 41.0+) "determines whether guest users view asset files shared with the site on publicly accessible pages and login pages", and its own field description adds: "If public access is enabled in Experience Builder at the page or site level, this property is automatically enabled" (`api_meta.txt:90832–90836`). A `false` you deployed earlier does not survive it.

**How to avoid:** Re-retrieve `networks/<Site>.network-meta.xml` after publishing any page-access change and read what `enableGuestFileAccess` actually says now, rather than trusting the value in source control. Audit which asset files are shared with the site before the first Public route ships. The related upload direction is a separate switch in a different file — `enableSiteGuestUserToUploadFiles` in `Content.settings` (`api_meta.txt:113131`) — and it is not auto-enabled.

---

## Gotcha 9: Retrieving the Guest Profile On Its Own Makes It Look Like It Grants Nothing

**What happens:** A reviewer retrieves `Profile:Help Center Profile` to audit what the site exposes. The returned file contains login hours, IP ranges, and a handful of user permissions — no `objectPermissions`, no `fieldPermissions`. They report the guest profile as clean. It is not; the org's copy grants Read on four objects.

**When it occurs:** On any Profile retrieve that does not name the objects alongside it. "When you use the `retrieve()` call to get information about profiles, the returned `.profile` files only include security settings for the other metadata types referenced in the retrieve request. Exceptions include user permissions, IP address ranges, and login hours, which are always retrieved" (`api_meta.txt:98477–98479`). The trap deepens with wildcards: "The wildcard `*` on `CustomObject` doesn't match standard objects" (`api_meta.txt:98503`), so `Case` and `Account` guest permissions stay invisible even in a `*` retrieve.

**How to avoid:** Never audit a guest profile from a profile-only retrieve. Name every object — custom *and* standard — as `CustomObject` members in the same `package.xml`, as in the manifest in `references/metadata-examples.md`. To answer "what does this guest user actually have" without a retrieve at all, query `ObjectPermissions` for the profile's permission set, which returns the org's real state regardless of manifest shape.

---

## Gotcha 10: `guestProfile` on the Site File Is Read-Only — There Is No Deploy That Rebinds It

**What happens:** A developer sees `<guestProfile>Guest</guestProfile>` in the Metadata API guide's own sample `CustomSite` definition (`api_meta.txt:47207`) and writes it into a site file to point a second site at an existing guest profile, or to move a hardened profile between orgs. The deploy succeeds. The binding does not change.

**When it occurs:** Whenever someone tries to treat the guest profile as an assignable, reusable artifact. The field table is explicit where the sample is not: `guestProfile` is "Read only. The name of the profile associated with the guest user" (`api_meta.txt:46959–46960`). The profile is created with the site and bound by creation.

**How to avoid:** Deploy the guest profile's *contents* — `objectPermissions`, `fieldPermissions`, `userPermissions` — against the profile the target org already generated for that site, and accept that its name differs per org. Do not put `guestProfile` in a source-controlled site file at all; a sample element that deploys without error and has no effect is worse than an absent one.

---

## Gotcha 11: Without `siteGuestRecordDefaultOwner`, the Guest User Owns Every Record It Creates

**What happens:** A public "Contact us" form gives the guest profile Create on Case. Cases arrive, and their `OwnerId` is the site's guest user. Assignment rules that route by owner behave oddly, reports grouped by owner show a system user, and the records sit under an identity nobody manages.

**When it occurs:** On any guest-writable object where the site file omits `siteGuestRecordDefaultOwner` (API 51.0+), "the username of the user who owns all new records that unauthenticated guest users create" (`api_meta.txt:47040–47042`). The org-level fallback that used to cover this is on its way out: `SiteSettings.enableSitesRecordReassignOrgPref` is "deprecated in API version 63.0 and later… when `false`, the guest user remains the owner of the record", default `false`, "available in API version 48.0 through 63.0" (`api_meta.txt:127224–127229`). Its Experience Cloud twin, `CommunitiesSettings.enableGuestRecordReassignOrgPref`, carries the same deprecation (`api_meta.txt:112839–112841`).

**How to avoid:** Set `siteGuestRecordDefaultOwner` on the `CustomSite` file in the same deploy that grants any `allowCreate` on the guest profile — never in a later cleanup pass, because the records created in between keep the guest owner. Point it at a named integration user, not at a person who will leave. `scripts/check_experience_cloud_guest_access.py` flags the create-without-owner combination.

---

## Gotcha 12: Apex Managed Sharing Cannot Reach a Guest User — the Declarative Rule Is the Only Path

**What happens:** A developer hits the "guest sharing rules can only grant Read" constraint and reaches for the escape hatch every other sharing problem has: insert a `__Share` row from Apex with the access level they need. The insert fails, or the row does nothing.

**When it occurs:** Whenever code tries to substitute for `sharingGuestRules`. On the share object's `UserOrGroupId` the Apex Developer Guide states flatly: "This field can't be updated. **You can't grant access to unauthenticated guest users using Apex**" (`apexdev.txt:12564`). And the declarative rule is pinned: "For `SharingGuestRule`, the `accessLevel` field can be set only to `Read`" (`api_meta.txt:129334`). Read is not a default you can widen; it is the ceiling.

**How to avoid:** Design guest record access as read-only by construction. When a public page genuinely needs a guest to affect a record, the shape is a create-only insert (gate 3 + gate 5 in `references/metadata-examples.md`), not a share grant — the guest writes a new record it never reads back. If a public page appears to show records no guest rule released, the cause is upstream of sharing: an object permission with `viewAllRecords`, or a `without sharing` Apex class. "Use the `without sharing` keyword when declaring a class to ensure that the sharing rules for the current user aren't enforced" (`apexdev.txt:4828–4830`), and triggers "always run implicitly in a `without sharing` context" (`apexdev.txt:4881–4884`). Hand that review to `security/guest-user-security`.

---

## Gotcha 13: A Guest Rule Silently Skips Records Owned by High-Volume Site Users

**What happens:** A criteria-based guest rule on `Publication_Status__c = 'Published'` releases most of the published records but not all of them. The ones missing have nothing different about their criteria field. They differ only in who owns them.

**When it occurs:** When some records are owned by high-volume Experience Cloud site users. `SharingGuestRule.includeHVUOwnedRecords` (API 52.0+) defaults to `false`, and the guide explains the consequence: "By default, only records owned by authenticated users, guest users, and queues are included in sharing rules" (`api_meta.txt:129344–129350`). Self-service portals that let external users create content hit this constantly.

**How to avoid:** Decide `includeHVUOwnedRecords` when you write the rule, not after. The same field carries "You can't edit this field after the sharing rule is created" — fixing it means deleting and recreating the rule, which drops and rebuilds every `GuestRule` share row in between. Prove the outcome by counting: compare the number of records matching your criteria against `SELECT COUNT() FROM <Object>__Share WHERE RowCause = 'GuestRule'`.

---

## Gotcha 14: Deploying `enableSecureGuestAccess` as `false` Succeeds and Changes Nothing

**What happens:** A team migrating an older org's config sees `<enableSecureGuestAccess>false</enableSecureGuestAccess>` in a retrieved `Sharing.settings` file, deploys it forward to reproduce the old behaviour, and gets a green deploy. Guest OWD stays Private. Every public page still needs guest sharing rules.

**When it occurs:** On any org, at any API version. "As of API version 50.0, this field's value is always true, regardless of the value that you set. Changing its value has no effect on Salesforce, even if it reads `false`. This change applies retroactively back to API version 47.0, when this field was first introduced" (`api_meta.txt:127101–127110`). The retrieved `false` is not a state you can restore; it is a value the API is willing to echo back.

**How to avoid:** Read the field as documentation, not as a switch. When a page shows nothing, do not spend time on this setting — go straight to gate 3 and gate 4. When migrating a pre-Spring '21 site, budget for building guest sharing rules that never existed, rather than for turning secure guest access off.

---

## Gotcha 15: A Public Route Is a Crawlable Route, and the Crawl Policy Is a File You Have to Author

**What happens:** A page is set to Public so that customers arriving from a support email can read it without logging in. Weeks later its content appears in search results, and so do records the guest sharing rule released — including ones the business considered "technically public but not advertised."

**When it occurs:** As soon as `pageAccess` is `Public` and the route is reachable on the site's domain. Nothing in the guest-access configuration expresses a crawl preference. The two levers are elsewhere and both are opt-in: `CustomSite.robotsTxtPage` is "the name of the Visualforce page to display for the robots.txt file used by web crawlers" (`api_meta.txt:47024–47025`) — a page you write, and an empty `robotsTxtPage` is an absent policy, not a restrictive one — and `preferredDomain` on the site config "represents the name of the domain to use for indexing a site's pages" (`api_meta.txt:60153–60155`).

**How to avoid:** Treat "public" and "indexed" as two separate decisions made in the same review, and record both in `templates/experience-cloud-guest-access-template.md`. Author and deploy `robotsTxtPage` alongside the first Public route rather than after launch — de-indexing a URL search engines already hold is slower than never publishing it. The indexing configuration itself belongs to `admin/experience-cloud-seo-settings`; this skill's job is only to notice that gate 2 created the exposure.
