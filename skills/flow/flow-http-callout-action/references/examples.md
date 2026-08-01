# Examples — Flow HTTP Callout Action

## Example 1: Address verification on lead capture

**Context:** a screen flow captures a lead and should verify the postal address against a
vendor API before saving.

**Problem:** the first attempt used an Apex wrapper, which put an admin-owned integration
behind a deployment. The second attempt used the HTTP Callout action but reused the
org's existing Named Credential — the one that had been serving Apex callouts for years —
and it was not selectable in the action's configuration.

**Solution — the credential first, because nothing else works until it does.**

The HTTP Callout action requires the current Named Credential model: an External
Credential holding the authentication protocol and principal, referenced by a Named
Credential holding the URL.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <authenticationProtocol>Custom</authenticationProtocol>
    <label>Address Verification</label>
    <externalCredentialParameters>
        <parameterName>AddrVerifyPrincipal</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
    <externalCredentialParameters>
        <parameterName>ApiKey</parameterName>
        <parameterType>AuthParameter</parameterType>
        <parameterValue>[REDACTED]</parameterValue>
        <sequenceNumber>2</sequenceNumber>
    </externalCredentialParameters>
</ExternalCredential>
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Address Verification</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <parameters>
        <parameterName>Url</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://api.addressvendor.example.com</parameterValue>
    </parameters>
    <parameters>
        <parameterName>ExternalCredential</parameterName>
        <parameterType>Authentication</parameterType>
        <parameterValue>Address_Verification</parameterValue>
    </parameters>
</NamedCredential>
```

Then grant the running users' permission set access to the **principal** on the External
Credential. This is the step that is almost always missed, and it fails in the most
misleading way possible: the administrator who built it can authenticate, and nobody else
can — so it passes every test the builder runs.

**The sample response is the schema.** Paste a real capture, and choose an unflattering
one — here, a partial match where `suite` and `plus4` are absent:

```json
{
  "status": "PARTIAL",
  "candidates": [
    {
      "street": "1 Market St",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94105",
      "confidence": 0.82
    }
  ]
}
```

Fields absent from the sample do not become flow resources at all, so pasting the vendor's
idealised documentation example produces a flow that cannot reference the fields it will
actually receive — and one that assumes fields are populated when the real API omits them.

**Flow shape:**

```text
Screen_Capture_Address
   └── HTTP Callout : Verify_Address  (GET /v3/verify)
         Named Credential : Address_Verification
         Query params     : street, city, state, zip  <- from the screen
         Success connector -> Decision_Confidence
         Fault connector   -> Screen_Verification_Unavailable

Decision_Confidence
   ├── High   {!Verify_Address.candidates} is not null
   │            AND {!Verify_Address.status} = 'EXACT'   -> Create_Lead_Verified
   └── Default (PARTIAL, empty candidates, or null)      -> Screen_Confirm_Manually
```

**Why it works:** the fault connector catches transport failures — timeout, 5xx, auth —
and the Decision catches the successful-but-unhelpful responses, which are far more
common. Those are different failure classes and the fault path only handles the first.
Routing a partial match to manual confirmation rather than blocking the save keeps a
vendor's bad day from stopping lead capture. Use
`templates/flow/FaultPath_Template.md` for the canonical fault-path shape.

---

## Example 2: Enriching service appointments without lengthening the user's save

**Context:** when a service appointment is scheduled, the dispatcher wants the forecast
conditions at the location recorded on the record.

**Problem:** the first build put the HTTP Callout in the after-save path of a
record-triggered flow. It worked, and it added the vendor's response time to every save
of the object. When the vendor degraded, dispatchers experienced it as Salesforce being
slow. The second build looped a collection and called the endpoint once per appointment —
a hundred appointments meant a hundred requests inside one transaction, against a
documented limit of 100 callouts per transaction and a cumulative callout timeout of 120
seconds for the whole transaction. It failed on elapsed time long before the count.

**Solution:** move the callout off the synchronous path, and batch where the API allows
it.

```text
Record-Triggered Flow : ServiceAppointment_Enrich
  Object            : ServiceAppointment
  Trigger           : A record is created or updated
  Entry conditions  : Status = 'Scheduled'  AND  Weather_Checked__c = false
  Run               : Asynchronously, after the transaction completes   <- the key setting

  1. Get Records  Get_Location   (ServiceTerritory of the appointment)
  2. HTTP Callout Fetch_Forecast (GET /v1/forecast?lat={!lat}&lon={!lon}&date={!date})
       Success -> 3
       Fault   -> Set_Unavailable
  3. Decision     Has_Forecast   ({!Fetch_Forecast.daily} is not null)
       Yes -> 4        No -> Set_Unavailable
  4. Update Records  Set_Weather
       Weather_Summary__c = {!Fetch_Forecast.daily.summary}
       Weather_Checked__c = true
       Fault connector -> Set_Unavailable

  Set_Unavailable : Update  Weather_Summary__c = 'Unavailable',
                            Weather_Checked__c = true
```

**Why it works:** running asynchronously means the callout happens after the transaction
commits, so the dispatcher's save completes at its normal speed and a slow vendor delays
an enrichment rather than a save. That is the declarative counterpart of the
callout-after-DML rule in Apex. The `Weather_Checked__c` flag in the entry conditions is
what stops the update in step 4 from re-triggering the flow — without it this is a
recursion, and the asynchronous path makes the recursion harder to spot because it does
not fail in the user's face.

Setting `Weather_Summary__c` to `Unavailable` on the fault path rather than leaving it
null is deliberate: a null means "not attempted yet" and a value means "attempted", which
is the distinction a retry job needs. A fault path that only logs leaves the record
indistinguishable from one the flow has not reached.
