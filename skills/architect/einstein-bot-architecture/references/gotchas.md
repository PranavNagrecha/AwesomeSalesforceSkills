# Gotchas — Einstein Bot Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Pre-Chat Form Data Does Not Automatically Populate Bot Variables

**What happens:** Pre-chat form fields (name, email, case subject) are submitted by the customer but the bot greets them with "What is your name?" because the pre-chat data was not mapped to bot variables.

**When it occurs:** When the Embedded Service deployment uses a pre-chat form but the bot configuration does not explicitly map pre-chat fields to bot variables using the Init rule or context variable bindings. The data exists on the LiveChatTranscript record but the bot has no access to it during the conversation.

**How to avoid:** In the bot's Menu version settings, map each pre-chat field to a corresponding bot variable. For Agentforce Agents, use the session context to access pre-chat data. Test with the pre-chat form enabled in a sandbox before deploying.

---

## Gotcha 2: Model Retraining Blocks New Intent Availability

**What happens:** A new intent is added to the bot, utterances are entered, and the bot is activated. Customers who trigger the new intent still hit the fallback because the new intent model has not finished training.

**When it occurs:** Every time intents or utterances are modified. The model trains asynchronously and the old model serves traffic until training completes. Training time scales with the number of intents and utterances; large models can take 15-30 minutes.

**How to avoid:** Retrain the model in a sandbox first and verify intent matching before promoting to production. Schedule intent changes during low-traffic windows. Never add a new intent and activate it in production without confirming the model training has completed (check the Bot Training Status in Setup).

---

## Gotcha 3: Transfer to Agent Fails Silently When No Agents Are Available

**What happens:** The bot executes a Transfer to Agent step, but no agents are online or all agents are at capacity. The customer sees no message and the conversation appears to hang. No error is thrown in the bot flow.

**When it occurs:** Outside of business hours, during traffic spikes that exceed agent capacity, or when the Omni-Channel routing configuration does not match the bot's target queue/skill.

**How to avoid:** Always add a check before the transfer step. Use the "Check Agent Availability" system action (Einstein Bots) or equivalent logic to verify agents are available. If none are available, branch to an alternative path: create a case, offer a callback, or display business hours. Never let the transfer be the only exit path.

---

## Gotcha 4: WhatsApp 24-Hour Session Window Breaks Long Conversations

**What happens:** A customer starts a conversation with the bot over WhatsApp, leaves for more than 24 hours, and returns. The bot cannot send a follow-up message because the WhatsApp session has expired. The conversation context is lost.

**When it occurs:** WhatsApp Business API enforces a 24-hour messaging window from the last customer message. If the customer does not respond within 24 hours, the business cannot send further messages without an approved template message.

**How to avoid:** Design bot dialogs for WhatsApp to be completable in a single session. For processes that require customer action (uploading a document, checking a reference number), send a proactive template message reminder within the 24-hour window. Architect long-running processes to create a Case and use email or SMS follow-up instead of relying on the WhatsApp session.

---

## Gotcha 5: Bot Variable Limits Constrain Complex Conversations

**What happens:** The bot stops collecting data mid-conversation because it has hit the maximum number of custom bot variables (250 per bot version in Einstein Bots).

**When it occurs:** When the bot serves many use cases and each dialog collects multiple pieces of data. Variable sprawl happens when teams create new variables for each dialog instead of reusing context variables across dialogs.

**How to avoid:** Design a variable naming convention and reuse generic variables (e.g., `collected_id`, `collected_date`) across dialogs where the data is consumed and discarded within the same dialog. Archive unused variables when decommissioning dialogs. For Agentforce Agents, session context is more flexible but should still be managed deliberately.

---

## Gotcha 6: Bot Versioning Does Not Support Rollback

**What happens:** A team activates a new bot version with updated dialogs and intents. The new version performs worse than the previous one (higher fallback rate, lower deflection). They attempt to reactivate the previous version but find that only one version can be active at a time, and the previous version's intent model must be retrained since the training state is tied to the version.

**When it occurs:** When teams treat bot versioning like code deployment with instant rollback. Einstein Bot versions are not git branches — activating an older version requires retraining the intent model for that version, which takes time and leaves the bot in a degraded state during the transition.

**How to avoid:** Always test a new bot version thoroughly in sandbox before promoting. Keep the previous version's intent model trained and validated in a sandbox mirror. If a rollback is needed, understand that there will be a 15-30 minute window while the old version's model retrains. Plan a rollback procedure in advance that includes a static fallback dialog (transfer all to agent) during the retraining window.

---

## Gotcha 7: Embedded Service Deployment Configuration Overrides Bot Behavior

**What happens:** The bot works correctly in the bot builder preview but behaves differently when deployed through Embedded Service on the actual website. Common symptoms include: pre-chat fields not reaching the bot, the bot greeting message not appearing, or the chat window styling breaking the bot's rich message components.

**When it occurs:** When the Embedded Service deployment snippet or configuration has settings that conflict with the bot configuration. The Embedded Service deployment has its own pre-chat form settings, branding overrides, and feature toggles that take precedence over what is configured in the bot builder.

**How to avoid:** Always test the bot through the actual Embedded Service deployment in a sandbox, not just in the bot builder preview. Verify that pre-chat form field names in the Embedded Service configuration exactly match the bot variable mappings. Check that the Embedded Service deployment's Chat Settings do not override bot-level settings like session timeout or auto-greeting.

---

## Gotcha 8: Entity Extraction Requires Exact System Entity Names

**What happens:** The bot fails to extract structured data (dates, numbers, currencies, locations) from customer input even though the customer provided the information clearly. The bot variable remains null and the dialog proceeds without the expected data.

**When it occurs:** When the dialog step uses a Question element with entity extraction but references the wrong system entity name or uses a custom entity that has not been trained. Einstein Bots provide system entities (DateTime, Date, Money, Number, Person, Location, Organization, Text) and each must be referenced by its exact API name. A common mistake is configuring a question to extract a "date" when the system entity is "DateTime" or "Date" (case-sensitive in some configurations).

**How to avoid:** Use the exact system entity names as documented. For custom entities, verify that the entity has been trained with sufficient examples (at least 10 annotation examples per entity value). Test entity extraction with varied input formats: "January 5th", "1/5/2025", "next Tuesday", "tomorrow" should all be tested for date extraction. If extraction fails, fall back to a direct question ("Please enter the date in MM/DD/YYYY format") rather than silently proceeding with null data.

---

## Gotcha 9: Conversation Timeout Behavior Differs by Channel

**What happens:** A customer pauses their conversation and returns after a few minutes. On web chat, the conversation has ended and the bot starts fresh. On messaging channels (In-App, WhatsApp), the conversation resumes where it left off but the bot's dialog state may have been lost while the messaging session remains open.

**When it occurs:** Web chat (Live Agent) sessions have a configurable inactivity timeout (default 5 minutes in many configurations) after which the session ends. Messaging channels (Messaging for In-App and Web, WhatsApp, SMS) have persistent sessions that do not timeout the same way — the messaging session stays open but the bot's dialog context may expire independently.

**How to avoid:** Design timeout behavior explicitly for each channel. For web chat, set the inactivity timeout in Chat Settings and configure the bot to send a warning message before timeout. For messaging channels, implement a "session resumption" dialog that detects when the customer returns after inactivity and either resumes context or restarts gracefully. Store critical collected data (account number, intent) in the MessagingSession record fields so it survives bot dialog context expiry.
