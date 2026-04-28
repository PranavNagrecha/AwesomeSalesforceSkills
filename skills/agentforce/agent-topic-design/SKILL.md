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
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Agent Topic Design

Use this skill when the agent's real problem is scope design, not model tuning. Topics are how Agentforce understands which job it is doing at a given moment. A weak topic design creates overlapping instructions, confused routing, and actions appearing available in the wrong conversational context. A strong topic design keeps the agent focused, predictable, and honest about what it cannot do.

The core job is to draw clean domain boundaries. A topic should represent a coherent business capability with clear entry signals, clear exclusions, and a clear exit or handoff path. If the topic description reads like a backlog label or a vague department name, the agent will not have enough structure to choose well. Agentforce guidance emphasizes small, explicit topic sets and deliberate use of topic selectors when the domain becomes too broad.

Current official guidance emphasizes keeping topic sets tight, using clear boundaries, and employing a topic selector when a broader agent landscape has more than roughly fifteen candidate topics. It also emphasizes that only one topic is active in context at a time, which means the topic boundary must be specific enough to drive the right instructions and action set.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- What user intents should the agent handle directly, and which should be out of scope?
- How many candidate topics exist, and where do they currently overlap?
- What actions belong to each topic, and what must trigger handoff to a person or another system?
- Does the agent need a topic selector because the domain is broader than one small topic set?
- What personas will use this agent? Different personas may warrant different topic sets.
- What's the agent's "north-star" job? (If you can't state it in one sentence, topic design won't save you.)

---

## Core Concepts

### A Topic Is A Capability Boundary

Topics are not team names, project codes, or loose labels. A topic should map to a real capability such as case deflection, order status, or appointment rescheduling.

**What makes a good topic name:**
- Noun-phrase or verb-phrase that describes a capability: `Case_Status_Check`, `Appointment_Reschedule`, `Order_Tracking`.
- NOT a department name: ❌ `Customer_Service`.
- NOT a tech term: ❌ `LLM_Handler`.
- NOT a catch-all: ❌ `General_Help`.

### Topic Instructions Need Both Inclusion And Exclusion

A topic that only says what it does is incomplete. It should also say what it does not do and when to hand off or refuse.

**Topic instruction template:**
```
## What this topic does
[Specific capability. One or two sentences.]

## When to activate
[Concrete user-intent signals that should route to this topic.]

## What this topic does NOT do
[Explicit exclusions. Important for avoiding over-selection.]

## Handoff rules
[Conditions that cause the topic to escalate, refuse, or route elsewhere.]

## Actions available
[The narrow action set this topic can use.]
```

The "does NOT do" section is where most topic designs fall apart. Without it, the LLM will use the topic for anything that's plausibly related.

### Smaller Topic Sets Produce Better Routing

When too many topics compete for similar intents, the agent becomes less reliable. Keep the direct topic set small and use a topic selector when the business domain is too large for one flat list.

| Topic count | Routing quality | Management cost |
|---|---|---|
| 1-5 | Excellent | Low |
| 6-10 | Good | Low-medium |
| 11-15 | OK; requires discipline | Medium |
| 16-25 | Degraded; need selector | Medium-high |
| 25+ | Poor; selector mandatory | High |

### Handoff Rules Are Part Of Topic Design

A topic should define when it stays in control, when it escalates, and what information should be collected before that handoff occurs.

**Handoff trigger types:**
- **Policy-based:** "If the user asks about refunds > $500, escalate to a human agent."
- **Confidence-based:** "If I cannot answer after 2 attempts, escalate."
- **Scope-based:** "If the user's question is not about <this topic>, hand off to the topic selector."
- **Data-based:** "If the customer's account is flagged for fraud, escalate immediately."
- **Authorization-based:** "If the action requires manager approval, pause and request it."

Each handoff type has different UX — escalation to a human is different from routing to another topic.

### Single Active Topic Semantics

Only one topic is active at a time in the Agentforce runtime. That means:
- Topic transition is a deliberate event, not implicit.
- Actions from other topics are UNAVAILABLE during the active topic's session.
- If the user changes intent, the topic must END and a new topic BEGIN; the context transfer must be explicit.

Design implication: actions that span multiple topics should NOT exist — duplicate them per topic OR use a shared "utility" topic that has broader action access but narrower scope.

---

## Common Patterns

### Pattern 1: Narrow Capability Topic

**When to use:** The agent handles one well-defined business job with its own signals and boundaries.

**Structure:** Write the topic around the specific job. Include clear out-of-scope statements. Attach only the actions relevant to that job. The topic's name, description, and instructions should all reinforce the one capability.

Example: `Appointment_Reschedule` topic only handles rescheduling existing appointments. It does NOT create new appointments (different topic). It does NOT cancel (different topic). Overlap is explicit and intentional.

### Pattern 2: Topic Selector

**When to use:** The overall agent domain contains many potential topics and one flat topic list would become noisy.

**Structure:** A higher-level "selector" (itself a topic) whose only job is to classify user intent and route to the specific topic. The selector's action set includes `Route_To_Topic("<name>")` or similar. The selector is minimal — no business actions, just routing.

Selector pattern:
```
User: "I need help"
Selector topic: identifies intent → routes to `Appointment_Issues` → specific topic takes over
```

### Pattern 3: Handoff-Ready Topic

**When to use:** A topic is useful up to a point, but certain cases need a person, queue, or alternate workflow.

**Structure:** Topic instructions explicitly list:
- The conditions that trigger handoff (policy / scope / authorization / fraud flag / etc.).
- The context to collect before handing off (case number, user preferences, attempted resolutions).
- The handoff destination (human agent via Omni-Channel, alternate workflow, external system).
- The user-facing message ("I'll connect you with a specialist who can help with this.").

### Pattern 4: Persona-Scoped Topic Family

**When to use:** Different personas need fundamentally different topic sets (e.g. customer-facing vs employee-facing vs partner-facing agents).

**Structure:** Build separate AGENTS per persona. Each has its own topic set. Don't try to use conditional instructions within topics to handle persona differences — too easy to leak. Persona-scoped agents also have different Trust Layer posture (what data each can access).

### Pattern 5: Utility Topic

**When to use:** A narrow set of cross-cutting capabilities (greeting, farewell, small-talk redirect) that ANY topic might need.

**Structure:** A lightweight topic with a very narrow action set (maybe just "greet" and "farewell"). NOT a dumping ground for "everything else" — that becomes a general-help anti-pattern.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One coherent business job with clear signals | Single narrow topic (Pattern 1) | Easier routing, safer instructions |
| Many overlapping candidate topics | Refine boundaries OR add selector (Pattern 2) | Reduces competition |
| Agent should stop after policy / risk conditions | Explicit handoff rule (Pattern 3) | Prevents false confidence |
| Topic sounds like a team/dept instead of a job | Rewrite around the capability | Better activation signals |
| Topic needs many unrelated actions | Split topic OR narrow action set | Keep behavior predictable |
| Multiple personas | Separate agents per persona (Pattern 4) | Avoids leaking context across personas |
| Cross-cutting concerns (greeting, small talk) | Utility topic (Pattern 5) with strict scope | Avoid "general help" anti-pattern |
| Domain has > 15 candidate topics | Topic selector mandatory (Pattern 2) | Flat lists don't scale |

## Review Checklist

- [ ] Every topic maps to a clear business capability.
- [ ] Topic instructions include explicit exclusions and handoff rules.
- [ ] Overlap between topics is intentionally minimized.
- [ ] Topic selectors considered when domain is too broad for one flat set.
- [ ] Each topic has only the actions it actually needs.
- [ ] Agent can fail safely by escalating or refusing when topic boundary is crossed.
- [ ] Topic instruction template (inclusion / exclusion / handoff / actions) applied.
- [ ] Direct topic count ≤ 15; selector used above that.
- [ ] Persona-scoped agents used instead of conditional topic instructions.
- [ ] Single-active-topic semantics explicitly designed (no cross-topic action assumptions).

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm business capabilities, persona set, handoff expectations
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above; use the topic instruction template
4. Validate — run the skill's checker script and verify against the Review Checklist above
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

1. **A topic with vague boundaries degrades both routing and action safety** — the agent may activate the wrong capability for the right user question.
2. **Too many topics are an architecture problem, not just a UX problem** — topic competition lowers reliability.
3. **Handoff behavior is not a separate cleanup task** — it belongs inside the topic design from the start.
4. **One active topic at a time means topic wording must be sharp** — fuzzy capability boundaries cannot be rescued later by prompt tuning alone.
5. **Topic instructions are prompt context** — they count against the model's token budget; extremely verbose instructions degrade other areas.
6. **Managed-package topics may have opaque instructions** — you see the topic exists but can't see why it activates; coordinate with the vendor.
7. **Topic names affect semantic search internally** — the LLM uses name tokens in classification; `Case_Status` and `CaseStatusLookup` may behave differently.
8. **Adding a topic changes routing behavior for existing topics** — introducing a new topic can poach intents from existing topics. Test regression paths.
9. **Instructions written for internal audiences don't generalize** — if the instruction uses jargon only your team understands, the LLM often misroutes.
10. **Topic-level Trust Layer settings are separate from agent-level** — masking / citation / guardrails can differ per topic; audit both layers.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Topic named after a department or team** → Flag as High. Likely wrong abstraction.
- **Topic without a "what this does NOT do" section** → Flag as Critical. Over-selection risk.
- **No handoff rules defined for a customer-facing topic** → Flag as High. User stuck in unrecoverable states.
- **> 15 direct topics without a selector** → Flag as High. Flat-list scaling problem.
- **Multiple topics with overlapping action sets** → Flag as Medium. Consolidation candidate.
- **Topic instruction > 500 words** → Flag as Medium. Token-budget drain; tighten.
- **Cross-persona conditional instructions in one topic** → Flag as High. Should be separate agents.
- **"General Help" or catch-all topic** → Flag as High. Anti-pattern.

## Output Artifacts

| Artifact | Description |
|---|---|
| Topic architecture review | Findings on overlap, boundary clarity, selector need |
| Topic rewrite guidance | Better scope, exclusions, handoff wording |
| Selector recommendation | Whether the agent needs topic narrowing before execution |
| Persona-scoping plan | Agent-per-persona decomposition when one agent can't serve all |
| Handoff rule catalog | Per-topic escalation triggers + destination + context-to-collect |

## Related Skills

- **agentforce/agent-actions** — when the main problem is action contract quality rather than topic boundaries.
- **agentforce/agentforce-persona-design** — persona-scoped agent strategy.
- **agentforce/agentforce-guardrails** — overall guardrail strategy (topic-level + agent-level).
- **agentforce/einstein-trust-layer** — Trust Layer settings per topic.
- **agentforce/agent-testing-and-evaluation** — how to test topic routing quality.
- **agentforce/prompt-builder-templates** — when the issue is prompt-template construction rather than topic scoping.
