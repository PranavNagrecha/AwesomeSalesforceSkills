---
name: lightning-bolt-template-authoring
description: "Use when an admin or partner needs to package an Experience Cloud (Community) site as a reusable Lightning Bolt Solution for distribution — covers the export workflow from Experience Builder, what gets bundled (ExperienceBundle, custom apps, flow categories, theme, layouts, navigation menus) versus what does NOT (data, CMS content, files), choosing Bolt vs managed package vs unlocked package vs cloning a site, sandbox-to-production promotion, multi-org distribution, AppExchange listing as a Bolt, and template versioning (LightningBolt has no version field; a managed package version carries it). Triggers: 'turn this community into a reusable template', 'package an Experience Cloud site to ship to multiple orgs', 'export Experience Builder template for AppExchange', 'should we use a Bolt or a managed package for this community', 'create an industry-specific community starter', 'how do we version our partner portal template', 'distribute branded Experience site across business units'. NOT for general Experience Cloud site build, content, or member setup (use admin/experience-cloud-site-setup, admin/experience-cloud-cms-content, admin/experience-cloud-member-management). NOT for shipping Apex / LWC / data-model functionality as a product (use devops/managed-package-development, devops/second-generation-managed-packages, devops/unlocked-package-development). NOT for moving a single Experience site between sandbox and prod as a one-off (use devops/experience-cloud-deployment-admin, devops/cicd-for-experience-cloud)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - lightning-bolt-template-authoring
  - lightning-bolt
  - experience-cloud
  - experience-bundle
  - appexchange
  - template-versioning
  - partner-distribution
triggers:
  - "we want to turn this Experience Cloud site into a reusable template our partners can install"
  - "package an Experience Builder community as a Lightning Bolt to ship to multiple business units"
  - "should we use a Lightning Bolt or a managed package to distribute our partner portal"
  - "export an Experience site as an AppExchange-listable template"
  - "how do we version a Lightning Bolt so existing installs can pick up updates"
  - "build an industry-specific community starter (financial services, healthcare, manufacturing) that includes flows and a theme"
  - "the partner team cloned the same community 14 times — can we Bolt it instead"
  - "what gets included when I export a community as a Bolt — does data come with it"
inputs:
  - "Source Experience Cloud site name and template type (Customer Service, Partner Central, Build Your Own LWR/Aura, etc.)"
  - "Distribution intent: single-org reuse, multi-org internal, partner-only AppExchange listing, public AppExchange listing"
  - "Custom apps, Flow categories, Theme, and any custom Lightning components the site relies on"
  - "Versioning expectation: do you need installed sites to pick up future updates, or are downstream sites forks once created"
outputs:
  - "Decision (Bolt vs managed package vs unlocked package vs site clone) with cited tradeoffs"
  - "ExperienceBundle export checklist plus a `LightningBolt` metadata definition (category, masterLabel, publisher, summary, lightningBoltFeatures, lightningBoltImages, lightningBoltItems)"
  - "Sandbox-to-production promotion plan and multi-org distribution recipe (direct deploy, package, or AppExchange)"
  - "Versioning policy: which package version carries the Bolt, what installed sites inherit, what they do not"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Lightning Bolt Template Authoring

Activate this skill when an Experience Cloud site needs to leave its origin org. `LightningBolt` "represents the definition of a Lightning Bolt Solution, which can include custom apps, flow categories, and Experience Builder templates" (api_meta 264 L86524) — the platform-native way to ship an Experience site *template* that other orgs can stamp out. The skill is about *packaging* — it is not about building the site itself, nor about distributing CRM functionality (use a managed or unlocked package for that).

---

## Before Starting

Gather this context before scaffolding a Bolt:

- **Which runtime the source site uses (LWR or Aura).** `LightningBolt` has no `templateApi` field (its fields are api_meta 264 L86543-86585); the site template enters the Bolt as a `CommunityTemplateDefinition` item (L86629-86633). The runtime matters for retrieval: LWR sites use `ExperienceBundle` by default, while Aura sites need "Enable ExperienceBundle Metadata API" in Digital Experiences settings (L62411-62413). UNVERIFIED (2026-10-20): that an LWR-built template cannot instantiate an Aura site.
- **Distribution intent.** Three different intents map to three different artifacts:
  - *Reuse the site within the same org* — clone the Experience site directly. No Bolt needed.
  - *Reuse across orgs you control* — deploy the Bolt metadata directly, or package it: `LightningBolt` is packageable in 1GP and 2GP managed packages (pkg2_dev 264 L11920-11921). No AppExchange listing required.
  - *Reuse across customer orgs you do not control* — Bolt listed on AppExchange. UNVERIFIED (2026-10-20): a separate Bolt listing flow, the partner Business Org requirement, and when security review applies are Help-only.
- **What the site references.** A Bolt's `lightningBoltItems` are only `CommunityTemplateDefinition`, `CustomApplication` and `FlowCategory` (api_meta 264 L86629-86633); a packaged `CommunityTemplateDefinition` must bring its `CommunityThemeDefinition` (pkg2_dev 264 L4777-4778). Apex classes, custom objects, custom fields, permission sets, sharing rules, CMS content, files and data are not item types, so any the site relies on ship separately (managed package, unlocked package, or post-install setup script). UNVERIFIED (2026-10-20): that the Bolt installs without them and the instantiated site then throws runtime errors.
- **Versioning expectation.** `LightningBolt` has no version field. In a managed package the Bolt component "Is Updated During Package Upgrade: Yes" (pkg2_dev 264 L11923), but sites already created from it are forks at instantiation time (UNVERIFIED (2026-10-20): the fork model is Help-only). Plan for this up front, especially for partner portals or shared tenants where downstream changes may need to propagate.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which data, records and seed content must the new site show on day one? | No data, CMS content or files ride in a Bolt (Gotcha 1) | A seed-data and content plan beside the Bolt |
| Which flows does the site use, and in which flow category? | Flows enter only through a `FlowCategory` item (Gotcha 2) | A `FlowCategory` per flow group, with every flow present |
| Does the site use CMS content? | CMS workspaces do not travel with the template (Gotcha 3) | A recreate, migrate or static-resource decision |
| Do navigation items or theme components hardcode URLs, record IDs or custom LWCs? | Those break in the target org (Gotcha 4) | Relative URLs and a companion package for custom components |
| Which custom domain will the new site use? | The target org sets its own site URL (Gotcha 5) | A domain plan in the installation guide |
| Which custom objects do the pages reference? | They are not Bolt item types (Gotcha 6) | A companion package installed first |
| Must existing sites pick up later template changes? | Created sites are forks; only the Bolt definition upgrades (Gotcha 7) | A managed-package layer for anything that must change later |

UNVERIFIED (2026-10-20): row 5 (the target org sets a fresh site URL) and row 7's fork-at-instantiation model are Help-only.

A proper configuration adds a declared dependency set and a version-carrying package, where "just exporting it" ships a template whose missing dependencies surface only after instantiation (UNVERIFIED (2026-10-20): the install-then-break sequence is field experience).

---

## Core Concepts

### Concept 1 — Bolt vs managed package vs unlocked package vs site clone

Four distribution shapes, four different problem domains. Pick by *what is being distributed*, not by familiarity:

| Shape | Distributes | When to use | Salesforce reference |
|---|---|---|---|
| **Lightning Bolt Solution** | An Experience site as a *template* — `lightningBoltItems` of type `CommunityTemplateDefinition`, `CustomApplication`, `FlowCategory` (api_meta 264 L86629-86633), plus preview images and feature text. NO data, NO CRM functionality. | The deliverable is a brandable, configurable Experience site that the target org will *instantiate* and customize further. Industry-specific community starters, partner-portal templates, branded community kits. | `LightningBolt` metadata; Build a Lightning Bolt Solution guide. |
| **Managed (2GP) package** | Apex / LWC / Aura / custom objects / fields / permission sets / Flow definitions / data model. Versioned with upgrade path. Optional security review for AppExchange. | The deliverable is *behavior* (an ISV product, a managed extension). Owner retains code; subscriber installs and upgrades. | `Package2` metadata; 2GP developer guide. |
| **Unlocked package** | Same metadata coverage as managed but unlocked — subscriber org owns and can edit installed components. Versioned with upgrade path but not security-reviewed. | Internal multi-org reuse where you want package versioning but the subscriber needs to be able to modify. Good for shared cross-BU CRM extensions. | Unlocked packages: "metadata in unlocked packages can be modified in a production org" (sfdx 264 L14470-14471). |
| **Site clone (in-org only)** | An Experience site copied to a new site within the same org. | One-off reuse within a single org. No need to leave the org boundary. | Setup → All Sites → New (UNVERIFIED (2026-10-20): UI path). |

A common mistake is reaching for a managed package because that is what the partner team is familiar with. If the deliverable is *the look and feel and starting structure of a community site*, a Bolt is the right tool — and shipping the site itself as packaged components would lock them for the subscriber — a packaged `CommunityTemplateDefinition` and `CommunityThemeDefinition` are editable only by the package developer (pkg2_dev 264 L4762-4763 and L4816-4817) — which works against site customization, the entire point of a template.

A second common mistake is using a Bolt to distribute Apex or a custom object dependency. Bolts cannot carry Apex / custom objects / fields — they are not `lightningBoltItems` types (api_meta 264 L86629-86633). If the site needs them, the dependency must ship separately. The pattern is: Bolt for the *site shape*, managed (or unlocked) package for the *behavior dependencies*, with Bolt installation gated on the package being installed first.

### Concept 2 — What is actually inside a Bolt

The `LightningBolt` definition (suffix `.lightningBolt`, folder `lightningBolts`, API 43.0+; api_meta 264 L86532-86536) is small — it points at the artifacts that constitute the bundle. Its fields (L86543-86633):

- **`category`** (Required) — one primary industry from `LightningBoltCategory`: Communications, Education, FinancialServices, GeneralBusiness, Government, HealthcareLifeSciences, HighTech, Manufacturing, Media, Nonprofits, ProfessionalServices, RealEstate, Retail, TravelTransportationHospitality. The guide's own sample uses `Sales` (L86642), which is not in that list — use a listed value.
- **`masterLabel`**, **`publisher`** ("the name of the partner org"), **`summary`** — all Required.
- **`lightningBoltFeatures`** — `title` (Required), `description`, `order` 1–4.
- **`lightningBoltImages`** — `image`, the developer name of a `ContentAsset` used as a preview image, and `order` 1–3.
- **`lightningBoltItems`** — `name` + `type`: `CommunityTemplateDefinition` (the site template, which needs its `CommunityThemeDefinition`, pkg2_dev 264 L4777-4778), `CustomApplication`, or `FlowCategory`. "Flows aren't added directly to a Lightning Bolt Solution. Instead, add the category the flows are in" (L76581-76582); a `FlowCategory` lists its flows in `flowCategoryItems` (L76600-76610).

There is no `templateApi`, `versionNumber`, `industries`, `flowCategories`, `images` or top-level `description` element.

What is **not** inside a Bolt:

- No data (Account / Contact records, Knowledge articles, etc.).
- No CMS content (CMS workspaces, channels, Enhanced CMS nodes — see Gotcha #4).
- No files / Files Connect content.
- No custom objects, custom fields, Apex, LWC, validation rules, sharing rules, or permission sets — these all need a separate package or post-install configuration.
- No site URL — a Bolt instantiated in a target org gets a fresh site URL; it does not retain the source's URL (see Gotcha #5; UNVERIFIED (2026-10-20)).

### Concept 3 — Export workflow (Experience Builder → ExperienceBundle → LightningBolt)

The export is two phases. Phase 1 produces the template. Phase 2 wraps it in `LightningBolt` metadata and builds the package. UNVERIFIED (2026-10-20): the Experience Builder menu path and dialog fields below are Help-only (the Help topic "Export a Customized Experience Builder Template for a Lightning Bolt Solution" is named in pkg2_dev 264 L4779).

Phase 1 — **Export from Experience Builder:**

1. Open the source site in Experience Builder.
2. From the Settings panel → Developer → "Export as a Template."
3. Provide a template name, description, image and category.
4. Salesforce stores the result as a *template* (a `CommunityTemplateDefinition`, "the definition of an Experience Builder site template", api_meta 264 L36547) available in the source org's New Site dialog. At this point the template is reusable inside the same org but has not left.

Phase 2 — **Wrap as a `LightningBolt` and package for distribution:**

1. Retrieve `LightningBolt`, `CommunityTemplateDefinition`, `CommunityThemeDefinition`, `FlowCategory` and the flows they list via SFDX (`sf project retrieve start --metadata LightningBolt:<name>` …).
2. Edit the `.lightningBolt` file to set `category`, `masterLabel`, `publisher`, `summary`, `lightningBoltFeatures`, `lightningBoltImages` and `lightningBoltItems`.
3. To distribute internally: deploy the metadata to the target org, or package it (1GP/2GP managed, pkg2_dev 264 L11920-11921). UNVERIFIED (2026-10-20): change set and unmanaged-package delivery, and where the Bolt then appears in Setup.
4. To distribute via AppExchange: create an AppExchange listing from the partner Business Org (UNVERIFIED (2026-10-20): the listing flow is Help-only).

The "Export as a Template" UI step does the heavy lifting of converting an in-org site into a reusable template. The `LightningBolt` metadata wrap is what lets you ship that template *out* of the org. Skipping Phase 2 leaves the template inside the source org only.

### Concept 4 — Versioning, upgrades, and the fork model

`LightningBolt` has no version field (fields: api_meta 264 L86543-86585). Versioning comes from the package that carries it: in a 1GP/2GP managed package the Bolt "Is Updated During Package Upgrade: Yes" and the subscriber cannot delete it (pkg2_dev 264 L11920-11925). Without a package, each deploy simply overwrites the definition.

Concretely (UNVERIFIED (2026-10-20): the fork-at-instantiation behaviour in this list is Help-only):

- When a target org installs Bolt v1.0 and uses it to instantiate Site A, Site A is a *fork* — a fully independent Experience site that no longer has any link back to the Bolt.
- When the source org publishes Bolt v2.0 and the target org installs that, the new Bolt definition is now available as a "New Site" template. Existing Site A is *not* updated. Site A continues to look like v1.0 forever.
- To propagate v2.0 changes to existing sites, the admin in the target org must manually re-create the site using v2.0 (and migrate any in-flight customization) or apply the diff between v1.0 and v2.0 by hand.

Under that model (UNVERIFIED (2026-10-20)), this is fine for *templates intended as starting points* — partner portal kits, industry community starters. It is the wrong shape for *operationally-shared sites* where downstream changes must propagate. For the latter case, a managed package containing a custom Lightning page reference (and treating the Experience site itself as a thin wrapper) is closer to what you want.

Record the version anyway — in the package version, the `summary`, or a feature `description` — so admins know what they are installing and bug fixes are traceable.

---

## Recommended Workflow

1. **Confirm Bolt is the right shape.** Walk through Core Concept 1 with the requester. If the deliverable is "a starting community site," continue. If it is "behavior" (Apex, custom objects), pivot to `devops/managed-package-development` or `devops/unlocked-package-development`. If it is "this single site, copied to one other org," use `devops/experience-cloud-deployment-admin` instead.
2. **Inventory dependencies on the source site.** Run `scripts/check_lightning_bolt_template_authoring.py --manifest-dir <retrieved tree>`. Confirm: every `lightningBoltItems` entry resolves to a `CommunityTemplateDefinition`, `CustomApplication` or `FlowCategory` in the tree; every flow a `FlowCategory` lists is present; any custom apps / themes referenced are present; no Apex or custom objects the site relies on are missing from the package plan. Output a dependency map showing what needs to ship in the Bolt vs what needs to ship separately as a managed/unlocked package.
3. **Export the site as a template from Experience Builder** (Settings → Developer → Export as a Template; UNVERIFIED (2026-10-20): UI path). Verify the template appears in the New Site dialog. This is the in-org checkpoint before adding the `LightningBolt` wrap.
4. **Author the `LightningBolt` metadata.** Retrieve the `.lightningBolt` file via SFDX, then fill in `category` (a `LightningBoltCategory` value), `masterLabel`, `publisher`, `summary` (all Required), up to 4 `lightningBoltFeatures`, up to 3 `lightningBoltImages` (ContentAsset names), and the `lightningBoltItems` (api_meta 264 L86543-86633).
5. **Promote sandbox → production for the source-of-truth Bolt.** Deploy the `LightningBolt` + `CommunityTemplateDefinition` + `CommunityThemeDefinition` + `FlowCategory` + the flows it lists + `CustomApplication` (any referenced) to the production org via SFDX. Production is now the shipping origin. Confirm the Bolt appears in the New Site dialog in production.
6. **Pick the distribution channel and ship.** Three options: (a) deploy directly to each target org (multi-org internal); (b) wrap in a managed package — `LightningBolt` is packageable in 1GP and 2GP (pkg2_dev 264 L11920-11921); UNVERIFIED (2026-10-20): unmanaged or unlocked packaging; (c) submit as an AppExchange listing (external distribution). Document which channel is used in the change record so future updates follow the same path.
7. **Define the version policy.** Document in the skill / handoff: what triggers a new package version, whether existing instantiations are expected to upgrade (no — they are forks; UNVERIFIED (2026-10-20)), and how downstream orgs should track which version they installed. If downstream upgrades matter, layer a managed package on top for the parts that need true upgrade semantics.

---

## Related Skills

- `admin/experience-cloud-site-setup` — building the Experience site itself before it becomes a Bolt source
- `admin/experience-cloud-cms-content` — CMS authoring; CMS content is *not* included in a Bolt and must ship separately
- `devops/experience-cloud-deployment-admin` — single-site sandbox-to-prod promotion when a Bolt is overkill
- `admin/experience-cloud-member-management` — member / profile setup post-instantiation in a target org
- `admin/partner-community-requirements` — partner portal templates and Partner Central considerations
- `devops/managed-package-development` — when the deliverable is behavior, not site shape
- `devops/unlocked-package-development` — when versioned package artifacts are needed for cross-BU reuse with editability
- `devops/cicd-for-experience-cloud` — automating Bolt promotion across environments
