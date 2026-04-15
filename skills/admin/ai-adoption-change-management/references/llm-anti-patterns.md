# LLM Anti-Patterns — AI Adoption Change Management

Common mistakes AI coding assistants make when generating or advising on Salesforce AI adoption change management. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Generic Change Management Frameworks Without AI-Specific Modifications

**What the LLM generates:** A change management plan based on Prosci ADKAR, Kotter's 8-Step Model, or similar generic frameworks applied directly to an Agentforce rollout. The output includes communication plans, training schedules, and stakeholder engagement steps that are indistinguishable from a standard CRM feature rollout.

**Why it happens:** LLMs are trained heavily on generic change management literature (ADKAR, Kotter, McKinsey 7-S) and apply these frameworks as defaults when the topic is "change management." The AI-specific nuances — the LEVERS model, the black-box trust problem, Feedback API instrumentation — are not prominent in general change management training data.

**Correct pattern:**

```
Correct approach:
1. Start with the Salesforce LEVERS model (Leadership, Ecosystem, Values,
   Enablement, Rewards, Structure) — the official Salesforce framework for AI CM
2. Run a LEVERS gap analysis BEFORE producing training content
3. Add AI-specific trust and transparency communication as a critical-path item
4. Include Feedback API instrumentation plan as a deployment prerequisite
5. Generic CM frameworks (ADKAR etc.) can supplement but do not replace LEVERS
   for an AI-specific rollout
```

**Detection hint:** If the output mentions ADKAR, Prosci, or Kotter without also mentioning the LEVERS model or Feedback API, the response is applying a generic framework to an AI-specific problem. Search the output for "LEVERS", "Feedback API", and "Agentforce Analytics" — if none are present, the response is incomplete.

---

## Anti-Pattern 2: Treating Acceptance Rate as the Primary Adoption Success Metric

**What the LLM generates:** A success metrics framework that centers AI feature acceptance rate as the headline KPI, with targets like "achieve 80% acceptance rate within 30 days." The plan may include a Data 360 dashboard focused on acceptance rate tracking.

**Why it happens:** Acceptance rate is a visible, quantifiable metric that appears prominently in Agentforce documentation and is easy to explain to executives. LLMs default to it as the primary metric because it sounds rigorous and is intuitive. The nuance that high early acceptance rates may indicate passive compliance rather than genuine adoption is not obvious from surface-level documentation.

**Correct pattern:**

```
Correct metrics framework pairs acceptance rate with feedback participation rate:

Primary metrics:
- Acceptance rate: target 55–75% (not 90%+, which signals passive compliance)
- Feedback participation rate: % of active users who submitted ≥1 feedback signal
- Invocation rate: % of eligible daily active users invoking AI features

Secondary metrics:
- Top rejection reasons by category (requires Feedback API reason text analysis)
- Per-role acceptance rate breakdown (identifies training gaps vs. model gaps)
- Week-over-week invocation trend (measures sustained engagement, not just launch spike)
```

**Detection hint:** If the output sets an acceptance rate target above 80% for a pilot cohort without qualifying it, or if it presents acceptance rate as the sole primary metric without feedback participation rate, flag it for revision. Search for "feedback participation" or "rejection reasons" — if absent, the metrics framework is incomplete.

---

## Anti-Pattern 3: Scheduling Trust Communication as a Post-Launch Activity

**What the LLM generates:** A rollout plan where the trust and transparency communication about how the AI model works is positioned as a launch-week communication or a post-go-live FAQ. The plan may include a "trust FAQ document" published in the Help portal after go-live.

**Why it happens:** In standard software rollouts, FAQs and support documentation are post-launch artifacts. LLMs generalize this sequencing to AI rollouts, not recognizing that AI distrust is a pre-existing condition that must be addressed before the feature is introduced, not after users have already encountered it and formed a negative impression.

**Correct pattern:**

```
Trust and transparency communication timeline:
- T-4 weeks: Executive-authored communication about what AI feature is coming,
              WHY (connect to org values), and explicit job security statement
- T-2 weeks: "How it works" communication: what data feeds the AI,
              what the AI cannot see, how users can override and give feedback
- T-0 (launch): "It's live" communication with where to get help and give feedback
- T+30 days: Executive follow-up with adoption data and "what we learned"

Transparency content must come BEFORE the feature, not after users encounter it.
```

**Detection hint:** If the trust or transparency communication appears in the rollout plan after the go-live date, or if it is described as a "FAQ document" or "support article" rather than a named executive communication, the sequencing is wrong.

---

## Anti-Pattern 4: Producing a LEVERS Scorecard Without Assigning Owners to Each Gap

**What the LLM generates:** A LEVERS gap analysis document that scores each lever 1–3 and notes which are at risk. The document ends with "recommend addressing Leadership and Rewards levers before go-live." No owners, no deliverables, no deadlines are specified.

**Why it happens:** LLMs are good at producing diagnostic documents and frameworks. Converting a gap analysis into owned work items requires organizational authority that an AI assistant does not have visibility into. The LLM defaults to analysis output rather than action assignment because it cannot know who the stakeholders are.

**Correct pattern:**

```
LEVERS gap analysis must produce owned action items:

| Lever       | Score | Gap Description         | Owner           | Deliverable               | Deadline   |
|-------------|-------|-------------------------|-----------------|---------------------------|------------|
| Leadership  | 1     | No exec sponsor visible | [VP Name]       | 3-min adoption video      | T-2 weeks  |
| Rewards     | 1     | No recognition program  | [HR Lead]       | Feedback leaderboard live | T-1 week   |
| Ecosystem   | 2     | No champions identified | [Enablement]    | 3 champions designated    | T-3 weeks  |

Go/no-go gate: 4+ levers at score 3 before pilot goes live.
If owner cannot be assigned: escalate to executive sponsor, do not proceed.
```

**Detection hint:** If the LEVERS output ends with a scored table and a recommendation paragraph without named owners, deliverables, and deadlines, the analysis is incomplete. Search for calendar dates and owner names — if absent, flag for revision.

---

## Anti-Pattern 5: Omitting the Feedback API from the Deployment Plan

**What the LLM generates:** A complete Agentforce adoption plan — training, communications, metrics — that does not mention the Feedback API or treats it as an optional enhancement. The plan may specify adoption measurement via Agentforce Analytics but assumes usage volume data alone is sufficient.

**Why it happens:** The Feedback API is a relatively recent addition to the Agentforce platform and is underrepresented in general Salesforce training data. LLMs frequently generate Agentforce adoption plans based on general CRM adoption patterns, where usage volume (logins, feature invocations) is sufficient signal. For AI features, behavioral signals (accept/reject) and qualitative signals (reason text) are required to distinguish model quality problems from training problems.

**Correct pattern:**

```
Feedback API must appear in the deployment plan as a prerequisite, not an option:

Pre-launch checklist:
☐ Feedback API enabled on all AI surfaces in scope (verify in org settings)
☐ Thumbs-up/down controls visible to users in the AI response UI
☐ Reason text prompt configured (users can explain why they gave a thumbs-down)
☐ Accept/Regenerate/Decline behavioral signals confirmed active
☐ Data 360 dashboard configured to surface thumbs ratio and reason text categories
☐ Weekly feedback review cadence scheduled with a named owner

Post-launch: Analyze rejection reasons weekly for first 90 days.
Distinguish model quality issues (specific factual errors) from calibration issues
(correct but poorly timed or formatted) from training gaps (user didn't know how to use it).
```

**Detection hint:** Search the output for "Feedback API", "thumbs", "rejection reasons", and "reason text". If none are present in an Agentforce adoption plan, the structured feedback loop is missing. A plan with only usage volume metrics and no feedback instrumentation is incomplete.

---

## Anti-Pattern 6: Applying One-Size Training to All User Roles

**What the LLM generates:** A single training curriculum ("AI Training for All Staff") that covers how to use Agentforce or Einstein features with no differentiation by role. The training covers click-paths, basic feature orientation, and a generic "trust the AI but verify" message.

**Why it happens:** LLMs default to producing unified training content because it is simpler and because role-specific curriculum requires knowledge of the specific org's roles and workflows that the LLM does not have. The "trust but verify" framing is a common heuristic that sounds balanced but provides no actionable guidance for specific roles.

**Correct pattern:**

```
Role-specific AI training must address role-specific trust concerns:

Sales rep training:
- What data the AI uses to generate suggestions (closed-won email threads, call transcripts)
- When to override: if customer context the AI cannot see changes the situation
- How to give feedback: thumbs-down + specific reason (not just "wrong")
- What happens to their feedback: it improves the model for the whole team

Service agent training:
- What the AI can suggest vs. what must come from the agent's own judgment
- How to handle a situation where the AI suggestion is correct but the customer
  needs to hear it in the agent's own words
- Compliance: which AI-generated outputs require human review before sending

Manager training:
- How to read team-level adoption dashboards in Data 360
- How to coach reps who are over-accepting vs. never accepting
- How to create space in 1:1s to discuss AI use without signaling surveillance
```

**Detection hint:** If the training section of the adoption plan does not break down by role or persona, or if it uses "trust but verify" as the primary guidance without role-specific context, the training design is generic and will produce lower adoption.
