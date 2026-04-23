# Well-Architected Notes — IP Cacheable Patterns

## Relevant Pillars

- **Performance** — cache is the shortest path to IP latency wins.
- **Scalability** — callout budgets and SOQL counts drop linearly with
  hit ratio.
- **Reliability** — well-designed fallback prevents cache outage from
  breaking the IP.

## Architectural Tradeoffs

- **TTL vs invalidation:** short TTL is safe but leaves cache value on
  the table; long TTL needs explicit invalidation infra.
- **Org-wide vs session:** org-wide maximizes reuse; session isolates.
- **Hash key vs readable key:** hashing is compact but blocks prefix
  purge; readable keys enable invalidation patterns.

## Official Sources Used

- OmniStudio Caching — https://help.salesforce.com/s/articleView?id=sf.os_use_platform_cache_to_improve_integration_procedure_performance.htm
- Platform Cache — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_cache_namespace_overview.htm
- Well-Architected Performant — https://architect.salesforce.com/docs/architect/well-architected/performant/performant
