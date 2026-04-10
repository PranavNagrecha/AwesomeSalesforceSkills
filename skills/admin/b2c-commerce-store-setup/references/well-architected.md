# Well-Architected Notes — B2C Commerce Store Setup

## Relevant Pillars

- **Performance** — The highest-impact pillar for B2C Commerce store setup. Cartridge path length, active promotion count, session payload size, and search index freshness all have direct performance consequences. The 1,000 active-promotion threshold and 10 KB session cap are concrete performance boundaries that practitioners must architect against, not react to.

- **Security** — Storefront URL configuration, Business Manager administrator roles, and API credentials for external integrations must be scoped correctly. Business Manager user roles follow least-privilege principles — storefront managers should not have administrator-level BM access. WebDAV credentials used for cartridge deployment must be rotated and stored in CI secret management, not committed to source control.

- **Reliability** — Search index staleness is a reliability risk: if the rebuild step is omitted from deployment runbooks, production storefronts serve degraded or incorrect search results. Replication jobs that exclude index rebuild create silent reliability gaps in production. Quota limits on active promotions and custom objects must be monitored proactively to avoid hard-limit failures at peak traffic.

- **Operational Excellence** — Deployments that lack a search index rebuild step, promotion hygiene processes, and cartridge path verification are operationally fragile. Repeatable runbooks and quota dashboards reduce reliance on tribal knowledge and prevent recurring production incidents.

## Architectural Tradeoffs

**Custom cartridge isolation vs. base cartridge modification:** Overriding files in a custom cartridge positioned left of `app_storefront_base` requires more initial setup (cartridge structure, path configuration) but eliminates upgrade friction on every SFRA release. Direct modification of `app_storefront_base` is faster initially but creates a compounding technical debt liability — each SFRA upgrade requires re-patching. The correct tradeoff is always cartridge isolation.

**Single site vs. multi-site per region:** A single SFCC site can support multiple locales via locale configuration. Multi-site (separate site IDs per region) is appropriate when brand, currency, or catalog differs substantially, or when regional regulatory requirements mandate data isolation. Multi-site increases operational overhead (separate search index rebuilds, separate replication jobs, separate cartridge path management) but provides cleaner separation of concerns.

**Promotion breadth vs. performance headroom:** Wide promotion programs (loyalty, personalization, seasonal) conflict with the active-promotion performance threshold. Architects should design promotion lifecycle management (start/end dates, auto-expiry jobs) at the same time as the promotion creation process — not after performance issues appear.

## Anti-Patterns

1. **Modifying app_storefront_base directly** — Any change to the base cartridge creates a merge conflict on every SFRA upgrade and makes the modification invisible to developers who assume the base is stock. All customizations must live in a separately-versioned custom cartridge to the left of the base.

2. **Omitting search index rebuild from deployment runbooks** — Treating catalog import as a complete deployment step without triggering a subsequent search index rebuild means production search always lags catalog truth. This is a systemic reliability failure that compounds with each deployment cycle.

3. **Unbounded promotion accumulation** — Creating promotions without an archival or expiry governance process causes active-promotion count to grow unboundedly. The performance cliff at 1,000 is reached gradually and invisibly, making root-cause analysis difficult when checkout times spike.

4. **Storing large objects in SFCC session** — Using session as a general-purpose client-side store for complex objects (full product records, personalization profiles) hits the 10 KB limit unpredictably and causes silent data loss. Session should hold only identifiers.

## Official Sources Used

- B2C Commerce Developer Guide — Architecture and Site Management: https://developer.salesforce.com/docs/commerce/b2c-commerce/guide/b2c-commerce-site-administration.html
- SFRA Developer Guide — Configure SFRA: https://developer.salesforce.com/docs/commerce/b2c-commerce/guide/sfra-configure.html
- Trailhead — Architecture of Commerce Cloud Digital: https://trailhead.salesforce.com/content/learn/modules/cc-digital-for-developers/cc-digital-architecture
- Trailhead — Guide to B2C Commerce Cartridges: https://trailhead.salesforce.com/content/learn/modules/cc-digital-for-developers/cc-digital-cartridges
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
