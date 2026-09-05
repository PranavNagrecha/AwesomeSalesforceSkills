---
name: outbound-message-setup
description: "Use when configuring Workflow-based Outbound Messages to push SOAP payloads to external endpoints — endpoint setup, field selection, retry behavior, and delivery monitoring. NOT for the listener's session ID callback into Salesforce — use integration/outbound-messages-and-callbacks. NOT for JSON webhooks or Flow-triggered pushes — use integration/outbound-webhook-from-salesforce. Keywords: WorkflowOutboundMessage, outboundMessages, endpointUrl, includeSessionId, integrationUser, useDeadLetterQueue, apiVersion, SOAP Ack, .workflow file, approval outbound message action."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "How do I set up an Outbound Message to notify an external system when a record changes?"
  - "Outbound Message shows as Delivered but the external system is not receiving data"
  - "External endpoint is getting the same Outbound Message hundreds of times — why?"
  - "Outbound Message retry is not stopping — how do I clear the queue?"
  - "What fields can I include in an Outbound Message payload?"
  - "outbound message isn't working"
  - "deploy an outbound message with Metadata API instead of clicking through Setup"
  - "workflow rule action OutboundMessage fails to deploy — action name not found"
  - "change the API version of an existing outbound message"
  - "should I turn on includeSessionId on an outbound message?"
  - "outbound message endpoint has no dead letter queue — how do I stop losing messages?"
  - "wire an outbound message to an approval process final rejection action"
tags:
  - outbound-message
  - workflow
  - integration-admin
  - outbound-message-setup
  - soap-delivery
  - retry
  - workflow-metadata
  - metadata-api
inputs:
  - "Workflow Rule that should trigger the Outbound Message"
  - "External endpoint URL (HTTPS required for production)"
  - "Salesforce object fields to include in the payload"
  - "External system's SOAP acknowledgment capability"
outputs:
  - "Workflow Rule Outbound Message action configuration"
  - "SOAP acknowledgment response template for the external endpoint"
  - "Delivery monitoring procedure via Setup > Process Automation > Outbound Messages"
  - "Retry management guidance for stuck or failed messages"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Outbound Message Setup

This skill activates when a practitioner needs to configure Salesforce Outbound Messages — the built-in SOAP-based notification mechanism that Workflow Rules use to push record data to external endpoints. It covers the acknowledgment format the external endpoint must return, the retry behavior, and the most critical anti-pattern: assuming an HTTP 200 response is sufficient for the external system to stop receiving retries.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Outbound Messages are workflow *and approval* actions — not Flow actions**: The Metadata API guide defines them as "workflow and approval actions that send the information you specify to an endpoint you designate" (api_meta.txt L140313–140315). `OutboundMessage` is a value of the `WorkflowActionType` enum (L139961) and appears in `ApprovalProcess` action blocks (L23615–23641). It is not a Flow element. If the triggering automation is a Flow or Apex, this skill does not apply — use Platform Events or direct API calls instead.
- **The "User to send as" decides what the endpoint can see**: "The chosen user controls data visibility for the message that is sent to the endpoint" ([Defining Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm)). `integrationUser` is not bookkeeping — it is the field- and record-level filter on the payload, and it is the identity `SessionId` represents.
- **The definition always lives in `workflows/<Object>.workflow`**: There is one `.workflow` file per standard or custom object that has workflow, stored in the `workflows` directory (L139896–139898). Even an outbound message used only by an approval process is declared in the `outboundMessages` array of that file (L139931). Retrieve before you edit.
- **SOAP only — no JSON**: Outbound Messages deliver SOAP 1.1 XML. The external endpoint must be able to parse XML SOAP envelopes and return a specific SOAP acknowledgment response. Systems that only accept JSON cannot use Outbound Messages without a SOAP-to-JSON translation layer.
- **Critical acknowledgment behavior**: The listener must return a `notificationsResponse`, whose schema in the outbound messaging WSDL is a single boolean: `<element name="Ack" type="xsd:boolean"/>`. The SOAP API Developer Guide calls it "the schema for sending an acknowledgment (ack) response to Salesforce" and its sample listener is one line of logic — `r.Ack = true` ([Understanding Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_understanding.htm), [Building a Listener](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_wsdl.htm)). An HTTP 200 with any other body — empty, JSON, plain text — carries no `Ack`, so the message is redelivered.

---

## Questions to Ask Before Configuring

Ask these before the first `<outboundMessages>` element is written. Each one maps to a failure in `references/gotchas.md`; an agent that skips them produces a `.workflow` file that deploys clean and delivers nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is the receiving endpoint a SOAP listener, or a REST/JSON service someone is about to point us at?" | A JSON service returns HTTP 200 with a JSON body, which Salesforce reads as a failed delivery (gotcha 1) | Either the listener owner's commitment to return the `Ack` envelope, or a decision to use `integration/platform-events-integration` instead |
| "Which WSDL version has the listener been generated against?" | `apiVersion` is `Required` on `WorkflowOutboundMessage`, valid values are 8.0 and 18.0 or later, and changing it to a version that doesn't support a configured field makes messages fail until the listener consumes the updated WSDL (api_meta.txt L140327–140337) | The exact `<apiVersion>` value to commit, and a rule that field changes and listener WSDL regeneration ship together |
| "Which user does this send as, and does the listener need to call back into Salesforce?" | `integrationUser` is `Required`; `includeSessionId` is what makes callback possible and is also how a live session leaves the org (L140354–140359) | A named integration user, and a yes/no on `includeSessionId` that is a decision rather than a default |
| "Does this org have the dead letter queue permission turned on?" | `useDeadLetterQueue` is "only available for organizations with dead letter queue permissions turned on" (L140368–140370) — without it, an undelivered message has no landing place | Either `<useDeadLetterQueue>true</useDeadLetterQueue>` in the file, or an explicit reconciliation plan (gotcha 2) |
| "Is the trigger a workflow rule, an approval action, or both?" | Outbound messages are "workflow **and approval** actions" (L140313–140315), but the definition always lives in `workflows/<Object>.workflow` regardless (gotcha 7) | The deploy manifest — an approval-only outbound message still needs the `Workflow` type in `package.xml` |
| "Should this fire once on create, on every save, or only when the criteria newly become true?" | `triggerType` takes `onCreateOnly`, `onAllChanges`, or `onCreateOrTriggeringUpdate` (L140420–140430) and silently decides whether a correction re-notifies | The `<triggerType>` value, and agreement on whether the listener sees corrections |
| "Which fields does the listener actually parse, and who owns that list?" | `fields` is the named references sent (L140346); adding one changes the generated WSDL the listener consumes | A field list with an owner, so field additions become a coordinated change rather than a silent listener break |

What a proper configuration adds over just creating an outbound message in Setup: the `apiVersion` and field list are in version control where a listener-breaking change is reviewable, the session-ID decision is recorded rather than inherited from a Setup default, and the dead-letter/reconciliation answer exists before the first 24-hour drop instead of after it.

---

## Core Concepts

### Metadata Shape

`WorkflowOutboundMessage` (api_meta.txt L140312–140371) — the fields you actually write:

| Element | Type | Required? | What the guide says |
|---|---|---|---|
| `fullName` | string | Required | Developer name; underscores and alphanumerics only, must begin with a letter, no spaces, no trailing underscore, no consecutive underscores (L140348–140352) |
| `name` | string | Required | Component label. Available in API 16.0 and later (L140361) |
| `endpointUrl` | string | Required | "The endpoint URL to which the outbound message is sent" (L140344) |
| `fields` | string[] | Not marked required | "The named references to the fields to be sent" (L140346) |
| `integrationUser` | string | Required | "The named reference to the user under which this message is sent" (L140359) |
| `includeSessionId` | boolean | Required | Includes the Salesforce session ID; "useful if you intend to make API calls and you don't want to include a username and password" (L140354–140357) |
| `apiVersion` | double | Required | Auto-set at creation. Valid values are **8.0 and 18.0 or later**. Modifiable only via Metadata API, not the Salesforce UI. API 18.0+ (L140327–140340) |
| `protected` | boolean | Required | Protected components can't be linked to or referenced by components created in the installing org (L140363–140366) |
| `useDeadLetterQueue` | boolean | Optional | "Only available for organizations with dead letter queue permissions turned on. If set, this outbound message uses the dead letter queue if normal delivery fails" (L140368–140371) |
| `description` | string | Optional | "Describes the outbound message" (L140342) |

The rule that fires it is a `WorkflowRule` `<actions>` block whose `type` is `OutboundMessage` and whose `name` matches the outbound message's `fullName` (L139952–139966). Full deployable XML: `references/metadata-examples.md`.

### The `notifications()` Envelope

Outbound messaging "uses the `notifications()` call to send SOAP messages over HTTP(S) to a designated endpoint when triggered by a workflow rule" ([Understanding Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_understanding.htm)). The WSDL's `notifications` element is a fixed sequence:

| Element | Type | What the guide says |
|---|---|---|
| `OrganizationId` | ID | "ID of the organization sending the message" |
| `ActionId` | ID | "The workflow rule (action) that triggers the message" |
| `SessionId` | string, **nillable** | "Optional, a session ID to be used by endpoint URL client that is responding to the outbound message. It's used by the receiving code to make calls back to Salesforce." Present only when `includeSessionId` is true |
| `EnterpriseUrl` | string | "URL to use to make API calls back to Salesforce using the enterprise WSDL" |
| `PartnerUrl` | string | "URL to use to make API calls back to Salesforce using the partner WSDL" |
| `Notification` | Notification, **`maxOccurs="100"`** | Up to 100 per message. Each is a `<Id>` plus an `<sObject>` carrying "the subset of the fields that you selected when you created the outbound message" |

Two consequences the rest of this skill turns on:

- **One message can carry up to 100 records.** `Notification` is `maxOccurs="100"`, and the response carries a single `Ack` for the whole message. A listener that half-processes a batch and returns `Ack=true` discards the remainder — see gotcha 10.
- **Idempotency is the listener's job, and the guide names the key:** "Each message Notification also has the object ID. Use the object ID to track redelivery attempts of notifications you've already processed."

### Delivery and Acknowledgment

1. Salesforce sends a SOAP payload to the configured endpoint.
2. The listener must return a `notificationsResponse` — "the schema for sending an acknowledgment (ack) response to Salesforce", whose entire content is `<element name="Ack" type="xsd:boolean"/>`:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

The target namespace is `http://soap.sforce.com/2005/09/outbound` — the WSDL's own `targetNamespace`. If the external system returns HTTP 200 with any body that does not carry `Ack` in that namespace — an empty body, a JSON response, a different namespace — there is no acknowledgment and Salesforce redelivers. `Ack` is a value in the response body, not a status code.

### Retry Behavior

What the [Tracking Outbound Message Status](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm) page grounds — Setup, Quick Find `Outbound Messages`, then **View Message Delivery Status**:

| Surface | What the guide says |
|---|---|
| Status list | "View the status of your outbound messages, including the total number of attempted deliveries" |
| Action link | "View the action that triggered the outbound message by clicking any workflow or approval process action ID" |
| **Retry** | "Click Retry to change the Next Attempt date to now. This action causes the message delivery to be immediately retried" |
| **Del** | "Click Del to permanently remove the outbound message from the queue" |

Note what Retry actually does: it moves **Next Attempt** forward, nothing more. Whether that also extends the overall delivery window is a separate claim, and it is the one below that is not grounded.

UNVERIFIED (2026-09-05): the backoff cadence, the 24-hour window, and the claim that a manual retry *resets* that window are not stated in the SOAP API Developer Guide's outbound messaging chapter, and a grep for "outbound" across the Salesforce App Limits Cheat Sheet returns one unrelated hit (change-set file counts). Treat the shape as correct and re-confirm the numbers against Salesforce Help before writing them into an SLA. What *is* grounded as the durability lever: `useDeadLetterQueue` exists for when "normal delivery fails" (api_meta.txt L140368–140371).

Outbound Message delivery retries follow an exponential backoff pattern up to 24 hours from the first failed delivery:
- Retries occur approximately at: 1 min, 2 min, 4 min, 8 min, 16 min, 32 min, and then hourly.
- After 24 hours, if acknowledgment has not been received, the message is permanently dropped — there is no automatic replay.
- Failed messages are visible in Setup > Process Automation > Outbound Messages (Pending Messages tab).
- Failed messages can be manually requeued from the Outbound Messages setup page, resetting the 24-hour window.

### Field Selection Limitations

Outbound Message payloads include:
- `OrganizationId`, `ActionId`, `EnterpriseUrl` and `PartnerUrl` on every message — see the envelope table above. `ActionId` is "the workflow rule (action) that triggers the message", which is what lets a listener that serves several outbound messages tell them apart.
- `SessionId`, but only when `includeSessionId` is true — the element is `nillable="true"` and the guide calls it "Optional". It "represents the user defined in the previous step and not the user who triggered the workflow" ([Defining Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging_setting_up.htm)).
- The record ID of the triggering record.
- Selected fields from the object (chosen when configuring the Outbound Message action).
- Formula fields and related object fields (via cross-object formula fields on the object) can be included.

Limitations:
- Binary fields (file attachments) cannot be included.
- Related records cannot be directly included — only fields on the triggering object and cross-object formula fields.
- The payload is a single record at a time. Outbound Messages are not batch delivery mechanisms.

---

## Common Patterns

### Setting Up an Outbound Message for Record Change Notification

**When to use:** An external ERP system needs to be notified when a Salesforce Opportunity stage changes to "Closed Won."

**How it works:**
1. Create a Workflow Rule on the Opportunity object: "Opportunity Stage changed to Closed Won."
2. Add a Workflow Action: "New Outbound Message."
3. Configure the Outbound Message:
   - Name and unique name.
   - Endpoint URL: `https://erp.example.com/salesforce-webhook/opportunity`.
   - User to send as: integration user (their session ID is included in the payload).
   - Select fields: Id, Name, Amount, StageName, CloseDate, AccountId.
4. Activate the Workflow Rule.
5. Configure the ERP endpoint to parse the SOAP envelope and return the acknowledgment response.
6. Test by closing an Opportunity Won and monitoring delivery in Setup > Process Automation > Outbound Messages.

**Why SOAP acknowledgment matters:** The ERP's HTTP 200 with JSON body is not sufficient. The endpoint must return the SOAP acknowledgment XML. If it returns JSON, Salesforce retries the message every few minutes for 24 hours, delivering the same payload hundreds of times before dropping it.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| External system needs record change notification, can handle SOAP | Outbound Message on Workflow Rule | Built-in, no code required, at-least-once guaranteed |
| External system only accepts JSON | Platform Event or Apex callout | Outbound Messages deliver SOAP only |
| Need to trigger from Flow or Apex | Platform Event or direct Apex HttpRequest | Outbound Messages are Workflow Rule actions only |
| External system returning HTTP 200 but receiving retries | Fix acknowledgment body to return SOAP Ack:true | HTTP 200 alone is not sufficient — SOAP body must match |
| Message delivery stuck/retrying for hours | Manual requeue from Outbound Messages Setup page | Resets the 24-hour window |
| Messages dropped after 24 hours | No automatic replay — manual requeue or re-trigger | After 24h drop, the message is gone; re-trigger by re-saving the record |
| Need batch delivery | Not suitable — Outbound Messages are single-record | Use Bulk API or batch Apex with platform events for bulk |

---

## Recommended Workflow

1. **Retrieve the object's existing `.workflow` file before writing anything** — outbound messages are not standalone metadata. There is one `.workflow` file per object, stored in the `workflows` directory (api_meta.txt L139896–139898), and it holds *every* alert, field update, rule, task and outbound message for that object. Run the retrieve command in `references/metadata-examples.md` § 6; deploying a hand-written file that omits the existing members deletes them.
2. **Answer the seven questions above, then author the `<outboundMessages>` entry** — copy the shape from `references/metadata-examples.md` § 1, not from the guide's own sample (which is not well-formed — gotcha 8). Set `fullName`, `name`, `endpointUrl`, `integrationUser`, `apiVersion`, `protected`, and an explicit `includeSessionId`; add one `<fields>` element per field the listener parses, including `Id`.
3. **Wire the trigger** — for a workflow rule, add a `<actions>` block with `<type>OutboundMessage</type>` and a `<name>` that matches the outbound message's `fullName` exactly (§ 2); for an approval process, add the same `<action>` shape under `finalRejectionActions` / `recallActions` / etc. in the `.approvalProcess` file (§ 4). The name resolves within the object's `.workflow` file — a mismatch fails the deploy.
4. **Hand the listener team the acknowledgment contract** — send `templates/outbound-message-setup-template.md` § "External Endpoint Requirements" and the `apiVersion` you committed in step 2, so they generate the matching WSDL. Do this before the deploy, not after the first retry storm.
5. **Run the checker** — `python3 scripts/check_outbound_message_setup.py --manifest-dir force-app/main/default`. It parses every `.workflow` file and fails on a non-HTTPS endpoint, a missing or `Id`-less field list, a missing `integrationUser`, a non-numeric or out-of-range `apiVersion`, and a rule action naming an outbound message that does not exist in the same file. It warns on `includeSessionId=true` and on an absent `useDeadLetterQueue`.
6. **Deploy, then verify in both directions** — deploy with the `package.xml` in § 5, then (a) confirm the message in Setup by entering `Outbound Messages` in the Quick Find box and selecting **Outbound Messages** (L140338–140340), and (b) re-retrieve the `.workflow` file and diff it against source to see what the org filled in — this is how you find the `apiVersion` the org actually assigned.
7. **Establish the drop-window watch** — a message that has not acknowledged has a bounded life (gotcha 2). Record who checks the pending queue, at what interval, and what the requeue/reconciliation step is, in `templates/outbound-message-setup-template.md` § Monitoring.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The `.workflow` file was **retrieved before it was edited** — `git diff` shows only additions, no removed `alerts` / `fieldUpdates` / `tasks` / `rules`
- [ ] `python3 scripts/check_outbound_message_setup.py --manifest-dir <root>` exits 0
- [ ] Every checker WARN is a recorded decision, not a default: `includeSessionId` and `useDeadLetterQueue`
- [ ] `<apiVersion>` is explicit in the file, legal (8.0, or 18.0+ — L140329), and shared with the listener team
- [ ] Every rule `<actions>` `<name>` of type `OutboundMessage` matches an `outboundMessages` `<fullName>` in the same file
- [ ] If an approval process references the message, `package.xml` carries both `Workflow` and `ApprovalProcess`
- [ ] `<triggerType>` was chosen against "should a correction re-notify?", not inherited
- [ ] `<fields>` includes `Id` and every field the listener parses; the list has a named owner
- [ ] Validate-only deploy (`--dry-run`) passed before the real deploy
- [ ] Post-deploy round-trip diff is clean — the org did not override `apiVersion`
- [ ] External endpoint implements the SOAP acknowledgment response, tested in a sandbox before go-live
- [ ] Message confirmed in Setup (Quick Find `Outbound Messages`, L140338–140340), and a test record change observed leaving the pending list
- [ ] Pending-queue check has an owner and a cadence, or a reconciliation plan stands in for it

---

## Salesforce-Specific Gotchas

The nine grounded failure modes live in `references/gotchas.md`. The three that end integrations:

1. **HTTP 200 without an `Ack` in the response body is not an acknowledgment** — `notificationsResponse` is a single boolean and the listener must actually return it. The external system then receives the same payload repeatedly until the delivery window closes (window length: see the Retry Behavior note).
2. **A message that never acknowledges is eventually discarded with no alert** — `useDeadLetterQueue` is the platform's own mitigation and is "only available for organizations with dead letter queue permissions turned on" (api_meta.txt L140368–140370), so most orgs need an external reconciliation instead.
3. **`apiVersion` is invisible in Setup and can break a live listener** — it is "Required", auto-set at creation, and "can only be modified by using Metadata API. It can't be modified using the Salesforce user interface" (L140327–140334). Changing it to a version that doesn't support a configured field makes messages fail "until you update your outbound message listener to consume the updated WSDL" (L140334–140337).

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Outbound Message configuration | Endpoint URL, field selection, Send As user setup |
| SOAP acknowledgment template | XML response the external system must return to confirm delivery |
| Monitoring procedure | Steps to check Outbound Messages pending and delivered queues |
| Retry management guide | Steps to manually requeue failed messages and reset the 24-hour window |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | You are writing the actual XML — the full `Account.workflow` with an `outboundMessages` entry and the `WorkflowRule` that fires it, the approval-process variant, `package.xml`, retrieve/deploy commands, and the post-deploy verification |
| `references/gotchas.md` | The file deployed and nothing arrives, a deploy failed on an action name, or you are about to trust a default — nine platform behaviours with `api_meta.txt` line citations |
| `references/examples.md` | You want the scenario end to end: the duplicate-delivery diagnosis, the endpoint-outage runbook with checker output, the approval-only outbound message, and the Flow anti-pattern |
| `references/well-architected.md` | You are justifying outbound messages over Platform Events or an Apex callout in a review, or locating the source behind a claim in this package |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated outbound-message advice — five failure modes with a detection hint each |
| `templates/outbound-message-setup-template.md` | Workflow steps 2, 4 and 7 — the configuration worksheet, the acknowledgment contract to hand the listener team, and the monitoring owner |
| `scripts/check_outbound_message_setup.py` | Workflow step 5, and in CI on every PR that touches `workflows/*.workflow` |

---

## Related Skills

- `integration/outbound-messages-and-callbacks` — The listener side: parsing the SOAP envelope and using the session ID from `includeSessionId` to call back into Salesforce
- `integration/outbound-webhook-from-salesforce` — When the target is a JSON webhook rather than a SOAP listener
- `integration/platform-events-integration` — The Flow- and Apex-triggerable alternative when the trigger is not a workflow rule or approval action
- `admin/approval-processes` — Wiring the same outbound message as an approval action (`finalRejectionActions`, `recallActions`, api_meta.txt L23615–23641)
- `admin/workflow-field-update-patterns` — The other action type declared in the same `.workflow` file you are about to retrieve and redeploy
- `admin/process-automation-selection` — Choosing between workflow-rule outbound messages, Flow, and Apex before any of this is built
- `integration/oauth-flows-and-connected-apps` — When the listener calls back with OAuth instead of the included session ID
- `admin/remote-site-settings` — Not required for outbound messages; Salesforce is the sender, not the caller
