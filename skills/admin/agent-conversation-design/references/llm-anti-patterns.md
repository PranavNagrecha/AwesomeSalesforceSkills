# LLM Anti-Patterns — Agent Conversation Design

Common mistakes AI coding assistants make when generating or advising on agent conversation design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating This Skill as Platform Configuration Guidance

**What the LLM generates:** Instructions for navigating Bot Builder UI, wiring Agentforce topics to actions, configuring routing rules in the Omni-Channel setup, or writing Apex to handle bot events — all presented as "conversation design" advice.

**Why it happens:** The term "conversation design" is associated with chatbot implementation in general training data. LLMs conflate copy/script authoring with platform configuration because both are part of a bot deployment project. The research notes explicitly called this out as the primary anti-pattern.

**Correct pattern:**

```
Agent conversation design = the textual content layer:
  - utterance authoring
  - fallback message copy
  - escalation phrasing
  - dialog scripts

Platform configuration = separate skills:
  - architect/einstein-bot-architecture (intent/dialog structure, NLU setup)
  - agentforce/agentforce-persona-design (system instruction writing)
  - agentforce-agent-creation (topic/action wiring, deployment)
```

**Detection hint:** If the generated output includes UI navigation steps ("In Setup, go to..."), Apex code, Flow references, or metadata deployment instructions, the LLM has drifted into platform configuration territory. Redirect to the appropriate skill.

---

## Anti-Pattern 2: Recommending a Fixed Utterance Count Without Register or Vocabulary Coverage Analysis

**What the LLM generates:** "Add 20 utterances to your intent." The generated utterances are 20 grammatically correct variations of the same formal phrasing: "I would like to cancel my subscription", "I want to cancel my subscription", "Please cancel my subscription", "Can you cancel my subscription"...

**Why it happens:** LLMs optimize for surface-level variety (different sentence structures) rather than the two dimensions that actually matter for NLU accuracy: register variation (formal vs. casual vs. frustrated) and vocabulary variation (synonyms and alternate terms). The resulting 20 utterances look diverse but test a narrow slice of real user behavior.

**Correct pattern:**

```
Utterance set must cover three dimensions:
1. Register: formal / casual / frustrated / abbreviated
   - "I would like to cancel my subscription" (formal)
   - "cancel my sub" (casual)
   - "just cancel it already" (frustrated)
   - "cncl acct" (abbreviated)

2. Vocabulary: all synonyms the user might use
   - cancel / terminate / end / stop / delete / remove / close

3. Error correction: common typos and partial phrasings
   - "cncel", "cancle", "how do i cancel", "want to cancel????"
```

**Detection hint:** If all generated utterances start with "I" and are grammatically complete sentences, the register and vocabulary dimensions have been missed. Check for at least one sub-10-word casual variant and one typo variant per intent.

---

## Anti-Pattern 3: Adding Utterances to the Fallback Intent

**What the LLM generates:** "To improve your bot's ability to handle ambiguous queries, add training examples to the Fallback intent so it learns what kinds of messages it should fall back on."

**Why it happens:** The fallback mechanism in Einstein Bots looks like a classification target to an LLM trained on general ML/NLP content. In standard multi-class classification, all classes including catch-all classes have training examples. LLMs apply this general pattern without accounting for how Einstein Bots specifically implements the fallback — as a threshold-based trigger, not an intent-matched class.

**Correct pattern:**

```
Fallback intent utterance list = EMPTY (always)

Fallback activates when no intent exceeds the confidence threshold.
Adding utterances to the fallback turns it into a competing intent
and causes legitimate queries to be misclassified as "fallback"
even when a correct intent exists.

To improve fallback handling:
  - Add missing utterance variants to the CORRECT intents
  - Lower or raise the confidence threshold in bot settings
  - Design progressive clarification fallback copy (3 stages)
```

**Detection hint:** Any instruction to "train the fallback intent" or add utterances to a fallback/catch-all intent is this anti-pattern.

---

## Anti-Pattern 4: Writing a Single-Stage "I Didn't Understand" Fallback

**What the LLM generates:**

```
Fallback dialog: "I'm sorry, I didn't understand that. Please try rephrasing your question."
```

**Why it happens:** This is the most common pattern in training data because it appears in tutorials, documentation examples, and Stack Overflow answers as a minimal valid fallback. LLMs reproduce the most common example they have seen. The pattern is not wrong on its face — it is simply incomplete and results in high escalation rates from fallback sessions.

**Correct pattern:**

```
[Fallback Stage 1] Acknowledge + offer a concrete pick list:
"I want to make sure I help with the right thing. Are you asking about:
  • [Top topic 1]
  • [Top topic 2]
  • [Top topic 3]
  • Something else?"

[Fallback Stage 2] Confirm escalation with named destination:
"I'm still not finding a match. Would you like me to connect you
with [User-facing team name] who can help directly?"

[Fallback Stage 3] Auto-handoff with context transfer:
"I'll connect you now. [Team name] will be with you shortly.
I'm passing along your message so they're ready to help."
```

**Detection hint:** A generated fallback that is a single turn without an offer set or a pick list is this anti-pattern. Check whether the fallback output has exactly one bot message with no user-choice scaffolding.

---

## Anti-Pattern 5: Writing Escalation Copy Using Internal System Identifiers

**What the LLM generates:**

```
Transfer message: "Transferring you to QUEUE_BILLING_T2_EN_US. Please wait."
```

Or alternatively:

```
Transfer message: "Routing to skill group ID: Billing_Specialist_SF_Q_2024."
```

**Why it happens:** When an LLM is given queue names, skill routing configuration, or metadata field values as context, it reproduces those identifiers directly in the generated copy without applying the translation step from system-internal labels to user-facing language. The LLM has no inherent awareness that a queue name is an internal identifier not meant to be customer-visible.

**Correct pattern:**

```
Escalation copy rule: use the team's function in user-facing terms,
never the internal queue or skill identifier.

System identifier: QUEUE_BILLING_T2_EN_US
User-facing copy: "I'm connecting you with our billing support team."

System identifier: Billing_Specialist_SF_Q_2024
User-facing copy: "A billing specialist will be with you shortly."

Additional requirement: write copy that is durable across queue renames.
"billing support team" survives a Salesforce queue rename;
"QUEUE_BILLING_T2_EN_US" does not.
```

**Detection hint:** Any generated transfer message that contains underscores, uppercase abbreviations, dates, or identifiers that look like system field names is this anti-pattern. The escalation copy should read like a human customer service message.

---

## Anti-Pattern 6: Conflating Agentforce Topic Descriptions with Einstein Bot Intent Names

**What the LLM generates:** Advice like "make sure your Agentforce topic description matches the intent name in your NLU model" or treating a topic description as equivalent to an utterance training label.

**Why it happens:** The two bot platforms (Einstein Bots dialog/intent model and Agentforce topic/action model) share domain vocabulary but have different routing mechanisms. In Einstein Bots, utterances drive NLU intent classification. In Agentforce, topic descriptions are evaluated at inference time by the LLM for routing — they are not training labels and there is no offline NLU training step. LLMs conflate the two models because they appear in similar documentation contexts.

**Correct pattern:**

```
Einstein Bots (dialog/intent model):
  - Routing = NLU model trained on utterance sets
  - Coverage = utterance quantity and diversity
  - Fix for misroute = add utterances to the correct intent

Agentforce (topic/action model):
  - Routing = LLM evaluates topic description text at inference time
  - Coverage = description clarity and scope boundary phrasing
  - Fix for misroute = rewrite topic description with explicit boundaries
    and exclusion clauses — utterances are NOT the fix here
```

**Detection hint:** If advice to fix an Agentforce routing problem involves adding utterances to a topic, or if advice to fix an Einstein Bot routing problem involves rewriting a description field, the platforms have been conflated.
