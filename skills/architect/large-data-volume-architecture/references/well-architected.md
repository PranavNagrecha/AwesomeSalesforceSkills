# Well-Architected Notes — Large Data Volume Architecture

## Relevant Pillars

- **Performance** — LDV work is dominated by query path cost, sharing recomputation, and bulk throughput. Choices must be justified with measured distributions, not assumptions.
- **Scalability** — Indexes, skinny tables, archival, and ownership models determine whether the same design holds at 5× or 10× row counts.
- **Reliability** — Loads that ignore sequencing or skew create hard-to-debug systemic slowdowns rather than isolated errors; architecture must preserve predictable recovery paths.

## Architectural Tradeoffs

Skinny tables and custom indexes improve read paths but increase platform-managed duplication or index maintenance—appropriate when evidence shows join or scan cost is the bottleneck. Big Objects trade rich platform features on rows for predictable scale. Wider org-wide defaults during migration reduce sharing cost temporarily but must be paired with a disciplined return to least privilege.

## Anti-Patterns

1. **Index-first without selectivity math** — Requesting indexes while filters still return millions of rows wastes cycles; prove thresholds first.
2. **Single integration owner forever** — Convenient for provisioning but concentrates sharing work; partition early.
3. **Keeping all history online** — Eventually breaks reporting and batch windows; define archival boundaries before crisis mode.

## Official Sources Used

- Salesforce Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
