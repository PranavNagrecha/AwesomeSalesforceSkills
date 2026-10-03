# Agentforce Tool Use Patterns: Work Template

Use this template when choosing and specifying the tools for one subagent.

## Scope

**Skill:** `agentforce-tool-use-patterns`

**Agent and subagent:** (agent API name, subagent API name)

**Serving channel:** (Builder preview only, Messaging, Agent API with its 120-second timeout)

## Capability Inventory

| Capability | Direction (read SF, read external, read unstructured, generate, write SF, write external) | Tool shape (decision tree branch) | `invocationTargetType` | Confirmation needed |
|---|---|---|---|---|
| | | | | |

## Contract per Tool

| Tool API name | Input (primitive type, description, user input?) | Output (description, show in conversation?, used by planner?) | Error field and values |
|---|---|---|---|
| | | | |

## Chaining Order

- Dependent step and the instruction that enforces it (by API name):

## Checklist

- [ ] Every capability has one tool shape chosen from the decision tree.
- [ ] Deterministic work uses Apex, flow or a standard action, not a prompt template.
- [ ] Inputs are primitive; no collections or sObjects in agent-facing request classes.
- [ ] Every output has an instruction; at least one is used by the planner.
- [ ] Text outputs stay at or under 250 characters, or use a multiline or rich text type.
- [ ] Invocables return one result per input, in order, with an error field.
- [ ] `scripts/check_agentforce_tool_use_patterns.py --manifest-dir <dir>` reports no ERROR.
- [ ] Eval cases exercise each tool alone and in its chain.

## Deviations

Record any departure from the patterns in SKILL.md and the reason for it.
