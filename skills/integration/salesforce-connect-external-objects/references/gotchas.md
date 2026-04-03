# Gotchas - Salesforce Connect External Objects

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: External Availability Becomes Salesforce Availability

**What happens:** Users think Salesforce is slow or broken, but the external system is the real bottleneck.

**When it occurs:** Page designs issue repeated or broad queries against external data.

**How to avoid:** Treat latency budgets and external uptime as first-class architecture inputs.

---

## Gotcha 2: Native Feature Assumptions Break Late

**What happens:** Reporting, automation, or data-shaping assumptions fail after stakeholders already expect native behavior.

**When it occurs:** Teams hear "object" and assume full parity with local Salesforce objects.

**How to avoid:** Validate feature fit against External Object behavior before building user expectations.

---

## Gotcha 3: Custom Adapter Work Grows Quietly

**What happens:** The project chooses a custom adapter because it is possible and discovers it has created a long-term integration product.

**When it occurs:** The external source does not support a standard protocol.

**How to avoid:** Choose a custom adapter only with explicit ownership and support commitment.
