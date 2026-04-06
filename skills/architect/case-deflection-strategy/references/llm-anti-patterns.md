# LLM Anti-Patterns — Case Deflection Strategy

Common mistakes AI coding assistants make when generating or advising on Case Deflection Strategy.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Chatbot Before Assessing Knowledge Readiness

**What the LLM generates:** A deflection roadmap that starts with "Step 1: Deploy Einstein Bot" without asking whether the org has customer-readable knowledge articles covering the intended deflection topics.

**Why it happens:** LLMs associate "case deflection" with chatbots because chatbot deployments are heavily documented in training data. The prerequisite knowledge readiness assessment is a less dramatic step and is underrepresented in how-to content.

**Correct pattern:**

```
Step 1: Run ECM or case volume analysis to identify top deflection topics
Step 2: Audit knowledge article coverage and readiness for those topics
Step 3: Remediate knowledge gaps (author missing articles, fix data categories)
Step 4: Deploy deflection channel (bot or portal search-first gate)
Step 5: Instrument KPIs and measure GCR + deflection rate
```

**Detection hint:** If the generated plan does not mention "knowledge" or "articles" before "bot," the prerequisite step has been skipped.

---

## Anti-Pattern 2: Using "Containment Rate" and "Deflection Rate" Interchangeably

**What the LLM generates:** KPI recommendations that equate containment rate with deflection rate, or that use only one of these metrics to evaluate deflection program success.

**Why it happens:** Many published bot case studies use "containment" and "deflection" as synonyms. LLMs trained on this corpus reproduce the conflation.

**Correct pattern:**

```
Deflection rate = (sessions where customer issue was resolved in self-service) / (total inbound sessions)
Containment rate = (sessions with no agent transfer) / (total bot sessions)
Goal completion rate = (sessions where customer achieved their stated goal) / (total self-service sessions)

All three metrics are required. Containment without GCR is a vanity metric.
```

**Detection hint:** Check whether the generated KPI list includes goal completion rate. If it only mentions deflection rate or containment rate without GCR, the metric framework is incomplete.

---

## Anti-Pattern 3: Treating ECM as Available for All Contact Channels

**What the LLM generates:** A recommendation to use Einstein Conversation Mining to analyze email, web form, or phone contact reasons alongside chat/messaging data.

**Why it happens:** "Einstein Conversation Mining" sounds like it should analyze all conversation types. LLMs often generalize it to all inbound contact channels without checking its actual data source requirements.

**Correct pattern:**

```
Einstein Conversation Mining analyzes: Messaging for In-App and Web transcripts, Live Agent Chat transcripts
Einstein Conversation Mining does NOT analyze: Email-to-Case, Web-to-Case, Phone/Voice (CTI)

For email-dominant orgs, use case report analysis:
- Export Case Subject and Description fields
- Run keyword frequency analysis or manual clustering
- Use this as the substitute topic identification input
```

**Detection hint:** If the plan says "run ECM on your email cases" or "ECM will show you your top phone contact reasons," the recommendation is incorrect.

---

## Anti-Pattern 4: Ignoring Data Category Visibility in Bot Article Search Advice

**What the LLM generates:** Instructions to configure Einstein Article Recommendations in an Einstein Bot with steps that reference only the bot builder configuration, without covering data category visibility setup for the guest user profile on the Experience Cloud site.

**Why it happens:** Bot builder documentation focuses on the bot dialog and NLU configuration. Data category visibility is documented separately in the Knowledge and Experience Cloud documentation, creating a documentation gap that LLMs reproduce.

**Correct pattern:**

```
For Einstein Article Recommendations in a bot embedded in Experience Cloud:
1. Confirm the Experience Cloud site has a Knowledge data category group assigned
2. Confirm the guest user profile has visibility to the appropriate data categories
3. Assign articles to data categories that match the guest user visibility grants
4. Test article search using Experience Cloud Site Preview (guest mode) — NOT the bot test harness
5. The bot test harness runs as admin; it bypasses data category visibility rules
```

**Detection hint:** If the bot article search instructions do not mention data category visibility or guest user profile configuration, the advice is incomplete and will produce "articles not found" issues in production.

---

## Anti-Pattern 5: Setting a Flat 27% Deflection Rate Target Without Context

**What the LLM generates:** A KPI plan that sets 27% deflection rate as the target for all deployments, citing the Salesforce industry average, without adjusting for the org's current state, topic coverage, or knowledge readiness.

**Why it happens:** The 27% figure is widely cited in Salesforce marketing and documentation. LLMs reproduce it as a universal target rather than a benchmark to calibrate against.

**Correct pattern:**

```
27% is an industry average across all Einstein Bot deployments — it is a benchmark, not a target.

Calibrate deflection rate targets based on:
1. What percentage of total inbound volume do wave 1 deflection topics represent?
   (If top 5 topics = 35% of volume, max achievable deflection rate from wave 1 is ~35%)
2. What is the bot's expected NLU confidence for those topics? (affects containment)
3. How complete is the knowledge base for those topics? (affects GCR)

A more useful framing: set a per-topic deflection rate target (e.g., 60% of "account balance"
contacts resolved in bot) and roll up to an overall program rate rather than targeting
the industry average as a fixed number.
```

**Detection hint:** If the target deflection rate is exactly 27% with no calculation showing how that number relates to the specific org's contact volume distribution, the target has been copied from a benchmark rather than derived from the org's data.

---

## Anti-Pattern 6: Recommending NLU Bots Without Sufficient Training Data

**What the LLM generates:** An architecture recommendation for an NLU-driven Einstein Bot for an org that has fewer than 90 days of chat transcripts or fewer than 100 examples per intent category.

**Why it happens:** NLU bots are the modern recommended pattern and appear prominently in Salesforce documentation. LLMs default to recommending NLU without assessing whether the org has the training data volume needed to produce reliable intent classification.

**Correct pattern:**

```
NLU bot: requires minimum ~100 utterance examples per intent for reasonable accuracy;
         benefits from ECM transcript analysis to identify and validate intents

Menu-driven bot: does not require NLU training data; reliable for known topic lists;
                 appropriate for orgs without transcript history or with <5 topics

Decision rule:
- <90 days of transcripts OR <5 deflection topics → menu-driven bot first
- 90+ days of transcripts AND 5+ validated ECM topics AND 100+ utterances/intent → NLU bot
```

**Detection hint:** If the recommendation is for an NLU bot but there is no discussion of training data volume, utterance examples, or transcript history requirements, the NLU prerequisite check has been skipped.
