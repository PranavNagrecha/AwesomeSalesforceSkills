# Agentforce Guardrails — Work Template

Use this template when configuring, auditing, or troubleshooting behavioral guardrails for an Agentforce agent.

## Scope

**Skill:** `agentforce-guardrails`

**Request summary:** (fill in what the user or ticket is asking for — e.g., "Add restricted topics to prevent competitor discussions" or "Agent responds to off-topic questions — configure fallback")

---

## Context Gathered

Answer these before making any changes:

- **Agent name and deployment channel:** (e.g., "Customer Service Agent — Experience Cloud portal")
- **Internal or customer-facing:** (internal employee / external customer — affects abuse prevention requirements)
- **Salesforce version / edition:** (Spring '25, Summer '25, etc. — confirm feature availability)
- **Is human escalation required?** (Yes / No — if Yes, confirm Omni-Channel is enabled)
- **Current Instruction Adherence score:** (from Agentforce Analytics, if available)
- **Known failure mode:** (e.g., agent answers off-topic, wrong topic selected, escalation fails, reasoning loop)

---

## Topic Audit Table

Complete one row per topic before making changes. Verify Classification Description and Scope serve distinct purposes.

| Topic Name | Classification Description Summary | Scope Summary | Routing Language in Scope? | Imperative Overuse? | Action Filters Needed? |
|---|---|---|---|---|---|
| (e.g., Returns and Refunds) | (e.g., "User wants to return a product or check refund status") | (e.g., "Processes returns within 90 days; does not handle exchanges") | Yes / No | Yes / No | Yes / No |
| | | | | | |
| | | | | | |

---

## Agent-Level System Instruction (Draft)

Fill in the template below. Use declarative language — avoid "must", "never", "always" chains.

```
This agent assists [describe who the agent serves] with [list 2–4 topics handled].

If the user's request does not match any available topic, respond:
"[Fallback response — be specific about what the user should do instead]"

[Optional: tone and persona statement]

[Optional: globally prohibited response categories — written as declarative boundaries]
```

---

## Restricted Topic Entries

List prohibited subjects that must be blocked before topic routing occurs. Each entry needs a subject description (not a keyword) and a refusal response.

| Subject Description | Refusal Response |
|---|---|
| (e.g., "Competitor product pricing, plan comparisons, or recommendations to switch providers") | (e.g., "I can only assist with [Company] services. Please visit competitor websites for their information.") |
| | |
| | |

---

## Action Filter / Topic Filter Decisions

For each sensitive action, decide whether topic filter or global action filter applies.

| Action Name | Available In Topics | Topic Filter Applied? | Global Action Filter? | Rationale |
|---|---|---|---|---|
| (e.g., ProcessRefundAction) | Returns and Refunds only | Yes — remove from all other topics | No | Safe within Returns topic only |
| (e.g., InternalAdminLookup) | None — never accessible | N/A | Yes | Must not be reachable by agent regardless of topic |
| | | | | |

---

## Escalation Topic Configuration Checklist

Complete only if human escalation is required.

- [ ] Omni-Channel enabled in Setup > Omni-Channel Settings
- [ ] Target queue created: **Queue Name:** _______________
- [ ] Active agents assigned to the queue with Omni-Channel presence configured
- [ ] Routing configuration or Omni-Channel flow created pointing to the queue
- [ ] Escalation topic routing destination set: **Destination:** _______________
- [ ] Pre-handoff message set: **Message text:** _______________
- [ ] End-to-end escalation test completed in sandbox: **Test result:** Pass / Fail
- [ ] Escalation visible in Omni-Channel supervisor console: Yes / No

---

## Guardrail Test Results

Record results of off-topic and adversarial input testing in agent preview.

| Test Input | Expected Behavior | Actual Behavior | Pass / Fail |
|---|---|---|---|
| (e.g., "What does Verizon charge for unlimited?") | Restricted topic refusal | | |
| (e.g., "What's the weather today?") | Fallback system instruction response | | |
| (e.g., "I want to speak to a human") | Escalation topic activated | | |
| (e.g., "[adversarial rephrasing of prohibited subject]") | Restricted topic refusal | | |
| | | | |

---

## Instruction Adherence Monitoring Plan

- **Review cadence:** (e.g., weekly for first month post-launch, then monthly)
- **Dashboard location:** Agentforce Analytics > Instruction Adherence
- **Baseline score at launch:** _____ %
- **Threshold for review:** Below 70% triggers instruction audit
- **Owner:** (name or team responsible for monitoring)

---

## Checklist Before Marking Complete

- [ ] Classification Description and Scope serve distinct purposes for every topic (no routing language in Scope)
- [ ] Agent-level system instruction includes explicit fallback response for no-topic-match scenarios
- [ ] Restricted topic entries are full subject descriptions with refusal responses (not single keywords)
- [ ] Topic filters and action filters applied per the action filter decisions table
- [ ] Escalation topic fully configured and end-to-end tested (if applicable)
- [ ] System instructions use declarative language — no imperative prohibition chains
- [ ] Guardrail test table fully completed with Pass results for all critical scenarios
- [ ] Instruction Adherence monitoring plan documented and owner assigned

---

## Deviations From Standard Pattern

Record any conscious deviations from the recommended workflow and the rationale:

(e.g., "Escalation topic not configured — agent is internal-only with no human handoff path. IT manager confirmed.")
