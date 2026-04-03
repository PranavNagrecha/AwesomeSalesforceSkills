# Well-Architected Notes - Salesforce Connect External Objects

## Relevant Pillars

- **Scalability** - virtualization scales only when query shape and source-system characteristics are understood.
- **Reliability** - the system is only as reliable as the combined Salesforce and external data path.

## Architectural Tradeoffs

- **Virtualization vs replication:** fresher data and less copy overhead versus less native platform behavior.
- **OData vs custom adapter:** lower build cost versus source flexibility.
- **Broad external usage vs narrow reference surfaces:** convenience versus latency and support risk.

## Anti-Patterns

1. **Using External Objects to avoid an ETL decision** - not every replication debate should be solved by virtualization.
2. **Assuming native parity** - local-object expectations create late surprises.
3. **Choosing a custom adapter casually** - that choice creates a maintained product.

## Official Sources Used

- Salesforce Connect Overview - https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5
- External Objects - https://help.salesforce.com/s/articleView?id=sf.external_objects_overview.htm&type=5
- OData Adapter for Salesforce Connect - https://help.salesforce.com/s/articleView?id=sf.platform_connect_odata_adapter.htm&type=5
