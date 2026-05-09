---
name: lightning-bolt-template-authoring
description: "Use when an admin or partner needs to package an Experience Cloud (Community) site as a reusable Lightning Bolt Solution for distribution — covers the export workflow from Experience Builder, what gets bundled (ExperienceBundle, custom apps, flow categories, theme, layouts, navigation menus) versus what does NOT (data, CMS content, files), choosing Bolt vs managed package vs unlocked package vs cloning a site, sandbox-to-production promotion, multi-org distribution, AppExchange listing as a Bolt, and template versioning via the LightningBolt metadata `versionNumber`. Triggers: 'turn this community into a reusable template', 'package an Experience Cloud site to ship to multiple orgs', 'export Experience Builder template for AppExchange', 'should we use a Bolt or a managed package for this community', 'create an industry-specific community starter', 'how do we version our partner portal template', 'distribute branded Experience site across business units'. NOT for general Experience Cloud site build, content, or member setup (use admin/experience-cloud-site-setup, admin/experience-cloud-cms-content, admin/experience-cloud-member-management). NOT for shipping Apex / LWC / data-model functionality as a product (use devops/managed-package-development, devops/second-generation-managed-packages, devops/unlocked-package-development). NOT for moving a single Experience site between sandbox and prod as a one-off (use admin/experience-cloud-deployment-admin, devops/cicd-for-experience-cloud)."
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
  - "Source Experience Cloud site name and template api type (Customer Service, Partner Central, Build Your Own LWR/Aura, etc.)"
  - "Distribution intent: single-org reuse, multi-org internal, partner-only AppExchange listing, public AppExchange listing"
  - "Custom apps, Flow categories, Theme, and any custom Lightning components the site relies on"
  - "Versioning expectation: do you need installed sites to pick up future updates, or are downstream sites forks once created"
outputs:
  - "Decision (Bolt vs managed package vs unlocked package vs site clone) with cited tradeoffs"
  - "ExperienceBundle export checklist plus a `LightningBolt` metadata definition (description, summary, industries, flowCategories, images, templateApi, versionNumber)"
  - "Sandbox-to-production promotion plan and multi-org distribution recipe (direct deploy, package, or AppExchange)"
  - "Versioning policy: when to bump `versionNumber`, what installed sites inherit, what they do not"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# Lightning Bolt Template Authoring

Activate this skill when an Experience Cloud site needs to leave its origin org. A Lightning Bolt is the platform-native way to package an Experience site (`ExperienceBundle` + theme + supporting metadata) as a *template* that other orgs or other Experience sites within the same org can stamp out. The skill is about *packaging* — it is not about building the site itself, nor about distributing CRM functionality (use a managed or unlocked package for that).

---

## Before Starting

Gather this context before scaffolding a Bolt:

- **What template api the source site uses.** Run Setup → All Sites → (your site) → Administration → Settings, or inspect the `ExperienceBundle` XML — the `<templateApi>` value is one of `webruntime` (LWR), `aura` (Aura/Visualforce-based templates like Customer Service, Partner Central), or a specific Salesforce-shipped Bolt id. The `LightningBolt.templateApi` field on the new template you are creating must match what the source site's runtime expects. A Bolt built from an LWR site cannot be used to instantiate an Aura-based Customer Service site, and vice versa.
- **Distribution intent.** Three different intents map to three different artifacts:
  - *Reuse the site within the same org* — clone the Experience site directly. No Bolt needed.
  - *Reuse across orgs you control* — Bolt distributed via change set / SFDX / unmanaged package is fine. No AppExchange listing required.
  - *Reuse across customer orgs you do not control* — Bolt listed on AppExchange (Bolts have a separate AppExchange listing flow from managed packages). Requires partner Business Org and security review only if the Bolt includes Apex / LWC / managed-package dependencies.
- **What the site references.** A Bolt bundles the `ExperienceBundle` + `Theme` + listed `flowCategories` + `customApps` + `images`. It does NOT bundle Apex classes, custom objects, custom fields, permission sets, sharing rules, CMS content, files, or any data. If the site relies on a custom object or Apex action, that dependency has to ship separately (managed package, unlocked package, or post-install setup script). The Bolt will install successfully into a target org without those dependencies — and then the instantiated site will throw runtime errors. This is the single most common Bolt failure mode.
- **Versioning expectation.** A `LightningBolt.versionNumber` is *informational* — it does NOT establish an upgrade relationship with previously instantiated sites. When a Bolt is updated, *existing* sites that were created from a prior version do not pick up the changes. They are forks at instantiation time. Plan for this up front, especially for partner portals or shared tenants where downstream changes may need to propagate.

---

## Core Concepts

### Concept 1 — Bolt vs managed package vs unlocked package vs site clone

Four distribution shapes, four different problem domains. Pick by *what is being distributed*, not by familiarity:

| Shape | Distributes | When to use | Salesforce reference |
|---|---|---|---|
| **Lightning Bolt Solution** | An Experience site as a *template* — the `ExperienceBundle` (pages, components, layouts, navigation menus), theme, listed flow categories, custom apps, images. NO data, NO CRM functionality. | The deliverable is a brandable, configurable Experience site that the target org will *instantiate* and customize further. Industry-specific community starters, partner-portal templates, branded community kits. | `LightningBolt` metadata; Build a Lightning Bolt Solution guide. |
| **Managed (2GP) package** | Apex / LWC / Aura / custom objects / fields / permission sets / Flow definitions / data model. Versioned with upgrade path. Optional security review for AppExchange. | The deliverable is *behavior* (an ISV product, a managed extension). Owner retains code; subscriber installs and upgrades. | `Package2` metadata; 2GP developer guide. |
| **Unlocked package** | Same metadata coverage as managed but unlocked — subscriber org owns and can edit installed components. Versioned with upgrade path but not security-reviewed. | Internal multi-org reuse where you want package versioning but the subscriber needs to be able to modify. Good for shared cross-BU CRM extensions. | `Package2` metadata, `IsOrgDependent`, `Container`-style scratch org build. |
| **Site clone (in-org only)** | An Experience site copied to a new site within the same org. | One-off reuse within a single org. No need to leave the org boundary. | Setup → All Sites → New → Use existing site as template. |

A common mistake is reaching for a managed package because that is what the partner team is familiar with. If the deliverable is *the look and feel and starting structure of a community site*, a Bolt is the right tool — and shipping it as a managed package would force the subscriber into the upgrade-path constraints (no metadata edits without unlocking) that work against site customization, which is the entire point of a template.

A second common mistake is using a Bolt to distribute Apex or a custom object dependency. Bolts cannot carry Apex / custom objects / fields. If the site needs them, the dependency must ship separately. The pattern is: Bolt for the *site shape*, managed (or unlocked) package for the *behavior dependencies*, with Bolt installation gated on the package being installed first.

### Concept 2 — What is actually inside a Bolt

The `LightningBolt` metadata definition itself is small — it points at the artifacts that constitute the bundle. The complete inventory:

- **`ExperienceBundle`** — the canonical site definition. Contains the page hierarchy, components placed on each page, layout regions, navigation menu, branding panel selections, audience targeting rules. This is the bulk of the Bolt.
- **`Theme` and `BrandingSet`** — colors, fonts, image references that make the site look like *your* site rather than the default template.
- **`flowCategories`** — listed categories of Flow definitions the site uses (typically Login Flow, screen flows referenced by Flow components on pages). The Bolt carries the *category reference*, and the flows in that category come along when the package is built. **Subtlety:** flow *categories* are referenced by name. Flow *definitions* (the actual screens / logic) come with their `Flow` metadata. If a flow is renamed or moved between categories, the Bolt's reference breaks.
- **`customApps`** — Lightning App definitions referenced by the site (typically internal-facing apps that the community surfaces).
- **`images`** — references to static images used in the Bolt's AppExchange listing or admin preview thumbnails. NOT site assets — site images live inside the `ExperienceBundle`.
- **`industries`** — declarative tag listing target industries (Financial Services, Healthcare, Manufacturing, etc.). Drives AppExchange filtering and discoverability. Cosmetic, but worth setting accurately.
- **`description`, `summary`, `templateApi`, `versionNumber`** — the rest of the `LightningBolt` definition.

What is **not** inside a Bolt:

- No data (Account / Contact records, Knowledge articles, etc.).
- No CMS content (CMS workspaces, channels, Enhanced CMS nodes — see Gotcha #4).
- No files / Files Connect content.
- No custom objects, custom fields, Apex, LWC, validation rules, sharing rules, or permission sets — these all need a separate package or post-install configuration.
- No site URL — a Bolt instantiated in a target org gets a fresh site URL; it does not retain the source's URL (see Gotcha #5).

### Concept 3 — Export workflow (Experience Builder → ExperienceBundle → LightningBolt)

The export is two phases. Phase 1 produces the `ExperienceBundle`. Phase 2 wraps it in `LightningBolt` metadata and builds the package.

Phase 1 — **Export from Experience Builder:**

1. Open the source site in Experience Builder.
2. From the Settings panel → Developer → "Export as a Template."
3. Provide a template name, description, summary, image, category (mapped from the `industries` field).
4. Salesforce extracts the `ExperienceBundle`, theme, branding, navigation, and any referenced flow categories / custom apps and stores them as a *template* in the source org's New Site dialog. At this point the template is reusable inside the same org but has not left.

Phase 2 — **Wrap as a `LightningBolt` and package for distribution:**

1. Retrieve the `LightningBolt` and `ExperienceBundle` metadata via SFDX (`sf project retrieve start --metadata LightningBolt:<name>` and the corresponding `ExperienceBundle`).
2. Edit `LightningBolt-meta.xml` to set `description`, `summary`, `industries`, `flowCategories`, `images`, `templateApi`, `versionNumber`.
3. To distribute internally: deploy the metadata bundle to the target org via change set, SFDX, or unmanaged package. The Bolt then appears in Setup → All Sites → New → Use as a template.
4. To distribute via AppExchange: log into the partner Business Org, create an AppExchange Bolt listing (separate flow from a managed-package listing), and submit. The listing flow is documented in the partner Salesforce community.

The "Export as a Template" UI step does the heavy lifting of converting an in-org site into a reusable template. The `LightningBolt` metadata wrap is what lets you ship that template *out* of the org. Skipping Phase 2 leaves the template inside the source org only.

### Concept 4 — Versioning, upgrades, and the fork model

`LightningBolt.versionNumber` is a string field for human-readable version labeling (`"1.0"`, `"2.3"`, etc.). It does *not* establish an upgrade relationship between Bolt versions in the way a managed package does.

Concretely:

- When a target org installs Bolt v1.0 and uses it to instantiate Site A, Site A is a *fork* — a fully independent Experience site that no longer has any link back to the Bolt.
- When the source org publishes Bolt v2.0 and the target org installs that, the new Bolt definition is now available as a "New Site" template. Existing Site A is *not* updated. Site A continues to look like v1.0 forever.
- To propagate v2.0 changes to existing sites, the admin in the target org must manually re-create the site using v2.0 (and migrate any in-flight customization) or apply the diff between v1.0 and v2.0 by hand.

This is fine for *templates intended as starting points* — partner portal kits, industry community starters. It is the wrong shape for *operationally-shared sites* where downstream changes must propagate. For the latter case, a managed package containing a custom Lightning page reference (and treating the Experience site itself as a thin wrapper) is closer to what you want.

`versionNumber` is still worth setting accurately because:

- It appears in the AppExchange listing and the New Site dialog so admins know what they are installing.
- It supports change-management hygiene — bug fixes and feature additions should bump the version label even if the platform does not enforce upgrade semantics.

---

## Recommended Workflow

1. **Confirm Bolt is the right shape.** Walk through Core Concept 1 with the requester. If the deliverable is "a starting community site," continue. If it is "behavior" (Apex, custom objects), pivot to `devops/managed-package-development` or `devops/unlocked-package-development`. If it is "this single site, copied to one other org," use `admin/experience-cloud-deployment-admin` instead.
2. **Inventory dependencies on the source site.** Run `scripts/check_lightning_bolt_template_authoring.py` against the retrieved metadata of the source org. Confirm: `ExperienceBundle` exists; the listed `flowCategories` map to real `Flow` metadata; any custom apps / themes referenced are present; no Apex or custom objects the site relies on are missing from the package plan. Output a dependency map showing what needs to ship in the Bolt vs what needs to ship separately as a managed/unlocked package.
3. **Export the site as a template from Experience Builder** (Settings → Developer → Export as a Template). Verify the template appears in Setup → All Sites → New → "Use existing template." This is the in-org checkpoint before adding the `LightningBolt` wrap.
4. **Author the `LightningBolt` metadata.** Retrieve the auto-generated `LightningBolt-meta.xml` via SFDX, then fill in `description`, `summary`, `industries`, `flowCategories` (must match the `Flow` metadata categories shipped with the bundle), `images`, `templateApi` (must match the source site's runtime — `webruntime` for LWR, `aura` for Customer Service / Partner Central), and `versionNumber`.
5. **Promote sandbox → production for the source-of-truth Bolt.** Deploy the `LightningBolt` + `ExperienceBundle` + `Theme` + `Flow` (any in the listed categories) + `CustomApplication` (any referenced) to the production org via change set or SFDX. Production is now the shipping origin. Confirm the Bolt appears in Setup → All Sites → New in production.
6. **Pick the distribution channel and ship.** Three options: (a) deploy directly to each target org (multi-org internal); (b) wrap in an unmanaged or unlocked package and distribute the package artifact (multi-org with version artifacts); (c) submit as an AppExchange Bolt listing (external distribution). Document which channel is used in the change record so future updates follow the same path.
7. **Define the version policy.** Document in the skill / handoff: what triggers a `versionNumber` bump, whether existing instantiations are expected to upgrade (no — they are forks), and how downstream orgs should track which version they installed. If downstream upgrades matter, layer a managed package on top for the parts that need true upgrade semantics.

---

## Related Skills

- `admin/experience-cloud-site-setup` — building the Experience site itself before it becomes a Bolt source
- `admin/experience-cloud-cms-content` — CMS authoring; CMS content is *not* included in a Bolt and must ship separately
- `admin/experience-cloud-deployment-admin` — single-site sandbox-to-prod promotion when a Bolt is overkill
- `admin/experience-cloud-member-management` — member / profile setup post-instantiation in a target org
- `admin/partner-community-requirements` — partner portal templates and Partner Central considerations
- `devops/managed-package-development` — when the deliverable is behavior, not site shape
- `devops/unlocked-package-development` — when versioned package artifacts are needed for cross-BU reuse with editability
- `devops/cicd-for-experience-cloud` — automating Bolt promotion across environments
