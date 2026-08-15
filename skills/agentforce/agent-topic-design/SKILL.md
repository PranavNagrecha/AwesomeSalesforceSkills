---
name: agent-topic-design
description: "Use when designing or reviewing Agentforce topic (renamed subagent in April 2026) structure, including topic boundaries, instruction quality, handoff rules, out-of-scope behavior, and topic-selector strategy. Triggers: 'agentforce subagents (formerly topics)', 'topic design', 'topic selector', 'agent scope boundary', 'handoff conditions'. NOT for restricting what the agent may do or say (topic Scope, action filters, abuse prevention) — use agentforce/agentforce-guardrails. NOT for the mechanics of transferring a live conversation out — Omni-Channel routing and the context package — use agentforce/agentforce-agent-handoff-patterns."
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
version: 2.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agent Topic Design

Use this skill when the agent's real problem is scope design, not model tuning. Subagents — called **topics** before April 2026, and still labelled that way in older documentation, in metadata API names, and in many orgs — are how Agentforce understands which job it is doing at a given moment. The rename changed nothing about behaviour. A weak subagent design creates overlapping instructions, confused routing, and actions appearing available in the wrong conversational context. A strong subagent design keeps the agent focused, predictable, and honest about what it cannot do.

The core job is to draw clean domain boundaries. A subagent should represent a coherent business capability with clear entry signals, clear exclusions, and a clear exit or handoff path. If the subagent description reads like a backlog label or a vague department name, the agent will not have enough structure to choose well. Agentforce guidance emphasizes small, explicit subagent sets and deliberate use of topic selectors when the domain becomes too broad.

Current official guidance emphasizes keeping subagent sets tight, using clear boundaries, and employing a topic selector when a broader agent landscape has more than roughly fifteen candidate subagents. It also emphasizes that only one subagent is active in context at a time, which means the subagent boundary must be specific enough to drive the right instructions and action set.

> **Terminology.** This skill leads with *subagent* because that is the current
> product term. It deliberately keeps *topic* in metadata and API names, in the
> "topic selector" pattern name, and in search keywords — those did not change,
> and readers arriving with the older vocabulary still need to find this skill.

---

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- What user intents should the agent handle directly, and which should be out of scope?
- How many candidate subagents exist, and where do they currently overlap?
- What actions belong to each subagent, and what must trigger handoff to a person or another system?
- Does the agent need a topic selector because the domain is broader than one small subagent set?
- What personas will use this agent? Different personas may warrant different subagent sets.
- What's the agent's "north-star" job? (If you can't state it in one sentence, subagent design won't save you.)

---

## Core Concepts

### A Subagent Is A Capability Boundary

Subagents are not team names, project codes, or loose labels. A subagent should map to a real capability such as case deflection, order status, or appointment rescheduling.

**What makes a good subagent name:**
- Noun-phrase or verb-phrase that describes a capability: `Case_Status_Check`, `Appointment_Reschedule`, `Order_Tracking`.
- NOT a department name: ❌ `Customer_Service`.
- NOT a tech term: ❌ `LLM_Handler`.
- NOT a catch-all: ❌ `General_Help`.

### Subagent Instructions Need Both Inclusion And Exclusion

A subagent that only says what it does is incomplete. It should also say what it does not do and when to hand off or refuse.

**Subagent instruction template:**
```
## What this subagent does
[Specific capability. One or two sentences.]

## When to activate
[Concrete user-intent signals that should route to this subagent.]

## What this subagent does NOT do
[Explicit exclusions. Important for avoiding over-selection.]

## Handoff rules
[Conditions that cause the subagent to escalate, refuse, or route elsewhere.]

## Actions available
[The narrow action set this subagent can use.]
```

The "does NOT do" section is where most subagent designs fall apart. Without it, the LLM will use the subagent for anything that's plausibly related.

### Smaller Subagent Sets Produce Better Routing

When too many subagents compete for similar intents, the agent becomes less reliable. Keep the direct subagent set small and use a topic selector when the business domain is too large for one flat list.

| Subagent count | Routing quality | Management cost |
|---|---|---|
| 1-5 | Excellent | Low |
| 6-10 | Good | Low-medium |
| 11-15 | OK; requires discipline | Medium |
| 16-25 | Degraded; need selector | Medium-high |
| 25+ | Poor; selector mandatory | High |

### Handoff Rules Are Part Of Subagent Design

A subagent should define when it stays in control, when it escalates, and what information should be collected before that handoff occurs.

**Handoff trigger types:**
- **Policy-based:** "If the user asks about refunds > $500, escalate to a human agent."
- **Confidence-based:** "If I cannot answer after 2 attempts, escalate."
- **Scope-based:** "If the user's question is not about <this subagent>, hand off to the topic selector."
- **Data-based:** "If the customer's account is flagged for fraud, escalate immediately."
- **Authorization-based:** "If the action requires manager approval, pause and request it."

Each handoff type has different UX — escalation to a human is different from routing to another subagent.

### Single Active Subagent Semantics

Only one subagent is active at a time in the Agentforce runtime. That means:
- Subagent transition is a deliberate event, not implicit.
- Actions from other subagents are UNAVAILABLE during the active subagent's session.
- If the user changes intent, the subagent must END and a new subagent BEGIN; the context transfer must be explicit.

Design implication: actions that span multiple subagents should NOT exist — duplicate them per subagent OR use a shared "utility" subagent that has broader action access but narrower scope.

---

## Common Patterns

### Pattern 1: Narrow Capability Subagent

**When to use:** The agent handles one well-defined business job with its own signals and boundaries.

**Structure:** Write the subagent around the specific job. Include clear out-of-scope statements. Attach only the actions relevant to that job. The subagent's name, description, and instructions should all reinforce the one capability.

Example: `Appointment_Reschedule` only handles rescheduling existing appointments. It does NOT create new appointments (different subagent). It does NOT cancel (different subagent). Overlap is explicit and intentional.

### Pattern 2: Topic Selector

**When to use:** The overall agent domain contains many potential subagents and one flat list would become noisy.

**Structure:** A higher-level "selector" (itself a subagent) whose only job is to classify user intent and route to the specific subagent. The selector's action set includes `Route_To_Topic("<name>")` or similar. The selector is minimal — no business actions, just routing.

Selector pattern:
```
User: "I need help"
Selector: identifies intent → routes to `Appointment_Issues` → specific subagent takes over
```

### Pattern 3: Handoff-Ready Subagent

**When to use:** A subagent is useful up to a point, but certain cases need a person, queue, or alternate workflow.

**Structure:** Subagent instructions explicitly list:
- The conditions that trigger handoff (policy / scope / authorization / fraud flag / etc.).
- The context to collect before handing off (case number, user preferences, attempted resolutions).
- The handoff destination (human agent via Omni-Channel, alternate workflow, external system).
- The user-facing message ("I'll connect you with a specialist who can help with this.").

### Pattern 4: Persona-Scoped Subagent Family

**When to use:** Different personas need fundamentally different subagent sets (e.g. customer-facing vs employee-facing vs partner-facing agents).

**Structure:** Build separate AGENTS per persona. Each has its own subagent set. Don't try to use conditional instructions within subagents to handle persona differences — too easy to leak. Persona-scoped agents also have different Trust Layer posture (what data each can access).

### Pattern 5: Utility Subagent

**When to use:** A narrow set of cross-cutting capabilities (greeting, farewell, small-talk redirect) that ANY subagent might need.

**Structure:** A lightweight subagent with a very narrow action set (maybe just "greet" and "farewell"). NOT a dumping ground for "everything else" — that becomes a general-help anti-pattern.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One coherent business job with clear signals | Single narrow subagent (Pattern 1) | Easier routing, safer instructions |
| Many overlapping candidate subagents | Refine boundaries OR add selector (Pattern 2) | Reduces competition |
| Agent should stop after policy / risk conditions | Explicit handoff rule (Pattern 3) | Prevents false confidence |
| Subagent sounds like a team/dept instead of a job | Rewrite around the capability | Better activation signals |
| Subagent needs many unrelated actions | Split it OR narrow action set | Keep behavior predictable |
| Multiple personas | Separate agents per persona (Pattern 4) | Avoids leaking context across personas |
| Cross-cutting concerns (greeting, small talk) | Utility subagent (Pattern 5) with strict scope | Avoid "general help" anti-pattern |
| Domain has > 15 candidate subagents | Topic selector mandatory (Pattern 2) | Flat lists don't scale |

## Review Checklist

- [ ] Every subagent maps to a clear business capability.
- [ ] Subagent instructions include explicit exclusions and handoff rules.
- [ ] Overlap between subagents is intentionally minimized.
- [ ] Topic selectors considered when domain is too broad for one flat set.
- [ ] Each subagent has only the actions it actually needs.
- [ ] Agent can fail safely by escalating or refusing when a subagent boundary is crossed.
- [ ] Subagent instruction template (inclusion / exclusion / handoff / actions) applied.
- [ ] Direct subagent count ≤ 15; selector used above that.
- [ ] Persona-scoped agents used instead of conditional subagent instructions.
- [ ] Single-active-subagent semantics explicitly designed (no cross-subagent action assumptions).

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm business capabilities, persona set, handoff expectations
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above; use the subagent instruction template
4. Validate — run the skill's checker script and verify against the Review Checklist above
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

1. **A subagent with vague boundaries degrades both routing and action safety** — the agent may activate the wrong capability for the right user question.
2. **Too many subagents are an architecture problem, not just a UX problem** — competition between them lowers reliability.
3. **Handoff behavior is not a separate cleanup task** — it belongs inside the subagent design from the start.
4. **One active subagent at a time means its wording must be sharp** — fuzzy capability boundaries cannot be rescued later by prompt tuning alone.
5. **Subagent instructions are prompt context** — they count against the model's token budget; extremely verbose instructions degrade other areas.
6. **Managed-package subagents may have opaque instructions** — you see the subagent exists but can't see why it activates; coordinate with the vendor.
7. **Subagent names affect semantic search internally** — the LLM uses name tokens in classification; `Case_Status` and `CaseStatusLookup` may behave differently.
8. **Adding a subagent changes routing behavior for existing ones** — a new subagent can poach intents from established ones. Test regression paths.
9. **Instructions written for internal audiences don't generalize** — if the instruction uses jargon only your team understands, the LLM often misroutes.
10. **Subagent-level Trust Layer settings are separate from agent-level** — masking / citation / guardrails can differ per subagent; audit both layers.
11. **The April 2026 rename is cosmetic, but the vocabulary split is real** — the UI says *subagent* while metadata, evaluation assertions, and older Help articles still say *topic*. Expect to read both in the same investigation.

## Proactive Triggers

Surface these WITHOUT being asked:

- **Subagent named after a department or team** → Flag as High. Likely wrong abstraction.
- **Subagent without a "what this does NOT do" section** → Flag as Critical. Over-selection risk.
- **No handoff rules defined for a customer-facing subagent** → Flag as High. User stuck in unrecoverable states.
- **> 15 direct subagents without a selector** → Flag as High. Flat-list scaling problem.
- **Multiple subagents with overlapping action sets** → Flag as Medium. Consolidation candidate.
- **Subagent instruction > 500 words** → Flag as Medium. Token-budget drain; tighten.
- **Cross-persona conditional instructions in one subagent** → Flag as High. Should be separate agents.
- **"General Help" or catch-all subagent** → Flag as High. Anti-pattern.

## Output Artifacts

| Artifact | Description |
|---|---|
| Subagent architecture review | Findings on overlap, boundary clarity, selector need |
| Subagent rewrite guidance | Better scope, exclusions, handoff wording |
| Selector recommendation | Whether the agent needs scope narrowing before execution |
| Persona-scoping plan | Agent-per-persona decomposition when one agent can't serve all |
| Handoff rule catalog | Per-subagent escalation triggers + destination + context-to-collect |

## Related Skills

- **agentforce/agent-actions** — when the main problem is action contract quality rather than subagent boundaries.
- **agentforce/agentforce-persona-design** — persona-scoped agent strategy.
- **agentforce/agentforce-guardrails** — overall guardrail strategy (subagent-level + agent-level).
- **agentforce/einstein-trust-layer** — Trust Layer settings per subagent.
- **agentforce/agent-testing-and-evaluation** — how to test subagent routing quality.
- **agentforce/prompt-builder-templates** — when the issue is prompt-template construction rather than subagent scoping.
