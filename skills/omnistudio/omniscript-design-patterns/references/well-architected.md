# Well-Architected Notes — OmniScript Design Patterns

## Relevant Pillars

### User Experience

OmniScript lives at the interaction layer, so step clarity, branching discipline, and save/resume behavior directly shape the user experience.

### Operational Excellence

The script must stay supportable. Thin guided flows, predictable branching, and clear delegation to backend services keep operations manageable.

### Reliability

Long guided journeys fail when state restoration, backend handoffs, or embedded custom components are not designed intentionally.

## Architectural Tradeoffs

- **Rich guided experience vs script complexity:** OmniScript is powerful for user journeys, but too much logic in the script harms maintainability.
- **Branch flexibility vs testability:** More branches can improve personalization, but they quickly raise the support and regression burden.
- **Custom components vs standard OmniStudio elements:** Custom LWCs unlock flexibility while adding more contracts and failure modes.

## Anti-Patterns

1. **Using OmniScript as the full integration and transformation layer** — backend-heavy logic should move behind the script.
2. **Excessive step counts with weak milestones** — the journey becomes harder for users and operators alike.
3. **Save/resume with no context revalidation plan** — resumed journeys can submit stale assumptions.

## Official Sources Used

- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
