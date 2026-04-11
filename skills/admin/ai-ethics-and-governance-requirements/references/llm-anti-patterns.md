# LLM Anti-Patterns — AI Ethics and Governance Requirements

Common mistakes AI coding assistants make when generating or advising on AI ethics and governance requirements for Salesforce implementations. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Einstein Trust Layer Configuration with AI Governance

**What the LLM generates:** When asked to help with AI governance, the assistant immediately starts describing how to enable the Einstein Trust Layer, configure prompt templates, and set toxicity score thresholds. It produces setup steps for the Trust Layer and frames this as completing the governance requirement.

**Why it happens:** "AI governance" and "Einstein Trust Layer" co-occur frequently in Salesforce AI documentation. Training data treats them as closely related, which causes the model to conflate them when asked about governance. The Trust Layer is a concrete, configurable feature — easy to describe; governance policy is abstract — easier to skip.

**Correct pattern:**

```
Governance requirements work covers:
- Risk inventory (use case classification, likelihood-impact grid)
- Responsible AI pillar mapping (Accuracy, Safety, Honesty, Empowerment, Sustainability)
- Human oversight gate design (approval workflows, reviewer roles, SLAs)
- Bias mitigation (protected attributes list, bias report review, proxy field removal)
- Transparency disclosures (AI-generated content labels, legal copy)
- Audit trail specification (what is logged, retention period, access control)

Trust Layer configuration is a separate skill: agentforce/einstein-trust-layer.
Always clarify which the user needs before proceeding.
```

**Detection hint:** If the response mentions "enable Einstein Trust Layer" or "configure prompt defense" as the primary answer to an AI governance question, this anti-pattern is present.

---

## Anti-Pattern 2: Producing a Governance Policy That Only Covers In-Scope Features at Time of Writing

**What the LLM generates:** A governance policy document that lists the specific Einstein features currently enabled in the org (e.g., "Einstein Lead Scoring and Next Best Action are governed under this policy") without any mechanism for capturing new features added in future releases or through admin configuration.

**Why it happens:** LLMs optimize for concreteness. Listing specific features produces a document that reads as complete. Including dynamic scoping language ("all AI features enabled now or in future") is vaguer and requires the human to do more work, so the model avoids it.

**Correct pattern:**

```
AI Governance Policy scope clause:
"This policy applies to all Salesforce Einstein features, Agentforce agents,
and third-party AI integrations enabled in [Org Name]'s production org and
all connected environments, whether active at the time of this policy's
adoption or enabled at any future date. New AI features must be reviewed
against this policy before being activated in production."
```

**Detection hint:** If the policy document contains only a named list of features with no forward-looking scope language, prompt the LLM to add a future-feature inclusion clause.

---

## Anti-Pattern 3: Recommending Field History Tracking as the Complete AI Audit Log

**What the LLM generates:** When asked how to audit AI decisions in Salesforce, the assistant recommends enabling Field History Tracking on the field that Einstein writes to (e.g., the Lead Score field) and points to Setup > Object Manager > Field History as the audit mechanism.

**Why it happens:** Field History Tracking is the most commonly documented Salesforce audit mechanism. It appears in training data far more frequently than custom AI audit log patterns. The model defaults to the familiar recommendation without reasoning about what Field History Tracking actually captures.

**Correct pattern:**

```
Field History Tracking records value changes — it does NOT capture:
- The AI model version that produced the value
- The model's confidence score
- The top contributing predictor fields
- Whether the change was AI-generated vs. human-edited

For AI audit compliance, supplement Field History Tracking with:
- A custom AI Decision Log object (fields: RecordId, AIFeature, ModelVersion,
  PredictionScore, ContributingFeatures, Timestamp, UserContext)
- A Flow or Apex trigger that writes to this object whenever Einstein
  updates the audited field
- A Data Cloud retention rule for long-term storage beyond Salesforce's
  18-month field history limit
```

**Detection hint:** Any response that mentions only Field History Tracking as the AI audit solution, without discussing model version, contributing features, or retention limits, is incomplete.

---

## Anti-Pattern 4: Treating Bias Detection as a One-Time Pre-Deployment Activity

**What the LLM generates:** A bias mitigation plan that includes "run the Einstein bias detection report before go-live and document the results" as a single checklist item, with no mention of what happens after the model retrains.

**Why it happens:** LLMs model governance as a deployment phase — a set of tasks completed before launch. The concept that a retrained model can introduce new bias, and that retraining is a recurring event requiring a new governance checkpoint, is less salient in training data than pre-deployment checklists.

**Correct pattern:**

```
Bias governance is continuous, not one-time:

Pre-deployment:
- Run bias report on initial training data
- Document protected and proxy attributes
- Remove or bucket proxy fields
- Sign off on bias report results before model activation

After each model retraining:
- Re-run bias report on retrained model BEFORE production promotion
- Compare results to baseline
- If disparate impact exceeds threshold, hold model in UAT pending investigation
- Document results and sign-off in the bias mitigation log

Retraining governance gate must be built into the model promotion process
(approval workflow or DevOps pipeline step), not left to manual reminder.
```

**Detection hint:** If the bias mitigation section ends at initial deployment without describing a retraining governance gate, the anti-pattern is present.

---

## Anti-Pattern 5: Omitting Jurisdiction-Specific Regulatory Requirements from the Governance Framework

**What the LLM generates:** A generic AI governance framework based on Salesforce's responsible AI pillars alone, with no mention of applicable external regulations (EU AI Act, CCPA/CPRA, HIPAA, FINRA). The document treats governance as a Salesforce-internal standard rather than a legal compliance requirement.

**Why it happens:** LLMs are trained on generic Salesforce documentation that emphasizes platform-native governance tools. External regulatory requirements vary by jurisdiction and industry, and the model often avoids specifics to remain broadly applicable, defaulting to the safest (least specific) answer.

**Correct pattern:**

```
Governance framework must include a jurisdiction and industry mapping:

For each AI use case, document:
1. Geographic scope of affected users (e.g., EU residents, California residents)
2. Industry context (healthcare → HIPAA, financial services → FINRA/SEC, insurance → state regulators)
3. Regulatory obligations triggered:
   - EU AI Act: risk tier classification, conformity assessment for high-risk, human oversight requirement
   - CCPA/CPRA: right to opt out of automated decision-making, disclosure requirement
   - HIPAA: AI use of PHI requires BAA coverage and minimum-necessary standard
4. Legal sign-off required before go-live for any use case with regulatory exposure

Do not substitute Salesforce's internal responsible AI pillars for regulatory compliance review.
```

**Detection hint:** A governance document that references only Salesforce's five responsible AI pillars (Accuracy, Safety, Honesty, Empowerment, Sustainability) without any mention of applicable external regulations should trigger a regulatory scoping question.

---

## Anti-Pattern 6: Designing Human Oversight Gates That Are Bypassed in Practice Due to Volume

**What the LLM generates:** A human oversight design that requires a named approver to review every AI recommendation before it is acted on, regardless of volume. The design does not address what happens when the volume of recommendations exceeds the approver's capacity, or when the SLA for review is not met.

**Why it happens:** LLMs optimize for compliance-sounding language. "Every recommendation must be reviewed by a licensed advisor" satisfies the oversight requirement on paper. The operational reality — that 500 AI recommendations per day cannot be reviewed by one advisor — is a downstream concern the model does not proactively surface.

**Correct pattern:**

```
Human oversight design must include:
1. Expected recommendation volume per day/week
2. Reviewer capacity (hours available for review per day, number of reviewers)
3. SLA for review turnaround
4. Escalation rule when SLA is breached (who is notified, what is the fallback)
5. Volume threshold above which the oversight model must change
   (e.g., if volume exceeds N per day, move to sampling-based review with
   documented statistical justification)
6. Prohibition on suppressing AI recommendations when review queue is backlogged
   (recommendations must be held, not auto-approved due to queue depth)
```

**Detection hint:** Any oversight design that specifies a reviewer role and approval requirement but does not address volume, SLA, or backlog handling is operationally incomplete.
