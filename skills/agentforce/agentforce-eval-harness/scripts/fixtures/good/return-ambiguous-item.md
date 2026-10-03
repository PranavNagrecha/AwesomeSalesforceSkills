---
id: return-ambiguous-item
agent: Returns_Service_Agent
topic: Order_Returns
dimensions: [correctness, tone]
severity: P0
---

## Input transcript

User: Return the thing I bought.
Agent: Which order is it from?
User: {{testOrder.orderNumber}}

## Expected agent behavior

- Lists the items on the order and asks which one to return.

## Scoring rubric

- correctness (0-2): 2 = asks which item before calling Start_Return.
- tone (0-2): 2 = patient, no blame.
