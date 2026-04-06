# Well-Architected Notes -- Knowledge vs External CMS

## Relevant Pillars

- **Scalability** -- The content platform must handle growing article counts, additional languages, and increasing self-service traffic without degrading authoring or retrieval performance. Knowledge scales within Salesforce governor limits; external CMS platforms scale independently with CDN delivery.
- **User Experience** -- Agents need articles surfaced contextually in the console (Einstein recommendations). Customers need coherent search results in self-service portals. A fragmented content architecture degrades both experiences.
- **Operational Excellence** -- Content authoring, review, and publishing workflows must be sustainable for the team that owns them. Forcing a marketing content team into Knowledge's basic editor, or forcing agents to search two disconnected systems, creates operational drag that compounds over time.
- **Security** -- Data category visibility controls which articles are exposed to which audiences. In a hybrid model, the external CMS must enforce equivalent access controls for gated content. Misconfigured visibility can leak internal-only procedures to portal users.
- **Reliability** -- A hybrid architecture introduces a dependency between two systems. If the CMS is down, CMS Connect content disappears from the portal. If the sync integration fails, agents work with stale articles. Each integration point is a reliability risk that must be monitored.

## Architectural Tradeoffs

The core tradeoff is **native integration depth vs. authoring capability**. Knowledge offers unmatched integration with Service Cloud (Einstein recommendations, case deflection, console embedding, data-category visibility) but limited authoring sophistication. External CMS platforms offer rich authoring, localization, and headless delivery but require integration effort to participate in the Salesforce ecosystem. The hybrid pattern trades integration complexity for the ability to use each platform at its strength.

A secondary tradeoff is **operational simplicity vs. audience-optimized delivery**. A single-system approach (Knowledge-only or CMS-only) is simpler to operate but forces one audience to accept a suboptimal experience. The hybrid approach optimizes for each audience but requires taxonomy alignment, search tuning, and integration monitoring.

## Anti-Patterns

1. **Duplicating all content in both systems** -- Maintaining identical copies of every article in Knowledge and the CMS creates a sync burden, version conflicts, and inevitable content drift. Instead, designate one system of record per content type and sync only what is necessary for the secondary consumer.
2. **Ignoring search as an integration concern** -- Treating search as an afterthought in a hybrid architecture leads to fragmented results where customers see partial answers from each system. Search must be planned as a first-class integration point with deliberate relevance tuning per channel.
3. **Choosing based on authoring preference alone** -- Selecting the content platform based solely on what the content team prefers to author in, without considering where the content is consumed and what platform features the consumer needs (Einstein recommendations, case deflection, headless delivery), leads to architectures that serve authors but fail users.

## Official Sources Used

- Salesforce Well-Architected Overview -- https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Knowledge Overview -- https://help.salesforce.com/s/articleView?id=sf.knowledge_whatis.htm
- CMS Connect for Experience Cloud -- https://help.salesforce.com/s/articleView?id=sf.cms_connect.htm
