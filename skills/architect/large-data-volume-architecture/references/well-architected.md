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

- Salesforce Large Data Volumes Best Practices — https://developer.salesforce.com/docs/atlas.en-us.salesforce_large_data_volumes_bp.meta/salesforce_large_data_volumes_bp/ldv_deployments_introduction.htm (read as the PDF edition below on 2026-10-03)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (HTTP 403 on 2026-10-03; pillar framing follows `standards/well-architected-mapping.md`)
- Best Practices for Deployments with Large Data Volumes, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_large_data_volumes_bp.pdf. LDV definition, "Skinny Tables" (objects, field types, 200 columns, no cross-object fields, Full sandbox copy, Support-managed definition), "Indexes" (Support or Metadata API, platform-maintained indexes, External ID types, non-indexable field types), "Index Tables" (nulls excluded by default), "Standard and Custom Indexed Fields" (30%/15%, 10%/5%, AND 20%, OR 10%, LIKE samples 100,000), "Two-Column Custom Indexes", "Divisions" (>1M rows, >35 licences, via Support), "Defer Sharing Calculation", best-practice tables (10,000 records per owner and per parent, group by ParentId, Bulk API hard delete for 1M+, Bulk API 2.0 query for >1M results, LIMIT 100,000)
- Local corpus copy: `knowledge/imports/salesforce-large-data-volumes-best-practices.md`
- REST API Developer Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf. "Get Feedback on Query Performance (Beta)" (`explain` parameter, `leadingOperationType`, `relativeCost`) and "Record Count" (cached snapshot, exclusions)
- Metadata API Developer Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. `CustomIndex` (`allowNullValues`, `booleanIndexedValue`, Support required), `Index` (big object composite key)
- Big Objects Implementation Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/big_objects_guide.pdf. Scale (hundreds of millions to billions of rows), object and field permissions only, no triggers or flows
- Apex Developer Guide, Summer '26 (PDF): https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf. "Execution Governors and Limits" (120-second SOQL run time before cancellation)
