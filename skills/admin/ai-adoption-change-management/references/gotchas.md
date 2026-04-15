# Gotchas — AI Adoption Change Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Feedback API Data Does Not Appear in Standard Salesforce Reports

**What happens:** The Feedback API collects thumbs-up/down signals and reason text on AI responses, but this data is not surfaced in standard Salesforce report types or the standard Analytics Studio dataset list. Teams enable the Feedback API on their AI surfaces, confirm signals are being captured in the platform, and then have no way to view aggregated feedback because they have not separately configured Agentforce Analytics via Data 360. The feedback data exists in the platform but is invisible to the adoption team.

**When it occurs:** This occurs whenever the Feedback API is enabled as part of an Agentforce deployment without an explicit step to configure Data 360 adoption dashboards. It is especially common when the admin handling the AI deployment is different from the admin who owns analytics — the feedback instrumentation gets done but the analytics configuration does not.

**How to avoid:** Make Agentforce Analytics Data 360 dashboard configuration a deployment prerequisite, not a post-go-live task. Specifically: configure the Agentforce Analytics dashboards before the pilot cohort goes live so that feedback signal is visible and actionable from the first day of the pilot. Assign a named owner to the weekly feedback review cadence before go-live.

---

## Gotcha 2: High Acceptance Rate in Early Weeks Can Indicate Passive Compliance, Not Genuine Adoption

**What happens:** An acceptance rate above 90% in the first one to two weeks of an Agentforce pilot is often interpreted as a strong success signal. In practice, very high early acceptance rates frequently indicate that users are clicking "Accept" without reading the AI output — either to meet a perceived quota, to please their manager, or simply to dismiss the prompt quickly. The model is learning from these uncritical acceptances and the adoption team believes the rollout is succeeding when users have not actually changed their behavior.

**When it occurs:** This is most likely when: (1) managers have told their teams to "use the AI tool" without explaining what good use looks like, (2) the AI surface is in the critical path of a workflow and accepting is faster than reviewing, or (3) the feedback leaderboard rewards acceptance count rather than feedback quality.

**How to avoid:** Do not use acceptance rate in isolation. Pair it with feedback participation rate (percentage of active users who have submitted at least one thumbs signal) and open-ended review sessions where reps narrate their actual decision process. A healthy pilot has an acceptance rate of 55–75% with meaningful rejection reasons in the feedback text — not 95% acceptance with zero thumbs-down.

---

## Gotcha 3: LEVERS Gap Analysis Must Produce Owned Work Items, Not Just a Score

**What happens:** Teams complete a LEVERS assessment, identify that Leadership and Rewards levers are not engaged, and produce a document that records the score. Nothing changes organizationally because the assessment output was a record of the gap, not a plan to close it. The go-live date arrives with the same two levers disengaged that the assessment identified, and the launch underperforms.

**When it occurs:** When the LEVERS assessment is treated as a one-time diagnostic artifact rather than a planning instrument. This often occurs when the admin owns the assessment but does not have organizational authority to assign action items to sales leadership or HR.

**How to avoid:** Each lever gap identified in the LEVERS assessment must immediately generate a tracked work item: a named owner, a concrete deliverable (e.g., "VP Sales records 3-minute adoption video"), and a deadline before the pilot start date. If an owner cannot be assigned for a lever gap, escalate to the executive sponsor before continuing. Four or more levers must be at active status before the pilot cohort goes live — this is the go-live gate, not a recommendation.

---

## Gotcha 4: Middle Manager Resistance is a Structure Lever Problem, Not a Training Problem

**What happens:** Individual contributors complete AI training and are nominally ready to use Agentforce. Their managers, however, never mention AI in 1:1 meetings, do not reference AI-assisted outputs in pipeline reviews, and signal through behavior that AI use is optional or even slightly suspicious. Individual reps read this signal correctly and deprioritize AI adoption regardless of their training completion.

**When it occurs:** This is extremely common when the rollout plan focuses on end-user enablement without explicitly addressing how managers will integrate AI outputs into their management behaviors. The Structure lever in the LEVERS model specifically requires that AI features be embedded in the workflows that managers already run — pipeline reviews, deal coaching, forecast calls.

**How to avoid:** Include a manager-specific training module that covers: how to read Agentforce Analytics adoption data for their team, how to incorporate AI-assisted summaries in coaching conversations, and how to model AI use themselves in visible settings. Provide talking points for managers to address AI questions from their teams. Make manager adoption visible in the team-level Data 360 dashboard.

---

## Gotcha 5: Pre-Launch Job Security Communication Must Come from a Named Executive, Not System Admins or Training Teams

**What happens:** The adoption team includes AI job-security messaging in the training materials or the go-live FAQ document. Employees read the messaging, recognize it as coming from the training team or an anonymous HR policy, and discount it. The credibility of job-security assurance depends entirely on who delivers it. A statement from the Chief Revenue Officer carries fundamentally different weight than the same statement in a training slide.

**When it occurs:** When the admin or enablement team drafts and delivers the transparency communication without explicit executive sign-off and visible attribution. This is common when executive sponsors are supportive of the launch in principle but are not personally involved in the communications.

**How to avoid:** The pre-launch trust and transparency communication must be explicitly authored or co-authored by a C-level or VP-level executive in the affected department, delivered in a channel the team uses daily (Slack, Chatter, all-hands meeting), and directly address job security by name — not via euphemism. The executive should follow up publicly at 30 days with adoption data and a statement about what the team's AI usage shows.
