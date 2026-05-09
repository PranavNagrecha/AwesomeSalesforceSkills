# Examples — Lightning Bolt Template Authoring

Worked examples covering the full lifecycle. Each example assumes the source Experience site is already built and stable; the work being done is wrapping it as a redistributable Bolt.

---

## Example 1 — Full export workflow for an LWR partner portal

**Scenario:** A medium-sized partner-management team has built an LWR-based partner portal in their dev org and wants to redistribute it to two additional business-unit orgs. No AppExchange listing — internal multi-org reuse only.

**Step 1 — Export as a template (Experience Builder).**

In the source org's Experience Builder for the partner portal site:

```
Settings (gear) → Developer → Export as a Template
  Template Name:     Acme_Partner_Portal_Bolt
  Description:       LWR-based partner portal with deal-registration, lead, and asset pages.
  Summary:           Branded LWR partner portal starter for Acme business units.
  Industry:          Manufacturing
  Image:             upload 256x256 thumbnail
```

After save, confirm in `Setup → All Sites → New Community → Use existing template`. The custom template should be listed alongside the standard ones. At this point, the template only exists inside the source org.

**Step 2 — Retrieve the metadata.**

```bash
sf project retrieve start \
  --metadata "LightningBolt:Acme_Partner_Portal_Bolt" \
  --metadata "ExperienceBundle:Acme_Partner_Portal" \
  --metadata "Theme:Acme_Theme" \
  --metadata "Flow" \
  --metadata "CustomApplication"
```

The retrieved tree:

```
force-app/main/default/
├── lightningBolts/
│   └── Acme_Partner_Portal_Bolt.lightningBolt-meta.xml
├── experiences/
│   └── Acme_Partner_Portal/   # the ExperienceBundle directory
│       ├── config/
│       ├── routes/
│       ├── themes/
│       └── views/
├── themes/
│   └── Acme_Theme.theme-meta.xml
├── flows/
│   └── Acme_Partner_Login.flow-meta.xml
└── applications/
    └── Acme_Partner_Internal.app-meta.xml
```

**Step 3 — Edit the LightningBolt metadata.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningBolt xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>LWR-based partner portal with deal-registration, lead, and asset management pages, branded for Acme partners.</description>
    <flowCategories>Partner_Login_Flows</flowCategories>
    <flowCategories>Partner_Approval_Flows</flowCategories>
    <images>partner_portal_thumb</images>
    <industries>Manufacturing</industries>
    <industries>Distribution</industries>
    <summary>Acme partner portal starter — LWR template with deal registration and lead conversion flows.</summary>
    <templateApi>webruntime</templateApi>
    <versionNumber>1.0</versionNumber>
</LightningBolt>
```

`templateApi = webruntime` because the source site is LWR. If it were a Customer Service / Partner Central template, it would be `aura`.

**Step 4 — Deploy to each target org.**

```bash
# Target BU org #1
sf project deploy start \
  --target-org bu1-prod \
  --source-dir force-app/main/default

# Target BU org #2
sf project deploy start \
  --target-org bu2-prod \
  --source-dir force-app/main/default
```

After deploy, in each target org:

```
Setup → All Sites → New → Use existing template
   → Acme_Partner_Portal_Bolt appears in the list
```

The admin in the target BU org clicks through, names their instance (e.g. `Acme_BU1_Partner_Portal`), and the new Experience site is created with the source's pages, theme, navigation, and referenced flows.

---

## Example 2 — Customizing a Bolt for a specific industry vertical

**Scenario:** The Bolt from Example 1 was originally a generic "manufacturing partner portal." The team now wants to ship a healthcare-flavored version with industry-specific page titles, branding tokens, and a Knowledge-link page replacing the deal-registration page.

**Two viable shapes:**

| Shape | Tradeoff |
|---|---|
| **Single Bolt with conditional content** | One artifact to maintain. Hard — Bolts do not support conditional content based on an industry parameter. The receiving site is what it is at instantiation. |
| **Two Bolts (one per industry)** | Two artifacts; some duplicated content. Pragmatic — admins pick the right starter at instantiation time. |
| **One Bolt + post-install configuration notes** | Single Bolt remains generic; downstream admin runs a documented configuration script (rename pages, update branding). Fragile, depends on documentation discipline. |

The **two-Bolt** approach is the typical answer. Steps:

1. In the source org, *clone* the existing partner portal site (`Setup → All Sites → New → Use existing template → Acme_Partner_Portal_Bolt`). Name the clone `Acme_HC_Partner_Portal`.
2. In Experience Builder for the clone, customize: replace the deal-registration page with a Knowledge component, swap industry-specific terminology in page titles, point the theme at healthcare brand tokens.
3. Re-run `Settings → Developer → Export as a Template` for the clone, naming the new template `Acme_HC_Partner_Portal_Bolt`.
4. Edit the new `LightningBolt-meta.xml`:

```xml
<industries>Healthcare</industries>
<industries>Healthcare Provider</industries>
<summary>Acme healthcare partner portal — Knowledge-centric LWR starter for HC providers.</summary>
<versionNumber>1.0</versionNumber>
```

5. Deploy / list the new Bolt alongside the original Manufacturing Bolt. Target orgs now see two starter templates and pick the right one for their vertical.

**Note:** Both Bolts pull from the same `Theme` if you want consistent base branding, or from separate `Theme` records if the brand tokens differ enough. If they share a theme, an update to that theme retroactively affects only *new* instantiations from either Bolt — existing sites are forks and unaffected.

---

## Example 3 — Dealing with included Flow categories

**Scenario:** The Bolt's `LightningBolt.flowCategories` lists `Partner_Login_Flows`. The source org has three flows in that category: `Partner_SSO_Login`, `Partner_Self_Register`, `Partner_Password_Reset`. After a Bolt deployment to a target org, the admin reports the SSO Login flow runs but the Self-Register flow throws "Flow not found" at runtime.

**Diagnosis:**

`flowCategories` ships the *category reference*, and Salesforce includes flows *that are members of that category at retrieve time*. Two ways the contract breaks:

1. A flow was renamed in the source org *after* the Bolt was retrieved but before deploy. The Bolt still references the old name; the deploy fails or runs with a stale flow definition.
2. A flow's `processMetadataValues` were modified to point at a different category, removing it from `Partner_Login_Flows` but leaving the flow file in the retrieved package. The Bolt's category list looks complete but the flow no longer answers when the category is queried at runtime.

**Fix:**

```bash
# 1. Verify which flows are actually in the category in the source org
sf data query --query "SELECT MasterLabel, ProcessType, Status FROM FlowDefinitionView WHERE Category = 'Partner_Login_Flows'" --target-org source-dev

# 2. Confirm those exact flows are in the retrieved force-app/main/default/flows/ tree
ls force-app/main/default/flows/

# 3. Open each flow's XML and verify the <processMetadataValues> includes the matching category
grep -l "Partner_Login_Flows" force-app/main/default/flows/*.flow-meta.xml
```

For each missing flow:

- If the flow is in the file system but not in the category — fix the `processMetadataValues` block in the flow XML.
- If the flow is missing from the file system — re-retrieve it explicitly (`sf project retrieve start --metadata Flow:Partner_Self_Register`).

After the fix, redeploy the bundle. The skill's bundled checker (`scripts/check_lightning_bolt_template_authoring.py`) reports flow categories that exist in `LightningBolt-meta.xml` but have zero matching flows in the package — run it before every Bolt deploy.

**Subtle gotcha:** Flow versions vs flow definitions. The Bolt carries the *active* flow version at retrieve time. If the source org later activates a new flow version, the Bolt does not pick that up unless re-retrieved. Versioning the Bolt should be coupled with re-retrieving the flow set.

---

## Example 4 — Distributing partner-only via AppExchange Bolt listing

**Scenario:** An ISV has built a community starter for a vertical and wants to distribute it on AppExchange — but only to vetted partners, not as a public listing. The Bolt is bundle-only (no Apex / custom objects), so security review is not required.

**Path:**

1. Build the Bolt in the development org following Examples 1–3.
2. Set up an AppExchange Partner Business Org (separate from the development org). The Business Org is what hosts AppExchange listings and is where the Bolt listing is owned.
3. Deploy the `LightningBolt` + dependencies into the Business Org (so the listing flow can find it).
4. In the Partner Business Org, navigate to AppExchange Publishing Console (or the Partner Console as named in the current release) → New Listing → "Lightning Bolt Solution" listing type. The Bolt listing flow is distinct from the managed-package listing flow:
   - No security review required for Bolts that contain only `ExperienceBundle` + `Theme` + `flowCategories` + `customApps` + `images`. Security review IS required if the Bolt is bundled with a managed package containing Apex / custom objects (then the *package* is reviewed, the Bolt itself is not).
   - Listing visibility can be set to "Private" — only the partners you explicitly grant access to can install. This is how partner-only distribution works without going public.
5. Submit. After listing approval (typically days, not weeks for Bolts because of no security review), the Bolt appears in the partners' AppExchange under their vendor listings.
6. Each partner installs from AppExchange. The Bolt then appears in their `Setup → All Sites → New → Use existing template`.

**Why not just deploy directly to each partner?** Because:

- Direct deploy requires you to have a logged-in admin session in the partner org, which most ISVs do not have.
- Direct deploy provides no audit trail, no install history, and no way to surface a new version to all installed partners.
- AppExchange installation gives both sides a clean install record and lets the partner re-install / uninstall on their own.

For a small number of partners (≤3) where direct relationships exist, direct deploy is acceptable. For more, the AppExchange listing path scales better.

---

## Example 5 — Versioning a Bolt from v1.0 to v2.0

**Scenario:** The Manufacturing Bolt from Example 1 has been live for six months. The source team has improved the deal-registration page and wants to release v2.0. Multiple orgs have already instantiated v1.0 sites.

**The hard truth first:** Existing v1.0 sites are forks. Releasing v2.0 does NOT update them. If their downstream admins want v2.0 features, they must manually re-create the site or apply changes by hand. Communicate this *before* shipping v2.0 so expectations are correct.

**Steps:**

1. In the source org, edit the Experience site to incorporate the v2.0 changes (deal-registration improvements). Test thoroughly — once shipped, you cannot retroactively patch v1.0 instances.
2. In Experience Builder → Settings → Developer → "Re-export as Template" (or update the existing template if the UI offers it). This refreshes the template definition in the source org with the v2.0 site content.
3. Retrieve the updated metadata via SFDX:

```bash
sf project retrieve start \
  --metadata "LightningBolt:Acme_Partner_Portal_Bolt" \
  --metadata "ExperienceBundle:Acme_Partner_Portal"
```

4. Bump the `versionNumber` in the `LightningBolt-meta.xml`:

```xml
<versionNumber>2.0</versionNumber>
<description>v2.0 — improved deal registration with lead-source attribution and ABM integration hooks.</description>
```

5. Deploy the updated Bolt to each target org (or re-publish the AppExchange listing).
6. **Communication step:** notify the downstream org admins that v2.0 is available and document the manual steps needed to apply v2.0 changes to their existing v1.0 sites:

```
Bolt v2.0 release notes — Acme_Partner_Portal_Bolt

What's new:
  - Deal Registration page now captures Lead Source and ABM tier.
  - Branded thank-you page after submission.

Existing v1.0 sites: NOT auto-upgraded. Bolts are forks at instantiation.
To apply v2.0 changes to your existing site:
  1. Compare v1.0 -> v2.0 page diff (attached).
  2. In your existing site, replicate the changes manually in Experience Builder.
  3. Re-test the deal-registration flow.
Estimated effort: 2-4 hours per site.

Or, instantiate a fresh site from v2.0 and migrate over time. We recommend
this only for sites with minimal customization since v1.0 install.
```

7. Track which orgs are on which version in your release tracker. The platform does not give you this view automatically.

This is Bolt's biggest weakness vs. a managed package — no upgrade semantics. If the upgrade pain becomes acute, consider moving the parts that change frequently into a managed package layered on top of the Bolt, so behavior changes can ride a real upgrade path while the site shape continues to ship as a Bolt.
