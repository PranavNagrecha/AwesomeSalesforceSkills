# Gotchas — Lightning Bolt Template Authoring

Non-obvious platform behaviors that bite admins and partners building Lightning Bolt Solutions. Each is a confirmed reason a Bolt deploy or instantiation has gone wrong in real implementations.

---

## Gotcha 1: A Bolt does NOT include any data, CMS content, or files

**Symptom:** Source org's community has rich Knowledge articles, CMS-managed banner content, and a few seeded `Account` records the home page references. After Bolt deploy + instantiation in the target org, the new community renders empty hero banners, broken Knowledge links, and a home page with `null` references where the seeded records used to be.

**Why:** The `LightningBolt` metadata bundles `ExperienceBundle`, `Theme`, `flowCategories`, `customApps`, and `images` only. It explicitly does NOT include:

- Data — no records of any kind (`Account`, `Contact`, `Knowledge__kav`, custom objects, etc.).
- Enhanced CMS content — CMS workspaces, channels, and content nodes do not move with the Bolt.
- Files / Files Connect content.
- Custom objects, custom fields, validation rules, sharing rules, permission sets, profiles, or Apex.

The receiving site has the *shape* but none of the *content*.

**Fix:** Plan the dependency layering up front:

| Dependency type | Ship via |
|---|---|
| Data (seed records) | Salesforce Inspector / SFDX `data import tree` post-install script |
| CMS content | CMS-to-CMS export-and-import or manual recreation; no automated path bundled with Bolt |
| Custom objects, fields, Apex, permission sets | Managed (or unlocked) package installed *before* the Bolt instantiates the site |
| Knowledge articles | Article import via Data Loader / Salesforce Knowledge migration tool |

Document in the Bolt's listing description what dependencies the receiving org must install first. The Bolt will install successfully without those dependencies — and the instantiated site will look broken until they are present. This is the #1 Bolt failure mode in the wild.

---

## Gotcha 2: Flow versions vs flow definitions in a Bolt

**Symptom:** Source team activates flow version 5 of `Partner_Self_Register` after retrieving the Bolt. Bolt is deployed to a target org. Target org runs version 3 of the flow (or the flow runs with stale logic).

**Why:** Two separate metadata items in play:

- `FlowDefinition` — the umbrella; specifies which version is *active*.
- `Flow` — the actual flow logic, one file per version.

When the Bolt's `flowCategories` references `Partner_Login_Flows`, the SFDX retrieve picks up the `Flow` metadata that was active *at retrieve time*. Re-activating a different version in the source org afterwards does not retroactively update the Bolt's bundled file. The Bolt becomes stale.

Worse: when the Bolt is deployed to a target org, the deployed `Flow` definition lands as a *new* version in the target's flow definition table. Whether it is auto-activated depends on the target org's `FlowDefinition` for that flow — if the target already has a different version active, the deployed version may sit inactive.

**Fix:**

1. Re-retrieve all `Flow` metadata immediately before each Bolt version cut. Don't trust the previously retrieved tree.
2. Verify post-deploy in the target org which flow version is active (`SELECT MasterLabel, VersionNumber, Status FROM Flow WHERE Definition.DeveloperName = 'Partner_Self_Register'`).
3. If the active version is not the one the Bolt shipped, manually activate the correct version via `Setup → Process Automation → Flows`, or include an `FlowDefinition` metadata file in the deploy that pins the active version number.

---

## Gotcha 3: CMS content is not in the Bolt by default

**Symptom:** Source community uses an Enhanced CMS workspace called `Partner_Marketing_Content` to author hero images, callout banners, and announcement cards. These are referenced by CMS Single Item / CMS Collection components on community pages. After Bolt deploy + instantiation, the components render but show "Content not found" placeholders.

**Why:** Enhanced CMS lives in `ManagedContentType`, `ManagedContent`, and `ContentVersion` objects, which are *separate* metadata types from `ExperienceBundle`. Bolt packaging does not include CMS workspaces or their content nodes. The component's reference is preserved (it knows it should render `Partner_Marketing_Content / hero_banner_001`) but the content object does not exist in the target org.

**Fix:** Three viable approaches, depending on intent:

1. **Recreate manually.** Document the CMS workspace structure and content needed. Target-org admin re-authors. Acceptable for small templates with ≤10 content items.
2. **CMS-to-CMS migration.** Use the Salesforce CMS REST API or Workbench to export/import workspaces and content. Scriptable but not bundled with the Bolt deploy.
3. **Switch to direct image references.** For static branding content (logos, banners), put images in `staticresources` and reference them directly from components instead of CMS. Static resources DO ship with metadata deploys. CMS is for *editorially-managed* content; if your community treats it as static, ship it as static resources.

The platform direction is increasingly "CMS for everything" — but for Bolt-portable communities, static-resource references are more shippable.

---

## Gotcha 4: Theme components and global navigation are templated, not branded

**Symptom:** Source team customizes the global navigation menu and applies a custom Theme component (e.g. a custom header LWC drop-zone) in the source community. After Bolt instantiation in the target org, the navigation appears but pointed at the source org's URLs (not the target's), and the custom Theme component shows but with broken sub-component references.

**Why:**

- **Navigation menu items**: Stored as `NavigationMenu` and `NavigationMenuItem` records, referenced by URL or by record-based target. Bolt bundles the menu structure, but URLs that hardcode the source community's domain or specific record IDs will break in the target.
- **Theme components**: A `Theme` metadata record references LWC / Aura components. Those components must exist in the target org (either as part of the package or as standard platform components). If the source's Theme uses a custom LWC `c-acme-partner-header`, that LWC must also ship — not via Bolt (Bolts don't carry LWC) but via a managed/unlocked package alongside the Bolt.

**Fix:**

1. Audit `NavigationMenuItem` records before Bolt cut. Replace hardcoded URLs with relative URLs (`/partners/registration` not `https://acme-source.my.site.com/partners/registration`). Replace hardcoded record IDs with named-credential / cross-org-portable references where possible.
2. Audit `Theme` references. Any custom LWC / Aura component referenced by the theme must ship as part of an accompanying managed/unlocked package. The Bolt + package combination is one shipment unit; document this dependency in the Bolt listing.
3. The bundled checker (`scripts/check_lightning_bolt_template_authoring.py`) reports navigation items with hardcoded `https://` URLs and theme references to non-standard component types so they can be triaged before publish.

---

## Gotcha 5: Site URL is reset on instantiation, not retained

**Symptom:** A team expects "we'll Bolt the existing community and the new instantiation will inherit the source's URL." After instantiation in the target org, the new site has a fresh `/s/` URL automatically generated by the target org.

**Why:** The site URL is established when the target-org admin instantiates a new site from the Bolt template. It is part of the *target* org's site administration, not the Bolt content. The source URL has no meaning outside its own org boundary anyway — DNS lookups for `acme-source.my.site.com` resolve to the source org, not anywhere else.

**Fix:** This is by design and not a bug to work around. Two implications:

1. Any in-Bolt content that hardcodes the source site URL (in custom HTML blocks, rich-text components, or scripted navigation) needs to be replaced with relative URLs before retrieving the bundle.
2. After Bolt instantiation, the target-org admin will set up their own custom domain (`Setup → All Sites → (new site) → Domains and Custom URLs`). Communicate this expectation in the Bolt listing's installation guide.

---

## Gotcha 6: A Bolt referencing standard objects works; referencing custom objects fails silently

**Symptom:** Source community has a "Knowledge Articles" page (referencing standard `Knowledge__kav`) and a "Partner Deals" page (referencing custom `Partner_Deal__c`). After Bolt deploy + instantiation in a target org that does NOT have the `Partner_Deal__c` custom object, the Knowledge page works but the Partner Deals page renders an error or a broken record-list component.

**Why:** Bolt bundles do not include custom object metadata. The `ExperienceBundle` carries the *page configuration* that says "show records of type `Partner_Deal__c`" — but the object itself doesn't exist in the target. The deploy succeeds (the metadata API doesn't validate cross-references for `ExperienceBundle` against the target's data model) and the failure surfaces only at component render time.

**Fix:**

1. Inventory custom-object references in the `ExperienceBundle` before publish. The bundled checker walks `experiences/<bundle>/views/*.json` and `experiences/<bundle>/routes/*.json` looking for `objectApiName` references and reports any that end with `__c`.
2. For each custom object referenced: ship a managed (or unlocked) package containing those objects + fields, and document that the package must be installed *before* the Bolt is used to instantiate a site.
3. If the dependency cannot be packaged, redesign the Bolt to use only standard objects. A truly portable Bolt should generally reference only `Account`, `Contact`, `Lead`, `Case`, `Opportunity`, `Knowledge__kav`, `Asset`, `Order`, `Product2`, `User`, plus standard chatter / experience objects.

---

## Gotcha 7: `versionNumber` is a label, not an upgrade contract

**Symptom:** Source team ships v2.0 of a Bolt. Existing target orgs that instantiated sites from v1.0 do not see any update. The expectation was that v2.0 would propagate.

**Why:** `LightningBolt.versionNumber` is a free-form string (`"1.0"`, `"2.0"`, `"v3-rc1"`). The platform does not maintain a version graph or upgrade relationship between Bolts of different `versionNumber` values. Crucially: when a target org *instantiates* a site from a Bolt, the resulting site is a fork. It carries no reference back to the Bolt definition. Even if you re-deploy the same Bolt with the same name and a higher `versionNumber`, the existing instantiated site is unaffected — that admin would have to manually re-instantiate or hand-merge changes.

**Fix:**

- Set expectations: communicate "Bolts ship starting points, not upgrade paths" in every release announcement.
- For parts of the community that *do* need to upgrade (especially Apex behavior, Lightning components used inside `ExperienceBundle` slots), put them in a managed package layered on top. The managed package gets real upgrade semantics; the Bolt remains the site-shape starter.
- Track which orgs installed which `versionNumber` in your release tracker. The platform doesn't surface this; you must maintain it externally if you have multiple orgs on different versions.
