---
name: agent-topic-design
description: "Use when designing or reviewing Agentforce topic structure, including topic boundaries, instruction quality, handoff rules, out-of-scope behavior, and topic-selector strategy. Triggers: 'agent topics', 'topic design', 'topic selector', 'agent scope boundary', 'handoff conditions'. NOT for action contract design or prompt-template wording when the main problem is not topic scoping."
category: agentforce
salesforce-version: "Spring '26+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Operational Excellence
triggers:
  - "how should I design agentforce topics"
  - "agent topic boundaries are overlapping"
  - "when do I need a topic selector"
  - "agent does not know when to hand off or say it is out of scope"
  - "topic instructions are too vague"
tags:
  - agentforce
  - topic-design
  - topic-selector
  - agent-boundaries
  - handoff-rules
inputs:
  - "business capabilities the agent should and should not cover"
  - "candidate topic count and overlap between them"
  - "handoff, fallback, and escalation expectations"
outputs:
  - "topic architecture recommendation"
  - "boundary and instruction review findings"
  - "topic selector and handoff guidance"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Agent Topic Design

Use this skill when the agent’s real problem is scope design, not model tuning. Topics are how Agentforce understands which job it is doing at a given moment. A weak topic design creates overlapping instructions, confused routing, and actions appearing available in the wrong conversational context. A strong topic design keeps the agent focused, predictable, and honest about what it cannot do.

The core job is to draw clean domain boundaries. A topic should represent a coherent business capability with clear entry signals, clear exclusions, and a clear exit or handoff path. If the topic description reads like a backlog label or a vague department name, the agent will not have enough structure to choose well. Agentforce guidance emphasizes small, explicit topic sets and deliberate use of topic selectors when the domain becomes too broad.

Current official guidance surfaced through Salesforce documentation search emphasizes keeping topic sets tight, using clear boundaries, and employing a topic selector when a broader agent landscape has more than roughly fifteen candidate topics. It also emphasizes that only one topic is active in context at a time, which means the topic boundary must be specific enough to drive the right instructions and action set.

---

## Before Starting

Gather this context before working on anything in this domain:

- What user intents should the agent handle directly, and which should be out of scope?
- How many candidate topics exist, and where do they currently overlap?
- What actions belong to each topic, and what must trigger handoff to a person or another system?
- Does the agent need a topic selector because the domain is broader than one small topic set?

---

## Core Concepts

### A Topic Is A Capability Boundary

Topics are not team names, project codes, or loose labels. A topic should map to a real capability such as case deflection, order status, or appointment rescheduling.

### Topic Instructions Need Both Inclusion And Exclusion

A topic that only says what it does is incomplete. It should also say what it does not do and when to hand off or refuse.

### Smaller Topic Sets Produce Better Routing

When too many topics compete for similar intents, the agent becomes less reliable. Keep the direct topic set small and use a topic selector when the business domain is too large for one flat list.

### Handoff Rules Are Part Of Topic Design

A topic should define when it stays in control, when it escalates, and what information should be collected before that handoff occurs.

---

## Common Patterns

### Narrow Capability Topic Pattern

**When to use:** The agent handles one well-defined business job with its own signals and boundaries.

**How it works:** Write the topic around the specific job, include clear out-of-scope statements, and attach only the actions relevant to that job.

**Why not the alternative:** Broad department-style topics collect unrelated intents and confuse routing.

### Topic Selector Pattern

**When to use:** The overall agent domain contains many potential topics and one flat topic list would become noisy.

**How it works:** Use a selector layer to narrow the candidate topic set before execution, then keep the active topic focused.

### Handoff-Ready Topic Pattern

**When to use:** A topic is useful up to a point, but certain cases need a person, queue, or alternate workflow.

**How it works:** Define the escalation triggers, collected context, and exact moment the topic should stop pretending it can solve the problem.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One coherent business job with clear signals | Single narrow topic | Easier routing and safer instructions |
| Many overlapping candidate topics | Refine boundaries or add a topic selector | Reduces competition between topics |
| Agent should stop after certain policy or risk conditions | Explicit handoff rule in the topic | Prevents false confidence |
| Topic wording sounds like a team or department instead of a job | Rewrite the topic around the capability | Better activation signals |
| Topic needs many unrelated actions | Split the topic or narrow the action set | Keep behavior predictable |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every topic maps to a clear business capability.
- [ ] Topic instructions include explicit exclusions and handoff rules.
- [ ] Overlap between topics is intentionally minimized.
- [ ] Topic selectors are considered when the domain is too broad for one flat set.
- [ ] Each topic has only the actions it actually needs.
- [ ] The agent can fail safely by escalating or refusing when the topic boundary is crossed.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A topic with vague boundaries degrades both routing and action safety** - the agent may activate the wrong capability for the right user question.
2. **Too many topics are an architecture problem, not just a UX problem** - topic competition lowers reliability.
3. **Handoff behavior is not a separate cleanup task** - it belongs inside the topic design from the start.
4. **One active topic at a time means topic wording must be sharp** - fuzzy capability boundaries cannot be rescued later by prompt tuning alone.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Topic architecture review | Findings on overlap, boundary clarity, and selector need |
| Topic rewrite guidance | Better scope, exclusions, and handoff wording |
| Selector recommendation | Whether the agent needs topic narrowing before execution |

---

## Related Skills

- `agentforce/agent-actions` - use when the main problem is action contract quality rather than topic boundaries.
- `agentforce/prompt-template-design` - use when the issue is prompt-template construction rather than topic scoping.
- `security/org-hardening-and-baseline-config` - use when the concern is baseline org security controls, not agent topic architecture.
