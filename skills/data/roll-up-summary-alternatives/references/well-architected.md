# Well-Architected Notes: Roll Up Summary Alternatives

## Relevant Pillars

- **Performance**: summary logic can create hot parents, repeated aggregates, and parent save procedures on every child edit. Write only parents whose total changed.
- **Reliability**: totals must stay correct through edits, deletes, undeletes, merges, cascaded deletes, and bulk loads. A scheduled recompute is the safety net for paths triggers never see.

## Architectural Tradeoffs

- **Native summary vs custom logic:** less flexibility versus platform-managed recalculation.
- **Flow vs Apex:** declarative ownership versus full event coverage (Flow has no after-delete or undelete trigger).
- **Incremental updates vs recompute from source:** lighter transactions versus correctness after missed events.

## Anti-Patterns

1. **Per-record aggregate recalculation**: scales badly.
2. **Ignoring parent-lock concentration**: totals become a concurrency problem.
3. **No repair job**: drift from merges and cascaded deletes is guaranteed.

## Official Sources Used

- Apex Developer Guide, Summer '26 (262): "Triggers and Order of Execution" (steps 16 and 17), "Operations That Don't Invoke Triggers," "Triggers and Merge Statements," "Triggers and Recovered Records," "Working with SOQL Aggregate Functions" (query-row note), trigger considerations for opportunity products. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide, Summer '26 (262): CustomField summary properties (`summarizedField`, `summaryFilterItems`, `summaryForeignKey`, `summaryOperation`), Flow `triggerType` and `recordTriggerType` values, deploy note on purging roll-up summary fields. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Best Practices for Deployments with Large Data Volumes, Summer '26 (262): "Minimizing parent record-locking conflicts," data skew case study. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_large_data_volumes_bp.pdf
- DLRS repository README (SFDO-Community, BSD-3-Clause; fetched 2026-10-03 through the GitHub API): https://github.com/SFDO-Community/declarative-lookup-rollup-summaries
- DLRS documentation home (operations list; fetched 2026-10-03): https://sfdo-community-sprints.github.io/DLRS-Documentation/

### Earlier references kept from version 1.0.1 (checked 2026-10-03: atlas pages return a script shell, help.salesforce.com returns an app shell, and Well-Architected guide pages redirect to the home page, so no claim in this skill rests on these links)

- Salesforce Help, Roll-Up Summary Fields: https://help.salesforce.com/s/articleView?id=sf.fields_about_roll_up_summary.htm&type=5 (help.salesforce.com does not return article text to a fetch)
- Apex Developer Guide, Aggregate SOQL (atlas page; the 262 PDF above was read instead): https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_agg_fns.htm
- Salesforce Help, Record-Triggered Flow: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm&type=5 (same limitation)
