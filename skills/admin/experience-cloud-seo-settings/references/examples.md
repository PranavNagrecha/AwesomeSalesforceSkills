# Examples — Experience Cloud SEO Settings

Cites are to the Winter '27 (264) `api_meta` guide and the Summer '26 (262) Security Implementation Guide (`secguide`).

## Example 1: Page Title and Description on an Article Detail Page

**Context:** A self-service portal serves hundreds of Knowledge articles. The team wants each article's search result to show a specific title and summary instead of the site default.

**Problem:** The detail page shares one set of SEO properties, so every article shares one title and description unless the page's SEO assistant component is configured.

**Solution:** In the retrieved `ExperienceBundle`, the page's `views/<view>.json` has a hidden region, `sfdcHiddenRegion`, holding the SEO assistant component (api_meta 264 L63443-63448). Set `pageTitle` and `description`; the guide's sample shows the four attributes (L56420-56425):

```json
{
  "title": "sfdcHiddenRegion",
  "type": "region",
  "children": [
    {
      "type": "component",
      "definition": "community_builder:seoAssistant",
      "attributes": {
        "customHeadTags": "",
        "description": "Answers to common support questions for Acme customers.",
        "pageTitle": "Support Article | Acme Support",
        "recordId": "{!recordId}"
      }
    }
  ],
  "name": "sfdcHiddenRegion"
}
```

In an Aura site the component's definition is `forceCommunity:seoAssistant` (api_meta 264 L63443-63444). You can't edit the other properties of the component (L63446-63447). Make sure the guest user can read the article records: guest users' org-wide defaults are Private and a guest user sharing rule (Read Only) is the only way to grant record access to unauthenticated guests (secguide 262 L2868-2869, L2986-2987, L3223-3225).

UNVERIFIED (2026-10-20): per-record merge expressions such as `{!Record.Title} | Acme Support` and `{!Record.Summary}` (used by earlier versions of this example) are Help-only; only `{!recordId}` appears in the guide's sample. The same applies to the Experience Builder path Page Settings > SEO, that the sitemap includes the article once a Topic is assigned, and the browser DevTools check of the rendered tags.

---

## Example 2: A Custom robots.txt Page Wired to the Site

**Context:** A partner community at `https://partners.example.com` wants crawlers kept off login, search and profile pages, with a sitemap line.

**Problem:** Without a robots.txt page, there is nothing to carry the directives.

**Solution:** Create the Visualforce page, then set `robotsTxtPage` on the site's `CustomSite` to that page's name. The field is "the name of the Visualforce page to display for the robots.txt file used by web crawlers" (api_meta 264 L49406-49407), so the page need not be called `robots`.

`pages/PartnerRobots.page`:

```visualforce
<apex:page contentType="text/plain" showHeader="false" sidebar="false" standardStylesheets="false">
User-agent: *
Disallow: /login
Disallow: /search
Disallow: /profile
Sitemap: https://partners.example.com/sitemap.xml
</apex:page>
```

`sites/Partners.site-meta.xml` (excerpt; the rest of the file is unchanged):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: keep the other CustomSite fields as retrieved -->
<CustomSite xmlns="http://soap.sforce.com/2006/04/metadata">
    <robotsTxtPage>PartnerRobots</robotsTxtPage>
</CustomSite>
```

Read the site's `urlPathPrefix` before choosing the paths: where it ends in `/s` the `Disallow` lines need that prefix, and where it does not they must not have it (api_meta 264 L62430-62435). Fetch `https://partners.example.com/robots.txt` and compare it with the page.

UNVERIFIED (2026-10-20): the page attributes (`contentType="text/plain"` and the three `false` attributes), that the sitemap URL exists, and the exact disallowed paths are Help-only; earlier versions of this example also said the page must be named exactly `robots` and be associated in Site.com Studio, which the `robotsTxtPage` field contradicts.

---

## Anti-Pattern: Using noindex to Block Crawl-Sensitive Pages

**What practitioners do:** Set a No Index property on the login and search pages and conclude that those pages are "protected from search engines."

**What goes wrong:** UNVERIFIED (2026-10-20): the No Index property and the meta tag it adds are Help-only. Whatever the property does, it is an indexing signal and not an access control; crawlers can still fetch a publicly reachable URL, and a robots.txt `Disallow` is the crawl control. Neither protects data: use sharing and permissions for that.

**Correct approach:** Use `Disallow` lines in the page named by `robotsTxtPage` for URLs crawlers should not fetch, and treat any indexing flag (the corpus shows `isIndexed` only on a Marketing workspace landing page, api_meta 264 L54499-54508, L54605-54607) as a secondary control.
