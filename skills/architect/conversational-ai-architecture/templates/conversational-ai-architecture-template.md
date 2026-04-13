# Conversational AI Architecture — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `conversational-ai-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Existing Einstein Bot deployments:** (yes/no — if yes, list channels served and whether session context variables are defined)
- **Target channel(s):** (IVR, chat, SMS, Slack, Experience Cloud, other)
- **Business functions to cover:** (list each function the conversational experience must handle)
- **Expected concurrent session volume:** (rough estimate per channel)
- **Org edition / Agentforce license confirmed:** (yes/no)
- **Known constraints or limits:** (any relevant platform or compliance constraints)
- **Primary failure mode risk:** (over-broad topics, missing context transfer, capacity mis-config, other)

## Paradigm Decision

Use the Decision Guidance table from SKILL.md. Document the decision here before building.

| Option | Notes |
|---|---|
| Einstein Bot only | |
| Agentforce only | |
| Hybrid (Einstein Bot front-end + Agentforce escalation) | |
| Multi-agent orchestration | |

**Decision:** (chosen option)

**Rationale:** (why this option, referencing the Decision Guidance table)

## Topic Design (Agentforce)

For each Agentforce Topic, complete one block:

---

**Topic name:** (topic identifier)

**Business function:** (what business domain this topic serves)

**In scope:** (specific request types this topic handles — written as prose, not utterance list)

**Explicitly out of scope:** (what this topic does NOT handle — name the other topics where applicable)

**Actions assigned:** (list of Actions attached to this topic)

**Overlap check:** (confirm no other topic description uses the same scope language as this one)

---

(repeat for each topic)

## Session Context Transfer Map (if Einstein Bot is in scope)

Complete this table for every bot variable that must be available downstream.

| Bot Variable | Transfer Attribute Name | Consumed By | Purpose |
|---|---|---|---|
| (e.g., VerifiedAccountId) | (e.g., verified_account_id) | (Agentforce Action name) | (e.g., pre-populate identity so agent skips re-verification) |

**Transfer Action location in bot dialog:** (which bot dialog step performs the transfer)

**Agentforce Action that consumes transfer attributes:** (Action name and what it injects into context)

## Channel Routing Diagram

Describe the routing flow (or attach diagram):

```
Channel entry point: [channel name]
  |
  v
[Einstein Bot — handles: ...]
  |
  | Transfer condition: [condition]
  v
[Agentforce Agent — topic routing by Atlas Reasoning Engine]
  |
  | Escalation condition: [condition]
  v
[Human agent queue — queue name]
```

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1: Einstein Bot IVR Front-End with Agentforce Escalation
- [ ] Pattern 2: Scope-Bounded Multi-Topic Agentforce Agent
- [ ] Other: (describe)

**Rationale:** (why this pattern fits the request)

## Checklist

Copied from SKILL.md Review Checklist — tick items as you complete them.

- [ ] Each Agentforce Topic has a description with explicit in-scope and out-of-scope statements
- [ ] No two Topic descriptions share overlapping scope language
- [ ] Session context transfer from Einstein Bot to Agentforce is explicitly mapped (bot variables to transfer attributes)
- [ ] Agentforce agent Actions are scoped to least-privilege record access
- [ ] Adversarial boundary routing tests pass for all adjacent topic pairs
- [ ] Omni-Channel routing rules correctly direct transfers between Einstein Bot, Agentforce, and human queues
- [ ] Multi-agent orchestration is used if any single agent would exceed 20 topics

## Notes

Record any deviations from the standard pattern and why.
