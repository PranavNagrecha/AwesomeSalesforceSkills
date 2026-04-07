# Well-Architected Notes — Multi-Site Architecture

## Relevant Pillars

### Trusted (Security)

Each Experience Cloud site has an independent security surface: a site-specific guest user profile, site-level CSP settings, clickjack protection settings, and HTTPS enforcement. In multi-site architectures, the security configuration of each site must be reviewed and configured independently — there is no inherited or shared security policy across sites.

Key security concerns:
- Guest user profiles must follow the principle of least privilege. Access granted on one site's guest profile does not carry over to other sites, but the absence of access on a new site can silently expose shared components to runtime failures.
- Cross-site navigation must not transmit authentication tokens via URL parameters. SSO via an external IdP is the only supported secure pattern for transparent cross-site authentication.
- CSP trusted site entries and CORS configurations are per-site and must reference the correct URL pattern for each environment (custom domain in production; `.my.site.com` pattern in sandbox).

### Adaptable (Scalability and Extensibility)

The 100-site org limit is a hard platform constraint that must be treated as a capacity resource. Multi-site architectures that do not include a site lifecycle management policy will accumulate inactive and preview sites and eventually hit the quota without warning.

Shared LWC component libraries are the primary extensibility mechanism across sites. Components built with `@api` property externalization can serve new audiences and regions without code changes — only new site configuration is required. This is the adaptable design pattern for multi-site Experience Cloud.

Custom domain strategy should be designed for flexibility: URL path segment conventions that allow new sites to be added under an existing domain without DNS changes reduce the operational cost of growing the site topology.

### Operational Excellence

Multi-site architectures require operational processes that single-site deployments do not:

- A site inventory with owner, purpose, audience, license type, and lifecycle status.
- A deployment pipeline that can push shared LWC component updates to all sites simultaneously.
- A per-site security configuration review cadence, particularly after Salesforce releases that change guest user behavior or CSP policies.
- A site creation and deletion workflow that prevents quota accumulation.

Without these processes, multi-site architectures drift toward inconsistent security postures, orphaned sites, and component version fragmentation.

---

## Architectural Tradeoffs

### Multi-Site in One Org vs. Multi-Org

| Factor | Multi-site (one org) | Multi-org |
|---|---|---|
| Data model | Shared — all sites access the same objects and records | Separate — each org has its own data model |
| User management | One user record; different license types per site access | Separate user records per org; duplication overhead |
| Sharing and access control | Per-site guest profiles + sharing rules + permission sets | Per-org — clean isolation but high duplication |
| Operational overhead | Moderate — shared DevOps pipeline | High — separate release pipelines, separate support processes |
| Site quota | 100-site limit within the org | Unlimited orgs; each org has its own 100-site limit |
| When to choose | Default for all portal use cases — customer, partner, employee | Only when data residency law, M&A, or ISV tenant isolation makes single-org structurally impossible |

### Shared Component Library vs. Site-Specific Components

| Factor | Shared library | Site-specific components |
|---|---|---|
| Maintenance burden | Low — fix once, deploy everywhere | High — same bug must be fixed in N places |
| Flexibility | Medium — configured per site via `@api` properties | High — each component can diverge freely |
| Consistency | High — design and behavior are uniform | Low — components drift over time |
| When to choose | Default for all reusable UI elements | Only for site-specific functionality with no overlap |

### Custom Domain vs. Default my.site.com URL

| Factor | Custom domain | Default my.site.com |
|---|---|---|
| Branding | Strong — company-branded URL | Weak — Salesforce domain visible |
| Edition requirement | Enterprise+ | All editions |
| Configuration environment | Production only | All environments |
| DNS and SSL complexity | Required (CNAME, SSL cert) | None |
| CDN | Automatic for Experience Builder sites | Same |
| When to choose | Customer-facing and partner-facing sites where branding matters | Internal or prototype sites; all sandbox environments |

---

## Anti-Patterns

1. **Accumulating preview and inactive sites without a lifecycle policy** — treats site creation as a free operation. The 100-site limit is a hard cap. Orgs that do not actively manage the site inventory will be blocked from creating production-critical sites at the worst possible moment.

2. **Designing cross-site session sharing via URL token passing** — creates a session token exposure vulnerability. Salesforce does not support cross-site session hand-off natively. The secure, supported pattern is SSO via an external IdP.

3. **Forking LWC components per site** — produces maintenance debt that compounds with each new site added. The correct pattern is a shared component library with `@api` property externalization for per-site configuration.

4. **Using separate production orgs for audience isolation when multi-site within one org is sufficient** — introduces cross-org data sync complexity, doubles user management overhead, and requires separate license allocations without providing meaningful benefit over a multi-site single-org architecture.

5. **Hardcoding production custom domain URLs in Apex, Flow, or component configuration** — breaks sandbox environments and is not portable across deployment targets. Externalize site base URLs via Custom Metadata or Named Credentials.

---

## Official Sources Used

- Salesforce Help — Experience Cloud Site Considerations — https://help.salesforce.com/s/articleView?id=sf.networks_considerations.htm
- Salesforce Help — How Many Sites Can My Org Have — https://help.salesforce.com/s/articleView?id=sf.networks_limits_sites.htm
- Salesforce Help — Configure a Custom Domain for Your Experience Cloud Site — https://help.salesforce.com/s/articleView?id=sf.communities_custom_domain_overview.htm
- Salesforce Help — Experience Cloud Usage Allocation — https://help.salesforce.com/s/articleView?id=sf.networks_licenses_and_usage_allocation.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
