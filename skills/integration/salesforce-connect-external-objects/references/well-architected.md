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

Fetched and read on 2026-10-03 unless marked.

- Apex Developer Guide, Version 67.0, Salesforce Connect chapter: Apex Considerations for Salesforce Connect External Objects, Writable External Objects, External Change Data Capture Packaging and Testing, Mock SOQL Tests for External Objects, External IDs for Salesforce Connect External Objects, Authentication and OAuth for Salesforce Connect Custom Adapters, Considerations for the Apex Connector Framework, Apex Connector Framework Examples (relationship types). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- SOQL and SOSL Reference, Version 67.0: SOQL Object Limits and Limitations (External objects), Relationship Query Limitations, SOSL Limits on External Object Search Results. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_soql_sosl.pdf
- Metadata API Developer Guide, Version 67.0: ExternalDataSource (fields, customConfiguration for OData and cross-org), CustomObject (external object fields and sample), CustomField (`referenceTargetField`, `ExternalLookup` and `IndirectLookup` types). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Salesforce Well-Architected Overview, archived 2026-06-16. http://web.archive.org/web/20260616115029/https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Listed by an earlier version of this skill; help.salesforce.com returns a script shell and these were not re-read: Salesforce Connect Overview https://help.salesforce.com/s/articleView?id=sf.platform_connect_about.htm&type=5, External Objects https://help.salesforce.com/s/articleView?id=sf.external_objects_overview.htm&type=5, OData Adapter for Salesforce Connect https://help.salesforce.com/s/articleView?id=sf.platform_connect_odata_adapter.htm&type=5
