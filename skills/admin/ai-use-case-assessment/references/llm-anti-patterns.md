# LLM Anti-Patterns — AI Use Case Assessment

Common mistakes AI coding assistants make when generating or advising on AI use case assessments for Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Skipping Data Readiness Scoring and Jumping Straight to Use Case Recommendations

**What the LLM generates:** A prioritized list of AI use cases to pursue ("You should implement Einstein Lead Scoring, Einstein Opportunity Scoring, and Work Summaries") without first scoring data readiness for each use case against the four sub-dimensions (availability, quality, unification, governance).

**Why it happens:** LLMs are trained to be helpful and produce actionable output quickly. The data readiness scoring step requires structured judgment about a specific org's data posture that is not present in the input, so LLMs skip it and produce recommendations based solely on use case popularity or strategic framing.

**Correct pattern:**

```
Before recommending any use case, score each against data readiness:

Use Case: Einstein Lead Scoring
- Availability: Are there 1,000+ Lead records with outcome data (converted/not)? Score: ?
- Quality: Are key signal fields (Industry, Company Size, Lead Source) consistently populated? Score: ?
- Unification: Is Lead data enriched from any external source in Data Cloud? Score: ?
- Governance: Is Lead data access controlled per data classification policy? Score: ?

Only proceed to recommendation if composite score >= 6/12.
```

**Detection hint:** Output contains a "recommended use cases" section without a preceding data readiness scorecard or any mention of the four data readiness sub-dimensions.

---

## Anti-Pattern 2: Conflating Assessment with Implementation Guidance

**What the LLM generates:** Assessment output that includes implementation steps, configuration instructions, or technical architecture details alongside the feasibility scorecard — e.g., "This use case is feasible. To implement it, go to Setup > Einstein > Lead Scoring and enable the toggle."

**Why it happens:** LLMs have extensive training data on "how to implement" Salesforce features and default to producing implementation guidance when the context involves a Salesforce AI feature. The boundary between pre-implementation assessment and implementation is not a natural stopping point for LLMs.

**Correct pattern:**

```
Assessment output (correct boundary):
- Use case: Einstein Lead Scoring
- Feasibility verdict: Approved — conditional on data quality remediation
- Recommended next step: Route to implementation project intake
- Related skill: agentforce-service-ai-setup (for Service features) or feature-specific implementation skill

Implementation guidance belongs in a separate skill activation, not in this output.
```

**Detection hint:** Assessment response includes Setup navigation paths, metadata API calls, Apex code snippets, or Flow configuration details.

---

## Anti-Pattern 3: Treating "We Have Unlimited Edition" as Full Technical Feasibility Confirmation

**What the LLM generates:** Technical feasibility marked as confirmed for Einstein for Service generative features, Einstein for Sales predictive features, or Agentforce based solely on the org's edition being Enterprise or Unlimited, without verifying specific add-on licenses.

**Why it happens:** LLMs associate "Enterprise Edition" or "Unlimited Edition" with broad feature access because much Salesforce marketing and documentation describes features as "available in Enterprise and above." The add-on license requirement layer is frequently underemphasized in training data relative to the edition-level access narrative.

**Correct pattern:**

```
Technical Feasibility Check — required for each use case:
1. Confirm base edition (Enterprise/Unlimited/Developer)
2. Confirm required add-on license present in Setup > Company Information > Permission Set Licenses:
   - Einstein for Service: required for Work Summaries, Service Replies
   - Einstein for Sales: required for Lead Scoring, Opportunity Scoring
   - Agentforce: required for all Agentforce agents
3. Only mark Technical Feasibility as confirmed if BOTH edition AND add-on are verified.
```

**Detection hint:** Technical feasibility section says "confirmed — Enterprise Edition supports this feature" without mentioning add-on license verification.

---

## Anti-Pattern 4: Producing a Financial ROI Projection Instead of an ROI Narrative

**What the LLM generates:** A spreadsheet-style table with specific dollar amounts, percentage improvements, and payback period calculations — e.g., "Expected annual savings: $450,000 based on 15% reduction in handle time at $30/hour average agent cost."

**Why it happens:** ROI requests trigger LLMs to produce financial models because that is what most ROI requests look like in training data (business cases, financial analyses). LLMs fill in the specific numbers using plausible-sounding assumptions without flagging that those assumptions are fabricated.

**Correct pattern:**

```
ROI Narrative (correct output):
- Value driver: Reduction in average handle time via Work Summaries
- Key assumption: Handle time reduction is in the 20-30% range reported by Salesforce customer benchmarks (source: Salesforce Success Stories)
- Payback period category: < 6 months (high confidence, based on quick-win profile and low activation effort)
- Risk: Actual handle time reduction depends on agent adoption and quality of Case data — validate with a 30-day pilot

Do NOT produce specific dollar amounts without the org's own baseline metrics and finance team validation.
```

**Detection hint:** Response contains specific dollar figures, percentage improvements stated as facts rather than estimates with sources, or a multi-row financial projection table.

---

## Anti-Pattern 5: Recommending a Single "Best" AI Use Case Without Running the Full Matrix

**What the LLM generates:** A single top recommendation or a ranked list ordered by the LLM's own implicit preference, without producing the full Impact-Effort matrix with all candidate use cases scored and quadrant-assigned.

**Why it happens:** LLMs optimize for conciseness and actionability. Presenting a full scoring matrix feels like unnecessary complexity when a clear recommendation is possible. LLMs also have implicit biases toward recently published or highly discussed Salesforce features (e.g., Agentforce, Einstein Copilot) that inflate their implicit ranking without explicit scoring.

**Correct pattern:**

```
All candidate use cases must appear in the matrix before a recommendation is made:

| Use Case               | Impact (1-3) | Effort (1-3) | Quadrant        |
|------------------------|-------------|-------------|-----------------|
| Work Summaries         |      3      |      1      | Quick Win       |
| Case Classification    |      2      |      1      | Quick Win       |
| 360 Customer View Agent|      3      |      3      | Big Bet         |
| Predictive CSAT Scoring|      2      |      3      | Big Bet         |
| Email Insights         |      1      |      1      | Low-Hanging Fruit|

Recommendation: Prioritize Quick Wins first. [Rationale follows from matrix, not from LLM preference.]
```

**Detection hint:** Response contains a single "recommended use case" or a ranked list without an accompanying Impact-Effort matrix showing all candidates that were considered.
