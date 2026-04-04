# Einstein Bots to Agentforce Migration — Work Template

Use this template when planning or executing a bot-to-Agentforce migration engagement.

---

## Scope

**Skill:** `einstein-bots-to-agentforce-migration`

**Request summary:** (fill in what the user asked for)

**Deadline:** Legacy Chat retires **February 14, 2026**. Confirm whether the bot is on Legacy Chat and whether this deadline is in scope.

---

## Bot Inventory

Complete this section before any migration work begins.

| Field | Value |
|---|---|
| Bot Name | |
| Bot Type | Classic / Enhanced (circle one) |
| Current Channel | Legacy Chat / Messaging for Web / Both |
| Number of Dialogs | |
| Number of Intents / Utterance Sets | |
| Integrations (Flows, Apex, APIs called by bot) | |
| Escalation targets (queues, agents) | |
| Bot Variables in use | |

---

## Migration Approach Decision

- [ ] Enhanced Bot — "Create AI Agent from Bot" tool is available
- [ ] Classic/Legacy Bot — manual scaffold required
- [ ] Full cutover to Agentforce
- [ ] Hybrid pattern: bot handles structured flows, Agentforce handles open-ended queries

**Rationale:** (fill in why this approach was chosen based on the dialog inventory and compliance requirements)

---

## Dialog to Topic Mapping

For each bot dialog, complete this mapping table.

| Bot Dialog | Agentforce Topic Name | Topic Description (routing instruction) | Actions Required | Implementation Status |
|---|---|---|---|---|
| (dialog name) | | | | Draft / In Progress / Complete |
| | | | | |
| | | | | |

---

## Bot Variable to Context Field Mapping

For hybrid pattern context handoff. Leave blank if not applicable.

| Bot Variable | MessagingSession Custom Field | Field Type | Written by (Flow name) | Read by (Action name) |
|---|---|---|---|---|
| | | | | |
| | | | | |

---

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] Pattern 1: Migration tool for Enhanced Bot
- [ ] Pattern 2: Manual migration for Classic Bot
- [ ] Pattern 3: Hybrid bot + Agentforce with context handoff

**Notes:** (record the key decision rationale)

---

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Bot type confirmed — Classic or Enhanced. Migration tool eligibility determined.
- [ ] Legacy Chat channel status confirmed — if in use, cutover planned before Feb 14 2026.
- [ ] Every Dialog has a corresponding Topic with a clear LLM-routing description (not just the dialog name).
- [ ] Raw utterance imports replaced with Topic description language or removed.
- [ ] Every Action placeholder from the migration tool has real logic implemented (Flow, Apex, or service action).
- [ ] GenAiPlannerBundle is present in the deployed BotVersion metadata.
- [ ] Agent User (EinsteinServiceAgent User) is selected via dropdown, not typed.
- [ ] Context handoff via MessagingSession custom fields tested end-to-end (hybrid pattern).
- [ ] Handoff latency measured and confirmed within experience SLA.
- [ ] Agent activated and assigned to the correct channel deployment.
- [ ] Einstein Trust Layer configuration reviewed for the new agent's data access patterns.
- [ ] Rollback plan documented — prior bot remains deployable until cutover is confirmed stable.

---

## Latency SLA Validation

| Metric | Existing Bot (baseline) | Agentforce Agent (measured) | SLA Target | Pass / Fail |
|---|---|---|---|---|
| First response time (ms) | | | | |
| Topic routing time (ms) | | | | |
| End-to-end dialog completion time (s) | | | | |

---

## Cutover Plan

| Step | Owner | Target Date | Status |
|---|---|---|---|
| Migrate all Topics and Actions to Agentforce | | | |
| Validate routing accuracy in sandbox | | | |
| Validate latency SLA in sandbox | | | |
| UAT sign-off | | | |
| Switch channel from Legacy Chat to Messaging for Web | | | |
| Activate Agentforce agent in production | | | |
| Monitor for 48 hours post-cutover | | | |
| Decommission legacy bot dialogs | | | |

**Rollback trigger:** (fill in the condition that would trigger reverting to the prior bot)

**Rollback procedure:** (document the steps to re-activate the prior bot if rollback is needed)

---

## Notes

Record any deviations from the standard pattern and why.
