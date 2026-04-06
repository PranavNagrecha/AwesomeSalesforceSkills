# Einstein Bot Architecture — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `einstein-bot-architecture`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Bot platform:** Einstein Bots (legacy) / Agentforce Agents (current) — confirm which
- **Salesforce edition:** (Service Cloud, Agentforce add-on, etc.)
- **Channels in scope:** (web chat, Messaging for In-App and Web, WhatsApp, SMS, Slack)
- **Omni-Channel status:** (enabled? skills-based routing? queues configured?)
- **Knowledge articles:** (article types in use, Einstein Article Recommendations enabled?)
- **Current intent count:** (if existing bot: how many intents, average utterances per intent)

## Intent Taxonomy

| Intent Name | Utterance Count | Resolution Path | Target Queue/Skill |
|---|---|---|---|
| (example: billing_inquiry) | (50+) | (Knowledge article) | (Billing queue) |
| | | | |
| | | | |
| fallback | N/A | Suggest top 3 intents, then escalate | General Support |

## Dialog / Topic Structure

### For Einstein Bots (legacy):

| Dialog Name | Trigger Intent | Steps (summary) | Exit Conditions |
|---|---|---|---|
| | | | |

### For Agentforce Agents (current):

| Topic Name | Description (2-3 sentences with NOT clause) | Actions Available |
|---|---|---|
| | | |

## Handoff Specification

| Bot Variable | Maps To Field | Object | Purpose |
|---|---|---|---|
| detected_intent | Intent__c | LiveChatTranscript | Agent sees which intent the bot detected |
| | | | |

**Agent availability fallback:** (describe what happens when no agents are online)

**Routing method:** (queue-based / skills-based routing — specify skill assignments)

## Analytics Measurement Plan

| Metric | Target | Review Cadence |
|---|---|---|
| Deflection rate | % | Monthly |
| Containment rate | % | Monthly |
| CSAT (bot-resolved) | /5 | Monthly |
| Intent confidence (avg) | 0.8+ | Monthly |
| Fallback intent volume | Declining trend | Weekly (first month) |

## Rollout Plan

| Phase | Intents | Duration | Success Criteria |
|---|---|---|---|
| Phase 1 (pilot) | 3-5 highest volume | 2-4 weeks | Deflection >X%, confidence >0.8 |
| Phase 2 (expand) | +3-5 intents | 2-4 weeks | No drop in Phase 1 metrics |
| Phase 3 (full) | Remaining intents | Ongoing | Stable deflection and CSAT |

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Platform confirmed (Einstein Bots vs. Agentforce) and edition/licensing validated
- [ ] Intent taxonomy documented with 15-25 intents, each with 20+ utterances
- [ ] Resolution path mapped for every intent (knowledge, self-service, or handoff)
- [ ] Handoff design specifies which variables transfer and how they map to transcript/session fields
- [ ] Omni-Channel routing configured for skill-based assignment from bot context
- [ ] Fallback intent behavior defined (suggested intents before escalation)
- [ ] Analytics targets set for deflection rate, containment, and CSAT
- [ ] Multi-channel behavior validated (rich components degrade gracefully on text-only channels)
- [ ] Rollout plan starts with limited intent scope and expands iteratively

## Notes

Record any deviations from the standard pattern and why.
