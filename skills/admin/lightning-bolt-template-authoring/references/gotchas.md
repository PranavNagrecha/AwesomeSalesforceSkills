# Gotchas — Lightning Bolt Template Authoring

Non-obvious platform behaviors that bite admins and partners building Lightning Bolt Solutions.

UNVERIFIED (2026-10-20) (file-level): runtime symptoms after instantiation (empty banners, broken pages, fresh URLs, forked sites) are Help-only or field experience; metadata facts carry their cite.

---

## Gotcha 1: A Bolt does NOT include any data, CMS content, or files

**Symptom:** Source org's community has rich Knowledge articles, CMS-managed banner content, and a few seeded `Account` records the home page references. After Bolt deploy + instantiation in the target org, the new community renders empty hero banners, broken Knowledge links, and a home page with `null` references where the seeded records used to be.

**Why:** A `LightningBolt` lists only `lightningBoltItems` of type `CommunityTemplateDefinition`, `CustomApplication` and `FlowCategory`, plus ContentAsset preview images (api_meta 264 L86574-86633). It does NOT include:

- Data — no records of any kind (`Account`, `Contact`, `Knowledge__kav`, custom objects, etc.).
- Enhanced CMS content — CMS workspaces, channels, and content nodes are not item types, so they do not move with the Bolt.
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

Document in the Bolt's listing description what dependencies the receiving org must install first. The Bolt will install successfully without those dependencies — and the instantiated site will look broken until they are present (UNVERIFIED (2026-10-20)).

---

## Gotcha 2: Flows ride in a FlowCategory, and activation follows the Flow file

**Symptom:** Source team activates a newer version of `Partner_Self_Register` after retrieving the Bolt. Bolt is deployed to a target org. Target org runs the older logic.

**Why:** "Flows aren't added directly to a Lightning Bolt Solution. Instead, add the category the flows are in" (api_meta 264 L76581-76582); the `FlowCategory` lists each flow in `flowCategoryItems` (L76600-76610). The retrieved `Flow` file is whatever was retrieved, so a later activation in the source does not update it. From API 44.0 Salesforce recommends flow files without version numbers and activating through the `Flow` itself, not `FlowDefinition`; "if you deploy with flow definitions, the active version numbers in the flow definitions override the status fields in the flows" (L76658-76663).

**Fix:**

1. Re-retrieve every flow the `FlowCategory` lists immediately before each Bolt version cut. Don't trust the previously retrieved tree.
2. Verify post-deploy in the target org which flow version is active (Tooling API `SELECT MasterLabel, VersionNumber, Status FROM Flow WHERE Definition.DeveloperName = 'Partner_Self_Register'`; UNVERIFIED (2026-10-20): the Tooling Flow object is not in the corpus).
3. If the active version is wrong, activate the correct version in Setup, or deploy the `Flow` with the intended `status`; a `FlowDefinition` with `activeVersionNumber` also works but overrides flow status and is the pre-44.0 pattern (L76658-76663).

---

## Gotcha 3: CMS content is not in the Bolt by default

**Symptom:** Source community uses an Enhanced CMS workspace called `Partner_Marketing_Content` to author hero images, callout banners, and announcement cards. These are referenced by CMS Single Item / CMS Collection components on community pages. After Bolt deploy + instantiation, the components render but show "Content not found" placeholders.

**Why:** Enhanced CMS lives in the `ManagedContentType` metadata type (api_meta 264 L89063) and `ManagedContent` / `ContentVersion` records (obj 264 L180276, L79202) — none of them a Bolt item type (api_meta 264 L86629-86633). Bolt packaging does not include CMS workspaces or their content nodes. The component's reference is preserved (it knows it should render `Partner_Marketing_Content / hero_banner_001`) but the content object does not exist in the target org.

**Fix:** Three viable approaches, depending on intent:

1. **Recreate manually.** Document the CMS workspace structure and content needed. Target-org admin re-authors. Acceptable for small templates with ≤10 content items.
2. **CMS-to-CMS migration.** Use the Salesforce CMS REST API or Workbench to export/import workspaces and content. Scriptable but not bundled with the Bolt deploy.
3. **Switch to direct image references.** For static branding content (logos, banners), put images in `staticresources` and reference them directly from components instead of CMS. Static resources DO ship with metadata deploys. CMS is for *editorially-managed* content; if your community treats it as static, ship it as static resources.

The platform direction is increasingly "CMS for everything" — but for Bolt-portable communities, static-resource references are more shippable.

---

## Gotcha 4: Theme components and global navigation are templated, not branded

**Symptom:** Source team customizes the global navigation menu and applies a custom Theme component (e.g. a custom header LWC drop-zone) in the source community. After Bolt instantiation in the target org, the navigation appears but pointed at the source org's URLs (not the target's), and the custom Theme component shows but with broken sub-component references.

**Why:**

- **Navigation menu items**: Stored in the `NavigationMenu` metadata type (api_meta 264 L93179-93181), referenced by URL or by record-based target. The template carries the menu structure (UNVERIFIED (2026-10-20)), but URLs that hardcode the source community's domain or specific record IDs will break in the target.
- **Theme components**: A `CommunityThemeDefinition` (which a packaged template must bring, pkg2_dev 264 L4777-4778) references LWC / Aura components. Those components must exist in the target org (either as part of the package or as standard platform components). If the source's Theme uses a custom LWC `c-acme-partner-header`, that LWC must also ship — not via Bolt (Bolts don't carry LWC) but via a managed/unlocked package alongside the Bolt.

**Fix:**

1. Audit `NavigationMenuItem` records before Bolt cut. Replace hardcoded URLs with relative URLs (`/partners/registration` not `https://acme-source.my.site.com/partners/registration`). Replace hardcoded record IDs with named-credential / cross-org-portable references where possible.
2. Audit `Theme` references. Any custom LWC / Aura component referenced by the theme must ship as part of an accompanying managed/unlocked package. The Bolt + package combination is one shipment unit; document this dependency in the Bolt listing.
3. The bundled checker (`scripts/check_lightning_bolt_template_authoring.py`) reports navigation items with hardcoded `https://` URLs and record-ID-shaped values so they can be triaged before publish.

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

**Why:** Custom objects are not a Bolt item type (api_meta 264 L86629-86633). The site's page configuration says "show records of type `Partner_Deal__c`" — but the object itself doesn't exist in the target. UNVERIFIED (2026-10-20): that the deploy succeeds without cross-reference validation and the failure surfaces only at render time.

**Fix:**

1. Inventory custom-object references in the `ExperienceBundle` before publish. The bundled checker walks every `experiences/<bundle>/**/*.json` file and reports names that end with `__c`.
2. For each custom object referenced: ship a managed (or unlocked) package containing those objects + fields, and document that the package must be installed *before* the Bolt is used to instantiate a site.
3. If the dependency cannot be packaged, redesign the Bolt to use only standard objects. A truly portable Bolt should generally reference only `Account`, `Contact`, `Lead`, `Case`, `Opportunity`, `Knowledge__kav`, `Asset`, `Order`, `Product2`, `User`, plus standard chatter / experience objects.

---

## Gotcha 7: A Bolt has no version field, and created sites do not upgrade

**Symptom:** Source team ships v2.0 of a Bolt. Existing target orgs that instantiated sites from v1.0 do not see any update. The expectation was that v2.0 would propagate.

**Why:** `LightningBolt` has no version element (fields: api_meta 264 L86543-86585). A managed package can version it — the component "Is Updated During Package Upgrade: Yes" (pkg2_dev 264 L11920-11923) — but that updates the Bolt definition, not the sites created from it. When a target org *instantiates* a site, the resulting site is a fork with no reference back to the Bolt (UNVERIFIED (2026-10-20): the fork model is Help-only); that admin would have to re-instantiate or hand-merge changes.

**Fix:**

- Set expectations: communicate "Bolts ship starting points, not upgrade paths" in every release announcement.
- For parts of the community that *do* need to upgrade (especially Apex behavior, Lightning components used inside `ExperienceBundle` slots), put them in a managed package layered on top. The managed package gets real upgrade semantics; the Bolt remains the site-shape starter.
- Track which orgs installed which package version in your release tracker. The platform doesn't surface this; you must maintain it externally if you have multiple orgs on different versions.
