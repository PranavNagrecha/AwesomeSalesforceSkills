# Gotchas — Experience Cloud SEO Settings

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Cites are to the Winter '27 (264) `api_meta` guide and the Summer '26 (262) Security Implementation Guide (`secguide`).

UNVERIFIED (2026-10-20): Gotchas 1 (environment limits), 2 (shared robots.txt), 3 (Knowledge and the sitemap) and 4 (the No Index setting) rest on Help-only behaviour. The corpus contains no line about sitemap generation at all; each gotcha is marked again where it is asserted.

## Gotcha 1: Environment Limits on SEO Features

**What happens:** UNVERIFIED (2026-10-20): that the sitemap returns an empty response, an error page or a redirect in sandbox and scratch orgs, that robots.txt is not served correctly there, and that per-page tags render differently on a non-production URL, is Help-only. If it holds, validation done in a sandbox proves nothing.

**When it occurs:** Whenever a practitioner validates SEO configuration before promoting to production.

**How to avoid:** Check the real behaviour in your own sandbox and record it. Inspect the page HTML for the `<title>` and `<meta name="description">` values that the SEO assistant component produces (api_meta 264 L63443-63448), fetch the robots.txt page from the production site after promotion, and do not treat a sandbox sitemap result as proof either way.

---

## Gotcha 2: Sites Sharing a Subpath Domain and robots.txt

**What happens:** UNVERIFIED (2026-10-20): that two Experience Cloud sites on subpaths of the same custom domain (for example `example.com/service` and `example.com/partners`) resolve to one robots.txt, and that separate robots pages per site do not produce separate files, is Help-only. What the corpus does say is that `CustomSite.robotsTxtPage` is a per-site field naming the Visualforce page for robots.txt (api_meta 264 L49406-49407) and that custom URLs with a non-root path prefix are not in `customWebAddresses` (L49291-49297).

**When it occurs:** Multi-site deployments that use subpath routing on a shared custom domain.

**How to avoid:** Fetch `/robots.txt` from the domain root and from each site's path and record what each serves. If independent files are required and the shared behaviour is confirmed, use one subdomain per site.

---

## Gotcha 3: Knowledge Articles and the Sitemap

**What happens:** UNVERIFIED (2026-10-20): that Knowledge articles for which the guest user has Read access are omitted from sitemap.xml unless each is also assigned to a Topic or Data Category is Help-only. What the corpus does say is that guest users' org-wide defaults are Private and cannot be changed (secguide 262 L2868-2869), and that a guest user sharing rule, Read Only, is the only way to grant record access to unauthenticated guest users (secguide 262 L2986-2987, L3223-3225). A guest profile object permission alone does not make records visible.

**When it occurs:** A Knowledge base is migrated into a portal with guest access configured and the pages are not found by search engines.

**How to avoid:** Verify guest record access with a guest sharing rule first, then check topic assignment as a hypothesis. Audit assignments with a SOQL query on `TopicAssignment` (`TopicAssignment` links a topic to a feed item, record or file and supports `query()`, object_reference 264 L292198, L292204; UNVERIFIED 2026-10-20: that it covers Knowledge articles is not stated).

---

## Gotcha 4: noindex Does Not Prevent Crawling

**What happens:** UNVERIFIED (2026-10-20): that a "No Index" property under Page Settings > SEO adds `<meta name="robots" content="noindex">` is Help-only. The distinction itself, that a robots meta tag controls indexing while robots.txt controls fetching, is general web behaviour and not a corpus statement. The corpus shows an `isIndexed` flag only on a Marketing workspace landing page in a DigitalExperienceBundle sample, not on a site page (api_meta 264 L54499-54508, L54605-54607), and a per-site `robotsTxtPage` (L49406-49407).

**When it occurs:** Practitioners assume noindex is equivalent to blocking access. A publicly reachable page stays reachable whatever its robots meta tag says.

**How to avoid:** Use a robots.txt Disallow for pages that should not be crawled and treat the indexing flag as a second control. Do not use either to protect sensitive data; secure it with sharing and permissions.

---

## Gotcha 5: URL Prefix Depends on Site Type and Creation Date

**What happens:** An admin writes robots.txt directives with `/s/login` and `/s/search` for a site whose URLs have no `/s`, or the reverse. The `urlPathPrefix` ends in `/s` for authenticated LWR sites created before Winter '23 and for Aura sites; it does not contain `/s` for unauthenticated LWR sites and authenticated LWR sites created after Winter '23 (api_meta 264 L62430-62435). The earlier text that "LWR sites use clean URLs without /s" is too coarse.

**When it occurs:** When robots.txt patterns are copied from another site without reading the target site's prefix.

**How to avoid:** Read `urlPathPrefix` from the retrieved `ExperienceBundle` (the bundle's meta file in the `experiences` folder, api_meta 264 L62391, L62436-62444) before writing any path-based rule, and fetch `/robots.txt` to confirm.
