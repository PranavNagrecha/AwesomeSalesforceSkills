# Gotchas — Experience Cloud Site Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Template Selection is Permanent

**What happens:** After a site is created with a specific template (e.g., Build Your Own Aura), there is no option to change the template. The site is permanently tied to the template family chosen at creation. Attempting to "upgrade" to LWR from Aura means deleting the site and starting over, losing all page configurations, navigation menus, branding settings, and any declarative customizations made in Experience Builder.

**When it occurs:** Any time a practitioner creates a site without fully evaluating the LWR vs Aura decision first — typically when a site is created quickly for a proof of concept and then gets treated as the production site.

**How to avoid:** Before creating the site, audit all components planned for the site. If any existing components are Aura-based and cannot be migrated to LWC within the project timeline, use the Aura Build Your Own template and document the constraint. If all components are LWC or will be built as LWC, choose LWR. Record the decision and its rationale before clicking Create.

---

## Gotcha 2: LWR Sites Require Explicit Republish — Changes Do Not Go Live Automatically

**What happens:** On an LWR site, all edits in Experience Builder (page layout, component configuration, branding token changes, navigation updates) are saved in draft state. The site continues to serve the previously published version from HTTP cache. Until the site is explicitly republished, visitors see no changes. This behavior is a direct consequence of the publish-time freeze that enables LWR's CDN caching model.

**When it occurs:** Every time a practitioner makes changes and assumes they are live because Experience Builder shows no error and the save confirms. This is especially common for practitioners migrating from Aura sites, where many changes are visible immediately without a full publish cycle.

**How to avoid:** Build an explicit "Publish" step into every deployment or change checklist. After any site modification, click the Publish button in Experience Builder. Confirm the published version timestamp updates in Site Settings. Do not mark a task as complete until the publish is confirmed.

---

## Gotcha 3: LWR and Aura Component Libraries Are Not Interchangeable

**What happens:** The Build Your Own (LWR) template's component picker in Experience Builder only surfaces LWC-compatible components. Aura components are not listed and cannot be added to LWR page regions. There is no error message explaining this — the component simply does not appear. Conversely, LWR-specific components that depend on the LWR runtime will not behave correctly if dragged into an Aura-based site.

**When it occurs:** When a team builds components in both Aura and LWC formats (common in orgs that predate the LWR templates) and assumes both types can be used in any site. Also occurs when a component built for internal Lightning App Builder pages is expected to work in an LWR Experience Cloud site without modification.

**How to avoid:** Before committing to the LWR template, run a component inventory. Check each planned component's `targetConfig` in its `*.js-meta.xml` to confirm it supports Experience Cloud (`lightning__AppPage`, `lightning__RecordPage`, or the Experience-specific target). Components without the correct targets will not be available in Experience Builder regardless of template type.

---

## Gotcha 4: Aura Sites Require the /s Path Prefix on All Page URLs

**What happens:** All page URLs in Aura-based Experience Cloud sites automatically include the `/s` prefix (e.g., `MyDomainName.my.site.com/portal/s/home`). This prefix is not configurable and cannot be removed from Aura sites. LWR sites do not have this prefix — pages are served at clean paths (e.g., `MyDomainName.my.site.com/portal/home`). When deep links, SEO configurations, or integrations are built assuming no `/s` prefix, they break on Aura sites.

**When it occurs:** When a project spec includes clean, SEO-friendly URL paths and the team creates an Aura site assuming URL configuration will be available later. Also occurs when an integration or email template embeds hard-coded links without the `/s` segment.

**How to avoid:** If clean URLs are a requirement, choose an LWR template. If an Aura template is required, document the `/s` path constraint in the URL design spec and ensure all deep links, email templates, and integration callbacks include the `/s` prefix from the start.

---

## Gotcha 5: Guest User Profile Permissions Must Be Explicitly Configured

**What happens:** By default, the guest user profile associated with a new Experience Cloud site has very restricted permissions. Public-facing pages may appear blank or show permission errors because the guest user cannot access required objects, fields, or records. This is intentional security behavior, but it surprises practitioners who expect a published site to "just work" for unauthenticated visitors.

**When it occurs:** When a site is published and tested only with an authenticated admin or partner user. The guest user experience is only broken when an unauthenticated test is performed.

**How to avoid:** After publishing, test the site explicitly as a guest user (open in an incognito/private browser window without logging in). Review the guest user profile permissions in Setup > Sites > [Site Name] > Guest User Profile. Grant object-level read access only to records the public should see. Enable field-level security for only the fields the guest user needs. Never grant guest users write access unless the use case explicitly requires it (e.g., a public case submission form) — and in that case, use a well-scoped Apex class with `without sharing` rather than direct guest user write permission.


---

## Gotcha 6: `emailSenderAddress` Is Write-Once Through the Metadata API and Later Updates Fail Silently

**What happens:** `emailSenderAddress` is a Required field on `Network` (Metadata API Guide, `Network`, api_meta.txt L90782). The guide's note on that field is unusually blunt: the address "can be added via the `emailSenderAddress` field only when you deploy Network for the first time to create a new Experience Cloud site", the address must be verified before it can be used, and — the part that costs time — "You can't update this field via Metadata API. If you attempt to update this field via Metadata API, your changes are ignored and Salesforce doesn't show an error" (api_meta.txt L90784–L90795). The deploy returns Succeeded. The sender address in the org is unchanged. Portal password-reset and welcome emails keep going out from the wrong address.

**When it occurs:** On the second and every later deploy of a site — a sandbox-to-production promotion, a copy of a site definition into a new org, or a routine "fix the from address" change committed to the `.network-meta.xml`. It never occurs on the first deploy, which is why it survives the initial build and surfaces during a rebrand or a domain migration.

**How to avoid:** Treat the `emailSenderAddress` element as a create-time-only value. To change it afterwards, go to the site's Administration workspace, select Emails, and edit the Email Address field there — the route the guide names (api_meta.txt L90793–L90795). Verify the new address in the org **before** the first deploy, not after. Diff the deployed value against the org rather than against the repo, because source and org will diverge without an error. `newSenderAddress` holds an address entered but not yet verified, and only overwrites `emailSenderAddress` after the verification email is answered (api_meta.txt L90978–L90984). UNVERIFIED (2026-09-04): the Metadata API Developer Guide says the address must be "verified" but does not say it must be an Organization-Wide Email Address; treat the OWEA framing as a working assumption, not a documented requirement.

---

## Gotcha 7: `UnderConstruction` Is a One-Way Door — There Is No Route Back to Preview

**What happens:** `Network.status` is Required and takes exactly `Live`, `DownForMaintenance` or `UnderConstruction` (api_meta.txt L91054–L91074). The Setup labels differ from the API values: `Live` is **Published**, `DownForMaintenance` is **Offline**, `UnderConstruction` is **Preview** (object_reference.txt L187347–L187373). `UnderConstruction` means the site has never been published, and the Object Reference states the constraint plainly: "After a site is published, it can never be in this status again" (object_reference.txt L187373). Deploying `<status>UnderConstruction</status>` at a site that has been Live once does not roll it back to a private preview.

**When it occurs:** When a team wants to pull a live portal back for rework and reaches for the status value they used during the build. Also when an org-to-org promotion carries a source file whose status was never advanced past the build-time value, and the deploy silently leaves the target site where it was.

**How to avoid:** Use `DownForMaintenance` to take a published site offline. Members lose access and the site shows in the picker as `SiteName (Offline)`, while users holding Create and Set Up Experiences keep setup access regardless of profile or membership (api_meta.txt L91064–L91073). Reserve `UnderConstruction` for the build phase of a site that has never gone Live, and confirm the real state with SOQL after every deploy — `SELECT Status FROM Network WHERE Name = '<site>'` — rather than reading the deploy result.

---

## Gotcha 8: LWR and Aura Sites Use Different Content Metadata Types, and Enhanced LWR Cannot Be Packaged

**What happens:** Site *settings* live in `Network`, but the site's pages, routes, themes and branding sets live in a separate bundle type — and which type is correct depends on when and how the site was created, not on what you prefer. The guide's rule: "In Experience Cloud, you can use DigitalExperienceBundle for enhanced LWR sites created in Winter '23 or later. For Aura sites and other LWR sites, use the ExperienceBundle (recommended) or the SiteDotCom metadata types. Packaging is unsupported for enhanced LWR sites" (api_meta.txt L51234–L51238). Retrieving with the wrong type returns nothing useful; the site metadata appears absent and the practitioner concludes the content is not source-controllable.

**When it occurs:** On the first retrieve of an inherited site, when the folder that comes back (`experiences/` versus `digitalExperiences/site/`) does not match the manifest that was written from a blog post. It also occurs at the packaging gate: a team plans to ship an enhanced LWR site in an unlocked or managed package and discovers packaging is unsupported for that site type only after building it.

**How to avoid:** Retrieve first, then write the manifest from the folders the org actually returned. `experiences/` means `ExperienceBundle`, addressed by bare name; `digitalExperiences/site/<name>` means `DigitalExperienceBundle`, addressed workspace-qualified as `site/<name>` in `package.xml` (api_meta.txt L51357–L51360) and paired with a `DigitalExperienceConfig` that carries the URL path prefix (api_meta.txt L54019–L54026). If the delivery mechanism must be a package, settle the site type before build, not after. Aura sites additionally need **Enable ExperienceBundle Metadata API** switched on in Setup → Digital Experiences → Settings; LWR sites use ExperienceBundle by default (api_meta.txt L59901–L59904).

---

## Gotcha 9: `SiteDotCom` in an ExperienceBundle Manifest, and the ExperienceBundle API-Version Trap

**What happens:** Two documented deploy behaviours that no error message explains in advance. First: "When deploying an Experience Builder site with ExperienceBundle, ensure that the SiteDotCom type isn't included in the manifest file" (api_meta.txt L61110). A manifest that lists both types — easy to produce, because a wildcard-heavy `package.xml` picks up `SiteDotCom` on its own — is outside what the guide supports. Second: "ExperienceBundle doesn't support retrieving and deploying across different API versions" (api_meta.txt L61111–L61112). Content retrieved at API 48.0 and deployed from a `package.xml` set to 62.0 is a version mismatch, not an upgrade.

**When it occurs:** On any org-to-org promotion where the source project was created against an older API version than the one in the current `sfdx-project.json` or `package.xml`, and on any manifest generated by a broad wildcard sweep rather than written deliberately.

**How to avoid:** Keep `SiteDotCom` out of any manifest that carries `ExperienceBundle`. To move ExperienceBundle metadata forward a version, follow the guide's three-step sequence: set `package.xml` to the *old* version and deploy, then set `package.xml` to the new version, then retrieve to pick up the newer-format updates (api_meta.txt L61113–L61115). Cross-org promotion mechanics beyond this belong to `devops/experience-cloud-deployment-admin`.

---

## Gotcha 10: `urlPathPrefix` Is Updatable — Which Is the Trap, Not the Relief

**What happens:** `Network.UrlPathPrefix` carries the properties `Filter, Group, Nillable, Sort, Update` in the Object Reference (object_reference.txt L187375–L187378), so the platform does permit changing it. What it does not do is change anything else. The Experience Builder content bundle carries its own `urlPathPrefix`, and the guide requires the two to agree: for Aura sites and authenticated LWR sites created before Winter '23 the bundle path ends in `/s` and the part without the `/s` must match the Network's URL; for unauthenticated LWR sites and authenticated LWR sites created after Winter '23 there is no `/s` (api_meta.txt L59918–L59937). An enhanced LWR site keeps a third copy inside `DigitalExperienceConfig` (api_meta.txt L54019–L54026). Change one and the site answers on a path its content does not agree with.

**When it occurs:** During a rename requested late — "can we move it from `/community` to `/support`" — and during org-to-org promotion where the source and target sites were created with different prefixes and one file in the set was hand-edited to match.

**How to avoid:** Treat the prefix as a decision to make once, at creation, and change it only as a coordinated set: `Network`, the bundle (`ExperienceBundle.urlPathPrefix` or `DigitalExperienceConfig.site.urlPathPrefix`), and the `CustomSite`. Then re-issue every deep link: welcome, forgot-password and lockout email templates named on the `Network`, plus any integration callback. Confirm the result with `SELECT UrlPathPrefix FROM Network WHERE Name = '<site>'` rather than by loading the home page, which may still resolve from cache.

---

## Gotcha 11: Membership by Permission Set Skips Chatter Customers, and Neither Path Grants a Licence

**What happens:** `networkMemberGroups` accepts both `<profile>` and `<permissionSet>` children — "The profiles and permission sets that have access to the site. Users with these profiles or permission sets are members of the site" (api_meta.txt L90963–L90966). Buried under it is a carve-out: "If a Chatter customer (from a customer group) is assigned a permission set that is also associated with a site, the Chatter customer isn't added to the site" (api_meta.txt L90967–L90970). That subset of users is quietly excluded from the membership the permission set was supposed to create. Separately, membership is a consequence, not a grant: `NetworkMember` supports only `describeSObjects()`, `query()`, `retrieve()` and `update()` (object_reference.txt L188301–L188302), so there is no row to insert and no licence conferred by adding a group.

**When it occurs:** When a site is switched from profile-based to permission-set-based membership as part of a profile-to-permission-set migration, and the member count afterwards is lower than the count before with no error anywhere.

**How to avoid:** Reconcile after every membership change with `SELECT COUNT(Id) FROM NetworkMember WHERE Network.Name = '<site>'` and compare against the assignment count for the permission sets you listed. The licence question — which community licence each persona needs, member-based versus login-based, and the Sales Cloud licence that Partner Community sits on — is settled in `admin/portal-requirements-gathering` (its Gotchas 2, 5 and 8) before any group is written into `networkMemberGroups`. Provisioning the users themselves is `admin/experience-cloud-member-management`.

---

## Gotcha 12: `selfRegistration` Without `selfRegProfile` Is a Valid Deploy and a Broken Site

**What happens:** `selfRegistration` is a plain boolean on `Network`, and `selfRegProfile` "is used only if selfRegistration is enabled for the site" (api_meta.txt L91035–L91042). Neither field is Required, so a `Network` with `<selfRegistration>true</selfRegistration>` and no `<selfRegProfile>` deploys cleanly. The site then advertises a self-registration path with no profile to assign registrants to. The two fields are also visible on the object as `OptionsSelfRegistrationEnabled` and `SelfRegProfileId` (object_reference.txt L187224, L187338), which is how to detect the mismatch in an org you did not build.

**When it occurs:** When self-registration is enabled during a demo or pilot and the profile is set through Setup rather than source, so the source file carries the switch but not the profile; the gap then travels to the next org on the next deploy.

**How to avoid:** Never deploy `selfRegistration` `true` without `selfRegProfile` in the same file — the skill's checker (`scripts/check_experience_cloud_site_setup.py`) treats that combination at `status` `Live` as an ERROR for this reason. Then handle what self-registration does to your Contact data: it is one site-wide switch, every registrant lands on that single profile, and duplicate Contacts are the predictable result. The matching-rule and duplicate-rule pairing that contains it is specified in `admin/portal-requirements-gathering`, Gotcha 10 — do not re-derive it here.
