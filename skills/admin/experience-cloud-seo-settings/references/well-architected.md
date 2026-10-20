# Well-Architected Notes — Experience Cloud SEO Settings

## Relevant Pillars

- **Trusted** — SEO configuration directly affects what content search engines can access. robots.txt Disallow directives and noindex tags are security-adjacent controls: misconfiguring them can expose login pages, admin tools, or draft content to public indexing. Guest record access comes from guest user sharing rules (secguide 262 L2986-2987, L3223-3225), so access governance is part of SEO correctness. UNVERIFIED (2026-10-20): that the guest profile access decides which records enter the sitemap is Help-only.
- **Operational Excellence** — SEO settings are often configured once and forgotten. Periodic sitemap audits (UNVERIFIED (2026-10-20): sitemap behaviour is Help-only), topic assignment governance for Knowledge articles (UNVERIFIED (2026-10-20): Help-only), and keeping `CustomSite.robotsTxtPage` pointing at the maintained Visualforce page through template migrations are operational discipline requirements. Runbooks and checklists prevent drift.
- **Adaptable** — Domain topology choices (subdomain vs. subpath) constrain future SEO configuration options significantly. UNVERIFIED (2026-10-20): that choosing a subpath domain locks all sites on it to a shared robots.txt is Help-only. If it holds, designing for subdomain-per-site preserves the ability to configure each site's crawl posture independently.

## Architectural Tradeoffs

**Subdomain vs. subpath routing:** Subpath routing simplifies DNS and certificate management; UNVERIFIED (2026-10-20): that it couples all sites on the domain to a single robots.txt is Help-only. Subdomain routing requires more DNS and TLS configuration. Test the robots.txt behaviour of a subpath topology before choosing it.

**Indexing flag vs. robots.txt Disallow:** UNVERIFIED (2026-10-20): the No Index setting is Help-only. In general web terms an indexing flag is page-granular and does not stop fetching, while a Disallow line in the Visualforce page named by `CustomSite.robotsTxtPage` (api_meta 264 L49406-49407) controls crawling by path prefix. For login and sensitive pages use both, and protect data with sharing, not either.

**Automatic sitemap vs. manual sitemap:** UNVERIFIED (2026-10-20): the auto-generated sitemap and its constraints (guest access, topic assignment) are Help-only. Plan the guest sharing model with sitemap outcomes in mind and verify them by fetching the sitemap.

## Anti-Patterns

1. **Configuring SEO in sandbox and declaring it done** — UNVERIFIED (2026-10-20): that SEO features are inactive in non-production orgs is Help-only. Verify the sitemap and robots.txt in production after deployment and record what the sandbox returned.

2. **Relying solely on an indexing flag to protect sensitive pages** — an indexing flag is not an access control (UNVERIFIED (2026-10-20): the No Index setting itself is Help-only). Use robots.txt Disallow for crawl control and sharing and permissions for data.

3. **Ignoring guest sharing rules as an SEO prerequisite** — Treating Knowledge article visibility as a profile permission question misses that record access for unauthenticated guests needs a guest user sharing rule (secguide 262 L3223-3225). UNVERIFIED (2026-10-20): that a Topic or Data Category assignment is also a sitemap prerequisite is Help-only.

## Official Sources Used

- SEO assistant component (`customHeadTags`, `description`, `pageTitle`) — api_meta 264 L63443-63448, L55970-55976, L56420-56425
- `CustomSite.robotsTxtPage` — api_meta 264 L49406-49407; `customWebAddresses` L49291-49297
- `ExperienceBundle.urlPathPrefix` and the `/s` rule — api_meta 264 L62430-62444; `preferredDomain` L62656-62658
- `sfdc_cms:seoProperties` / `isIndexed` sample, on a Marketing workspace landing page and not a site page — api_meta 264 L54499-54508, L54605-54608
- Guest user org-wide defaults and guest user sharing rules — secguide 262 L2868-2869, L2986-2987, L3223-3225
- SEO for Experience Builder Sites — https://help.salesforce.com/s/articleView?id=sf.networks_seo.htm (UNVERIFIED (2026-10-20): Help-only; the source for sitemap generation, the No Index setting and the Setup UI paths)
- Create Custom robots.txt for Your Experience Cloud Site — https://help.salesforce.com/s/articleView?id=sf.networks_custom_robots_txt.htm (UNVERIFIED (2026-10-20): Help-only; the source for the Visualforce page attributes)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (architecture quality framing)
- Experience Cloud LWR Sites Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/ (UNVERIFIED (2026-10-20): not fetched; the `/s` rule above comes from api_meta 264 L62430-62435 instead)
