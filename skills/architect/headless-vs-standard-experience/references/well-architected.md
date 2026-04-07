# Well-Architected Notes — Headless vs Standard Experience

## Relevant Pillars

- **Performance Efficiency** — This is the primary driver for most Aura-to-LWR decisions. LWR's two-layer architecture (CDN-cached static shell + dynamic data) delivers approximately 50% faster Time to First Contentful Paint than Aura. Headless sites can outperform LWR when hosted on purpose-built edge infrastructure, but the delta over LWR is smaller than the delta between LWR and Aura. The Well-Architected framework asks: is the architecture sized appropriately for the performance requirements? For most portal use cases, LWR is the right fit without the overhead of a full custom frontend.

- **Operational Excellence** — LWR introduces a publish-gated change model that Aura does not have. This changes operational runbooks: every deployment must include a Publish step, and teams must monitor publish status. Headless sites introduce an entirely separate deployment pipeline and hosting infrastructure. Operational Excellence alignment requires that the chosen architecture's operational model is documented, practiced, and supported by the team's tooling — not assumed to behave like the previous architecture.

- **Security** — Each tier has a distinct security model. Aura uses Locker Service (runtime DOM sandboxing). LWR uses Lightning Web Security (module-level namespace isolation) — these are not equivalent and some code that is Locker-compliant is not LWS-compliant. Headless exposes Salesforce APIs directly to external clients; the entire access control model must be explicit (Connected App scopes, Apex `with sharing`, record-level security). There is no Experience Builder security configuration to fall back on in a headless architecture.

- **Reliability** — LWR sites have a dependency on CDN availability for the static layer. This is generally more reliable than Aura (edge nodes are geographically redundant) but introduces propagation latency after publish. Headless sites introduce external hosting as a reliability dependency — the custom frontend's uptime is separate from Salesforce's uptime SLA.

- **Scalability** — LWR's static CDN layer absorbs page load traffic without hitting Salesforce compute. Only dynamic data calls hit Salesforce infrastructure. This makes LWR more scalable under traffic spikes than Aura, where every page load involves Salesforce rendering. Headless gives the most control over scalability at the frontend layer but does not reduce Salesforce API call volume, which remains the scalability constraint.

## Architectural Tradeoffs

**LWR vs Aura (migration):** The performance and feature benefits of LWR are real and compounding — Aura is in maintenance mode and new Experience Cloud capabilities are LWR-only. However, the migration cost is front-loaded: every Aura component must be rewritten as LWC, and every third-party library must be tested for LWS compatibility. The tradeoff is upfront rewrite investment vs. compounding maintenance debt on Aura. For most organizations with moderate Aura customization, LWR migration is the right long-term decision.

**LWR vs Headless:** LWR keeps the Experience Builder visual tooling, standard component library, and declarative admin workflows. Headless trades all of that for complete UI freedom. The correct tradeoff question is: "Can the required UX be delivered within Experience Builder's layout and component model?" If yes, LWR is faster and cheaper. If no (native mobile, non-standard navigation, design system that cannot be approximated with SLDS), headless is warranted.

**Development cost gradient:** Aura < LWR < Headless in terms of ongoing maintenance burden for a Salesforce-skilled team. The gradient reverses for a full-stack web team with no Salesforce experience — headless lets them stay in their stack, while LWR or Aura requires learning the Salesforce component model.

## Anti-Patterns

1. **Choosing headless for performance alone** — Headless is not meaningfully faster than LWR for standard portal workloads. LWR's CDN-cached static layer closes most of the performance gap. Choosing headless purely for performance, without a genuine UX constraint that LWR cannot satisfy, introduces substantial engineering cost for marginal gain.

2. **Migrating to LWR without auditing Aura components first** — Committing to an LWR migration timeline without a complete inventory of Aura components and their LWS library dependencies is the most common cause of overrun and abandoned LWR migrations. The component audit is not optional — it is the primary input to effort estimation.

3. **Treating headless as equivalent to an Experience Cloud site for governance** — Headless frontends do not inherit Experience Cloud sharing rules, audience targeting, or guest user profile controls. Treating them as if they do leads to access control gaps. Every headless endpoint must enforce security explicitly at the API layer.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- LWR Sites for Experience Cloud (Salesforce Developer Docs) — https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/lwr_intro.htm
- LWR Template Limitations (Salesforce Developer Docs) — https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/lwr_limitations.htm
- Differences in Behavior in LWR Sites (Salesforce Developer Docs) — https://developer.salesforce.com/docs/atlas.en-us.exp_cloud_lwr.meta/exp_cloud_lwr/lwr_differences.htm
- Salesforce Developer Blog — Faster Sites with OmniStudio and LWR — https://developer.salesforce.com/blogs/2022/06/faster-sites-with-omnistudio-and-lwr
