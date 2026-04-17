# Well-Architected Notes — Flow Migration From Trigger

## Relevant Pillars

- **Reliability** — A successful migration preserves behavior via test parity + shadow rollout. A rushed migration introduces silent regressions.
- **Operational Excellence** — Admin-maintainable automation reduces developer friction at portfolio scale, but only if migrations don't cost more in fragile transitions than they save in ongoing maintenance.
- **Performance** — Flow has per-element overhead; hot-path triggers need benchmarking before migration.

## Architectural Tradeoffs

### Full vs partial migration

| Full migration | Partial migration |
|---|---|
| Simpler mental model post-migration | Fragile during transition |
| Requires Flow to handle every branch | Can keep complex Apex branches |
| Single tech stack | Dual ownership — admin + developer |

Rule: migrate fully when every trigger branch passes the decision matrix. Migrate partially (split) when some branches require Apex capabilities.

### Shadow-mode vs direct cutover

Shadow: custom permission gates the old/new behavior; ramp gradually.

Direct: single commit; trigger off, flow on.

Rule: shadow for business-critical triggers. Direct for low-risk derivations.

## Anti-Patterns

1. **Migrating a trigger with SavePoints or recursion control** — Flow can't express these cleanly. Fix: keep Apex.

2. **Deleting Apex trigger source on day-one** — no rollback path if regression appears. Fix: retain source for 2 release cycles.

3. **No benchmark before migrating hot-path triggers** — silent perf regressions. Fix: measure CPU + SOQL before and after.

4. **Assuming Flow fault paths = Apex exception handling** — different surface, different logging. Fix: wire Integration_Log__c in the migration PR.

## Official Sources Used

- Salesforce Help — Decide Between Flow and Apex: https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger.htm
- Salesforce Developer — Trigger Order of Execution: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Salesforce Architects — Automation Modernization: https://architect.salesforce.com/
- Salesforce Help — Flow Trigger Types: https://help.salesforce.com/s/articleView?id=sf.flow_ref_triggers.htm
