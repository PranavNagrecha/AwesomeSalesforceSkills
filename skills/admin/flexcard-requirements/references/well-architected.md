# Well-Architected Notes — FlexCard Requirements

## Relevant Pillars

- **Reliability** — Documented build dependencies (child card activation order, IP active status, LWC deployment) prevent activation failures in production; without requirements-time dependency mapping, deployment outages are predictable.
- **Operational Excellence** — FlexCard requirements documents serve as the canonical reference for future card maintenance; state template conditions and data source bindings are opaque inside Card Designer without external documentation.
- **Security** — Requirements must capture user context (internal agent vs Experience Cloud community user); guest-user FlexCards require explicit object sharing settings and FLS that must be specified at requirements time.
- **Performance** — Choosing Integration Procedure vs SOQL vs DataRaptor data source is a performance decision; IP with sequential actions adds latency; SOQL with a narrow WHERE clause is fastest for single-object display.
- **Scalability** — FlexCards embedded in list views should specify data source queries with LIMIT clauses; requirements that leave query scope undefined risk loading hundreds of records into a card panel.

## Architectural Tradeoffs

**Flat FlexCard vs Nested FlexCard Architecture:** A single FlexCard with all data from one IP is simpler to deploy and maintain. A parent-child FlexCard architecture allows reuse of child cards across multiple parent cards but creates activation dependencies. Requirements should recommend nested architecture only when child card reuse is a genuine requirement — not by default.

**SOQL vs Integration Procedure Data Source:** SOQL is the simplest choice for single-object display and should be the default unless multi-object aggregation or external API data is required. Using an Integration Procedure for data that SOQL could serve adds unnecessary latency and an extra component to maintain.

**OmniScript Launch in Modal vs Inline:** For guided processes launched from a FlexCard action, modal OmniScript launch preserves the card context and is appropriate for short flows. Inline OmniScript launch replaces the card content and is appropriate for longer flows. Requirements should specify which model is appropriate.

## Anti-Patterns

1. **Unspecified data source type** — Requirements that list fields without specifying whether they come from SOQL, DataRaptor, IP, or Apex force the developer to make architectural choices mid-build. SOQL defaults cause silent blank fields for IP-required data. All data source types must be specified at requirements time.

2. **Missing card state specification** — Requirements that describe "different views based on status" without enumerating the states, their condition expressions, and their layout differences lead to mid-project state additions requiring reactivation during business hours.

3. **No build dependency order** — Requirements that include child FlexCards, Integration Procedures, or custom LWC components without noting activation/deployment dependencies lead to blocked deployments.

## Official Sources Used

- OmniStudio FlexCards — https://help.salesforce.com/s/articleView?id=sf.os_flexcards.htm
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `omnistudio/flexcard-design-patterns` — implementation skill to use after requirements are complete
- `admin/omniscript-flow-design-requirements` — companion BA requirements skill for OmniScripts launched from FlexCard actions
- `omnistudio/integration-procedures` — use when requirements specify IP as a data source
