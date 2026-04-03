# Well-Architected Notes — Flow Bulkification

## Relevant Pillars

### Performance

Bulkification is directly tied to Flow performance because query count, DML fan-out, and unnecessary after-save work all increase transaction cost.

### Scalability

A flow that only works for one record is not production-ready. Scalable Flow design means handling mass updates, imports, and API-driven operations without per-record amplification.

### Reliability

Poorly bulkified flows are a reliability risk because they fail unpredictably during the highest-volume business events.

## Architectural Tradeoffs

- **Declarative simplicity vs transaction efficiency:** Flow is faster to change, but high-volume logic sometimes belongs in Apex or async patterns.
- **After-save flexibility vs before-save efficiency:** After-save can update related records, but before-save is the better fit for same-record enrichment.
- **Subflow reuse vs hidden complexity:** Reuse improves maintainability, but it can hide expensive loop behavior if nobody reviews the full call chain.

## Anti-Patterns

1. **Query or DML inside a Flow loop** — the classic scale failure that turns record volume into limit usage.
2. **After-save for same-record field updates** — unnecessary DML and extra automation firing for a requirement that belongs in before-save.
3. **Leaving high-volume orchestration in Flow when Apex is the safer boundary** — maintainability suffers when declarative tooling is pushed past its fit.

## Official Sources Used

- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
