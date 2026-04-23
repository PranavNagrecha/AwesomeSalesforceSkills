# Shield Event Retention Matrix

## Events And Tiers

| Event Type | Value Tier | Hot Retention | Warm Retention | Cold Retention | Storage |
|---|---|---|---|---|---|
| Login |   |   |   |   |   |
| LoginAs |   |   |   |   |   |
| RestApi |   |   |   |   |   |
| ApexExecution |   |   |   |   |   |
| ReportExport |   |   |   |   |   |
| URI |   |   |   |   |   |
| LightningInteraction |   |   |   |   |   |

## Regulatory Mapping

| Rule | Applicable Events | Minimum Retention |
|---|---|---|
|   |   |   |

## Routing Architecture

- Hot: (SIEM / index / retention):
- Warm: (storage / retention / re-hydration cost):
- Cold: (storage / retention / legal hold?):

## Query Runbook

| Audit Question | Tier Hit First | Query | Expected Latency |
|---|---|---|---|
|   |   |   |   |

## Sign-Off

- [ ] Regulatory minimums met per event type.
- [ ] Cost model attached.
- [ ] Query runbook tested against a real question.
- [ ] Pipeline monitored for missing hourly intervals.
