# Omni-Channel Capacity Model — Work Template

Use this template when designing or tuning an Omni-Channel capacity model.

## Scope

**Skill:** `omni-channel-capacity-model`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Omni-Channel enabled:** Yes / No
- **Org edition:** (Enterprise / Unlimited / etc.)
- **Current capacity mode:** Tab-based / Status-based / Not yet configured
- **Service Channels in use:** (list: Case, Chat, Voice, Messaging, Custom)
- **Agent headcount:** (total agents and breakdown by team/skill)
- **Known volume peaks:** (seasonal, day-of-week, time-of-day patterns)
- **Existing skills configuration:** (list skills currently defined, if any)
- **Failure modes to watch for:** (current pain points — long wait times, overloaded agents, idle agents)

## Capacity Model Design

### Total Capacity

| Presence Configuration Name | Total Capacity | Target Agent Group |
|---|---|---|
| (e.g., Standard Agent) | (e.g., 10) | (e.g., Tier 1 Support) |
| | | |

### Service Channel Weights

| Service Channel | Weight (units) | Rationale |
|---|---|---|
| Voice | 10 | Fully occupies agent — no concurrent work |
| Case | 5 | Moderate effort, asynchronous |
| Chat | 3 | Real-time, agents can handle 2-3 concurrently |
| Messaging | 3 | Similar effort to chat |
| (Custom) | | |

### Interruptible Flags

| Channel | Interruptible? | Reason |
|---|---|---|
| Case | Yes | Can be paused for higher-priority real-time work |
| Messaging | Yes | Can be paused briefly |
| Chat | No | Live conversation — interruption causes poor CX |
| Voice | No | Customer is on the line — cannot pause |

## Skills Matrix

| Agent / Group | Skill 1 | Skill 2 | Skill 3 | Notes |
|---|---|---|---|---|
| (e.g., Team A) | Billing (Level 5) | General (Level 3) | | Primary: Billing |
| (e.g., Team B) | Technical (Level 5) | General (Level 3) | | Primary: Technical |
| | | | | |

**Minimum agents per skill:** 3 (to avoid single-point bottlenecks)

## Presence Status Design

| Presence Status Name | Presence Configuration | Allowed Channels | Use Case |
|---|---|---|---|
| Available - All Channels | Standard Agent | Case, Chat, Voice, Messaging | Default working state |
| Available - Chat Only | Chat Agent | Chat, Messaging | Chat-focused shifts |
| Break | N/A (offline) | None | Scheduled breaks |
| Training | N/A (offline) | None | Training sessions |

## Overflow / Secondary Routing

| Primary Queue | Timeout (seconds) | Overflow Target | Required Skill (overflow) |
|---|---|---|---|
| (e.g., Billing Queue) | 90 | General Overflow Queue | General Support |
| (e.g., Technical Queue) | 90 | General Overflow Queue | General Support |

## Approach

Which pattern from SKILL.md applies? Why?

- [ ] **Tiered Capacity by Channel Mix** — multi-channel org needing weighted capacity
- [ ] **Skills Matrix with Overflow** — specialized queues with peak volume risk
- [ ] **Both** — most production deployments use both patterns together

## Review Checklist

Copy from SKILL.md and tick items as you complete them.

- [ ] Total capacity per Presence Configuration is set and documented
- [ ] Service Channel weights are configured and reflect channel effort differences
- [ ] Skills matrix has no single-agent bottlenecks (minimum 3 agents per skill)
- [ ] Presence Statuses cover all real agent working modes
- [ ] Interruptible flag is set correctly (cases/messaging = interruptible, voice = not interruptible)
- [ ] Secondary routing / overflow is configured for every specialized queue
- [ ] Queue timeout thresholds are set (60-120 seconds recommended)
- [ ] Pilot plan defined with monitoring metrics (wait time, overflow rate, utilization)

## Notes

Record any deviations from the standard pattern and why.
