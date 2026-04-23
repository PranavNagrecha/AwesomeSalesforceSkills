# Well-Architected Notes — OmniStudio vs Flow Decision

## Relevant Pillars

- **Operational Excellence** — matching tool to owning team keeps iteration cost low.
- **Reliability** — each tool has known failure modes; mixing tools adds contract complexity.
- **Performance** — tool choice shapes per-transaction cost and governor exposure.

## Architectural Tradeoffs

- **OmniStudio power vs ops cost:** OmniStudio handles complex guided UX but ships through DataPacks; core Salesforce ops teams pay a learning tax.
- **Flow simplicity vs ceiling:** Flow is fast to build and ship but hits expressive-ness limits on complex branching or multi-step external orchestration.
- **Managed vs custom:** Industry Cloud ships managed OmniStudio assets — customizing them has long-term override-vs-upgrade cost.

## Anti-Patterns

1. Defaulting to "OmniStudio everywhere" on Industry Cloud orgs without per-layer analysis.
2. Defaulting to Flow for multi-callout journeys that an IP would handle more cleanly.
3. Replacing Lightning Record Pages with FlexCards for "consistency."

## Official Sources Used

- OmniStudio overview — https://help.salesforce.com/s/articleView?id=sf.omnistudio.htm
- Flow Builder overview — https://help.salesforce.com/s/articleView?id=sf.flow.htm
- Salesforce Architects — automation selection — https://architect.salesforce.com/decision-guides
- Salesforce Well-Architected Operational Excellence — https://architect.salesforce.com/docs/architect/well-architected/trusted/operations
