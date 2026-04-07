---
name: experience-cloud-seo-settings
description: "Configure SEO for Experience Cloud sites: per-page titles and meta descriptions, sitemap.xml generation, robots.txt, and URL structure. Triggers: 'configure SEO for community site', 'Experience Cloud page titles meta descriptions', 'sitemap generation community portal', 'robots.txt Experience Cloud', 'noindex Experience Builder page'. NOT for external SEO tools (Moz, Ahrefs, Google Search Console setup). NOT for Salesforce CMS headless SEO."
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
  - configure SEO for community site
  - Experience Cloud page titles meta descriptions
  - sitemap generation community portal
  - robots.txt Experience Cloud
  - noindex Experience Builder page
  - Knowledge articles not appearing in search results
inputs:
  - Experience Cloud site type (Aura/LWR/Visualforce-based)
  - Target pages or objects requiring SEO configuration
  - Whether a custom domain is in use and whether it uses subpaths or subdomains
  - Whether Knowledge articles need to appear in sitemap
outputs:
  - Per-page SEO property settings (title, meta description, noindex) guidance
  - Sitemap.xml configuration guidance and checklist
  - Custom robots.txt Visualforce page implementation
  - SEO readiness checklist for production promotion
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Experience Cloud SEO Settings

This skill activates when a practitioner needs to configure search-engine visibility for an Experience Cloud site — covering per-page SEO properties in Experience Builder, automatic sitemap.xml generation, custom robots.txt implementation via Visualforce, and URL structure choices. It does not cover external SEO tooling or Salesforce CMS headless delivery.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Org type:** SEO features are only active on production orgs. Sandbox and scratch org sites will not generate a live sitemap or honor robots.txt for external crawlers. Confirm the target environment is production before diagnosing SEO issues.
- **Site technology:** LWR sites use clean URL paths without the `/s` prefix. Aura (Community Builder) sites include `/s` in URLs. This affects URL structure decisions and sitemap paths.
- **Domain model:** Determine whether the site uses a custom domain on a subdomain (`community.example.com`) or on a subpath of a shared domain (`example.com/community`). Sites sharing a subpath share a single robots.txt file — this is the most common source of robots.txt confusion.
- **Guest profile access:** Sitemap.xml automatically includes pages and objects that the site's guest user profile can read. Objects or pages the guest user cannot access will be silently excluded from the sitemap.
- **Knowledge articles and topics:** Knowledge articles are excluded from sitemap.xml unless they are assigned to a Data Category or a Topic. This is a common source of missing Knowledge pages in search engines.

---

## Core Concepts

### Per-Page SEO Properties in Experience Builder

Every page in an Experience Builder site has an SEO properties panel accessible from the page's gear icon (Page Settings > SEO). Available properties:

- **Title** — becomes the `<title>` HTML element; also populates Open Graph `og:title`.
- **Meta Description** — populates `<meta name="description">`. Recommended 150–160 characters. If left blank, the platform may auto-generate one from page content.
- **No Index** — when checked, adds `<meta name="robots" content="noindex">` to the page. This signals search engines not to index the page but does not prevent crawling. A noindex page that is publicly accessible will still be crawled; only indexing is suppressed.

For object detail pages (e.g., Knowledge article detail), the title and description can reference record fields using merge fields. This allows dynamic, record-specific SEO metadata without custom code.

### Sitemap.xml Auto-Generation

Experience Cloud auto-generates a `sitemap.xml` at `<site-base-url>/sitemap.xml`. The sitemap includes:

- All standard site pages the guest user profile can access.
- Object-backed pages (e.g., Knowledge article list and detail) when the guest user has read access to the underlying object records.
- Knowledge articles specifically require assignment to a Topic or Data Category before they appear in the sitemap — access alone is not sufficient.

The sitemap regenerates on a platform-managed schedule, typically within 24 hours of changes. There is no on-demand regeneration trigger available through the UI. The sitemap is only served in production; it returns an empty response or an error in sandbox orgs.

### Custom robots.txt via Visualforce Page

Experience Cloud does not expose a managed robots.txt UI. A custom `robots.txt` is implemented as a Visualforce page named exactly `robots` with `contentType="text/plain"`. The page is served at `<site-base-url>/robots.txt`.

```visualforce
<apex:page contentType="text/plain" showHeader="false" sidebar="false" standardStylesheets="false">
User-agent: *
Disallow: /s/profile
Disallow: /s/login
Disallow: /s/search
Allow: /
Sitemap: https://community.example.com/sitemap.xml
</apex:page>
```

**Critical constraint:** Sites that share a custom domain via subpaths share a single robots.txt file. If `example.com/service` and `example.com/partners` are two separate Experience Cloud sites on the same domain, both sites resolve to the same `robots.txt`. You cannot have site-specific robots.txt files in this topology. The only way to have independent robots.txt files is to give each site its own subdomain.

### URL Structure and LWR Clean URLs

LWR (Lightning Web Runtime) sites do not include the `/s` path segment that Aura-based sites use. LWR pages are served directly from the site root path:

- Aura: `https://community.example.com/s/article/my-topic`
- LWR: `https://community.example.com/article/my-topic`

This affects all sitemap entries, canonical tag values, and any robots.txt Disallow directives. Confirm the site template type before writing any path-based rules.

---

## Common Patterns

### Configuring SEO for a Knowledge Article Detail Page

**When to use:** A self-service portal serves Knowledge articles and the team wants article-specific titles and descriptions in search results.

**How it works:**
1. In Experience Builder, navigate to the Knowledge Article Detail page.
2. Open Page Settings (gear icon) > SEO.
3. Set Title to a merge field expression, e.g.: `{!Record.Title} | Support Portal`
4. Set Meta Description to a merge field that maps to the article summary field, e.g.: `{!Record.Summary}`
5. Leave No Index unchecked unless the article is draft/internal.
6. Ensure the guest user profile has Read access to the Knowledge object.
7. Confirm the article is assigned to a Topic or Data Category so it appears in sitemap.xml.

**Why it works:** Merge fields in SEO properties resolve server-side, producing unique title and description tags for each article URL without custom LWC or Apex.

### Blocking Non-Indexable Pages via Custom robots.txt

**When to use:** The site has login, search, profile, and checkout pages that should not appear in search results.

**How it works:**
1. Create a Visualforce page named exactly `robots` in the org.
2. Set `contentType="text/plain"`, `showHeader="false"`, `sidebar="false"`, `standardStylesheets="false"`.
3. Write `Disallow` directives for non-indexable paths. For Aura sites prefix paths with `/s/`; for LWR sites use the clean path.
4. Include a `Sitemap:` directive pointing to `<site-base-url>/sitemap.xml`.
5. Add the Visualforce page to the Experience Cloud site's site configuration (Site.com Studio or site settings).
6. Verify the output at `<site-base-url>/robots.txt` in a browser.

**Why not the alternative:** Adding `noindex` meta tags to individual pages suppresses indexing but does not suppress crawl budget consumption. For pages you never want indexed, blocking at robots.txt is more efficient and explicit.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Prevent a page from appearing in search results | Add noindex via Page Settings > SEO | Platform-native; no code required |
| Prevent crawlers from accessing a page at all | Add Disallow in robots.txt VF page | robots.txt blocks crawl; noindex only blocks indexing |
| Knowledge articles missing from sitemap | Assign articles to a Topic or Data Category | Platform requirement for sitemap inclusion |
| Two sites on same domain need different robots.txt | Move one site to its own subdomain | Subpath sites share a single robots.txt |
| SEO not working despite correct config | Confirm environment is production | SEO features inactive in sandbox/scratch |
| LWR site paths differ from expected | Confirm site template type; LWR has no /s prefix | Wrong prefix breaks Disallow rules and sitemap paths |

---

## Recommended Workflow

1. **Confirm environment and site type.** Verify the org is production. Identify whether the site uses an Aura or LWR template. Note whether the domain is a subdomain or a subpath.
2. **Audit guest user profile access.** In Experience Builder, open Administration > Guest User Profile. Confirm the guest user has Read on all objects whose records should appear in the sitemap and in search results.
3. **Configure per-page SEO properties.** For each key page, open Page Settings > SEO in Experience Builder. Set Title and Meta Description; use merge fields for object-backed pages. Set noindex only on pages that must not be indexed.
4. **Assign Knowledge articles to topics or data categories.** For each Knowledge article that should appear in the sitemap, confirm it has at least one Topic or Data Category assigned.
5. **Implement or update the custom robots.txt.** Create or update the `robots` Visualforce page. Use correct path prefixes for the site template type. Include a `Sitemap:` directive. Associate the VF page with the site.
6. **Validate in production.** Browse to `<site-base-url>/sitemap.xml` and `<site-base-url>/robots.txt`. Confirm sitemap entries match expected pages. Submit the sitemap URL in Google Search Console. Allow up to 24 hours for sitemap regeneration after publishing changes.

---

## Review Checklist

- [ ] Org is production (not sandbox or scratch)
- [ ] Guest user profile has Read access on all objects that should appear in search results
- [ ] All key pages have explicit Title and Meta Description set in Page Settings > SEO
- [ ] Knowledge articles intended for search are assigned to a Topic or Data Category
- [ ] Custom robots.txt Visualforce page is named exactly `robots` and uses correct path prefixes for site template type
- [ ] Sitemap directive in robots.txt points to the correct `<site-base-url>/sitemap.xml`
- [ ] If multiple sites share a custom domain, the shared robots.txt is acceptable for all sites or each site has its own subdomain

---

## Salesforce-Specific Gotchas

1. **SEO features inactive in non-production orgs** — Experience Cloud sitemap.xml returns an empty response or an error in sandbox and scratch orgs. robots.txt changes cannot be verified in sandbox because the VF page is not served as a real robots.txt there. All SEO validation must happen in production.

2. **Shared robots.txt on subpath domains** — If two or more Experience Cloud sites are hosted on subpaths of the same custom domain (e.g., `example.com/service` and `example.com/partners`), they share a single `robots.txt`. Attempting to configure separate robots.txt files for each site is not possible in this topology. The only resolution is to move each site to its own subdomain.

3. **Knowledge articles excluded from sitemap unless assigned to a topic** — Guest user Read access on the Knowledge object is necessary but not sufficient for articles to appear in sitemap.xml. Each article must also be assigned to at least one Topic or Data Category. Articles that meet access requirements but lack topic assignment are silently omitted from the sitemap.

4. **noindex does not prevent crawling** — Setting noindex on a page via Page Settings > SEO adds a `<meta name="robots" content="noindex">` tag. This tells search engines not to index the page, but crawlers will still visit the URL. If the page must not be crawled (e.g., for performance or confidentiality), add a `Disallow` directive in robots.txt.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SEO page properties configuration | Per-page title, description, and noindex settings applied in Experience Builder |
| robots.txt Visualforce page | VF page named `robots` implementing crawl directives and sitemap reference |
| Sitemap validation results | List of confirmed sitemap.xml entries verified against expected pages |
| SEO readiness checklist | Completed checklist confirming production environment, guest access, topic assignments, and robots.txt |

---

## Related Skills

- `knowledge-vs-external-cms` — when deciding whether Knowledge or an external CMS is the better content store for SEO-driven use cases
- `experience-cloud-guest-user-security` — guest user profile configuration, which directly controls sitemap inclusion
