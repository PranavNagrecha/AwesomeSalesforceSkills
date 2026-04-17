# Gotchas — Agent Deployment Checklist

## Gotcha 1: Staging differs from prod

**What happens:** Rehearsal green, prod rollback fails.

**When it occurs:** Sandbox data not representative.

**How to avoid:** Rehearse in Full or Partial sandbox refreshed within 14 days.


---

## Gotcha 2: Alert rules not enabled until after go-live

**What happens:** First incident is observed by a customer.

**When it occurs:** Monitoring set up 'once we see traffic'.

**How to avoid:** Alert rules live before activation; validated with synthetic traffic.


---

## Gotcha 3: Sign-off via Slack, no record

**What happens:** Post-mortem cannot reconstruct the decision chain.

**When it occurs:** Approvals over chat.

**How to avoid:** Always use the `Agent_Activation__c` record as the system of record.

