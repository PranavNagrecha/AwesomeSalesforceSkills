# Well-Architected Notes — DataRaptor Transform Optimization

## Relevant Pillars

- **Performance** — evaluator choice and bulk mode dominate runtime; formula-first gives the best return per refactor minute.
- **Reliability** — fewer chained transforms means fewer intermediate failure modes.
- **Operational Excellence** — consistent conventions (formula first, explicit bulk) make Transforms auditable.

## Architectural Tradeoffs

- **Formula vs Apex:** formula is faster and limit-free but less expressive; Apex is more powerful but has per-row cost.
- **Bulk vs row-by-row:** bulk is almost always faster for array inputs; row-by-row is occasionally needed for per-row side effects.
- **Many small Transforms vs one big Transform:** many reads as modular but costs intermediate materialization; fewer-but-bigger is faster at a small readability cost.

## Anti-Patterns

1. Defaulting to Apex for trivial string and arithmetic logic.
2. Leaving row-by-row mode on array-input Transforms.
3. Treating Transforms as free "shape the JSON" steps when they can dominate runtime.

## Official Sources Used

- OmniStudio DataRaptor Guide — https://help.salesforce.com/s/articleView?id=sf.os_dataraptor.htm
- OmniStudio Performance Considerations — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_performance.htm
- Salesforce Well-Architected Performance — https://architect.salesforce.com/docs/architect/well-architected/trusted/performant
