# LLM Anti-Patterns — Self-Service Design

Common mistakes AI assistants make when generating or advising on self-service portal design for Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Providing Community Setup Steps Instead of Design Guidance

**What the LLM generates:** Step-by-step instructions for creating an Experience Cloud site, enabling the Customer Community license, configuring community settings in Setup, and assigning profiles to the community — presented as self-service portal "design" guidance.

**Why it happens:** "Self-service portal" and "Experience Cloud" are frequently co-occurring terms in Salesforce documentation and training content. LLMs conflate the design question (how should the portal work for users?) with the configuration question (how do I technically set up the portal?). The setup instructions are plentiful in training data; the design principles are sparser.

**Correct pattern:**

When the practitioner asks about self-service portal design, respond with:
- UX structure decisions (search vs. browse, friction calibration, zero-results handling)
- Article coverage and findability requirements before launch
- Deflection measurement setup
- Community peer support readiness criteria

Not with:
- Experience Cloud site creation steps
- Profile and permission set assignment for community users
- Network settings or domain configuration

**Detection hint:** If the response includes phrases like "Go to Setup > Digital Experiences > All Sites" or "assign the Customer Community Plus license," it has drifted into configuration guidance rather than design guidance.

---

## Anti-Pattern 2: Omitting Pre-Submission Search Prompts from the Case Submission Flow

**What the LLM generates:** A case submission form design that presents fields (subject, description, category, priority) directly without a pre-deflection article surfacing step. The LLM describes the Case Creation component but does not mention enabling Knowledge article suggestions or placing a search prompt before the form.

**Why it happens:** The Case Creation component's article suggestion feature is a configuration option, not a default behavior. LLMs trained on generic form design patterns default to direct form presentation. The pre-deflection pattern requires knowledge of the specific Salesforce Case Creation component setting and the Case Deflection component — both of which are less prominent in training data than the case form itself.

**Correct pattern:**

Every case submission flow design for a portal with a Knowledge base should specify:
1. Where the article suggestion prompt appears (after subject entry, before or after description entry)
2. How many article suggestions are displayed
3. What happens when no suggestions match (zero-results behavior, immediate case form reveal vs. prompt to refine search)
4. Whether article acknowledgment is required before the Submit button activates

**Detection hint:** If the case submission flow design does not mention Knowledge article suggestions, the Case Creation component's pre-deflection feature, or a search prompt step, the pre-deflection mechanism has been omitted.

---

## Anti-Pattern 3: Confusing Deflection with Abandonment

**What the LLM generates:** A recommendation to add multiple friction steps to the case submission form (article rating requirements, mandatory explanation fields for why no article helped, multi-page pre-submission wizards) to "maximize deflection." The LLM frames all case form exits as positive deflection outcomes.

**Why it happens:** LLMs associate friction with deflection in a linear relationship: more friction = more deflection. This is correct up to a point but ignores abandonment as a distinct failure mode. Training data on self-service design often focuses on deflection rate without equally covering abandonment rate as a counter-metric.

**Correct pattern:**

Deflection = customer found an answer and did not need to submit a case.
Abandonment = customer left the case form without submitting AND without finding an answer — an unresolved need that will resurface through a higher-cost channel.

Design guidance must:
- Specify both metrics as required measurements
- Define a friction ceiling (e.g., "if abandonment exceeds 15%, reduce the friction step")
- Recommend progressive disclosure or a low-friction mandatory search prompt with a clear "I still need to submit" escape, rather than article rating requirements

**Detection hint:** If the response recommends friction additions without mentioning abandonment measurement, or if it treats any case form exit as a deflection success, this anti-pattern is present.

---

## Anti-Pattern 4: Not Measuring Baseline Contact Volume Before Portal Launch

**What the LLM generates:** A self-service portal design and implementation plan with no mention of establishing a pre-launch baseline for case volume, contact rate per portal session, or contact reason distribution. The plan proceeds directly to UX design and goes live without defining what "success" looks like numerically.

**Why it happens:** LLMs default to actionable next steps. Establishing a measurement baseline is a precondition activity, not a build activity, and is frequently absent from design-focused content in training data. The deflection measurement value is only apparent post-launch when compared against a baseline — without a baseline, the metric is uninterpretable.

**Correct pattern:**

Before any portal design work begins, document:
- Total case volume by contact reason for the preceding 90 days (minimum)
- Contact rate: total cases per 1,000 portal sessions (if portal already exists)
- The specific deflection rate target (e.g., "reduce warranty claim cases by 25%")

This baseline becomes the benchmark against which post-launch deflection metrics are evaluated. Without it, no business case for the portal investment can be made post-launch, and no intervention decisions (add friction, remove friction, invest in more articles) can be data-driven.

**Detection hint:** If the design plan or workflow does not include a step for establishing baseline metrics before launch, this anti-pattern is present.

---

## Anti-Pattern 5: Recommending Community Q&A Without Seeding and Moderation Capacity

**What the LLM generates:** A recommendation to enable Experience Cloud Questions or Chatter Q&A as a peer support deflection channel with no mention of content seeding requirements, internal advocate coverage, or moderation workflow. The recommendation implies community engagement will develop organically after launch.

**Why it happens:** Community peer support is described as a self-sustaining, scalable deflection mechanism in Salesforce marketing and trailhead content. The seeding and moderation prerequisites are documented but receive less emphasis. LLMs reproduce the aspirational description of peer community without the operational requirements.

**Correct pattern:**

Community Q&A is only appropriate to recommend when the following can be committed before launch:
- 20–50 pre-seeded Q&A pairs using real customer question phrasings
- Internal advocate coverage: 2–3 people with a 24-hour response SLA for the first 30 days
- Expert recognition mechanism active from day one
- Moderation workflow defined and resourced

If these cannot be committed, the correct recommendation is to defer community Q&A, not launch it empty. An unseeded community contributes zero deflection and creates a perception of neglect that suppresses all future engagement.

**Detection hint:** If the response recommends enabling community Q&A without specifying pre-seeded content volume, internal advocate coverage, and a moderation plan, this anti-pattern is present.

---

## Anti-Pattern 6: Treating Article Authoring as Out of Scope for Self-Service Design

**What the LLM generates:** A self-service portal design that specifies UX layout, search configuration, and deflection measurement without addressing the article inventory. The LLM presents article authoring as a separate, pre-completed prerequisite and proceeds to design as if the article base is already adequate.

**Why it happens:** Design and content are often treated as separate workstreams in project management frameworks. LLMs respect these boundaries and scope self-service design to UX artifacts, treating content as an input rather than a design variable.

**Correct pattern:**

Article coverage and findability are the primary determinants of self-service deflection rate — more impactful than any UX improvement. A self-service design deliverable must include:
- Article coverage assessment for the top contact reasons
- Gap list: contact reasons with no matching published article
- Findability audit: article title terminology vs. customer search vocabulary
- Explicit recommendation to block portal launch if coverage is below threshold

Design work is gated on this assessment. If the LLM skips this gate, the resulting design will be implemented correctly and produce no deflection improvement.

**Detection hint:** If the self-service design guidance does not include an article coverage assessment step as a prerequisite or gate, this anti-pattern is present.
