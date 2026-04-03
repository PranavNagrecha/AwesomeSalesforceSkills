# Well-Architected Notes — Dataraptor Patterns

## Relevant Pillars

- **Performance** - choosing Turbo Extract versus Extract and keeping mappings lean affects response time directly.
- **Reliability** - clear data contracts and focused asset roles reduce brittle OmniStudio behavior.
- **Operational Excellence** - well-bounded DataRaptors are easier to version, review, and support.

## Architectural Tradeoffs

- **Turbo Extract speed vs Extract flexibility:** Turbo is attractive for performance, but it is not meant for complex mapping scenarios.
- **One large mapping asset vs several focused assets:** a single asset looks simpler initially, but focused assets are easier to maintain.
- **DataRaptor-only design vs IP or Apex boundary:** staying declarative is convenient, but orchestration and service logic often need a different home.

## Anti-Patterns

1. **Turbo Extract for a complex mapping problem** - the asset choice no longer matches the requirement.
2. **Load asset with vague input contract** - declarative writes still need disciplined design.
3. **DataRaptor sprawl as substitute for orchestration** - mapping layers become the wrong place for process logic.

## Official Sources Used

- OmniStudio Developer Guide - https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- OmniStudio Developer Guide — DataRaptors - https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/os_dataraptor_overview.htm
- Integration Patterns - https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
