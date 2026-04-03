# Well-Architected Notes - Roll Up Summary Alternatives

## Relevant Pillars

- **Performance** - summary logic can create hot parents, repeated aggregates, and avoidable recalculation load.
- **Reliability** - totals must stay correct through ordinary edits and exceptional bulk events.

## Architectural Tradeoffs

- **Native summary vs custom logic:** less flexibility versus much lower maintenance.
- **Flow vs Apex:** declarative ownership versus stronger control at higher volume.
- **Incremental updates vs full recompute:** lighter transactions versus more correctness risk.

## Anti-Patterns

1. **Per-record aggregate recalculation** - scales badly.
2. **Ignoring parent-lock concentration** - totals become a concurrency problem.
3. **No re-sync story** - eventual drift is guaranteed and unrecoverable.

## Official Sources Used

- Roll-Up Summary Fields - https://help.salesforce.com/s/articleView?id=sf.fields_about_roll_up_summary.htm&type=5
- Apex Developer Guide Aggregate SOQL - https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/langCon_apex_SOQL_agg_fns.htm
- Record-Triggered Flow - https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm&type=5
