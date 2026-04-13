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

| Field | Value |
|---|---|
| Name | |
| Unique Name | |
| Endpoint URL | https:// (required) |
| User to Send As | (integration user username) |
| Protected Component | [ ] Yes  [ ] No |

**Fields selected for payload:**

| Field API Name | Reason Included |
|---|---|
| Id | Record identifier (always included) |
| | |
| | |

## External Endpoint Requirements

Provide to the external development team:

**Required response format:**
```xml
HTTP 200 OK
Content-Type: text/xml; charset=UTF-8

<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <notifications xmlns="http://soap.sforce.com/2005/09/outbound">
      <Ack>true</Ack>
    </notifications>
  </soapenv:Body>
</soapenv:Envelope>
```

WARNING: HTTP 200 with any other body (JSON, empty, XML with wrong namespace) triggers 24-hour retry storm.

## Testing

- [ ] Workflow Rule activated
- [ ] Test record updated to trigger Workflow
- [ ] Message appears in Setup > Process Automation > Outbound Messages > Pending
- [ ] External endpoint returns correct SOAP acknowledgment
- [ ] Message moves to Delivered tab
- [ ] No duplicate deliveries observed in external system logs

## Monitoring

- [ ] Monitoring procedure documented for pending queue
- [ ] Alert configured for messages stuck in Pending > 1 hour
- [ ] Manual requeue procedure documented for endpoint outages

## Notes

(Record any deviations from standard configuration.)
