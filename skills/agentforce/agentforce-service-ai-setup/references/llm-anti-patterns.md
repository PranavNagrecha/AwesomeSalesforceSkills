# LLM Anti-Patterns — Agentforce Service AI Setup

Common mistakes AI coding assistants make when generating or advising on Einstein for Service AI feature setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming Work Summaries Is Included in Service Cloud Einstein

**What the LLM generates:** Advice that says "Enable Work Summaries by navigating to Setup > Service > Einstein Work Summaries — this feature is included with your Service Cloud Einstein license." Or a setup guide that lists Work Summaries alongside Case Classification and Article Recommendations as if all three are covered by the same Service Cloud Einstein add-on.

**Why it happens:** LLMs conflate "Einstein for Service" as a product family name with specific license tiers within that family. Training data likely includes Salesforce marketing content that describes the full Einstein for Service feature set without consistently distinguishing which features require which license tier.

**Correct pattern:**

```
Einstein for Service features split across TWO license tiers:

PREDICTIVE AI (Service Cloud Einstein add-on OR Einstein 1 Service):
  - Case Classification
  - Article Recommendations
  - Reply Recommendations

GENERATIVE AI (Einstein Generative AI add-on OR Einstein 1 Service — NOT included in base Service Cloud Einstein):
  - Work Summaries (After-Visit Summary)
  - Service Replies with Einstein

Always verify: Setup > Company Information > Permission Set Licenses
Look for: "Einstein Generative AI" PSL
If absent: Work Summaries and Service Replies CANNOT be enabled
```

**Detection hint:** Any response that lists Work Summaries and Case Classification as enabled by the same single license without distinguishing license tiers is likely wrong. Look for "Service Cloud Einstein includes all Einstein for Service features" — that claim is false for generative AI features.

---

## Anti-Pattern 2: Stating the Minimum Case Threshold for Case Classification Is 400

**What the LLM generates:** "Case Classification requires at least 400 closed cases to train. If your org has 400 or more closed cases, you can enable the feature and expect reliable predictions."

**Why it happens:** 400 is the documented Salesforce minimum for the model training pipeline to run. LLMs reproduce this number from Help documentation without surfacing the nuance that 400 is the floor for training to execute, not the threshold for useful predictions. The distinction is meaningful for implementation advice but absent from most training data sources.

**Correct pattern:**

```
Two different thresholds — understand both:

TRAINING FLOOR (model will attempt to train): 400 closed cases
PRACTICAL ACCURACY THRESHOLD (predictions worth trusting): 1,000+ closed cases
  with >80% non-null values in each classified field

At 400–1,000 closed cases: Model trains but accuracy is typically 50–70%.
Agents will override frequently and lose trust in the feature.

Recommendation: Defer Case Classification until 1,000+ closed cases with
>80% field completeness per classified field. Document case volume and
set a milestone review date.
```

**Detection hint:** Any response that treats 400 closed cases as sufficient for reliable production use of Case Classification without qualification is applying the documented floor incorrectly as a readiness threshold.

---

## Anti-Pattern 3: Omitting the Reply Recommendations Training Data Job Step

**What the LLM generates:** A setup guide that says "Enable Reply Recommendations in Setup > Service > Einstein Reply Recommendations, then add the Suggested Replies component to the messaging console. Agents will see suggestions after the model trains." The guide omits any mention of the Training Data job.

**Why it happens:** Most Einstein for Service features begin model training automatically after the feature is enabled. Reply Recommendations is the exception — it requires a separate, explicit admin action (running the Training Data job) before training can begin. LLMs trained on documentation that describes the general Einstein for Service activation pattern apply that pattern uniformly, missing the Reply Recommendations exception.

**Correct pattern:**

```
Reply Recommendations activation sequence:
1. Enable in Setup > Service > Einstein Reply Recommendations
2. ← REQUIRED, NON-OBVIOUS STEP: Click "Build Training Data"
   and wait for the Training Data job to complete (2–24 hours)
3. Confirm Training Data job status = "Completed" in Setup
4. Wait for model training to complete after Training Data job finishes
   (additional 24–48 hours)
5. Add Suggested Replies component to messaging console layout
6. Test with a live messaging session

Without Step 2: Feature is "enabled" but produces zero suggestions.
No error is surfaced. Feature appears broken with no obvious diagnosis.
```

**Detection hint:** Any Reply Recommendations setup guide that does not explicitly mention the "Build Training Data" step is incomplete. Check whether the LLM output includes "Training Data job" — if absent, the guide will fail in production.

---

## Anti-Pattern 4: Recommending Auto-Populate Mode for Initial Case Classification Deployment

**What the LLM generates:** "Enable Case Classification in auto-populate mode to maximize efficiency. Fields will be filled automatically so agents can focus on resolving cases rather than data entry."

**Why it happens:** Auto-populate mode is described as the efficient choice in Salesforce documentation and marketing content. LLMs optimize toward what sounds like the best outcome (efficiency, automation) without surfacing the reliability risk of deploying autonomous field population before model accuracy is validated.

**Correct pattern:**

```
Initial deployment: ALWAYS start in Suggestion mode

Why:
- Auto-populate propagates incorrect values silently
- Agents may not notice wrong values → bad data enters pipeline
- Wrong data corrupts future model training (feedback loop failure)
- Low-accuracy model + auto-populate = trust destruction within 30 days

Suggestion mode:
- Agents see proposed value + Accept/Reject control
- Explicit rejections provide training feedback that improves the model
- Admin can monitor suggestion acceptance rate before trusting auto-populate

Migration path:
- Run in Suggestion mode for 30–60 days
- Review model accuracy in Setup > Einstein Classification Apps > View Model
- If precision > 85% for 30+ days → consider switching to auto-populate
- Document the decision and rationale
```

**Detection hint:** Any setup recommendation that leads with auto-populate mode for a new deployment without qualifying model accuracy verification is a red flag for operational risk.

---

## Anti-Pattern 5: Ignoring Data Cloud as a Prerequisite for Work Summaries

**What the LLM generates:** "To enable Work Summaries, you need Einstein Generative AI license or Einstein 1 Service. Once that license is provisioned, navigate to Setup > Service > Einstein Work Summaries and enable the feature."

**Why it happens:** The Einstein Generative AI license is the most prominently documented prerequisite for Work Summaries. Data Cloud is a secondary dependency that appears in specific org configurations and is less consistently documented in feature overview pages. LLMs reproduce the primary prerequisite but omit the secondary dependency.

**Correct pattern:**

```
Work Summaries prerequisites — check ALL of the following:

1. License: Einstein Generative AI PSL or Einstein 1 Service edition
   → Setup > Company Information > Permission Set Licenses

2. Data Cloud entitlement (required in many org configurations):
   → Setup > Data Cloud > verify provisioning
   → If absent: Work Summaries may be unavailable regardless of AI license

3. Active Messaging or Voice channel:
   → Work Summaries generates output from conversation transcripts
   → Email-only orgs have no applicable transcript source

4. Einstein Trust Layer active:
   → Generative AI features route content through Trust Layer
   → Verify Trust Layer settings before enabling

Missing Data Cloud + Einstein Generative AI license: Feature may still
be absent or non-functional depending on org configuration.
```

**Detection hint:** Any Work Summaries setup guide that lists only the Einstein Generative AI license as the sole prerequisite without mentioning Data Cloud or channel requirements is likely missing a critical prerequisite check.

---

## Anti-Pattern 6: Treating Einstein for Service Setup as a One-Time Configuration Event

**What the LLM generates:** A setup checklist that ends at "features enabled and components added to page layouts." The guide presents enablement as the completion state — no mention of ongoing model feedback loops, agent behavior requirements, or post-go-live optimization.

**Why it happens:** LLMs optimize toward completion. Setup guides naturally have a terminal state. The ongoing nature of ML model quality — which depends on agent behavior creating training feedback — is not commonly expressed as part of a setup document; it is expressed in optimization or administration documentation that may not surface in setup-focused training data.

**Correct pattern:**

```
Einstein for Service is NOT a configure-and-forget platform feature.
Model quality depends on ongoing agent behavior creating training feedback:

Case Classification:
  → Model improves when agents review and correct suggestions (Suggestion mode)
  → Auto-populate without agent correction = no feedback loop = model drift

Article Recommendations:
  → Model improves when agents consistently link articles to cases at resolution
  → Orgs that never link articles = flat or degrading recommendation quality

Reply Recommendations:
  → Model improves as messaging volume grows and good replies are used
  → Low messaging volume = thin corpus = weak suggestions

Post-go-live actions that MUST be included in any setup plan:
1. Train agents on the importance of reviewing and correcting AI suggestions
2. Establish an article-linking habit for case resolution
3. Schedule a 30-day and 90-day model quality review
4. Monitor model accuracy metrics in Setup > Einstein Classification Apps
```

**Detection hint:** Any setup guide that does not address agent behavior as part of feature quality maintenance is presenting Einstein for Service as a technology configuration problem rather than an adoption and feedback-loop problem.
