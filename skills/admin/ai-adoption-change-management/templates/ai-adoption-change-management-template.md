# AI Adoption Change Management — Work Template

Use this template when planning or executing a human adoption strategy for an Agentforce or Einstein AI feature rollout.

---

## Scope

**Skill:** `ai-adoption-change-management`

**AI feature(s) in scope:** (e.g., Agentforce Sales Agent, Einstein Reply Recommendations, Einstein Copilot)

**Target user population:** (role names, team size, org structure)

**Rollout model:** [ ] Pilot-then-phased  [ ] Phased by region/team  [ ] Big-bang

**Go-live target date:** ___________

**Request summary:** (describe what the user asked for — adoption plan, feedback instrumentation, trust communication, metrics framework, or all of the above)

---

## LEVERS Gap Analysis

Score each lever 1 (not engaged) / 2 (partially engaged) / 3 (actively engaged). Assign an owner and deliverable for every lever scoring 1 or 2.

| Lever | Score | Current State | Gap Description | Owner | Deliverable | Deadline |
|-------|-------|---------------|-----------------|-------|-------------|----------|
| Leadership | | | | | | |
| Ecosystem | | | | | | |
| Values | | | | | | |
| Enablement | | | | | | |
| Rewards | | | | | | |
| Structure | | | | | | |

**Total levers at active (score 3):** ___ / 6

**Go/no-go gate:** Must reach 4+ levers at score 3 before pilot goes live.
If gate is not met by T-1 week, escalate to: (name of executive sponsor)

---

## Trust and Transparency Communication Plan

### Pre-Launch Communication (T-4 weeks)

**Author/sender:** (must be C-level or VP-level in the affected department — not the admin team)

**Channel:** (Slack channel name / Chatter group / All-hands format)

**Required content:**
- [ ] What AI feature is being deployed and what it does
- [ ] Why the org is deploying it — connected to org values, not just efficiency
- [ ] Explicit job security statement (must use those words, not euphemism)
- [ ] How users can give feedback and what happens to it
- [ ] Who to contact with questions or concerns

**Draft message:**

> [Executive name] communication draft goes here. Reference the AI feature by name.
> Explicitly address: "This tool is here to help you, not replace you."
> Explain what data the AI uses: [list data sources].
> Explain what the AI cannot see: [list exclusions].
> Tell users how to give feedback: [describe thumbs-up/down mechanism].

### How-It-Works Communication (T-2 weeks)

**Channel:** (training session / Slack / recorded video)

**Required content:**
- [ ] Plain-language explanation of what data feeds the AI model
- [ ] What the AI cannot access (personal data, external systems, pre-import history)
- [ ] How to interpret confidence signals or alternative options shown in the UI
- [ ] How to override — users must know overriding is always allowed
- [ ] Feedback mechanism walkthrough

### 30-Day Follow-Up Communication (T+30 days)

**Author/sender:** (same executive as pre-launch)

**Required content:**
- [ ] Adoption data summary (invocation rate, acceptance rate, feedback participation rate)
- [ ] What the team's feedback revealed and what was done about it
- [ ] Recognition of adoption champions by name
- [ ] Next steps or upcoming AI feature improvements

---

## Feedback API Instrumentation Plan

**Feedback API status in org:** [ ] Enabled  [ ] Not enabled (block until resolved)

**AI surfaces with Feedback API instrumented:**

| Surface / Feature | Thumbs UI Active | Reason Text Prompt | Accept/Reject Signals | Confirmed by |
|---|---|---|---|---|
| | [ ] | [ ] | [ ] | |
| | [ ] | [ ] | [ ] | |

**Data 360 Agentforce Analytics dashboard configured:** [ ] Yes  [ ] No (block until resolved)

**Feedback review cadence:**

- Frequency: [ ] Weekly (required for first 90 days)  [ ] Bi-weekly  [ ] Monthly
- Named owner: ___________
- Review agenda: thumbs ratio trend, top rejection reason categories, per-role acceptance breakdown, action items from previous week

---

## Agentforce Analytics Adoption Metrics

Define these BEFORE go-live so baselines can be established from day one.

| Metric | Baseline (Day 0) | Target (Day 30) | Target (Day 90) | Owner |
|--------|-----------------|-----------------|-----------------|-------|
| Invocation rate (% of daily active users invoking AI) | | | | |
| Acceptance rate (% of AI outputs accepted by user) | | | | |
| Feedback participation rate (% of users with ≥1 feedback submitted) | | | | |
| Active users invoking AI at least weekly | | | | |

**Note on acceptance rate:** Target 55–75% for a healthy pilot. Rates above 90% in weeks 1–2 warrant investigation for passive compliance. Do not set targets above 80%.

---

## Role-Specific AI Enablement Plan

For each target user role, define a training session that covers AI-specific trust and feedback — not just click-paths.

### Role: ___________

**AI feature used by this role:** ___________

**Top trust concerns for this role:** (job security angle, data privacy concern, override confidence)

**Training curriculum outline:**

1. What the AI does for this role (20 min) — feature walkthrough
2. What data feeds it and what it cannot see (10 min) — transparency session
3. When to trust it, when to override it (15 min) — role-specific scenarios
4. How to give feedback: thumbs + reason text walkthrough (10 min)
5. Q&A and role-play: "What would you do if the AI suggested X?" (15 min)

**Training delivery format:** [ ] Live Zoom  [ ] Recorded video  [ ] Trailhead module  [ ] In-person

**Training completion tracking:** (LMS name or Salesforce training tracking mechanism)

---

## Pilot Cohort Plan

**Pilot cohort size:** ___ users (recommended: 10–20)

**Cohort selection criteria:** (early adopters, high AI curiosity, respected by peers)

**Pilot start date:** ___________

**Promotion gate — criteria to advance to next cohort:**

- [ ] Acceptance rate: ___% (target: 55–75%)
- [ ] Feedback participation rate: ___% (target: 80% of pilot users have submitted ≥1 signal)
- [ ] No unresolved model quality issues in rejection reason text
- [ ] At least 2 pilot user stories collected for use in broader rollout comms

**Promotion decision date:** ___________

**Decision owner:** ___________

---

## 90-Day Post-Launch Review Cadence

| Week | Metrics to Review | Action Items | Owner |
|------|-------------------|--------------|-------|
| Week 1 | Invocation rate, acceptance rate, feedback participation | Review rejection reasons, identify early blockers | |
| Week 2 | Same + trend vs. Week 1 | Escalate model quality issues to Salesforce support if needed | |
| Week 4 (30-day) | All metrics vs. Day 0 baseline | Executive follow-up communication | |
| Week 8 | Cohort comparison if phased | Identify under-adopting teams for targeted intervention | |
| Week 12 (90-day) | Full metrics review vs. all targets | Decision: expand, sustain, or re-evaluate program | |

---

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them:

- [ ] LEVERS gap analysis completed and at least four levers actively engaged
- [ ] Executive-authored trust and transparency communication drafted and reviewed
- [ ] Feedback API enabled and instrumented on all deployed AI surfaces
- [ ] Agentforce Analytics Data 360 dashboards configured with baseline and target metrics defined pre-launch
- [ ] Role-specific AI training covers trust, override authority, and feedback — not just click-paths
- [ ] Phased rollout plan includes a pilot cohort and a measurable promotion gate
- [ ] 90-day post-launch adoption review cadence scheduled with named owners
- [ ] Job security messaging explicitly addressed in all-hands or manager communication

---

## Notes

Record any deviations from the standard pattern and why:
