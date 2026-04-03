# Well-Architected Notes - Custom Metadata In Apex

## Relevant Pillars

- **Reliability** - configuration should be versioned, predictable, and not depend on accidental org state.
- **Operational Excellence** - teams should know where config is read, how it is promoted, and who owns changes.

## Architectural Tradeoffs

- **CMT vs Custom Settings:** deployable versioned configuration versus older runtime-oriented patterns.
- **Direct queries vs reader service:** faster initial coding versus clearer ownership and testability.
- **Subscriber freedom vs package protection:** easier local edits versus stronger publisher control.

## Anti-Patterns

1. **Treating `__mdt` like ordinary `__c` data** - the read/write model is different.
2. **Hidden org-metadata dependency in tests** - green tests with brittle assumptions.
3. **Using labels for structured configuration** - text storage is not rule architecture.

## Official Sources Used

- Apex Developer Guide - https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide - https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
