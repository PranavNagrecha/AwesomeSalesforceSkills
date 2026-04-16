# Revenue Lifecycle Management — Work Template

## Scope

**Skill:** `revenue-lifecycle-management`

**Request summary:** (fill in: DRO design, billing schedule creation, amendment, or invoice management)

## Product Confirmation

- **Product type:** [ ] Native RLM (Revenue Cloud, standard objects)  [ ] CPQ + Salesforce Billing (blng__*)
- **Confirmed by:** [ ] Setup > Revenue Cloud features present  [ ] No Salesforce Billing package installed

## DRO Fulfillment Plan Design

- **Plan name:**
- **Swimlanes:**
  | Swimlane | Steps | Dependencies |
  |---|---|---|
  | Billing | | |
  | Provisioning | | |
  | Communications | | |
- **Milestone synchronization points:**
- **Auto-task idempotency confirmed:** [ ] Yes — safe to re-execute on failure

## Billing Schedule Creation

- **Method:** Connect API POST (not DML, not auto-created)
- **Trigger:** [ ] DRO Auto-Task  [ ] Apex callout  [ ] Flow
- **OrderItem IDs to schedule:**
- **Billing frequency:** [ ] Monthly  [ ] Quarterly  [ ] Annual
- **Number of periods:**

## Amendment Handling

- **Amendment creates NEW BillingSchedule:** [ ] Understood
- **Aggregation query needed for total billing:** [ ] Yes — aggregate all records per asset

## Checklist

- [ ] Product confirmed as native RLM (no blng__* objects)
- [ ] DRO Fulfillment Plan designed with appropriate swimlanes
- [ ] Billing schedules created via Connect API POST (not auto-created)
- [ ] Amendment billing creates new BillingSchedule — aggregation needed
- [ ] FinanceTransaction accessed read-only — no DML
- [ ] DRO stall monitoring and runbook documented

## Notes

(Record DRO design decisions, amendment reconciliation approach)
