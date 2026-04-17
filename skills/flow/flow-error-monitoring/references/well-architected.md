# Well-Architected Notes — Flow Error Monitoring

## Relevant Pillars

- **Reliability** — Unmonitored failures accumulate silently as data inconsistency. Monitoring makes failure visible, which is the precondition for fixing it.
- **Operational Excellence** — Ops teams can't maintain flow portfolios by reading individual fault emails. Centralized logs + dashboards are the force multiplier at scale.

## Architectural Tradeoffs

### Native Salesforce vs external observability

| Native (Reports, dashboards, Integration_Log__c) | External (Splunk, Datadog) |
|---|---|
| No extra cost | Requires subscription |
| Integrated with org data | More sophisticated alerting + trend analysis |
| Can trigger automations from log writes | Can't natively trigger Salesforce automations |

Rule: native for small orgs / inside ops teams; external for enterprises already invested in observability platforms.

### Inline alerting vs batched

| Inline (alert per failure) | Batched (alert per N failures in window) |
|---|---|
| Fastest notification | Resistant to flood-from-bulk-failure |

Rule: P0 = inline; P1/P2 = batched.

## Anti-Patterns

1. **All-flow email to one inbox** — nobody reads it. Fix: route by domain or severity.
2. **Log without severity or correlation Id** — can't filter, can't group root causes. Fix: structured schema with both fields.
3. **Dashboard refresh as P0 alerting** — dashboards are for trends, not paging. Fix: direct email/SMS alerts triggered by log inserts.
4. **Retention forever** — storage cost compounds. Fix: archive policy (Big Object at 90d, delete at 2y).
5. **PII in error messages** — compliance risk. Fix: log Id references only.

## Official Sources Used

- Salesforce Help — Troubleshoot Flows with Flow Runtime Error Reports: https://help.salesforce.com/s/articleView?id=sf.flow_troubleshoot_runtime.htm
- Salesforce Help — Set Flow Apex Exception Email: https://help.salesforce.com/s/articleView?id=sf.flow_admin_exception_email.htm
- Salesforce Developer — FlowInterviewLog: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_flowinterviewlog.htm
- Salesforce Architects — Observability: https://architect.salesforce.com/
