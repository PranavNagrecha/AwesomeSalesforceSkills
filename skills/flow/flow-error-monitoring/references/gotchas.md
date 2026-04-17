# Gotchas — Flow Error Monitoring

## Gotcha 1: Default fault emails go to the flow's created-by user

Unless overridden, all flow errors email the person who built the flow. Ex-employees' inboxes collect errors forever. Fix: set org-wide alternative via Process Automation Settings.

---

## Gotcha 2: FlowInterviewLog retention is 14 days by default

Runtime error reports based on FlowInterviewLog only show recent data. Long-term trend analysis requires copying to a custom object or external warehouse.

---

## Gotcha 3: Fault-path Create Records can itself fault

If Integration_Log__c has a required field the flow doesn't populate, the log write fails silently. Fix: keep log-object schema minimal; Required fields only where truly needed.

---

## Gotcha 4: Publishing Platform Events from the log consumes DML

Every log record + event publish adds to the transaction's DML count. In high-error scenarios, this can push the transaction over limits.

Fix: batch-publish events via a scheduled job that reads unsent Integration_Log__c records, not inline.

---

## Gotcha 5: Dashboard refresh lag

Native dashboards refresh on a schedule (typically hourly). P0 alerting can't depend on dashboards; use email alerts triggered by Integration_Log__c inserts.

---

## Gotcha 6: Fault paths in autolaunched subflows don't always route to parent

Depending on how the subflow is invoked, a fault in a subflow may bubble up to the parent's next element instead of the parent's fault path. Test the specific combination you're using.

---

## Gotcha 7: Email alert floods on batch failures

A bulk save of 200 records that hits a flow fault sends 200 emails. Fix: alerting logic should aggregate — "3+ failures in 5 minutes" not "each failure".
