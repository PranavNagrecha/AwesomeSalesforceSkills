# Well-Architected Notes — B2B vs B2C Commerce Architecture

## Relevant Pillars

- **Reliability** — The platform choice creates a long-term extensibility constraint. B2B Commerce on Core is extended through the Salesforce platform's standard extension mechanisms (Apex, Flow, LWC, Commerce Extensions). SFCC is extended through SFRA cartridges, Business Manager extensions, and hooks. Choosing the wrong extensibility model for the team's skills or the business's future requirements creates technical debt that cannot be refactored without a platform migration. Architecturally sound decisions evaluate extensibility and long-term reliability across the expected system lifespan, not just initial delivery.

- **Performance** — The two platforms have fundamentally different performance envelopes. SFCC is purpose-built for high-volume anonymous consumer traffic with dedicated infrastructure, CDN integration, and caching layers. B2B Commerce on Core runs within Salesforce platform governor limits, which are appropriate for authenticated account-based workloads but constrain anonymous-consumer scale. Selecting the wrong platform against peak traffic requirements produces an architecture that cannot be performance-tuned without a platform change.

- **Scalability** — SFCC scales horizontally at the infrastructure layer, independent of the Salesforce org's API tier. B2B Commerce on Core scales within the org's resource envelope, which is appropriate for B2B transaction volumes but not for Black Friday-style consumer traffic spikes. Scalability requirements must be quantified (concurrent sessions, annual order volume, peak throughput) before the architecture decision is finalized.

- **Security** — B2B Commerce on Core inherits Salesforce platform security: profiles, permission sets, sharing rules, field-level security, and Named Credentials for callouts. All standard Salesforce security controls apply. SFCC has its own security model: Business Manager roles, site preferences, API key authentication for OCAPI/SCAPI, and server-side certificate management. Architects must evaluate security requirements against each platform's model — particularly for PCI DSS compliance (payment tokenization differs between platforms).

- **Operational Excellence** — DevOps pipelines differ completely. B2B Commerce on Core uses standard Salesforce DX (SFDX): source-tracked orgs, scratch orgs, CI with Apex test execution, metadata deployment via `sf deploy`. SFCC uses the SFCC deployment model: cartridge zip uploads, code version activation, Business Manager configuration export/import, and the SFCC Command Line Tools (sgmf-scripts / b2c-tools). A team that has mature Salesforce DX practices gains no operational advantage on SFCC, and vice versa. Operational Excellence requires matching the DevOps model to the team's existing toolchain.

## Architectural Tradeoffs

**CRM integration depth vs. infrastructure independence:** B2B Commerce on Core provides zero-latency, zero-integration-cost access to all Salesforce CRM data. This is a structural advantage for account-based commerce with complex pricing and entitlement requirements. The tradeoff is that the storefront is coupled to the Salesforce org's infrastructure — scaling and performance are bounded by the platform. SFCC provides infrastructure independence and consumer-scale performance. The tradeoff is that any CRM data needed at checkout requires a designed, maintained, and monitored integration layer.

**Declarative flexibility vs. code-first extensibility:** B2B Commerce on Core's Flow-based checkout is accessible to admins and low-code practitioners. Custom logic is addable without full Apex development for many scenarios. SFCC's SFRA cartridge model is code-first, requiring Node.js development for any customization beyond Business Manager configuration. For organizations with strong admin/declarative skill sets, B2B Commerce on Core offers faster initial delivery. For organizations with strong engineering teams preferring code-first control, SFCC offers more granular override capability at the cost of higher initial engineering investment.

**Single-platform simplicity vs. purpose-built scale:** Running B2B Commerce on Core keeps the entire technology estate on one platform (Salesforce org), simplifying vendor management, data governance, and support escalation. SFCC adds a second platform with separate licenses, separate support contracts, separate monitoring, and separate DevOps tooling. Organizations with limited operational bandwidth should weigh this total cost of ownership difference explicitly.

## Anti-Patterns

1. **Treating "Salesforce Commerce" as a single product** — Conflating B2B Commerce on Core and SFCC into a single mental model leads to architecture decisions that apply the wrong extensibility mechanism, miss integration requirements, and produce effort estimates that are off by orders of magnitude. Always establish which platform is in scope before any technical recommendation.

2. **Selecting SFCC for a B2B use case because of team familiarity** — SFCC is the right choice for high-volume consumer workloads. It is architecturally inappropriate for account-based B2B commerce with deep CRM integration requirements. Selecting SFCC for a B2B use case because the team has prior SFCC experience results in a multi-integration architecture that is complex to build and maintain, where B2B Commerce on Core would have provided a simpler, cheaper, and more reliable solution.

3. **Selecting B2B Commerce on Core for consumer-scale traffic without load testing** — B2B Commerce on Core's Salesforce platform governor limits are not designed for anonymous consumer traffic at e-commerce peak scale. Selecting B2B Commerce on Core for a consumer storefront without explicit load analysis risks building an architecture that requires a platform migration once traffic grows.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- B2B Commerce Developer Guide — Data Model and Integration Architecture — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/b2c_comm_dev_intro.htm
- B2C Commerce Developer Guide — SFRA Overview — https://developer.salesforce.com/docs/commerce/sfra/overview
- Salesforce Help — B2B Commerce and D2C Commerce Introduction — https://help.salesforce.com/s/articleView?id=sf.comm_intro.htm
- Commerce Extensions Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.b2b_b2c_comm_dev.meta/b2b_b2c_comm_dev/comm_dev_extensions.htm
