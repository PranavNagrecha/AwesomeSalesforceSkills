# Experience Cloud SEO Settings — Work Template

Use this template when working on SEO configuration tasks for an Experience Cloud site.

## Scope

**Skill:** `experience-cloud-seo-settings`

**Request summary:** (fill in what the user asked for)

---

## Environment and Site Context

- **Org type:** [ ] Production  [ ] Sandbox (UNVERIFIED 2026-10-20: that SEO features are inactive in sandbox is Help-only; record what you observe)
- **Site template:** [ ] Aura  [ ] LWR  [ ] Other: ___  **`urlPathPrefix` from the retrieved ExperienceBundle:** ___ (api_meta 264 L62430-62435)
- **Domain topology:** [ ] Subdomain per site  [ ] Subpath on shared domain (UNVERIFIED 2026-10-20: whether the sites then share one robots.txt is Help-only; test it)
- **Custom domain in use:** [ ] Yes, domain: ___  [ ] No, using default Salesforce site URL

---

## SEO Requirements Checklist

### Per-Page SEO Properties

For each page that needs SEO configuration, complete the following:

| Page | pageTitle | description | customHeadTags | Notes |
|------|-----------|-------------|----------------|-------|
| Home | | | | |
| Knowledge Article Detail | | | | record-specific values: see note below |
| Search Results | | | | Candidate for a robots.txt Disallow |
| Login | | | | Candidate for a robots.txt Disallow |
| (add pages) | | | | |

The three property columns are the ones the SEO assistant component exposes (api_meta 264 L63443-63448). The guide's sample carries `recordId` as `{!recordId}` (api_meta 264 L56425). UNVERIFIED (2026-10-20): other merge expressions such as `{!Record.Title}`, and a "No Index" setting per page, are Help-only.

### Sitemap Configuration

- [ ] Guest user sharing rules exist for the objects whose records should be public (secguide 262 L3223-3225)
  - Objects verified: ___
- [ ] Knowledge topic or data category assignment checked (UNVERIFIED 2026-10-20: the sitemap rule is Help-only)
  - Method used to verify: ___
- [ ] Sitemap URL fetched and the result recorded: `<site-base-url>/sitemap.xml` (UNVERIFIED 2026-10-20: Help-only)
- [ ] Sitemap submitted to Google Search Console (optional)

### robots.txt Configuration

- [ ] A Visualforce page for robots.txt exists and `CustomSite.robotsTxtPage` names it (api_meta 264 L49406-49407)
- [ ] Page attributes set as in the example (UNVERIFIED 2026-10-20: the attribute set is Help-only)
- [ ] Path prefixes match the `urlPathPrefix` (ends in `/s` or not; api_meta 264 L62430-62435)
- [ ] `Sitemap:` directive included only if a sitemap is confirmed (UNVERIFIED 2026-10-20)
- [ ] Verified output at `<site-base-url>/robots.txt` in browser

---

## robots.txt Draft

```
User-agent: *

# Pages to block from crawling
Disallow: /login         # with the /s prefix if urlPathPrefix ends in /s
Disallow: /search        # with the /s prefix if urlPathPrefix ends in /s
Disallow: /profile       # with the /s prefix if urlPathPrefix ends in /s
Disallow: /register      # with the /s prefix if urlPathPrefix ends in /s

# Allow key content areas explicitly
Allow: /articles         # with the /s prefix if urlPathPrefix ends in /s
Allow: /products         # with the /s prefix if urlPathPrefix ends in /s
Allow: /

Sitemap: https://<site-base-url>/sitemap.xml
```

Replace placeholder paths and the Sitemap URL with actual values.

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Per-page SEO properties (SEO assistant component)
- [ ] Custom robots.txt via Visualforce and `robotsTxtPage`
- [ ] Sitemap troubleshooting (guest sharing rules first; topic assignment UNVERIFIED 2026-10-20)
- [ ] URL structure review (`urlPathPrefix`)

---

## Pre-Deployment Checks

- [ ] Environment of every SEO check recorded (UNVERIFIED 2026-10-20: production-only behaviour is Help-only)
- [ ] All pages in table above have pageTitle and description filled
- [ ] Knowledge topic assignments checked (UNVERIFIED 2026-10-20)
- [ ] robots.txt VF page deployed and named in `CustomSite.robotsTxtPage`
- [ ] robots.txt verified at correct URL in browser
- [ ] Sitemap.xml fetched and the refresh delay recorded (UNVERIFIED 2026-10-20: a 24-hour regeneration is Help-only)

---

## Notes

Record any deviations from standard patterns and why. For example: subpath domain constraint, non-standard template, legacy Aura-to-LWR migration in progress.
