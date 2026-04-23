# Well-Architected — Get Records

## Relevant Pillars

- **Performance Efficiency** — one bulk query with tight filters and
  trimmed fields is 10-100× the cost of N loop queries.
- **Reliability** — explicit limits avoid the 50k default that produces
  sporadic LDV failures.

## Architectural Tradeoffs

- **Query vs in-memory filter:** narrower SOQL is cheaper, but a wider
  SOQL plus in-memory filter can reuse a single query across multiple
  downstream decisions. Benchmark at realistic volume.
- **Flow Get Records vs Apex Selector:** Apex gives full control and
  caching; Flow is declarative. For hot paths with complex joins, Apex
  wins.
- **Re-query vs collection cache:** caching is faster but the cache
  can go stale across Pauses. Re-query if the cache age is a risk.

## Hygiene

- No Get Records inside a Loop.
- Every Get Records has an explicit limit and specific fields.
- First filter field on high-volume queries is indexed.
- Per-flow SOQL-count target documented.

## Official Sources Used

- Get Records —
  https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_data_get.htm
- LDV Best Practices —
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/
