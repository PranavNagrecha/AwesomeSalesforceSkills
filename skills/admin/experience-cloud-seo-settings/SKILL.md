---
name: experience-cloud-seo-settings
description: "Configure SEO for Experience Cloud sites: per-page titles and meta descriptions, sitemap.xml generation, robots.txt, and URL structure. Triggers: 'configure SEO for community site', 'Experience Cloud page titles meta descriptions', 'sitemap generation community portal', 'robots.txt Experience Cloud', 'noindex Experience Builder page'. NOT for creating the site, LWR vs Aura, or custom domain setup — use admin/experience-cloud-site-setup. NOT for pages a crawler cannot reach because the guest user lacks access — use admin/experience-cloud-guest-access."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
tags:
  - experience-cloud
  - seo
  - sitemap
  - robots-txt
  - experience-builder
  - lwr
  - community
triggers:
  - "configure SEO for community site"
  - "Experience Cloud page titles meta descriptions"
  - "sitemap generation community portal"
  - "robots.txt Experience Cloud"
  - "noindex Experience Builder page"
  - "Knowledge articles not appearing in search results"
inputs:
  - Experience Cloud site type (Aura/LWR/Visualforce-based)
  - Target pages or objects requiring SEO configuration
  - Whether a custom domain is in use and whether it uses subpaths or subdomains
  - Whether Knowledge articles need to appear in search (sitemap rules are UNVERIFIED 2026-10-20, Help-only)
outputs:
  - Per-page SEO property settings (pageTitle, description, customHeadTags) guidance
  - Sitemap validation checklist (sitemap behaviour is UNVERIFIED 2026-10-20, Help-only)
  - Custom robots.txt Visualforce page implementation wired through CustomSite.robotsTxtPage
  - SEO readiness checklist for production promotion
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Experience Cloud SEO Settings

This skill activates when a practitioner needs to configure search-engine visibility for an Experience Cloud site — covering per-page SEO properties in Experience Builder, the sitemap, a custom robots.txt Visualforce page, and URL structure choices. It does not cover external SEO tooling or Salesforce CMS headless delivery.

Cites: `api_meta` is the Winter '27 (264) Metadata API guide; `secguide` is the Summer '26 (262) Security Implementation Guide. Line numbers are those files'.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Org type:** UNVERIFIED (2026-10-20): that SEO features, the sitemap and robots.txt are active only on production orgs, and that a sandbox sitemap returns an empty response or an error, is Help-only; the corpus has no line on either. Confirm the behaviour in your own sandbox before relying on it.
- **Site technology and URL prefix:** `ExperienceBundle.urlPathPrefix` ends in `/s` for authenticated LWR sites created before Winter '23 and for Aura sites; for unauthenticated LWR sites and authenticated LWR sites created after Winter '23 it does not contain `/s` (api_meta 264 L62430-62435). Read the prefix from the retrieved bundle instead of assuming it from the template name.
- **Domain model:** `CustomSite.customWebAddresses` holds the root custom URLs; custom URLs that use a non-root path prefix are not in that list (api_meta 264 L49291-49297). UNVERIFIED (2026-10-20): that sites sharing a subpath share a single robots.txt, and that a subdomain per site is the only way to separate them, is Help-only.
- **Guest record access:** guest users' org-wide defaults are Private for all objects and cannot be changed (secguide 262 L2868-2869), and a guest user sharing rule is the only way to grant record access to unauthenticated guest users, with Read Only access (secguide 262 L2986-2987, L3223-3225). Object permission on the guest profile alone does not open records. UNVERIFIED (2026-10-20): that the sitemap lists exactly the pages and objects the guest user can read, and that unreadable ones are silently excluded, is Help-only.
- **Knowledge articles and topics:** UNVERIFIED (2026-10-20): that Knowledge articles are excluded from the sitemap unless assigned to a Data Category or a Topic is Help-only; no corpus line mentions sitemap generation at all.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the site Aura, LWR created before Winter '23, or LWR created after? | The `urlPathPrefix` rule decides whether robots.txt paths carry `/s` (Core Concept 4; Gotcha 5) | The prefix read from the retrieved `ExperienceBundle` |
| Which VF page does `robotsTxtPage` name on the site's `CustomSite`? | The site is wired to the page by that field, so the page name is not fixed (Core Concept 3) | The field value and the page file it points to |
| Do several sites share a custom domain? | Whether they share one robots.txt is unverified (Gotcha 2) | A domain map and a sandbox check of what each path serves |
| Which pages need their own title and description? | The SEO assistant exposes `pageTitle`, `description` and `customHeadTags` per page (Core Concept 1) | A page table with the three values |
| Can the guest user read the records that should be indexed? | Record access for unauthenticated guests needs guest sharing rules (Before Starting) | A list of objects with the guest sharing rule for each |
| Where will the sitemap and robots.txt be validated? | Environment limits on SEO features are unverified (Gotcha 1) | A production check, plus the sandbox behaviour you observed |
| Should a page be kept out of search results or out of the crawl? | A noindex setting and a robots.txt Disallow do different jobs (Gotcha 4) | One control per page, with the reason |

A proper configuration reads the prefix and wiring from retrieved metadata and sets all three page properties deliberately; "just doing it" copies an Aura robots.txt onto an LWR site and trusts an unverified sitemap.

---

## Core Concepts

### 1. Per-Page SEO Properties in Experience Builder

Each page's `view` JSON in an `ExperienceBundle` has a hidden region, `sfdcHiddenRegion`, that holds the SEO assistant component: `forceCommunity:seoAssistant` in Aura sites and `community_builder:seoAssistant` in LWR sites. It corresponds to the SEO page properties you set in Experience Builder, and you use it to set `customHeadTags`, `description` and `pageTitle` for public and custom pages; you can't edit its other properties (api_meta 264 L63443-63448, L55970-55976). The sample component carries `customHeadTags`, `description`, `pageTitle` and `recordId` attributes (L56420-56425).

The one `isIndexed` flag in the corpus is on a Marketing workspace landing page (`sfdc_cms__landingPage`) in a DigitalExperienceBundle sample: `sfdc_cms:seoProperties` with `isIndexed` false and a `title` (api_meta 264 L54499-54508, L54605-54608). It is not shown as an Experience Builder site page property.

UNVERIFIED (2026-10-20): the "Page Settings > SEO" gear-icon path, that the title also fills Open Graph `og:title`, the 150 to 160 character guidance, auto-generated descriptions when blank, a "No Index" checkbox that adds `<meta name="robots" content="noindex">`, which head tags are allowed in `customHeadTags`, and merge-field expressions such as `{!Record.Title}` in the title are Help-only.

### 2. Sitemap

UNVERIFIED (2026-10-20): the whole sitemap model is Help-only. The corpus contains no line about an auto-generated `sitemap.xml`, its location, which pages or objects it lists, Knowledge topic assignment, a 24-hour regeneration schedule, or its behaviour in a sandbox. The one indexing-related setting in the corpus is `preferredDomain` in the site's `config` JSON, "the name of the domain to use for indexing a site's pages", which improves search engine results (API 48.0 and later; api_meta 264 L62656-62658).

### 3. Custom robots.txt via Visualforce Page

`CustomSite.robotsTxtPage` is "the name of the Visualforce page to display for the robots.txt file used by web crawlers" (api_meta 264 L49406-49407). The site is wired to the page through that field, so the page is not required to be named `robots`; the earlier text that the page must be named exactly `robots` is contradicted by it.

```visualforce
<apex:page contentType="text/plain" showHeader="false" sidebar="false" standardStylesheets="false">
User-agent: *
Disallow: /login
Disallow: /search
Sitemap: https://community.example.com/sitemap.xml
</apex:page>
```

UNVERIFIED (2026-10-20): the page attributes (`contentType="text/plain"` and the three `false` attributes), the sitemap URL in the `Sitemap:` line, the exact paths to disallow, that Experience Cloud has no managed robots.txt UI, and that sites on subpaths of one domain share a single robots.txt (so a subdomain per site is the only way to separate them) are Help-only.

### 4. URL Structure

Read `urlPathPrefix` from the retrieved `ExperienceBundle` meta file in the `experiences` folder (api_meta 264 L62391): `SampleStarterSite2/s` in the guide's sample meta.xml (L62436-62444). Where the prefix ends in `/s`, the path before it must match the `Network` URL; where it does not, "the path can be anything as long as there's no conflict" (L62430-62435). Write robots.txt paths from that prefix.

---

## Common Patterns

### Per-Page Title and Description for an Object Detail Page

**When to use:** A self-service portal wants article-specific titles and descriptions in search results.

**How it works:**
1. Retrieve the `ExperienceBundle` and find the detail page's `views/<view>.json`.
2. Set `pageTitle` and `description` on its `seoAssistant` component (api_meta 264 L63443-63448).
3. For record-specific values, the sample carries `"recordId" : "{!recordId}"` (L56425). UNVERIFIED (2026-10-20): `{!Record.Title}` and `{!Record.Summary}` expressions, as used by earlier versions of this pattern, are Help-only.
4. Make sure the guest user can read the records (guest sharing rule; secguide 262 L3223-3225).

**Why it works:** The SEO assistant component is the stored form of the Experience Builder SEO properties.

### Blocking Non-Indexable Pages via a Custom robots.txt

**When to use:** The site has login, search, profile and checkout pages that should not be crawled.

**How it works:**
1. Create a Visualforce page for robots.txt.
2. Set the site's `robotsTxtPage` to that page's name (api_meta 264 L49406-49407).
3. Write `Disallow` lines using the site's real path prefix (Core Concept 4).
4. Fetch `<site-base-url>/robots.txt` and compare it with the page.

**Why not the alternative:** A noindex setting (UNVERIFIED 2026-10-20: Help-only) suppresses indexing but not crawling; a Disallow line is the crawl control.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Keep a page out of search results | A noindex property (UNVERIFIED 2026-10-20: Help-only) | The only corpus `isIndexed` flag is on a Marketing workspace landing page, not a site page (api_meta 264 L54499-54508, L54605-54607) |
| Keep crawlers off a page | Disallow in the `robotsTxtPage` Visualforce page | robots.txt is the crawl control; the wiring is `CustomSite.robotsTxtPage` |
| Knowledge articles missing from the sitemap | Check topic or data category assignment (UNVERIFIED 2026-10-20) | Sitemap rules are Help-only |
| Two sites on one domain need different robots.txt | Test in a sandbox; a subdomain per site is the conservative answer (UNVERIFIED 2026-10-20) | Shared-robots.txt behaviour is Help-only |
| Paths in robots.txt look wrong | Read `urlPathPrefix` from the bundle | The `/s` rule depends on site type and creation date (api_meta 264 L62430-62435) |

---

## Recommended Workflow

1. **Confirm site type and wiring.** Retrieve the `ExperienceBundle` and `CustomSite`; note `urlPathPrefix`, `preferredDomain` and `robotsTxtPage`.
2. **Audit guest record access.** Confirm guest user sharing rules exist for the objects whose records should be indexed (secguide 262 L3223-3225).
3. **Set per-page properties.** Set `pageTitle`, `description` and `customHeadTags` on each page's `seoAssistant` component; run `python3 scripts/check_experience_cloud_seo_settings.py --manifest-dir <metadata dir>`.
4. **Create or update the robots.txt page.** Point `robotsTxtPage` at it and use paths that match the prefix.
5. **Validate.** Fetch `<site-base-url>/robots.txt` and, if the org produces one, `<site-base-url>/sitemap.xml` (UNVERIFIED 2026-10-20: Help-only). Record the environment you tested in.

---

## Review Checklist

- [ ] `urlPathPrefix` was read from the retrieved bundle and the robots.txt paths match it
- [ ] `CustomSite.robotsTxtPage` names an existing Visualforce page
- [ ] Every key page has `pageTitle` and `description` set on its SEO assistant component
- [ ] Guest user sharing rules exist for records that should be public
- [ ] `preferredDomain` is set when the site is served on more than one domain
- [ ] The sandbox versus production behaviour of the sitemap and robots.txt was observed, not assumed (UNVERIFIED 2026-10-20: Help-only)
- [ ] If several sites share a custom domain, the shared-robots.txt question was tested (UNVERIFIED 2026-10-20)

---

## Salesforce-Specific Gotchas

1. **Environment limits on SEO features** — UNVERIFIED (2026-10-20): that the sitemap and robots.txt are inactive in sandbox and scratch orgs is Help-only; observe the behaviour and validate in production.

2. **Shared robots.txt on subpath domains** — UNVERIFIED (2026-10-20): that sites on subpaths of one custom domain share a single robots.txt, and that the only fix is a subdomain per site, is Help-only. `CustomSite.robotsTxtPage` is a per-site field (api_meta 264 L49406-49407), so test what each site's path serves.

3. **Knowledge articles and the sitemap** — UNVERIFIED (2026-10-20): that Read access is necessary but not sufficient and that articles also need a Topic or Data Category is Help-only. Record access for guests needs a guest sharing rule (secguide 262 L3223-3225).

4. **noindex does not prevent crawling** — UNVERIFIED (2026-10-20): the "No Index" property and the `<meta name="robots" content="noindex">` tag it adds are Help-only; the crawl-versus-index distinction is general web behaviour, not a corpus statement. Use a robots.txt Disallow to control crawling.

5. **URL prefix depends on site type and age** — A robots.txt copied from an Aura site (`/s/...`) may not match an LWR site, but the rule is not "LWR has no `/s`": it depends on authentication and creation date (api_meta 264 L62430-62435).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SEO page properties configuration | Per-page `pageTitle`, `description` and `customHeadTags` applied in the SEO assistant component |
| robots.txt Visualforce page | The page named by `CustomSite.robotsTxtPage`, with the crawl directives |
| Sitemap validation results | What `<site-base-url>/sitemap.xml` returned, with the environment tested (sitemap behaviour UNVERIFIED 2026-10-20) |
| SEO readiness checklist | Completed checklist confirming prefix, wiring, guest access and observed environment behaviour |

---

## Related Skills

- `architect/knowledge-vs-external-cms` -- when deciding whether Knowledge or an external CMS is the better content store for SEO-driven use cases
- `admin/experience-cloud-guest-access` -- guest user profile and sharing configuration, which controls what unauthenticated visitors can read
- `admin/experience-cloud-site-setup` -- site creation, template choice and custom domain setup
