---
name: agentforce-guardrails
description: "Use this skill when designing, auditing, or troubleshooting behavioral boundaries for Agentforce agents — including topic (now subagent) Scope fields, agent-level system instructions, topic/action filters, the Escalation topic, restricted topics, and Instruction Adherence monitoring. Trigger keywords: agent guardrails, agent out of scope, restrict agent behavior, topic scope, agent instructions, agent fallback, Escalation topic, abuse prevention, action filters. NOT for Trust Layer content filtering (Einstein Trust Layer is a separate product concern), NOT for general topic routing design (use agentforce/agent-topic-design), NOT for prompt template construction (use agentforce/prompt-builder-templates)."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "how do I prevent my Agentforce agent from going off-topic or discussing prohibited subjects"
  - "agent keeps responding to questions outside its intended scope despite topic instructions"
  - "how to configure topic scope and agent-level system instructions to enforce guardrails"
  - "Escalation topic is not routing to a human agent — Omni-Channel configuration issue"
  - "agent ignores my must and never keywords in topic instructions and enters a reasoning loop"
  - "how to set up restricted topics and action filters for a customer-facing Agentforce agent"
  - "Instruction Adherence score is low — how to diagnose and improve agent compliance"
tags:
  - agentforce
  - guardrails
  - topic-scope
  - agent-instructions
  - escalation-topic
  - action-filters
  - restricted-topics
  - instruction-adherence
  - abuse-prevention
  - customer-facing-agent
inputs:
  - "Agent name and deployment channel (in-app, Experience Cloud, Messaging, etc.)"
  - "List of topics the agent must handle and topics it must refuse"
  - "Actions configured on each topic (Apex, flow, prompt template, standard actions)"
  - "Whether human escalation is required and which Omni-Channel queue/flow is in place"
  - "Current topic Scope and Classification Description text for each topic"
  - "Any Instruction Adherence monitoring data from Agentforce Analytics"
outputs:
  - "Revised topic Scope field text defining what the topic will and will not do"
  - "Agent-level system instruction text covering fallback behavior and prohibited subjects"
  - "Topic filter and action filter configuration decisions with rationale"
  - "Escalation topic configuration checklist"
  - "Instruction Adherence improvement recommendations"
  - "Abuse prevention pattern applied to customer-facing agent instructions"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# Agentforce Guardrails

This skill activates when a practitioner needs to define, enforce, or troubleshoot behavioral boundaries for an Agentforce agent — covering the four-layer guardrail architecture: Subagent Scope, agent-level system instructions, subagent/action filters, and Instruction Adherence monitoring. It does not cover Trust Layer content filtering or general subagent routing design.

> **Terminology.** Agent *topics* were renamed **subagents** in April 2026, with
> no change to functionality. This skill leads with *subagent*, and deliberately
> keeps *topic* where it is still literal — Restricted Topics (which block subject
> matter, not subagents), metadata and API names, and search keywords.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which Salesforce version and Agentforce tier the org is on. Guardrail features, including Instruction Adherence analytics, are generally available from Spring '25 but feature availability may vary by edition.
- Know whether the agent is internal (employee-facing) or external (customer-facing, Experience Cloud, Messaging). Customer-facing agents require stricter abuse prevention patterns because untrusted users can craft adversarial inputs.
- Know whether human escalation is required. If so, confirm that Omni-Channel is enabled and a routing configuration or flow exists — the Escalation subagent is a standard system construct that only activates when Omni-Channel is properly wired. Misconfiguring or omitting Omni-Channel causes the Escalation subagent to silently fail.
- Collect the current Classification Description and Scope field text for every subagent. A common wrong assumption is that the Scope field drives LLM subagent routing — it does not. The Classification Description field is what the LLM reads to decide which subagent handles a conversation turn. The Scope field governs what actions and responses are allowed once a subagent is selected.
- Note the platform limit: an agent supports up to 25 subagents per agent definition (varies by Salesforce version; verify in current release notes).

---

## Core Concepts

### Guardrail Layer 1 — Subagent Scope Field

The Scope field on a Bot Topic defines the behavioral boundaries that apply once the LLM has selected that subagent. It tells the agent what it should do, what it should not do, and what information it is allowed to share within that subagent's context. This field is enforced during the action-planning phase of the agent's reasoning loop, not during subagent classification.

The Scope field is distinct from the Classification Description, which is the text the LLM reads when deciding which subagent matches the current user input. Conflating these two fields is the single most common guardrail misconfiguration. A Scope field that reads "do not help with billing questions" will not prevent billing conversations from routing to this subagent — only the Classification Description can do that.

Effective Scope field patterns: use declarative boundary statements ("This subagent only addresses order status inquiries. It does not provide refunds or credits."). Keep the Scope under 1,500 characters. Do not repeat the Classification Description verbatim.

### Guardrail Layer 2 — Agent-Level System Instructions

Agent-level system instructions apply globally across all subagents and conversations. They are the correct location for:

- Default fallback behavior when no subagent matches a user's input
- Prohibited subject matter that must be blocked regardless of which subagent is active
- Tone and persona constraints that apply to the whole agent
- Abuse prevention language for customer-facing deployments

When no subagent matches a user input, the agent uses its system instructions to determine how to respond. Without explicit fallback instructions ("If no subagent matches the user's request, respond: 'I can only help with X, Y, and Z.'"), the agent may attempt to answer anyway, producing hallucinated or off-policy responses.

Overuse of imperative keywords — must, never, always, do not, you must not — causes the LLM reasoning loop to produce contradictory self-instructions and can result in the agent repeatedly re-evaluating the same turn without producing output. Use declarative boundary statements instead: "This agent addresses only [scope]. Requests outside this scope receive: '[canned response].'"

### Guardrail Layer 3 — Subagent Filters and Action Filters

Subagent filters restrict which actions (Apex, flow, prompt templates, standard actions) are available within a specific subagent. Use subagent filters to ensure that an action can only be invoked in the subagent context where it is safe — for example, allowing a refund flow only within a Returns subagent, never in a General Inquiry subagent.

Action filters apply globally to an invocable action, preventing it from being called by any subagent regardless of how the agent reasons. Use action filters for actions that should be completely inaccessible to the agent (e.g., an internal admin action that is in the org's invocable action registry but must never be exposed to the agent).

Subagent filters and action filters are separate configuration constructs. Both are needed in different scenarios. Action filters are the stronger control.

### Guardrail Layer 4 — Instruction Adherence Monitoring

Instruction Adherence is an out-of-the-box Agentforce Analytics metric that scores how consistently the agent follows its subagent instructions across conversations. A score below ~70% indicates that the instructions are ambiguous, contradictory, or too imperative in tone. Low scores are a signal to review instruction language (declarative vs. imperative), check for conflicting subagent Scope statements, and look for adversarial input patterns in conversation logs.

Instruction Adherence is monitored in the Agentforce Analytics dashboard. It does not fire alerts automatically — practitioners must build monitoring habits or set up custom report subscriptions.

### Escalation Subagent — Standard System Construct

The Escalation subagent is a system-defined subagent automatically available on every Agentforce agent. Its purpose is to route a conversation to a human agent when the user requests escalation or the agent cannot resolve the request. The Escalation subagent requires Omni-Channel to be enabled with a valid routing configuration or flow. Without this, the Escalation subagent appears active but silently fails to route the conversation.

Practitioners cannot modify the Escalation subagent's Classification Description. They can configure the routing destination (queue, flow, or skill-based routing) and add a brief customer message displayed before handoff.

### Restricted Topics

Restricted topics are a guardrail configuration that prevents the agent from engaging with specific subject matter regardless of which active subagent was selected. Restricted topic entries are configured at the agent level (not per subagent). Examples: block all discussion of competitor pricing, legal advice, medical diagnoses.

Restricted topic entries are matched against user input before subagent classification occurs, making them a pre-classification filter. A user input that matches a restricted topic entry receives a configurable refusal response and the conversation is not routed to any subagent.

---

## Common Patterns

### Pattern: Layered Scope + Fallback System Instruction

**When to use:** Any agent where users might ask questions outside the intended subagent set, especially customer-facing agents on Messaging or Experience Cloud.

**How it works:**
1. Write a Classification Description for each subagent that tightly describes the user intent the subagent handles.
2. Write a Scope field for each subagent that declares what the agent will and will not do once in that subagent — use declarative sentences, not imperative commands.
3. Write an agent-level system instruction that explicitly names the fallback behavior: "If the user's request does not match any available subagent, respond: 'I can only assist with [list]. For other questions, please contact [channel].'"
4. Test by sending off-topic messages in the agent preview and confirming the fallback text appears verbatim.

**Why not rely on subagent Scope alone:** Subagent Scope only applies after subagent selection. Without a fallback system instruction, the agent may try to answer off-topic questions using general LLM knowledge, producing policy-violating responses.

### Pattern: Restricted Topic Blocklist for Customer-Facing Agents

**When to use:** Customer-facing agents where regulatory, legal, or brand risk requires that certain subjects are never discussed — regardless of how a user phrases the request.

**How it works:**
1. Navigate to Agent Setup > Restricted Topics.
2. Add one entry per prohibited subject. Write the entry as a clear subject description, not a keyword: "Competitor pricing and promotions" rather than "competitor".
3. Configure a consistent refusal response: "I'm not able to assist with that. Please contact our support team at [channel]."
4. Test with paraphrased and adversarial phrasings of the prohibited subject to confirm the restriction fires consistently.
5. Review restricted topic matches weekly in conversation logs for edge cases that bypassed the filter.

**Why not use subagent Scope or system instructions alone:** Subagent Scope and system instructions are post-classification controls. A well-phrased adversarial prompt can sometimes steer the LLM to classify into an adjacent subagent. Restricted topics operate as a pre-classification, keyword-and-semantic filter, providing an additional defensive layer.

### Pattern: Escalation Subagent with Omni-Channel Queue Routing

**When to use:** Any agent that must support human handoff, including service agents on Messaging for In-App and Web or Experience Cloud.

**How it works:**
1. Enable Omni-Channel in the org (Setup > Omni-Channel Settings).
2. Create a queue or configure an Omni-Channel flow for the human agent pool.
3. In the agent's Escalation subagent configuration, select the routing destination (queue or flow).
4. Set the pre-handoff message: "Connecting you to a support agent. Please hold."
5. Test the escalation path end-to-end in a sandbox: confirm the conversation appears in the Omni-Channel supervisor dashboard and is accepted by a human agent.

**Why not skip Omni-Channel:** The Escalation subagent requires Omni-Channel routing infrastructure. Without it, the subagent technically exists but the handoff call fails silently. The user sees the pre-handoff message but is never connected to a human agent.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to block specific subjects before any subagent is selected | Restricted Topics (agent-level) | Pre-classification filter; most reliable block for prohibited subjects |
| Need to constrain what one subagent can do once selected | Subagent Scope field + subagent-level action filters | Scope is post-classification; action filters remove specific action availability within that subagent |
| Need to block a specific action globally across all subagents | Action filter on the action | Prevents any subagent or reasoning path from invoking the action |
| Need a consistent fallback when no subagent matches | Agent-level system instruction with explicit fallback response | Subagent Scope does not apply when no subagent is selected; system instructions are always in scope |
| User requests human escalation but handoff fails silently | Check Omni-Channel routing configuration is complete | Escalation subagent requires valid Omni-Channel destination |
| Instruction Adherence score is below 70% | Audit instruction language for imperative overuse; switch to declarative boundaries | Must/never/always chains cause reasoning loops; declarative statements are more stable |
| Agent answers questions it should refuse | Add restricted topic entries and explicit fallback in system instructions | Defense-in-depth: both pre- and post-classification controls are needed |
| Customer-facing agent receiving adversarial prompts | Apply abuse prevention system instruction + restricted topics | Untrusted users require explicit refusal patterns and pre-classification blocks |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring or auditing Agentforce guardrails:

1. **Audit current subagent configuration.** For each subagent, read the Classification Description and Scope field separately. Confirm they serve different purposes: Classification Description drives routing, Scope drives behavioral boundaries post-selection. Flag any Scope text that attempts to block routing (it will not work).
2. **Configure agent-level system instructions.** Write a concise system instruction (under 2,000 characters) covering: (a) what the agent is for, (b) explicit fallback response when no subagent matches, (c) tone and persona, (d) any globally prohibited responses. Use declarative language — avoid starting sentences with "you must" or "never". Example: "This agent assists employees with IT helpdesk requests. Requests outside IT support receive: 'I can only assist with IT requests. Please contact HR or Finance directly.'"
3. **Configure restricted topics for prohibited subjects.** Add one entry per subject that must be blocked at the pre-classification level. Write entries as subject descriptions, not raw keywords. Set a consistent refusal response text.
4. **Review subagent and action filters.** For each action in each subagent, decide: should this action be available only in this subagent (subagent filter) or blocked globally (action filter)? Apply the minimum necessary filter — over-filtering breaks expected agent behavior.
5. **Configure the Escalation subagent if human handoff is required.** Verify Omni-Channel is enabled. Set routing destination (queue or flow). Test the handoff end-to-end in sandbox before deploying to production.
6. **Test guardrail coverage.** Send at least five off-topic, adversarial, and edge-case inputs in the agent preview. Confirm: restricted topics fire, fallback response appears for no-match scenarios, prohibited actions are not invoked, escalation routes correctly.
7. **Monitor Instruction Adherence post-launch.** Check the Agentforce Analytics dashboard after the first week of live traffic. If adherence is below 70%, review conversation logs for patterns — common causes are ambiguous Scope text, imperative instruction language, or user phrasings not covered by Classification Descriptions.

---

## Review Checklist

Run through these before marking guardrail work complete:

- [ ] Every subagent has a Classification Description that drives routing and a Scope field that drives post-selection behavior — they are not the same text
- [ ] Agent-level system instructions include an explicit fallback response for no-subagent-match scenarios
- [ ] All prohibited subjects are added as Restricted Topic entries with a consistent refusal response
- [ ] Subagent filters are configured for actions that must not cross subagent boundaries
- [ ] Action filters are applied to any globally prohibited invocable actions
- [ ] Escalation subagent routing destination is set and Omni-Channel configuration is verified end-to-end
- [ ] Agent-level instructions use declarative boundary language, not imperative chains (must/never/always)
- [ ] Guardrail coverage has been tested with off-topic, adversarial, and edge-case inputs in agent preview
- [ ] Instruction Adherence monitoring plan is in place (dashboard review cadence established)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Scope field does not control subagent routing** — The Scope field on a subagent is read after the subagent is selected. Adding "do not answer billing questions" to the Scope field of an IT Support subagent does not prevent billing questions from routing there. Classification Description controls routing. This gotcha causes practitioners to write increasingly long Scope fields in an attempt to block off-topic routing, which has no effect.
2. **Escalation subagent silently fails without Omni-Channel** — If Omni-Channel is not enabled or no routing configuration is assigned, the Escalation subagent appears to activate (the user sees the pre-handoff message) but the conversation is never delivered to a human agent. There is no error surfaced to the end user. Test escalation end-to-end, not just by confirming the subagent exists.
3. **Imperative instruction language degrades reasoning loop reliability** — Stacking must, never, always, and do not in system instructions or Scope fields can cause the LLM reasoning loop to produce contradictory internal instructions, leading to repeated self-evaluation without output (a "reasoning loop"). This appears to the user as the agent stalling or timing out. Replace with declarative statements that describe desired state.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Subagent Scope field text | Declarative boundary statements for each subagent, reviewed against Classification Description to ensure no routing logic bleeds in |
| Agent-level system instruction | Global instruction covering fallback behavior, prohibited subjects, tone, and abuse prevention |
| Restricted topic entries | List of prohibited subjects with refusal response text |
| Action filter decisions | Per-action table showing whether subagent filter or global action filter applies, with rationale |
| Escalation subagent configuration checklist | Verified Omni-Channel routing destination, pre-handoff message, and end-to-end test result |
| Instruction Adherence review notes | Post-launch adherence score and recommended instruction revisions |

---

## Related Skills

- `agentforce/agent-topic-design` — use when the main problem is subagent boundary design and routing logic rather than behavioral guardrails and abuse prevention
- `agentforce/prompt-builder-templates` — use when the issue is prompt template construction inside a subagent action, not the guardrail architecture around the agent
- `agentforce/agentforce-testing-strategy` — use when writing test scenarios to validate agent behavior, including guardrail coverage tests
