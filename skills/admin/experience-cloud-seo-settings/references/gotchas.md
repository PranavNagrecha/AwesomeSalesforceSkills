# Gotchas — Experience Cloud SEO Settings

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SEO Features Are Inactive in Sandbox and Scratch Orgs

**What happens:** sitemap.xml returns an empty response, an error page, or a redirect to the login page in sandbox and scratch orgs. robots.txt is not served correctly either. Per-page SEO meta tags may also render differently when the site is accessed from a non-production URL or when the guest user session is not active.

**When it occurs:** Any time a practitioner tries to validate SEO configuration in a sandbox, developer org, or scratch org before promoting to production.

**How to avoid:** All SEO validation must be performed on the production org against the production site URL. For pre-production review, inspect the HTML source of individual pages to confirm `<title>` and `<meta name="description">` tags are rendering correctly, and review the robots VF page output directly at `/robots.txt` after promotion. Do not attempt to verify sitemap.xml before going live.

---

## Gotcha 2: Sites Sharing a Subpath Domain Share One robots.txt

**What happens:** When two or more Experience Cloud sites are hosted on subpaths of the same custom domain (e.g., `example.com/service` and `example.com/partners`), they resolve to the same `robots.txt` file. Creating separate `robots` Visualforce pages in each site's configuration does not produce separate robots.txt files — only the one associated with the root domain path takes effect.

**When it occurs:** This affects any multi-site deployment that uses subpath routing on a shared custom domain. It is a common architecture for orgs that started with one Experience Cloud site and added more over time on the same domain.

**How to avoid:** Design multi-site deployments with one subdomain per site if independent robots.txt files are required (`service.example.com`, `partners.example.com`). If subpath routing is already in use and the shared robots.txt is not acceptable, the domain topology must be changed — there is no configuration workaround within Experience Cloud.

---

## Gotcha 3: Knowledge Articles Excluded from Sitemap Without Topic Assignment

**What happens:** Knowledge articles for which the guest user has Read access do not appear in sitemap.xml unless each article is also assigned to at least one Topic or Data Category. Articles that pass the access check but lack a topic assignment are silently omitted from the sitemap.

**When it occurs:** Occurs when a Knowledge base is migrated to an Experience Cloud portal and guest access is configured correctly, but topic assignment workflows were not established. The sitemap appears smaller than expected and Knowledge pages receive little organic traffic.

**How to avoid:** Establish a content governance rule that every published Knowledge article must have at least one Topic assigned before publication. Audit existing articles using a SOQL query against `TopicAssignment` where `EntityId` is the Knowledge article Id. Bulk-assign topics via Data Loader or a Flow for legacy articles.

---

## Gotcha 4: noindex Does Not Prevent Crawling

**What happens:** Setting No Index in Page Settings > SEO adds `<meta name="robots" content="noindex">` to the page. Crawlers still fetch the page — only indexing is suppressed. Sensitive pages (login, admin tools) that are publicly accessible remain reachable and crawlable even with noindex set.

**When it occurs:** Practitioners assume noindex is equivalent to blocking access. Login pages, search results pages, and user profile pages with noindex set still show up in crawl logs and can be reached via direct URL by anyone.

**How to avoid:** Use `Disallow` directives in the custom robots.txt for pages that should not be crawled at all. noindex is appropriate as a secondary measure but must not be the sole protection for sensitive or low-value pages.

---

## Gotcha 5: LWR Sites Use Clean URLs Without /s Prefix

**What happens:** An admin writes robots.txt Disallow directives using `/s/login` and `/s/search` (the pattern for Aura sites), then deploys to an LWR site. The directives have no effect because LWR sites serve those pages at `/login` and `/search` without the `/s` segment.

**When it occurs:** When practitioners copy robots.txt patterns from Aura site documentation or existing Aura sites and apply them to an LWR template site.

**How to avoid:** Before writing any path-based rules, confirm the site template type in Experience Builder (Administration > Settings > Template). For LWR sites, omit the `/s` prefix from all paths in robots.txt Disallow directives and in the Sitemap directive URL.
