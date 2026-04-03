# Well-Architected Notes - Sosl Search Patterns

## Relevant Pillars

- **Performance** - search should return useful results quickly without recreating cross-object search in many SOQL queries.
- **User Experience** - search experiences should feel relevant, grouped, and bounded.

## Architectural Tradeoffs

- **SOSL vs SOQL:** discovery versus structured retrieval.
- **Static SOSL vs dynamic `Search.query`:** safer composition versus more flexible but riskier query text.
- **Broad object search vs focused object search:** convenience versus predictability.

## Anti-Patterns

1. **Cross-object LIKE fan-out** - a poor substitute for SOSL.
2. **Unsafe dynamic search strings** - avoidable injection risk.
3. **Search UI with no result discipline** - technically correct but unusable.

## Official Sources Used

- SOQL and SOSL Reference SOSL - https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_sosl.htm
- Apex Developer Guide SOSL - https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOSL.htm
- Search Manager Overview - https://help.salesforce.com/s/articleView?id=sf.search_manager_overview.htm&type=5
