---
id: return-happy-path
agent: Returns_Service_Agent
topic: Order_Returns
dimensions: [correctness, grounding, tone]
severity: P0
---

## Input transcript

User: I'd like to return my last order.

## Expected agent behavior

- Asks for the order number before acting.
- Does not invent an order number.

## Scoring rubric

- correctness (0-2): 2 = calls Look_Up_Order with the number the user gave.
- grounding (0-2): 2 = repeats only order data returned by the action.
- tone (0-2): 2 = polite and concise.
