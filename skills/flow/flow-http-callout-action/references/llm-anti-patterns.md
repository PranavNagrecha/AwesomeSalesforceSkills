# LLM Anti-Patterns — Flow HTTP Callout Action

Scope: the declarative HTTP Callout action in Flow Builder — its credential
prerequisites, its schema-by-example model, and the fault handling it requires. External
Services registrations are covered by `flow/flow-external-services`; the surrounding flow
structure by `flow/auto-launched-flow-patterns`.

## Anti-Pattern 1: Producing an Apex callout class for a one-field GET

Asked "call this address-verification endpoint from a flow", assistants generate an
`@InvocableMethod` wrapper, an `HttpCalloutMock`, a test class and a deployment. That is
a code artefact an admin cannot change, added to an org that can now do the same thing
declaratively.

❌ Invocable Apex wrapper for a simple request/response with a flat payload.
✅ The HTTP Callout action, defined against a Named Credential and configured in Flow
Builder. Move to Apex when there is real logic to run — retries with state, response
correlation, orchestration across several endpoints, or a payload the schema-by-example
model cannot describe.

## Anti-Pattern 2: Pointing the action at a legacy Named Credential

The most common hard failure, and the error message does not say what is wrong. The HTTP
Callout action requires the current Named Credential model — a Named Credential paired
with an **External Credential** that carries the authentication protocol and principal.
An older-style Named Credential with authentication configured directly on it will not be
selectable, or will fail at runtime.

❌ Reuse the Named Credential that has been serving Apex callouts for years.
✅ Create an External Credential with the authentication protocol and a named principal,
grant the running user's permission set access to that principal, then create or migrate
the Named Credential to reference it. The permission-set grant is the step most often
missed — without it, authentication fails for everyone except the administrator who built
it, which is precisely the person who tests it.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <authenticationProtocol>OAuth</authenticationProtocol>
    <label>Address Verification</label>
    <externalCredentialParameters>
        <parameterName>NamedPrincipal</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
</ExternalCredential>
```

Source: Named Credentials and External Credentials —
https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm

## Anti-Pattern 3: Treating the sample response as a contract

The action derives its output schema from a sample response you paste in. Assistants
supply an idealised sample — every field present, every value populated — and the flow
then depends on a shape the API does not always return. Fields absent from the sample do
not exist as flow resources at all, and fields the sample showed as populated arrive null
in the cases that matter.

**Wrong** — the vendor's documentation sample, in which everything is present:

```json
{
  "status": "MATCHED",
  "address": {
    "line1": "1 Market Street",
    "line2": "Suite 300",
    "city": "San Francisco",
    "postalCode": "94105",
    "geo": { "lat": 37.7938, "lon": -122.3948 }
  },
  "confidence": 0.98
}
```

**Right** — a real response from a non-ideal case, which is what defines the usable schema:

```json
{
  "status": "PARTIAL",
  "address": {
    "line1": "1 Market Street",
    "city": "San Francisco",
    "postalCode": null
  },
  "confidence": 0.41
}
```

`line2` and `geo` are absent here, so if the schema were generated from this sample they
would not exist as flow resources at all — and if it were generated from the first sample,
`{!Callout.address.geo.lat}` would resolve to null on every partial match. Paste a real
response captured from the actual endpoint, prefer one from a non-ideal case — a partial
match, an empty result set, a record with optional fields missing — and null-check every
output before use. If the API returns structurally different shapes for success and
failure, the schema-by-example model cannot represent both, and that is a genuine reason
to move to Apex.

## Anti-Pattern 4: No fault connector on the action

The action's fault path is not optional in practice, and assistants omit it because the
happy path is what was asked for. Without it, an HTTP failure ends the flow with an
unhandled error — a screen flow shows the user a raw error, and a record-triggered flow
rolls the transaction back and emails the flow's error recipient.

❌ Wire the action's success connector and stop.
✅ Every callout action gets a fault connector. In a screen flow, route to a message
screen that says what failed and what the user should do. In an autolaunched flow, route
to error handling that records the failure and lets the transaction complete. Use
`templates/flow/FaultPath_Template.md` for the canonical shape rather than inventing one
per flow.

## Anti-Pattern 5: Putting the callout inside a loop

The generated flow loops a collection and calls the endpoint once per record. Every one of
those is a separate HTTP request inside a single transaction, bounded by the documented
limit of 100 callouts per transaction and by a cumulative callout timeout of 120 seconds
for the whole transaction — so a hundred-record collection against a slow endpoint fails
on elapsed time well before it reaches the callout count.

❌ Loop → HTTP Callout → Assignment, once per record.
✅ If the API accepts a batch, send one request for the collection. If it does not, move
the work out of the synchronous path — a scheduled flow processing a bounded slice, or an
Apex queueable — so a slow endpoint delays a job rather than failing a user's save.

## Anti-Pattern 6: Calling out from a record-triggered flow before the DML has settled

A record-triggered flow that performs a callout inherits the platform's ordering
constraints. Assistants place the callout in a fast-field-update or before-save context,
where callouts are not permitted at all, or in an after-save path where the callout
extends the user's transaction and its latency becomes the user's save latency.

❌ HTTP Callout in a before-save record-triggered flow.
✅ Run the callout from the asynchronous path of a record-triggered flow, so it executes
after the transaction commits. That is the declarative equivalent of the
callout-after-DML rule in Apex, and it also stops a slow partner API from lengthening
every save on the object.

## Anti-Pattern 7: Hand-rolling pagination across flow elements

Assistants build a loop with a page counter, a decision on whether more pages exist, and
an assignment accumulating results. Flow has no cursor primitive, so this construction is
fragile, hard to read, and multiplies the callout count by the page count inside one
transaction.

❌ A five-element loop implementing cursor pagination.
✅ Request a page size large enough that one call suffices, and treat multi-page retrieval
as the signal that this integration belongs in Apex — where the loop, the cursor and the
accumulated state are ordinary code rather than a diagram.
