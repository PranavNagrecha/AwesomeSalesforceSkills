# Outbound Message Setup — Work Template

Use this template when configuring a Workflow Outbound Message integration.

## Scope

**Skill:** `outbound-message-setup`

**Object:** (e.g., Opportunity, Case)

**Trigger event:** (e.g., Stage changed to Closed Won)

**External endpoint:** (HTTPS URL)

**External system SOAP capability:** [ ] Can parse SOAP  [ ] JSON only (use Platform Events instead)

## Workflow Rule

- **Rule name:** ___
- **Object:** ___
- **Evaluation criteria:** [ ] Created  [ ] Created and subsequent edits  [ ] Criteria met
- **Rule criteria:** ___
- **Status:** [ ] Active

## Outbound Message Configuration

All rows below are elements of `WorkflowOutboundMessage` (api_meta.txt L140312–140371). The
"Required" column is the guide's own, not a house rule.

| Element | Required? | Value |
|---|---|---|
| `fullName` | Required | (developer name — the string every rule and approval action must match) |
| `name` | Required | (display label) |
| `endpointUrl` | Required | https:// |
| `integrationUser` | Required | (integration user username) |
| `apiVersion` | Required | (valid values: 8.0, or 18.0 and later — L140329. Not settable in the UI, L140332–140334) |
| `includeSessionId` | Required | [ ] false (default choice)  [ ] true — only if the listener calls back |
| `protected` | Required | [ ] false (org-native)  [ ] true (managed package only) |
| `useDeadLetterQueue` | Optional | [ ] true  [ ] org lacks the DLQ permission — reconciliation plan below instead (L140368–140371) |
| `description` | Optional | (owner team + the fact that the field list is contract-bound) |

**Trigger** — one of:

| | Value |
|---|---|
| Workflow rule `fullName` | |
| `triggerType` | [ ] onCreateOnly  [ ] onAllChanges  [ ] onCreateOrTriggeringUpdate (L140420–140430) |
| Approval process (if any) | (object.processName, and which action block: `finalRejectionActions` / `recallActions` / …) |

**Fields selected for payload:**

| Field API Name | Reason Included |
|---|---|
| Id | Record identifier (always included) |
| | |
| | |

## External Endpoint Requirements

Provide to the external development team:

**Required response format** — the `notificationsResponse` schema is a single boolean `Ack`
(SOAP API Developer Guide, *Understanding Outbound Messaging*).

Status line and headers:

```http
HTTP/1.1 200 OK
Content-Type: text/xml; charset=UTF-8
```

Body:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notificationsResponse xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notificationsResponse>
  </soapenv:Body>
</soapenv:Envelope>
```

WARNING: HTTP 200 with any other body (JSON, empty, XML with wrong namespace) is not an acknowledgment. Salesforce redelivers.

WARNING: one `Ack` acknowledges the **whole message**, and `Notification` has `maxOccurs="100"` in the WSDL. A listener that processes 60 of 100 notifications and returns `Ack=true` silently discards the other 40. Correlate on each `Notification`'s object `Id` — "use the object ID to track redelivery attempts of notifications you've already processed".

- [ ] Listener returns `Ack=false` (or no ack) when it cannot process the whole message
- [ ] Listener is idempotent on the `Notification` object `Id`

## Testing

- [ ] Workflow Rule activated
- [ ] Test record updated to trigger Workflow
- [ ] Message appears in Setup > Process Automation > Outbound Messages > Pending
- [ ] External endpoint returns correct SOAP acknowledgment
- [ ] Message moves to Delivered tab
- [ ] No duplicate deliveries observed in external system logs

## Monitoring

Durability decision (settle this before go-live, not during the first outage):

- [ ] Org **has** the dead letter queue permission → `<useDeadLetterQueue>true</useDeadLetterQueue>` is committed in the `.workflow` file
- [ ] Org **lacks** it → reconciliation plan below is the durability answer

Reconciliation plan (required if the box above is the second one): ______________________

- [ ] Monitoring procedure documented for the pending queue — Setup, Quick Find `Outbound Messages`, then **Outbound Messages** (L140338–140340)
- [ ] Owner and cadence named for that check
- [ ] Manual requeue procedure documented for endpoint outages
- [ ] `check_outbound_message_setup.py --strict` wired into CI on `workflows/**`, so a later edit that drops `useDeadLetterQueue` or flips `includeSessionId` fails the build

## Version Contract With the Listener Team

- [ ] `apiVersion` value shared with the listener team, and their WSDL generated against it
- [ ] Agreement recorded that any change to the `<fields>` list ships in the same window as a listener WSDL regeneration — a mismatch makes messages "fail until you update your outbound message listener to consume the updated WSDL" (L140334–140337)
- [ ] Post-deploy round-trip performed (`sf project retrieve start --metadata Workflow:<Object>` + `git diff`) to confirm the org did not override `apiVersion`

## Notes

(Record any deviations from standard configuration.)
