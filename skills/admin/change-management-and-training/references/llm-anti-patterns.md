# LLM Anti-Patterns — Change Management and Training

Common mistakes AI coding assistants make when generating or advising on Salesforce change management, user adoption, and training planning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Producing generic training plans not tied to Salesforce personas

**What the LLM generates:** "Create a training plan for all users. Include a 2-hour session on Salesforce basics and a follow-up quiz."

**Why it happens:** LLMs generate one-size-fits-all training plans that ignore role-based differences. A sales rep learning Opportunity management needs different training than a service agent learning Case routing or a manager learning dashboards. Generic training fails because users see irrelevant content and disengage.

**Correct pattern:**

```
Role-based training plan:
| Persona        | Topics                                    | Duration | Format       |
|----------------|-------------------------------------------|----------|--------------|
| Sales Rep      | Lead conversion, Opportunity stages, Quotes| 90 min   | Hands-on lab |
| Service Agent  | Case creation, Knowledge articles, Macros  | 90 min   | Hands-on lab |
| Sales Manager  | Dashboards, Reports, Forecast              | 60 min   | Demo + Q&A   |
| System Admin   | User management, Flow troubleshooting      | 120 min  | Workshop     |

Each persona gets content relevant to their daily workflow.
```

**Detection hint:** If the training plan has one session for "all users" without role or persona segmentation, it is too generic. Search for `all users` without corresponding persona breakdown.

---

## Anti-Pattern 2: Omitting go-live communication timing and channel strategy

**What the LLM generates:** "Send an email to all users announcing the Salesforce go-live."

**Why it happens:** LLMs produce a single announcement and call it communication. Effective change management requires multiple touchpoints before, during, and after go-live, delivered through channels that reach each audience (email, Slack, Chatter, in-app guidance, town hall meetings).

**Correct pattern:**

```
Communication timeline:
- 4 weeks before: Executive sponsor announcement (email + town hall).
- 2 weeks before: Role-specific "What's Changing" guides (email + Chatter).
- 1 week before: "How to Prepare" checklist with sandbox access for practice.
- Go-live day: In-app guidance prompts + support channel announcement.
- 1 week after: "Tips & Tricks" follow-up + feedback survey.
- 1 month after: Adoption metrics review + targeted re-training for low adopters.

Use the channels your users already check — not just email.
```

**Detection hint:** If the output has a single communication event rather than a phased communication plan, the strategy is incomplete. Search for a timeline with multiple dates or the word `phased`.

---

## Anti-Pattern 3: Recommending Trailhead as the entire training strategy

**What the LLM generates:** "Assign the relevant Trailhead modules to your users. Trailhead will handle the training."

**Why it happens:** LLMs know Trailhead is Salesforce's learning platform and default to it. Trailhead teaches generic Salesforce concepts but does not cover org-specific configurations, custom objects, business processes, or company-specific workflows. Users trained only on Trailhead still do not know how to do their actual job in the org.

**Correct pattern:**

```
Trailhead is a supplement, not a replacement for org-specific training:
1. Use Trailhead for foundational concepts (navigation, record creation).
2. Build org-specific training materials that show:
   - The actual page layouts, fields, and picklist values users will see.
   - The specific business processes and approval workflows in your org.
   - Screenshots or recordings from your sandbox, not generic Trailhead content.
3. Combine Trailhead badges with hands-on practice in a training sandbox.
4. Measure completion of both Trailhead AND org-specific exercises.
```

**Detection hint:** If the output lists only Trailhead modules as the training plan without org-specific materials, the training is incomplete. Search for `Trailhead` without accompanying `org-specific` or `custom` training references.

---

## Anti-Pattern 4: Skipping change impact assessment before training design

**What the LLM generates:** "Here is a training plan for the new Salesforce features: Session 1 covers Lightning Experience basics..."

**Why it happens:** LLMs jump to training content without first assessing what changed for each user group. Without a change impact assessment, the training plan may cover features that are unchanged or miss the features that actually disrupt user workflows.

**Correct pattern:**

```
Change impact assessment first, training plan second:

| Change                  | Affected Persona | Impact Level | Training Need       |
|-------------------------|------------------|--------------|---------------------|
| New approval workflow   | Sales Reps       | High         | Hands-on walkthrough|
| Dashboard redesign      | Sales Managers   | Medium       | Demo + quick ref    |
| New picklist values     | Service Agents   | Low          | Release note only   |
| Retired Process Builder | None (backend)   | None         | No user training    |

Only build training for High and Medium impact changes.
Low impact → release notes. No impact → skip entirely.
```

**Detection hint:** If the output produces a training plan without a preceding change impact assessment, the plan may be misaligned with actual user impact. Search for `change impact` or `impact assessment`.

---

## Anti-Pattern 5: Ignoring adoption metrics and post-go-live feedback loops

**What the LLM generates:** "After go-live, the change management phase is complete."

**Why it happens:** LLMs treat go-live as the finish line. In reality, adoption problems surface in the first 2-4 weeks after launch. Without defined adoption metrics and feedback mechanisms, low adoption goes undetected until it becomes a crisis.

**Correct pattern:**

```
Post-go-live adoption tracking:
1. Define measurable adoption KPIs before go-live:
   - Login frequency by role (Setup → Login History or reports).
   - Record creation rates (new Opportunities, Cases per week).
   - Feature usage (Flow execution counts, report subscriptions).
2. Set up a feedback channel (Chatter group, Slack channel, or survey).
3. Review adoption metrics weekly for the first month.
4. Conduct targeted re-training for roles with < 70% adoption.
5. Document and address the top 5 user complaints within 2 weeks.
```

**Detection hint:** If the output ends at go-live without mentioning adoption metrics, feedback channels, or post-launch follow-up, the change management plan is incomplete. Search for `adoption`, `metrics`, or `feedback` in the post-go-live section.
