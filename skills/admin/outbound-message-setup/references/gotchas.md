# Gotchas — Outbound Message Setup

## Gotcha 1: HTTP 200 Without SOAP Acknowledgment Triggers Continuous Retries

**What happens:** The external endpoint returns HTTP 200 (success status) but with a non-SOAP body (JSON, empty, or plain text). Salesforce treats this as a delivery failure and begins retrying. Over 24 hours, the external system receives the same Outbound Message payload hundreds of times — approximately 200-300 deliveries before the message is permanently dropped. The acknowledgment contract is grounded: `notificationsResponse` is "the schema for sending an acknowledgment (ack) response to Salesforce" and its entire content is `<element name="Ack" type="xsd:boolean"/>` ([Understanding Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_understanding.htm)). `Ack` lives in the response *body*; HTTP 200 is the transport saying the bytes arrived, which is a different statement. UNVERIFIED (2026-09-05): the retry cadence and the "200-300 deliveries" figure are not in the SOAP API guide's outbound messaging chapter and appear in no extracted PDF — re-confirm them against Salesforce Help before quoting them in an SLA.

**When it occurs:** Any external endpoint that acknowledges success with a non-SOAP response. Extremely common because most modern web services expect to return JSON for any HTTP response. The SOAP acknowledgment requirement is specific to Salesforce Outbound Messages and is not intuitive for developers building modern REST/JSON services.

**How to avoid:** Always provide the external development team with the exact SOAP acknowledgment template before they build the receiving endpoint. Require them to test with the correct response format in a staging environment before going live. The SOAP response must include `<Ack>true</Ack>` inside a `<notifications>` element in the `http://soap.sforce.com/2005/09/outbound` namespace. Any deviation from this format — including the wrong XML namespace — results in continuous retries.

---

## Gotcha 2: Messages Are Permanently Dropped After 24 Hours With No Notification

**What happens:** Outbound Messages that fail to deliver for 24 hours disappear from the Pending queue without any alert, email notification, or log entry. UNVERIFIED (2026-09-05): the 24-hour figure is help-only — a grep for "outbound" across the Salesforce App Limits Cheat Sheet returns one unrelated hit (change-set file counts) and no delivery, retry or queue limit. What is grounded is that the platform ships a dead letter queue for exactly this case, gated behind an org permission (api_meta.txt L140368–140371) — see gotcha 5. The integration silently stops delivering data for the affected records. Business users discover the gap hours or days later when downstream data is stale.

**When it occurs:** Any sustained endpoint outage exceeding 24 hours. Also occurs when the acknowledgment issue (Gotcha 1) goes undetected for more than 24 hours — all messages in the retry queue are dropped simultaneously.

**How to avoid:** Implement proactive monitoring. Options include:
1. Schedule a daily report or alert that queries the Outbound Message Pending queue size via the Salesforce API.
2. If the External Service has its own logging, compare incoming Salesforce notification counts against the triggering Workflow event counts.
3. For critical integrations, implement record-level reconciliation — periodically compare the source Salesforce object's state against the external system's state and alert on discrepancies.
4. Use manual requeue before the 24-hour window expires for any known endpoint outage.

---

## Gotcha 3: New Outbound Message Actions Cannot Be Added to Flows

**What happens:** A developer attempts to add an Outbound Message as a Flow Action. The "Outbound Message" option is not available in the Flow Designer's element palette or action picker. The feature appears to be missing.

**When it occurs:** Any new Flow-based automation that requires external SOAP notification. What is grounded: `OutboundMessage` is a value of the `WorkflowActionType` enum (api_meta.txt L139961) and of the approval-process action type (L23615–23641); `FlowAction` is a *separate* enum value whose "pilot program for flow trigger workflow actions is closed" (L139962–139966). Nothing makes an outbound message reachable from Flow Builder. UNVERIFIED (2026-09-05): the specific claim that new Workflow Rules cannot be created as of Spring '23 is not stated anywhere in the extracted Metadata API guide — a grep for "retire", "no longer create" and "can't create workflow" returns nothing, and `WorkflowRule` is still fully documented with a `failedMigrationToolVersion` field added in API 54.0 for migration retries (L140399–140404). Confirm against the Release Notes for your org's release before telling a customer they cannot create one.

**How to avoid:** For new integration automation that will be built in Flow, use Platform Events as the notification mechanism:
1. Define a Platform Event object with the fields to publish.
2. Use a "Create Records" element in Flow to publish the Platform Event (events are records in Salesforce).
3. Configure the external system to subscribe to the Salesforce Streaming API (CometD) to receive events.
Platform Events support JSON-compatible data structures and are the strategic replacement for Outbound Messages in Flow-first architectures.

---

## Gotcha 4: `apiVersion` Is Invisible in Setup and Silently Breaks the Listener

**What happens:** An outbound message's `apiVersion` is `Required`, is "automatically set to the current API version when the outbound message is created", and "can only be modified by using Metadata API. It can't be modified using the Salesforce user interface" (api_meta.txt L140327–140334). An admin looking at the outbound message in Setup sees the endpoint, the user and the field list — and no version. Meanwhile the guide warns: "If you change the apiVersion to a version that doesn't support one of the fields configured for the outbound message, the messages fail until you update your outbound message listener to consume the updated WSDL" (L140334–140337). So a Metadata API deploy that carries a different `apiVersion` than the org held can stop delivery outright, and there is nothing in the UI to see it in.

**When it occurs:** Three routes. (1) A hand-written `.workflow` file copied from the guide's sample, which omits `apiVersion` entirely (L140624–140633) — the deploy fills in a default rather than your intent. (2) A `.workflow` file copied between orgs on different releases. (3) A value outside the legal set: "Valid API versions for outbound messages are 8.0 and 18.0 or later" (L140329), so `17.0` is not deployable and nothing about the field name signals that.

**How to avoid:** Commit an explicit `<apiVersion>` in the file (`references/metadata-examples.md` § 1) and treat it as a contract with the listener team, not a build artifact. After every deploy, round-trip the file (`§ 7A`) and diff — a changed `<apiVersion>` line is the only warning you get. Pair any field-list change with a listener WSDL regeneration in the same change window. `scripts/check_outbound_message_setup.py` fails a missing, non-numeric, or out-of-range `apiVersion`.

---

## Gotcha 5: `useDeadLetterQueue` Is Inert Unless the Org Has the Permission

**What happens:** `useDeadLetterQueue` "is only available for organizations with dead letter queue permissions turned on. If set, this outbound message uses the dead letter queue if normal delivery fails" (api_meta.txt L140368–140371). In an org without the permission, the element is not a control — it is decoration. The deploy does not fail, no warning appears, and the undelivered-message behaviour is whatever the default drop behaviour is (gotcha 2).

**When it occurs:** Any org that has not had the permission enabled, which is the default state. It bites hardest when a team copies a `.workflow` file from an org that *does* have it, reads `<useDeadLetterQueue>true</useDeadLetterQueue>` in source control, and concludes the durability question is answered. It is the one element in `WorkflowOutboundMessage` whose presence in the file tells you nothing about whether it is doing anything.

**How to avoid:** Confirm the org's dead letter queue permission before you treat the element as a mitigation — the file is not evidence. If the permission is not on, the durability answer has to be built outside the platform: a reconciliation job comparing the source object against the listener's receipt log, or a monitored pending-queue threshold. Record which of the two applies in `templates/outbound-message-setup-template.md` § Monitoring, so the next person does not re-derive it from an element that looks reassuring.

---

## Gotcha 6: `includeSessionId` Puts a Live Session in the Payload

**What happens:** `includeSessionId` is `Required` on every outbound message and, when true, includes the Salesforce session ID — "useful if you intend to make API calls and you don't want to include a username and password" (api_meta.txt L140354–140357). The session belongs to `integrationUser`, "the named reference to the user under which this message is sent" (L140359). So the payload carries a working credential for that user, and it travels to whatever `endpointUrl` says. The guide's own sample sets `<includeSessionId>true</includeSessionId>` and points at `http://www.test.com` — cleartext (L140626–140630).

**When it occurs:** Whenever the value is inherited rather than decided. Setup presents it as a checkbox with no warning about blast radius, and a `.workflow` file copied from another integration carries whatever that integration needed. The exposure scales with the integration user's permissions: a "just make it work" integration user with Modify All Data hands the listener the org.

**How to avoid:** Set it to `false` unless the listener genuinely calls back, and when it must be `true`, make three things follow: an `https` endpoint (there is no other protection for the credential in transit), an integration user scoped to exactly what the callback does, and a note in the field list about what the listener is permitted to call. When the callback is more than trivial, `integration/oauth-flows-and-connected-apps` gives a revocable credential instead of a session that lives as long as the message does. The checker warns on every `includeSessionId=true` for exactly this reason.

---

## Gotcha 7: An Approval-Only Outbound Message Still Lives in the Workflow File

**What happens:** Outbound messages are "workflow **and approval** actions" (api_meta.txt L140313–140315), and `ApprovalProcess` action blocks reference them by name with `<type>OutboundMessage</type>` (L23615–23641). But the *definition* has exactly one home: the `outboundMessages` array of `workflows/<Object>.workflow` (L139931), and workflow files are "one file per standard or custom object that has workflow" (L139896–139898). An outbound message used only by an approval process therefore sits in a file whose name says "workflow" and which contains no rule referencing it.

**When it occurs:** On deploy, when `package.xml` names the `ApprovalProcess` member but not the `Workflow` member — the approval action cannot resolve a name that was never sent. On cleanup, when someone deletes a workflow rule and assumes the outbound message went with it, or deletes the whole `.workflow` file because "this object has no workflow rules any more" and takes the approval process's action with it. And on search, when an admin greps the approval process for an endpoint URL and finds nothing.

**How to avoid:** Deploy `Workflow` and `ApprovalProcess` in the same `package.xml` (`references/metadata-examples.md` § 5), always in that order of dependency. Before deleting anything from a `.workflow` file, grep the `approvalProcesses/` folder for the `fullName` — the reference is a plain string and nothing enforces it from the workflow side. Give approval-only messages a name that says so (`Notify_ERP_Of_Tier_Rejection`, not `Notify_ERP`) so the orphan looks intentional.

---

## Gotcha 8: The Guide's Own Sample Workflow XML Is Not Well-Formed

**What happens:** The Metadata API Developer Guide's Declarative Metadata Sample Definition for `Workflow` (api_meta.txt L140553–140736) — the block most people copy as a starting point — contains a mismatched tag at L140666–140669:

```
<actions>
    <fullName>Field_Update</name>
        <type>FieldUpdate</type>
</actions>
```

`<fullName>` is closed with `</name>`. An XML parser rejects the whole document, and the deploy fails with a parse error pointing at a line number rather than at the real problem. The same block is also wrong semantically: `WorkflowActionReference` has fields `name` and `type` (L139952–139958) — there is no `fullName` on an action reference at all.

**When it occurs:** Any time an agent or admin scaffolds a `.workflow` file by copying the published sample. It is a documentation defect, so it survives across guide versions and looks authoritative.

**How to avoid:** Scaffold from `references/metadata-examples.md` § 3, which is the same shape with the defect corrected, or from a real `sf project retrieve start --metadata Workflow:<Object>`. Parse every hand-edited `.workflow` file before deploying — `scripts/check_outbound_message_setup.py` reports a parse error as a hard failure rather than skipping the file. The wider lesson for anything in this guide: an element name inside a sample block is weaker evidence than the same name in the type's field table.

---

## Gotcha 9: `triggerType` Decides Whether a Correction Ever Reaches the Listener

**What happens:** `WorkflowRule.triggerType` takes three values: `onAllChanges` ("considered on all changes"), `onCreateOnly` ("considered only on create"), and `onCreateOrTriggeringUpdate` ("considered on create and triggering updates") — api_meta.txt L140420–140430. The outbound message fires only when the rule is considered *and* its criteria evaluate true. A rule on `onCreateOnly` sends one notification at insert and never sends another, no matter how the record changes afterwards. Nothing about the outbound message configuration reveals this; the endpoint simply stops hearing about a record it was told about once.

**When it occurs:** Most often when the rule was written for a create-time handoff and the business later starts editing the field it keys on. It also occurs the other way: `onAllChanges` combined with a criterion that stays true — like `Customer_Tier__c notEqual Prospect` — re-fires the message on every unrelated save of the record, which the listener experiences as duplicates it cannot distinguish from retries.

**How to avoid:** Pick the trigger type from the question "should a correction re-notify?", not from a default. For change detection, the guide's own pattern pairs a `formula` with `onAllChanges`: `<formula>ISCHANGED(Name)</formula>` with `<triggerType>onAllChanges</triggerType>` (L140696–140701); "either `criteriaItems` or `formula` must be set" (L140390–140393). For a state-entry handoff, `onCreateOrTriggeringUpdate` with a criterion that only newly becomes true is the shape you want. Whichever you choose, tell the listener team — their idempotency key depends on it.

---

## Gotcha 10: One `Ack` Acknowledges Up to 100 Notifications

**What happens:** In the outbound messaging WSDL the `notifications` element ends with
`<element name="Notification" maxOccurs="100" type="tns:OpportunityNotification"/>` — a single message
can carry up to 100 records. The response schema carries no per-record status: `notificationsResponse`
is exactly one boolean, `<element name="Ack" type="xsd:boolean"/>`
([Understanding Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_understanding.htm)).
So a listener that processes 60 of 100 notifications, hits an error on the 61st, and returns `Ack=true`
has told Salesforce the entire message was handled. The remaining 40 records are never redelivered and
never appear as failures anywhere — the delivery status page shows a successful delivery.

**When it occurs:** Silently, and only under load. Most listeners are built and tested against
single-record messages, where "loop the notifications, return true at the end" is indistinguishable from
correct. Batching appears when a bulk update, a data load or a mass reassignment fires the rule for many
records at once — which is exactly when the listener is most likely to hit a downstream timeout partway
through. The failure surfaces later as unexplained gaps in the external system that reconciliation
attributes to a network problem.

**How to avoid:** Treat `Ack` as a statement about the whole message, because that is what it is. Return
`true` only after every notification in the message has been durably handled; on partial failure return
`false` (or no acknowledgment) and let the whole message redeliver. That makes redelivery of already-processed
records the normal case rather than the exception, so the listener must be idempotent — and the guide
names the key to do it with: "Each message Notification also has the object ID. Use the object ID to
track redelivery attempts of notifications you've already processed." Persist the processed object IDs
before acknowledging, not after.

---

## Gotcha 11: The Listener's Own Writes Can Re-trigger the Rule That Called It

**What happens:** A listener that uses the included `SessionId` to write back to Salesforce updates the
same record that triggered the message. That update re-evaluates the workflow rule, which fires the
outbound message again, which the listener processes and writes back again. The SOAP API Developer Guide
carries this as an explicit **Warning**: "To avoid an infinite loop of outbound messages that trigger
changes that trigger more outbound messages, ensure that the user who updates the objects does not have
the 'Send Outbound Messages' permission"
([Defining Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm)).

**When it occurs:** Whenever the callback path writes to the triggering object — a status stamp, an
external ID, a "synced" checkbox — and the rule's criteria do not exclude that write. It is easy to miss
in design because the two halves are usually owned by different teams: the admin writes the rule, the
integration team writes the listener, and neither sees the cycle. It is made worse by `triggerType`
`onAllChanges`, where any save re-evaluates the rule (gotcha 9).

**How to avoid:** Use two distinct users and give only one of them the ability to send. The guide's own
recommendation: "We recommend specifying a single user to respond to outbound messages and disabling this
user's ability to send outbound messages" — "To disable outbound message notifications for a user,
deselect Send Outbound Messages in the user's Profile." So the `integrationUser` on the message and the
user the listener authenticates as for the write-back should not be the same account, and the write-back
account must not hold Send Outbound Messages. Belt and braces: make the rule criteria exclude the
listener's own stamp field, so the loop cannot form even if the permission is later granted.

