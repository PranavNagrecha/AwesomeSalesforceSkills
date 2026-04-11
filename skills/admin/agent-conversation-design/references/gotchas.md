# Gotchas — Agent Conversation Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Fallback Intent Must Have Zero Utterances

**What happens:** If any utterance is added to the Fallback intent's training data in Einstein Bots, that phrasing can compete with — and beat — the intent it belongs to. The NLU model treats the fallback intent as a normal classification target when utterances are present. Queries that should resolve to a specific intent are instead classified as "fallback" because the fallback utterance has higher confidence.

**When it occurs:** When a practitioner attempts to "train" the fallback intent with examples of confusing queries, thinking it will help the model learn what to fall back on. This is the opposite of how the fallback mechanism works — it activates below the confidence threshold, not by matching utterances.

**How to avoid:** Keep the Fallback intent's utterance list empty at all times. If you need to capture confusing query patterns for analysis, log them via conversation analytics rather than using them as training data. Any query you want to route to a specific intent should have utterances added to that intent, not the fallback.

---

## Gotcha 2: Agentforce Topic Descriptions Are Evaluated at Routing Time, Not Indexed

**What happens:** Unlike Einstein Bots where the NLU model is trained offline and deployed, Agentforce topic routing evaluates the topic description text at inference time using the underlying LLM. This means a topic description change takes effect immediately on the next conversation — there is no training delay. However, it also means topic descriptions that are semantically similar will produce probabilistic and sometimes inconsistent routing even after you believe you have fixed the boundary.

**When it occurs:** When two topics have overlapping subject matter described in similar language. The LLM does not produce a deterministic routing result for borderline queries — the same query submitted twice may route to different topics if the topic descriptions are too similar. This can mask itself as a testing environment issue when it is actually a description authoring problem.

**How to avoid:** After rewriting topic descriptions, test the same borderline query at least five times in conversation preview. If routing varies, the descriptions are still too close. Add stronger exclusion language to one or both descriptions. Use language that directly references the *other* topic by subject ("does not handle refunds — for refunds, use the Refund Requests topic") to create an explicit disambiguation signal.

---

## Gotcha 3: Bot Response Length Limits Vary by Channel and Are Not Configured in Dialog Copy

**What happens:** Einstein Bots and Agentforce responses are subject to rendering limits that vary by channel. A response authored in the bot builder may appear correctly in the embedded Salesforce web chat widget but be truncated or render with broken markdown in a mobile SDK deployment or a third-party messaging channel (WhatsApp, Slack). The truncation happens silently — the bot does not warn the author or the end user that content was cut.

**When it occurs:** Most commonly when a practitioner writes long explanatory responses (300+ characters) in the dialog builder and tests only in the Service Cloud web chat. Mobile channels typically have a lower visible character threshold before the user must scroll. WhatsApp has a 4096-character hard limit but also renders no markdown, so asterisk-formatted bold text appears as literal asterisks.

**How to avoid:** Before writing dialog copy, document the target channels and their rendering constraints. For each channel, set a soft character limit (aim for under 300 characters per bot message turn for mobile). Use channel-specific message variants if the content genuinely requires different lengths. Never use markdown formatting in dialog scripts that will be deployed to plain-text channels.

---

## Gotcha 4: Escalation Intent Utterances Must Include Profanity and High-Emotion Variants

**What happens:** Users who are highly frustrated often express their desire to speak to a human agent with emotionally charged language, including profanity or all-caps urgency ("GET ME A HUMAN NOW", "this is bull*, let me talk to someone real"). If the escalation intent's utterance set only covers polite variants ("I'd like to speak to an agent", "connect me to a representative"), these high-emotion phrasings may fall to the fallback intent instead of triggering the escalation path.

**When it occurs:** Any time a frustrated user types an escalation request that doesn't match the polite utterances in the training set. The bot's fallback fires instead of the escalation handoff, adding one more bot interaction to a user who is already angry — the worst possible experience.

**How to avoid:** Include 5–10 high-emotion and urgency variants in the escalation intent's utterance set. You do not need to include actual profanity if org policy prohibits it, but include all-caps variants, emphatic phrasing ("just get me a person"), and impatient shorthand ("agent!!!", "human pls"). Test the escalation path specifically with frustrated-register test utterances in conversation preview.

---

## Gotcha 5: First Customer Message Is the Best Utterance Source, Not Subsequent Messages

**What happens:** When mining case data for utterances, practitioners often sample the full case description or all messages in the thread rather than specifically the first customer message. Subsequent messages are responses to clarifying questions, confirmations, or follow-ups — they do not represent the phrasing a user would type to initiate a bot conversation. Including these in utterance training contaminates the intent model with mid-conversation fragments.

**When it occurs:** When the case data export does not separate the initial contact message from the conversation thread, and the practitioner pastes all message text into the utterance builder without filtering.

**How to avoid:** When exporting case data for utterance mining, explicitly filter or sort to capture only the first inbound message per case. In Salesforce, this is typically the Email Message with `Incoming = true` and the earliest `MessageDate`, or the first `LiveChatTranscript` body entry with `SpeakerType = Customer`. Discard all subsequent messages from utterance candidates.
