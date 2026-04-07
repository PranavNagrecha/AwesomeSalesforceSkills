# Experience Cloud SEO Settings — Work Template

Use this template when working on SEO configuration tasks for an Experience Cloud site.

## Scope

**Skill:** `experience-cloud-seo-settings`

**Request summary:** (fill in what the user asked for)

---

## Environment and Site Context

- **Org type:** [ ] Production  [ ] Sandbox (SEO features inactive in sandbox — production required for validation)
- **Site template:** [ ] Aura  [ ] LWR  [ ] Other: ___
- **Domain topology:** [ ] Subdomain per site (independent robots.txt possible)  [ ] Subpath on shared domain (shared robots.txt — note constraint)
- **Custom domain in use:** [ ] Yes, domain: ___  [ ] No, using default Salesforce site URL

---

## SEO Requirements Checklist

### Per-Page SEO Properties

For each page that needs SEO configuration, complete the following:

| Page | Title | Meta Description | noindex? | Notes |
|------|-------|-----------------|----------|-------|
| Home | | | No | |
| Knowledge Article Detail | {!Record.Title} \| Site Name | {!Record.Summary} | No | Merge fields recommended |
| Search Results | | | Yes (noindex) | Not useful for search engines |
| Login | | | Yes (noindex) | Also Disallow in robots.txt |
| (add pages) | | | | |

### Sitemap Configuration

- [ ] Guest user profile has Read access on all objects whose records should appear in sitemap
  - Objects verified: ___
- [ ] All Knowledge articles intended for organic search have a Topic or Data Category assigned
  - Method used to verify: ___
- [ ] Sitemap URL confirmed in production: `<site-base-url>/sitemap.xml`
- [ ] Sitemap submitted to Google Search Console

### robots.txt Configuration

- [ ] Visualforce page named exactly `robots` exists in org
- [ ] `contentType="text/plain"`, `showHeader="false"`, `sidebar="false"`, `standardStylesheets="false"` attributes set
- [ ] Path prefixes match site template type (Aura: `/s/path`; LWR: `/path`)
- [ ] `Sitemap:` directive included pointing to `<site-base-url>/sitemap.xml`
- [ ] VF page associated with site in site configuration
- [ ] Verified output at `<site-base-url>/robots.txt` in browser

---

## robots.txt Draft

```
User-agent: *

# Pages to block from crawling
Disallow: /login         # (LWR) or /s/login (Aura)
Disallow: /search        # (LWR) or /s/search (Aura)
Disallow: /profile       # (LWR) or /s/profile (Aura)
Disallow: /register      # (LWR) or /s/register (Aura)

# Allow key content areas explicitly
Allow: /articles         # (LWR) or /s/articles (Aura)
Allow: /products         # (LWR) or /s/products (Aura)
Allow: /

Sitemap: https://<site-base-url>/sitemap.xml
```

Replace placeholder paths and the Sitemap URL with actual values.

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Per-page SEO properties (merge fields for object detail pages)
- [ ] Custom robots.txt via Visualforce
- [ ] Sitemap troubleshooting (guest access + topic assignment)
- [ ] URL structure review (LWR clean URLs vs. Aura /s prefix)

---

## Pre-Deployment Checks

- [ ] Confirmed org is production before any SEO validation
- [ ] All pages in table above have Title and Meta Description filled
- [ ] Knowledge topic assignments completed or verified
- [ ] robots.txt VF page deployed and associated with site
- [ ] robots.txt verified at correct URL in browser
- [ ] Sitemap.xml verified in production (allow up to 24h post-publish for regeneration)

---

## Notes

Record any deviations from standard patterns and why. For example: subpath domain constraint, non-standard template, legacy Aura-to-LWR migration in progress.
