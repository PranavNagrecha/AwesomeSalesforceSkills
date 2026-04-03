# Well-Architected Notes - List Views And Compact Layouts

## Relevant Pillars

### User Experience

These features directly affect how quickly users recognize records, pick the next item to work, and trust what they are seeing on desktop and mobile.

### Operational Excellence

List-view governance matters operationally. Without ownership and review, every object turns into a cluttered set of duplicate queues that are expensive to support.

### Reliability

Reliable work routing is not only about automation. If the browse surface is noisy or misleading, users process the wrong records or miss urgent ones.

## Architectural Tradeoffs

- **Fewer governed views vs user freedom:** Unlimited shared views feel flexible, but they increase clutter and inconsistency.
- **More highlight fields vs scan speed:** Adding information seems helpful until the highlights panel stops functioning as a fast recognition layer.
- **One generic setup vs persona-specific tuning:** Generic browse surfaces are cheaper to administer, but they often fail the real workflow.

## Anti-Patterns

1. **Public list-view sprawl** - too many near-duplicate views make the object harder to navigate than the records themselves.
2. **Overloaded compact layouts** - treating the highlights panel like a mini page layout destroys scanability.
3. **Trying to solve search and browse with the same configuration** - each surface serves a different user question and needs separate tuning.

## Official Sources Used

- Compact Layouts (Help) - https://help.salesforce.com/s/articleView?id=sf.compact_layout_overview.htm&type=5
- List Views (Help) - https://help.salesforce.com/s/articleView?id=sf.customviews.htm&type=5
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
