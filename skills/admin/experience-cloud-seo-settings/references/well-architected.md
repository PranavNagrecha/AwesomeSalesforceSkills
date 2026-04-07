# Well-Architected Notes — Experience Cloud SEO Settings

## Relevant Pillars

- **Trusted** — SEO configuration directly affects what content search engines can access. robots.txt Disallow directives and noindex tags are security-adjacent controls: misconfiguring them can expose login pages, admin tools, or draft content to public indexing. Guest user profile access controls which records enter the sitemap, making access governance part of SEO correctness.
- **Operational Excellence** — SEO settings are often configured once and forgotten. Topic assignment governance for Knowledge articles, periodic sitemap audits, and maintaining the robots.txt VF page through template migrations are operational discipline requirements. Runbooks and checklists prevent drift.
- **Adaptable** — Domain topology choices (subdomain vs. subpath) constrain future SEO configuration options significantly. Choosing a subpath domain to save DNS effort locks all sites on that domain to a shared robots.txt. Designing for subdomain-per-site preserves the ability to independently configure each site's crawl posture as requirements change.

## Architectural Tradeoffs

**Subdomain vs. subpath routing:** Subpath routing simplifies DNS and certificate management but permanently couples all sites on that domain to a single robots.txt. Subdomain routing requires more DNS and TLS configuration but gives each site full SEO autonomy. For organizations expecting to run multiple Experience Cloud sites, subdomain topology is strongly preferred.

**noindex vs. robots.txt Disallow:** noindex is easier to configure (no code required) and is page-granular, but it does not prevent crawling. Disallow in robots.txt prevents crawling but requires a Visualforce page and is less granular (path-prefix matching only). For login and sensitive pages, use both. For low-value content pages (pagination, search results), Disallow in robots.txt is the preferred tool.

**Automatic sitemap vs. manual sitemap:** Experience Cloud's auto-generated sitemap.xml requires no maintenance but is constrained by guest user access and topic assignment rules. Organizations with complex content governance (embargo dates, staged rollouts) may need to suppress sitemap entries via guest user access controls rather than a manually curated sitemap. Plan the guest profile access model with sitemap outcomes in mind.

## Anti-Patterns

1. **Configuring SEO in sandbox and declaring it done** — SEO features are inactive in non-production orgs. An admin who validates sitemap.xml and robots.txt in sandbox is validating nothing. All SEO work must be verified in production after deployment.

2. **Relying solely on noindex to protect sensitive pages** — noindex suppresses indexing but not crawling. Pages marked noindex that are publicly accessible will still be visited by crawlers. For pages that must not be reachable by crawlers, robots.txt Disallow is required.

3. **Ignoring topic assignment as an SEO prerequisite** — Treating Knowledge article visibility as purely an access control question misses the platform requirement that articles must also have a Topic or Data Category assignment to enter the sitemap. Content governance workflows must include topic assignment as a publication gate.

## Official Sources Used

- SEO for Experience Builder Sites — https://help.salesforce.com/s/articleView?id=sf.networks_seo.htm (Salesforce Help: SEO behavior, per-page properties, sitemap generation)
- Create Custom robots.txt for Your Experience Cloud Site — https://help.salesforce.com/s/articleView?id=sf.networks_custom_robots_txt.htm (Salesforce Help: robots.txt VF page pattern)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (architecture quality framing)
- Experience Cloud LWR Sites Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/ (LWR URL structure and clean paths)
