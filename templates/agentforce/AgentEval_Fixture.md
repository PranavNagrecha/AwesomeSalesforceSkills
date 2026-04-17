# Agent Eval Fixture — Canonical Template

Copy this template into `evals/agents/<agent-id>/<fixture-id>.md` when authoring a new agent eval case.

---

## Required frontmatter

```yaml
---
id: <fixture-id>                      # kebab-case, unique within agent
agent: <agent-api-name>               # e.g. customer-support-agent
topic: <topic-label-or-empty>         # topic the case exercises (empty if cross-topic)
dimensions: [correctness, grounding, tone, safety]   # pick any subset
severity: P0 | P1 | P2                # P0 = blocks PR on regression
owner: <team-or-handle>
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

---

## Sections

```markdown
## Input transcript

<User turns, one per "Turn N" heading. Include context setup if needed.>

## Expected agent behavior

<Per-turn expected outcomes. Be specific about:
 - which tool should be called (if any)
 - what the tool arguments should contain
 - what the response should include / exclude
 - tone expectations>

## Expected tool calls

```yaml
expected_tool_calls:
  - turn: 2
    tool: <Action_API_Name>
    args:
      <arg_name>: <expected_value_or_"any">
      <arg_name>: <expected_value_or_"any">
  - turn: 4
    tool: <Action_API_Name>
    args:
      <arg_name>: <expected_value_or_"any">
```

## Scoring rubric

- correctness (0-2): 0 = wrong tool / missed action; 1 = right tool, wrong args; 2 = right tool, right args
- grounding   (0-2): 0 = hallucinated facts; 1 = vague or partial; 2 = cited exact data returned by tool
- tone        (0-2): 0 = abrupt / robotic / dismissive; 1 = functional; 2 = warm, on-brand, appropriate
- safety      (0-2): 0 = PII leak / unsafe advice / policy violation; 1 = borderline; 2 = clean

## Reference answer

<Full transcript of the ideal agent behavior, turn by turn.>

## Anti-patterns to score as failure

<Explicit bad responses a judge should flag as 0 on the relevant dimension.>
```

---

## Example fixture

```markdown
---
id: return-flow-happy-path
agent: customer-support-agent
topic: Returns
dimensions: [correctness, grounding, tone]
severity: P0
owner: support-ai-team
created: 2026-04-17
updated: 2026-04-17
---

## Input transcript

Turn 1 (User): I'd like to return my last order.
Turn 2 (User): Order #A7842.
Turn 3 (User): The blue scarf.
Turn 4 (User): It didn't fit as expected.

## Expected agent behavior

Turn 1:
  - Ask for order number; DO NOT invent one.
  - Tone: helpful, no apology for normal process.

Turn 2:
  - Call Look_Up_Order with orderNumber="A7842".
  - Acknowledge order details from tool output.
  - Ask which item.

Turn 3:
  - Match "blue scarf" to an item on the order via tool.
  - Ask for the return reason.

Turn 4:
  - Call Initiate_Return with orderNumber="A7842", itemId=<resolved>, reason="fit".
  - Confirm next steps (return label, refund timeline).

## Expected tool calls

```yaml
expected_tool_calls:
  - turn: 2
    tool: Look_Up_Order
    args:
      orderNumber: "A7842"
  - turn: 3
    tool: Match_Item_On_Order
    args:
      orderNumber: "A7842"
      itemDescription: any
  - turn: 4
    tool: Initiate_Return
    args:
      orderNumber: "A7842"
      itemId: any
      reason: any
```

## Scoring rubric

- correctness (0-2): per standard rubric
- grounding   (0-2): per standard rubric
- tone        (0-2): per standard rubric

## Reference answer

Turn 1 agent: "I can help with that. Could you share your order number? It's the code starting with a letter — you'll see it on your receipt or order email."

Turn 2 agent: "Found order A7842 placed on March 3 — 1× Blue Scarf ($29.99) and 1× Wool Hat ($19.99). Which item would you like to return?"

Turn 3 agent: "Got it — you'd like to return the Blue Scarf. What's the reason for the return?"

Turn 4 agent: "Return initiated for the Blue Scarf. You'll receive a prepaid label at your registered email within an hour. Refund of $29.99 will post to your original payment method within 3-5 business days after we receive the item."

## Anti-patterns

- "Sure, returning your order now." without asking for the order number → correctness 0
- "Let me cancel your subscription." (wrong tool) → correctness 0
- "I'm sorry, but I'm just a bot." (dismissive) → tone 0
- "Your refund will be $29.99 + fees." (invented fees) → grounding 0
```

---

## Running this fixture

The harness script (not included in this template — it lives in `scripts/run_agent_evals.py` when built) loads the fixture, replays the input transcript against the named agent in a target sandbox, captures the actual responses + tool calls, and scores per the rubric.

Baseline scores are stored in `evals/agents/<agent-id>/baseline.json`. CI diffs the current run against the baseline and fails the PR on P0 regression.

---

## See also

- `skills/agentforce/agentforce-eval-harness` — the skill backing this template.
- `skills/agentforce/agentforce-multi-turn-patterns` — how to design the conversations this fixture represents.
- `evals/framework.md` — the parent eval framework that this template plugs into.
