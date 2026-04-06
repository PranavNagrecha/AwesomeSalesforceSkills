# Well-Architected Notes — Service Cloud Architecture

## Relevant Pillars

- **Security** — Service Cloud handles sensitive customer data (PII, support history, financial details in cases). The sharing model must ensure agents only see cases they are authorized to work. Knowledge article visibility must be segmented by audience (internal, partner, customer). Shield Platform Encryption applies to case fields containing regulated data. FLS enforcement in any custom Apex supporting the service process is mandatory.

- **User Experience** — The Service Console is the primary agent workspace. Architecture decisions directly affect agent productivity: page load time, tab management, component density, and utility bar design. A poorly architected Console adds seconds to every interaction — at 8,000 cases/month, even 10 extra seconds per case is 22 hours of wasted agent time monthly.

- **Scalability** — Service Cloud architectures must handle peak volume gracefully. Omni-Channel routing, case automation, and Knowledge search all consume governor limits. A design that works at 100 cases/day may fail at 1,000. Capacity modeling must account for peak concurrency (e.g., Monday morning email backlog, holiday shopping spikes).

- **Reliability** — Case routing and SLA enforcement must be dependable. If Omni-Channel goes down or an entitlement process miscounts business hours, customers experience SLA violations and agents work without routing guidance. Failover patterns (e.g., assignment rule fallback if Omni-Channel is unavailable) are essential for production reliability.

- **Operational Excellence** — Service Cloud architectures require ongoing tuning: routing configuration updates as team structure changes, knowledge base maintenance, entitlement process adjustments as SLA contracts evolve. The architecture must be operable by administrators, not just the original architect.

## Architectural Tradeoffs

### Queue-Based vs Skills-Based Routing

Queue-based routing is simpler to configure, easier to administer, and sufficient for contact centers with generalist agents. Skills-based routing improves first-contact resolution and reduces transfers but requires the managed package, skill definitions, agent skill profiles, and more complex capacity planning. The tradeoff is operational simplicity vs routing precision. Choose queue-based unless agent specialization is a documented requirement — you can migrate to skills-based later, but migrating back is disruptive.

### Synchronous Chat vs Asynchronous Messaging

Synchronous chat (legacy Live Agent) provides a familiar real-time interaction model but limits agent concurrency to 2-3 sessions and creates poor experiences when customers go idle. Asynchronous messaging (Messaging for In-App and Web) supports 4-6 concurrent sessions and persistent conversations but requires session lifecycle management (auto-close policies, dormant session handling). The tradeoff is simplicity of session management vs agent utilization efficiency.

### Knowledge Investment vs Channel Expansion

Adding channels (chat, messaging, social) increases the volume of interactions agents must handle. Investing in knowledge and deflection (self-service portal, bot-assisted resolution) reduces the volume that reaches agents. The tradeoff is coverage (more ways to reach support) vs efficiency (fewer interactions needing human agents). The Well-Architected approach is to invest in deflection before expanding channels — otherwise each new channel multiplies volume without improving resolution rates.

### Native Voice (Service Cloud Voice) vs Open CTI Partner

Service Cloud Voice provides a deeply integrated telephony experience using Amazon Connect — call transcription, AI recommendations, and unified Omni-Channel routing. Open CTI adapters (Genesys, Five9, NICE) preserve existing telephony investments and may offer features not available in Amazon Connect. The tradeoff is depth of native integration vs flexibility and existing investment protection.

## Anti-Patterns

1. **Building channel-specific case routing instead of unified Omni-Channel routing** — Creating separate assignment rule logic for email cases, chat cases, and phone cases results in three parallel routing systems that cannot be tuned together. Use Omni-Channel as the single routing engine for all channels. Channel-specific logic belongs in the routing configuration priority and skill requirements, not in separate automation.

2. **Designing Knowledge taxonomy after go-live instead of during architecture** — Data categories are the foundation of Knowledge article visibility and organization. Restructuring categories after thousands of articles exist requires re-classifying every article. Design the full taxonomy (internal/external visibility, topic hierarchy, article types) during the architecture phase and validate it with content authors before build begins.

3. **Ignoring entitlement process configuration during architecture and bolting it on post-launch** — SLA enforcement touches case record types, page layouts, automation, and reporting. Adding entitlements as an afterthought requires retroactive changes across the case lifecycle. Design entitlement processes as part of the initial case lifecycle architecture, even if the first release uses simple SLAs.

4. **Over-customizing the Service Console with Apex-heavy components** — Replacing standard Service Console features (Knowledge sidebar, Omni-Channel widget, case history) with custom LWC components backed by synchronous Apex degrades performance and creates maintenance burden. Use standard components first; customize only what standard components genuinely cannot support.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Easy — https://architect.salesforce.com/docs/architect/well-architected/guide/easy.html
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/docs/architect/well-architected/guide/adaptable.html
- Service Cloud Overview — https://help.salesforce.com/s/articleView?id=sf.support_agents_intro.htm
