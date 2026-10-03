# Gotchas — Multi Channel Service Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names its source. Claims that could not be confirmed from a fetched source carry an inline `UNVERIFIED (2026-10-03):` marker. "Metadata API" means the Metadata API Developer Guide, Version 67.0; "Object Reference" means the Object Reference, Version 67.0.

## Gotcha 1: Messaging Sessions Are Not the Same Object as Live Chat Transcripts

**What happens:** After migrating from legacy chat to Messaging for In-App and Web, reports, dashboards, and flows that reference `LiveChatTranscript` return nothing for new conversations. Historical chats stay on `LiveChatTranscript`; new conversations land on `MessagingSession`. Routing built for the chat service channel does not pick up messaging work.

**When it occurs:** Any org moving off legacy chat. There is no automatic migration of automation references.

**How to avoid:** Before migration, inventory every automation, report, and component that references `LiveChatTranscript`, `LiveChatButton`, or `LiveAgentSession`, and rebuild each against `MessagingSession`, `MessagingEndUser`, and `MessagingChannel`. Run both channels in parallel until downstream dependencies are validated. Do not start new designs on legacy chat.

**Source:** Object Reference: LiveChatTranscript ("automatically created for each Live Agent chat session"), MessagingSession (`CaseId`, `ChannelType`), and ConversationEntry Usage: "The legacy chat product is in maintenance-only mode, and we won't continue to build new features." UNVERIFIED (2026-10-03): the earlier statement that Messaging for In-App and Web became GA in Spring '24 was not confirmed.

---

## Gotcha 2: Email Over The Daily Limit Is Bounced, Discarded, Or Requeued By A Setting

**What happens:** On a heavy day, inbound email beyond the org's daily Email-to-Case limit is handled by `overEmailLimitAction`: `Bounce`, `Discard`, or `Requeue`. With `Discard`, customers get no case and no bounce. Mail from senders outside the routing address's authorized list is handled by `unauthorizedSenderAction` (`Bounce` or `Discard`). UNVERIFIED (2026-10-03): the earlier claim that On-Demand Email-to-Case silently drops individual emails over 25 MB is documented in Salesforce Help only.

**When it occurs:** During incidents and campaigns that spike inbound email, and when `authorizedSenders` is set on a routing address and customers write from personal addresses.

**How to avoid:** Set `overEmailLimitAction` to `Requeue` or `Bounce`, never `Discard`, unless losing mail is acceptable. Review `authorizedSenders` per routing address. Compare mail-server counts with created cases to detect gaps. Offer a portal upload path for large attachments. Note that once Email-to-Case is enabled it cannot be disabled.

**Source:** Metadata API, CaseSettings > EmailToCaseSettings: `overEmailLimitAction` ("what happens to email messages that are received after an organization exceeds its daily Email-to-Case limits"), `unauthorizedSenderAction`, `enableEmailToCase` ("After Email-to-Case is enabled, it can't be disabled"); EmailToCaseRoutingAddress `authorizedSenders`, `caseOrigin`, `fallbackQueue`.

---

## Gotcha 3: A Presence Status Covers Exactly The Channels Listed On It

**What happens:** An agent sets "Available" expecting only chats and receives calls and email cases too. A presence status grants work from every service channel assigned to it; one with no channels is automatically an Away status.

**When it occurs:** When orgs assume presence works per channel by default.

**How to avoid:** Create presence statuses for the channel combinations agents actually need ("Available - All", "Available - Messaging Only", "Available - Phone Only") and train agents on them. Each extra status adds agent-managed complexity, so keep the set small.

**Source:** Metadata API, ServicePresenceStatus: `channels`, "the service channels assigned to the presence status. If no service channels are included, the presence status is automatically marked as 'Away'."

---

## Gotcha 4: An Agent On A Voice Call Takes No Other Work

**What happens:** A blended design expects agents to answer messaging while on a call by lowering the voice "capacity weight". The platform does not allow it: "Voice calls must have a capacity percentage of 100", and with unit capacity "voice calls must use the entire capacity weight". An agent on a call receives no new work until the call ends. This corrects an earlier statement in this skill that the voice weight "can be changed" to allow chats during calls.

**When it occurs:** When capacity planning for blended agents assumes concurrency across voice and digital channels.

**How to avoid:** Plan blended agents as voice-or-digital at any moment. Size staffing for voice peaks separately. Use after-conversation work settings, not reduced voice capacity, to give agents wrap-up time.

**Source:** Metadata API, QueueRoutingConfig: `capacityPercentage` ("Voice calls must have a capacity percentage of 100") and `capacityWeight` ("Voice calls must use the entire capacity weight"). Object Reference, AgentWork `CapacityPercentage`: "an agent on a call doesn't receive new work items until the call ends." Wrap-up time: ServiceChannel `hasAfterConvoWorkTimer` and `afterConvoMaxTime` (10 to 3,600 seconds; Messaging or Voice channels only).

---

## Gotcha 5: Capacity Lives On The Routing Configuration And The Presence Configuration, Not The Service Channel

**What happens:** Designers look for a capacity field on the service channel and either miss it or configure it in the wrong place. Each work item's consumption is set on the routing configuration (`capacityWeight` or `capacityPercentage`), and each agent's total on the presence configuration (`capacity`). The service channel defines the object and, from API 65.0, the capacity model.

**When it occurs:** During initial multi-channel setup and when several queues route the same object with different routing configurations.

**How to avoid:** Document capacity per routing configuration, not per channel, and keep queues that route the same work type on the same configuration unless a different weight is intended. UNVERIFIED (2026-10-03): the earlier claim that a capacity weight of zero lets Omni-Channel push unlimited items was not found in a fetched source; always set a positive weight.

**Source:** Metadata API, QueueRoutingConfig (`capacityWeight`, `capacityPercentage`, `routingModel`, `routingPriority`), PresenceUserConfig (`capacity`: "The maximum number of work units an agent can be assigned at one time"), ServiceChannel (`relatedEntityType`, `capacityModel`).

---

## Gotcha 6: Tab-Based Capacity Releases Work When The Tab Closes, Not When The Work Is Done

**What happens:** With the tab-based capacity model, closing the console tab frees the agent's capacity even if the case is still open, so agents can accept more work than they can finish. With the status-based model, work keeps consuming capacity until its status says completed or it is reassigned.

**When it occurs:** On email and case channels where agents park work, and when reports on `AgentWork.ActiveTime` are compared across channels: active time is tracked only for the tab-based model.

**How to avoid:** Choose the capacity model per service channel deliberately. Use status-based capacity for case work that spans sessions, mapping the status field values that mean in-progress, paused, and completed. Paused capacity (consuming less while paused) requires status-based capacity and Enhanced Omni-Channel.

**Source:** Metadata API, ServiceChannel: `capacityModel` (`STATUS_BASED`, `TAB_BASED`; "the tab-based capacity routing model releases an agent's capacity when a work tab is closed", API 65.0+), `statusField`, `serviceChannelStatusFieldMappings`; QueueRoutingConfig `PausedCapacityPercentage` and `PausedCapacityWeight` (API 64.0+). Object Reference, AgentWork `ActiveTime`.

---

## Gotcha 7: Channel Priority Is A Routing-Configuration Number Where Lower Wins

**What happens:** The business asks for "phone first, then chat, then email". The team reorders queues or adjusts weights and nothing changes. Priority across channels is the routing configuration's `routingPriority`, and lower values route first. Within a channel, a secondary priority field can order work.

**When it occurs:** When queues are organized by topic and several routing configurations feed the same agents.

**How to avoid:** Assign `routingPriority` per routing configuration to express channel priority (for example voice 0, messaging 1, email 2), and use the service channel's `secondaryRoutingPriorityField` for ordering inside a channel.

**Source:** Metadata API, QueueRoutingConfig `routingPriority`: "Work items from routing configurations that have lower priority values (for example, 0) are routed to agents first"; ServiceChannel `secondaryRoutingPriorityField` and `serviceChannelFieldPriorities`.

---

## Gotcha 8: Service Cloud Voice Is Several Telephony Models, Each With Its Own Provisioning

**What happens:** The design says "Voice requires an Amazon Connect instance" and the licensing plan follows. Service Cloud Voice has several vendor models: Amazon Connect provisioned through Salesforce, Partner Telephony (including Partner Telephony from Amazon Connect), and Bring Your Own Channel for contact-center-as-a-service. For the Salesforce-provisioned model, an AWS subaccount is created automatically when Voice is turned on in the org. Organizations with production plus a full sandbox for training then try to share one Amazon Connect instance and calls reach the wrong org. UNVERIFIED (2026-10-03): that one Amazon Connect instance cannot serve two Salesforce orgs is from earlier versions of this skill, not a fetched source.

**When it occurs:** When the telephony model is chosen after licensing, and in multi-org environments that need live phone testing in a sandbox.

**How to avoid:** Choose the telephony model first and record it. For the Amazon Connect model, plan provisioning per org that needs live calls, and budget for it.

**Source:** Metadata API, ConversationVendorInfo: `vendorType` (`Amazon_Connect`, `ServiceCloudVoicePartner`, `BringYourOwnChannelPartner`, `BringYourOwnContactCenter`) and `awsAccountKey` ("The 12-digit AWS subaccount ID that's automatically provisioned for you when Service Cloud Voice was turned on").
