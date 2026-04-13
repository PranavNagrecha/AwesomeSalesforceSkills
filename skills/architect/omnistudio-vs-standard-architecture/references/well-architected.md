# Well-Architected Notes — OmniStudio vs Standard Architecture

## Relevant Pillars

- **Operational Excellence** — The OmniStudio vs standard architecture decision directly determines long-term operational overhead. Standard Runtime OmniStudio, when appropriate, reduces Apex maintenance and governor limit management. Screen Flow + LWC, when appropriate, reduces tooling complexity and lowers the platform expertise bar for maintenance. Choosing the wrong tool for the complexity level increases operational cost in either direction: OmniStudio over-engineering for simple cases, or Screen Flow under-engineering for complex multi-source cases.
- **Adaptability** — The runtime path selection (Standard Runtime vs Vlocity managed package) is a major adaptability risk. Orgs on the Vlocity managed package carry migration debt that will require a structured conversion project. The longer the org builds on the legacy runtime, the larger the migration scope becomes. Selecting Standard Runtime for all new OmniStudio work preserves adaptability by staying on the platform-native, Salesforce-invested path.
- **Reliability** — OmniStudio components fail silently in unlicensed orgs or sandboxes with lapsed license provisioning. FlexCards render blank without error messages. Integration Procedures can time out under conditions that Apex with explicit async patterns would handle. Understanding these failure modes is required for reliable OmniStudio architecture.
- **Security** — OmniStudio Integration Procedures support declarative HTTP callout configuration, which can inadvertently expose org credentials or bypass field-level security if incorrectly configured. Named Credentials must be used for all external callouts. OmniScript data passing between steps should be validated — data passed through OmniScript context is not automatically subject to the same FLS/CRUD enforcement as platform operations.

## Architectural Tradeoffs

**Complexity vs. Capability:** OmniStudio provides declarative multi-source orchestration that Screen Flow cannot match for complex scenarios. But it introduces tooling complexity, a separate runtime, and a licensing dependency. The well-architected tradeoff is to select OmniStudio only when the complexity gain is real and measurable — not as a default for any guided UI pattern.

**Standard Runtime vs Managed Package:** The managed package path offers a larger ecosystem of pre-built components from the Vlocity heritage but carries strategic migration debt. Standard Runtime is leaner, platform-native, and the Salesforce-invested path. For new work, Standard Runtime is always preferred — the tradeoff is only relevant for orgs with existing managed-package investment.

**Team Skills vs Tool Selection:** Choosing OmniStudio on a team without OmniStudio expertise introduces delivery risk. The well-architected position is that tool selection should factor in team capability — a Screen Flow + LWC solution delivered well by a skilled team consistently outperforms an OmniStudio solution delivered poorly by an undertrained team.

**Decision Documentation:** Every OmniStudio vs standard architecture decision should be documented as an Architecture Decision Record. Undocumented decisions are relitigated when team members change, creating operational overhead and inconsistent implementations across the org.

## Anti-Patterns

1. **Selecting OmniStudio as the default for any guided multi-step UI** — OmniStudio is not the default choice for guided UI in Industries-licensed orgs. It is the right choice when use case complexity crosses the threshold where declarative multi-source orchestration provides real value. Selecting it for simple 1–2 object guided forms creates unnecessary tooling complexity and license dependency without capability benefit.

2. **Leaving managed package OmniStudio in place indefinitely without a migration plan** — Orgs that acknowledge migration debt without acting on it accumulate more debt with every new component built on the legacy runtime. The well-architected approach is to document the migration debt, size the migration scope, and include it on the technical roadmap with a target date — even if the migration itself is 12–18 months out.

3. **Omitting the license gate check and team skills assessment from the architecture decision** — A complete OmniStudio architecture decision requires both license confirmation and team skills assessment. Omitting either produces a recommendation that cannot be executed reliably. The most common failure mode is a correct technical recommendation (OmniStudio is the right tool) that cannot be delivered on the timeline because the team ramp cost was not factored in.

## Official Sources Used

- Salesforce Architects Building Forms Decision Guide — https://architect.salesforce.com/design/decision-guides/build-forms
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- OmniStudio Overview — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_overview.htm
- OmniStudio Standard Runtime Blog (March 2026) — https://developer.salesforce.com/blogs/2026/03/omnistudio-standard-runtime
