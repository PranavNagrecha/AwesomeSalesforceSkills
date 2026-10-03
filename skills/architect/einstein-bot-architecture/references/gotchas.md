# Gotchas — Einstein Bot Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Metadata API" below means the Metadata API Developer Guide, Version 67.0 (Summer '26); "Object Reference" means the Object Reference, Version 67.0.

## Gotcha 1: Customer Facts Reach The Bot Only Through Mapped Context Variables

**What happens:** Pre-chat or channel data (name, email, case subject) is captured, but the bot greets the customer with "What is your name?" The data sits on the session record and the bot has no variable bound to it.

**When it occurs:** When context variables are not mapped for the channel type in use. A mapping is per channel: a Messaging for In-App and Web mapping (`EmbeddedMessaging`) does not cover WhatsApp or SMS (`Text`).

**How to avoid:** For every fact the bot needs, define a context variable and map it per channel type to the sObject field that holds it (`MessagingSession`, `MessagingEndUser`, or `LiveChatTranscript`). Test with the real channel, not the builder preview.

**Source:** Metadata API, Bot: `contextVariables`, "context variables that enable your bot to gather customer information regardless of channel"; ConversationContextVariableMapping: `fieldName`, `messageType` (`EmbeddedMessaging`, `WhatsApp`, `Text`, `WebChat`, and others), `SObjectType` (`LiveChatTranscript`, `MessagingEndUser`, `MessagingSession`).

---

## Gotcha 2: Bot Versions Share One Intent Set, So Reactivating An Old Version Does Not Roll Back Intents

**What happens:** A release adds and edits intents, performs worse, and the team reactivates the previous version expecting the old intent model to come back. Only one version can be active, and all versions of a bot share the same intent set. The reactivated version still sees the edited intents.

**When it occurs:** When versioning is treated like a code branch. The earlier statement in this skill that each version keeps its own trained model is contradicted by the Metadata API description of `botMlDomain`.

**How to avoid:** Treat intents and utterances as shared data with their own change control. Keep an exported copy (retrieved `Bot` metadata) of the intent set before every change, and roll back intents by redeploying that copy, not by switching versions. Use version switching only for dialog changes.

**Source:** Metadata API, Bot: "Only one version can be active"; `botMlDomain`: "All Einstein Bot versions under the same bot now share an intent set" (API 44.0+). Object Reference, BotVersion `Status`: "Only one version for a related BotDefinition can be active at once."

---

## Gotcha 3: Intent Strictness Is A 1-to-5 Setting That Support Must Enable

**What happens:** A design tells the admin to "set the confidence threshold to 0.7". No such field exists in that form. The documented control is `intentThreshold`, which "specifies how strictly a user message must match with a bot intent", takes values from 1 (least strict) to 5 (most strict), and must be turned on by Salesforce Customer Support. This corrects the earlier 0.7 guidance in this skill.

**When it occurs:** When misroutes are blamed on a "default threshold" and the fix is written from generic NLU knowledge.

**How to avoid:** Fix overlapping intents first; strictness cannot separate intents whose utterances overlap. If stricter matching is still needed, request the feature, set `intentThreshold`, and route low-confidence input to a fallback dialog.

**Source:** Metadata API, BotVersion: `intentThreshold`, "Valid values are between 1 and 5 ... To turn on this feature, contact Salesforce Customer Support. This field is available in API version 63.0 and later."

---

## Gotcha 4: A Failed Transfer Needs A Designed Path

**What happens:** The bot runs a transfer when no rep is online or the routing target is wrong. Without a designed path, the customer waits in silence.

**When it occurs:** Outside business hours, during spikes, or when the channel's routing does not match the transfer target. UNVERIFIED (2026-10-03): the "Check Agent Availability" system action named in earlier versions of this skill could not be found in the Metadata API.

**How to avoid:** Assign a dialog to the `TransferFailed` system event that creates a case with the collected context, offers a callback, or shows business hours. Decide per channel whether the bot runs only while reps are online (`agentRequired` on the channel provider). For Agentforce Service Agents, set `defaultOutboundFlow` as the fallback escalation.

**Source:** Metadata API, ConversationSystemDialog types (`ErrorHandling`, `KnowledgeAction`, `KnowledgeFallback`, `TransferFailed`); BotNavigation type `TransferToAgent`; ConversationDefinitionChannelProvider `agentRequired`; Bot `defaultOutboundFlow` (API 65.0+).

---

## Gotcha 5: Messaging Channel Links Do Not Travel In Metadata

**What happens:** A bot deploys cleanly to production but is not connected to its messaging channel. The channel link was set in the sandbox UI and never left it.

**When it occurs:** On the first deployment of a bot to a new org, and on every sandbox refresh pipeline that expects metadata to rebuild the org.

**How to avoid:** Add a manual post-deploy step to the runbook: connect each messaging channel to the bot in Setup, then test through the channel. Do not rely on `conversationChannelProviders` for messaging channels.

**Source:** Metadata API, Bot, ConversationDefinitionChannelProvider note: "To add, edit, or remove a messaging channel, you must use the UI. If you deploy a bot with messaging channel providers, those providers aren't visible in Metadata API."

---

## Gotcha 6: Einstein Bots And Agentforce Agents Share A Definition Object, Not A Design Model

**What happens:** Teams assume "migrating to Agentforce" is a new metadata type and a new deployment pipeline, or the reverse, that because the object is shared the dialogs convert. The definition object is shared: `BotDefinition` represents "Einstein Bots or Agentforce Agents", with `Type` values `Bot`, `ExternalCopilot`, and `InternalCopilot`. The design model is not: dialogs and steps versus topics and actions.

**When it occurs:** During migration planning and when reporting on "how many bots we have".

**How to avoid:** Inventory with `BotDefinition.Type` and `AgentType` (query in `references/examples.md`). Plan migration as a redesign of the conversation, and reuse the deployment pipeline. Note that Bot metadata deployment and retrieval are not supported for Lead Nurturing and Sales Coach agents.

**Source:** Object Reference, BotDefinition: "Represents a top level object for Einstein Bots or Agentforce Agents", `Type` and `AgentType` fields. Metadata API, Bot: `type` values and the special access rule on Lead Nurturing and Sales Coach agents.

---

## Gotcha 7: Bots On Legacy Chat Sit On A Product That Gets No New Features

**What happens:** A new bot is designed on the legacy chat channel because the org already has chat buttons. Its context lands on `LiveChatTranscript`, and the channel will not gain capabilities.

**When it occurs:** In orgs that adopted chat before Messaging for In-App and Web.

**How to avoid:** Design new bots for Messaging for In-App and Web (`MessagingSession`). If a bot must stay on legacy chat, record that in a decision record with a migration trigger. UNVERIFIED (2026-10-03): a legacy chat retirement date was not found in a fetched source.

**Source:** Object Reference, ConversationEntry, Usage: "The legacy chat product is in maintenance-only mode, and we won't continue to build new features."

---

## Gotcha 8: Idle Timeout Is A Bot Setting; Channel Windows Are Separate

**What happens:** A customer returns after a pause. On one channel the bot restarts; on another the messaging session is still open but the bot has dropped its dialog state. On WhatsApp, the business may be unable to message the customer at all after a long gap.

**When it occurs:** When idle behavior is left at defaults and the same dialog serves web and asynchronous messaging channels. UNVERIFIED (2026-10-03): the WhatsApp 24-hour customer-service window is Meta platform policy and is not documented in a fetched Salesforce source.

**How to avoid:** Set the bot's `sessionTimeout` deliberately and design a resume dialog for asynchronous channels. Store facts the conversation must not lose (account number, detected intent) on `MessagingSession` fields through context variables.

**Source:** Metadata API, Bot: `sessionTimeout`, "the maximum amount of minutes that a bot session can be idle" (API 58.0+).

---

## Gotcha 9: Variable Types And Limits Constrain Complex Conversations

**What happens:** A dialog collects many values, each in its own variable, until the bot hits a variable ceiling or a value will not fit the declared type. UNVERIFIED (2026-10-03): the "250 custom variables per bot version" ceiling quoted in earlier versions of this skill was not found in a fetched source.

**When it occurs:** When every dialog creates its own variables instead of reusing a small, typed set.

**How to avoid:** Define a naming convention and reuse typed variables across dialogs. Declared types are limited to `Text`, `Number`, `Boolean`, `Object`, `Date`, `DateTime`, `Currency`, and `Id`; choose them deliberately because the type drives what the variable can hold and pass to actions.

**Source:** Metadata API, ConversationContextVariable and PageContextVariable `dataType` values; BotVersion `conversationVariables`.

---

## Gotcha 10: Entity Extraction Depends On The Entity Definition, Not On What The Customer Typed

**What happens:** The customer gives a date or an order number clearly, and the variable stays empty. The question step's entity did not match the input format.

**When it occurs:** With custom entities that have few examples, and with system entities referenced under the wrong name. UNVERIFIED (2026-10-03): the system entity list (DateTime, Date, Money, Number, Person, Location, Organization, Text) and the "10 examples per value" guidance are not in a fetched source; entities appear in metadata as `mlSlotClasses` on the intent set.

**How to avoid:** Test extraction with varied formats ("5 January", "1/5", "next Tuesday"). On a failed extraction, ask a constrained follow-up question instead of continuing with an empty variable.

**Source:** Metadata API, Bot, LocalMlDomain: `mlIntents` and `mlSlotClasses` ("List of entities associated with this local intent set").

---

## Gotcha 11: The Embedded Service Deployment Has Its Own Settings

**What happens:** The bot works in the builder preview but behaves differently on the website: pre-chat fields do not arrive, the greeting does not appear, or styling breaks rich components.

**When it occurs:** When the Embedded Service deployment's own form, branding, and channel settings disagree with the bot configuration. UNVERIFIED (2026-10-03): that deployment settings take precedence over bot-level settings such as greeting and timeout is stated in earlier versions of this skill and in Salesforce Help, not in a fetched source.

**How to avoid:** Test through the deployed Embedded Service snippet in a sandbox. Check that form field names in the deployment match the context variable mappings from Gotcha 1. Version the deployment metadata alongside the bot.

**Source:** Metadata API: Embedded Service deployments are their own metadata types (`EmbeddedServiceConfig`, "a setup node for creating an Embedded Service for Web deployment", with related `EmbeddedServiceBranding` and `EmbeddedServiceForm` types), separate from `Bot`.

---

## Gotcha 12: New Intents Are Invisible Until The Model Finishes Training

**What happens:** A new intent and its utterances are added and the bot is activated. Customers who say the new thing still reach the fallback, because the intent model has not finished training and the previous model is still serving.

**When it occurs:** On every intent or utterance change. UNVERIFIED (2026-10-03): the asynchronous training behavior, the "15-30 minutes for large models" duration, and the training status indicator in Setup are stated in earlier versions of this skill and in Salesforce Help only.

**How to avoid:** Train and verify in a sandbox first. Schedule intent changes for low-traffic windows and confirm training has completed before announcing the new capability. Because versions share the intent set (Gotcha 2), a training change affects every version of the bot at once.

**Source:** Metadata API, Bot `botMlDomain` (shared intent set). Training duration and status: UNVERIFIED as noted.
