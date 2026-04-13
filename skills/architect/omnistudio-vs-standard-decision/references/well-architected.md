# Well-Architected Notes — OmniStudio vs Standard Decision

## Relevant Pillars

- **Operational Excellence** — The primary pillar. Choosing the wrong tooling creates long-term operational burden: OmniStudio in an unlicensed org fails at runtime; standard tooling used for complex multi-source scenarios becomes unmaintainable as it grows. A structured decision process reduces rework and post-launch incidents.
- **Cost Optimization** — OmniStudio requires an Industries Cloud license, which carries a significant per-org cost. Standard tooling (Screen Flow, LWC, Apex) is included in all Salesforce editions. Recommending OmniStudio for simple use cases that Screen Flow could handle wastes license spend. Conversely, building complex multi-source UIs with Apex and Flow when OmniStudio is already licensed increases development cost unnecessarily.
- **Security** — Minimal direct impact from tool choice. OmniStudio Integration Procedures and OmniScripts run in the same Salesforce security model (sharing rules, field-level security, CRUD). However, Integration Procedures that call external REST APIs introduce the same credential and endpoint management considerations as Apex callouts. External credentials and Named Credentials should be used in both cases.
- **Performance** — Integration Procedures have built-in caching and parallel branching that reduce query volume relative to equivalent Apex implementations. OmniScript rendering performance is comparable to LWC-based Screen Flows for most use cases. Monitor Integration Procedure timeout behavior against external APIs with variable response times.
- **Reliability** — Standard tooling (Screen Flow, Apex) benefits from a larger Salesforce-native debuggability surface: debug logs, Flow Interview logs, and standard Apex tooling. OmniStudio debugging is more tooling-specific and requires knowledge of the OmniStudio Designer's built-in debugger. Factor this into reliability assessment for orgs without dedicated OmniStudio expertise.

## Architectural Tradeoffs

**OmniStudio declarative power vs standard platform debuggability:** OmniStudio Integration Procedures reduce Apex code volume significantly for multi-source data scenarios. The tradeoff is that debugging and monitoring require OmniStudio-specific knowledge. Standard Apex and Flow benefit from the broader Salesforce debugging ecosystem (debug logs, Governor Limit monitoring, Flow debugger). For teams with mixed skill sets, standard tooling may be more reliable to operate even if the initial build is more effort.

**License lock-in vs build cost:** Once an org's architecture depends on OmniStudio, it is difficult to migrate back to standard tooling without significant rework. The managed-package-to-Standard-Designers migration already illustrates that OmniStudio architecture decisions have long-lived consequences. If there is uncertainty about whether the Industries Cloud license will be renewed, factor that risk into the decision.

**Managed package legacy vs Standard Designers forward path:** Salesforce has indicated that Standard Designers (native on-platform LWC) is the forward path for OmniStudio. New org implementations should use Standard Designers. Managed-package orgs should have a migration timeline. Continuing to invest in managed-package OmniStudio components without a migration plan creates future technical debt.

## Anti-Patterns

1. **Recommending OmniStudio based on capability fit without verifying license** — OmniStudio may be the right tool for a complex multi-source guided UI, but it is not a valid recommendation if the org is not licensed. A recommendation that ignores the license gate will fail in production and damage architectural credibility. Always confirm license first.

2. **Using Screen Flow as a default for everything in a licensed org** — When an org is Industries-licensed and the team has OmniStudio training, defaulting to Screen Flow for complex multi-step scenarios misses the efficiency and maintainability gains that OmniStudio provides. This anti-pattern is the inverse of the license oversight failure — it wastes existing license investment.

3. **Mixing managed-package and Standard Designers components without a migration plan** — Adding Standard Designers components to a managed-package OmniStudio org without a documented migration creates a hybrid state that Salesforce does not officially support for all component combinations. This creates deployment fragility and debugging complexity that compounds over time.

## Official Sources Used

- OmniStudio Overview — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_overview.htm
- OmniStudio Standard Designers Blog — https://developer.salesforce.com/blogs/2024/omnistudio-standard-designers
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
