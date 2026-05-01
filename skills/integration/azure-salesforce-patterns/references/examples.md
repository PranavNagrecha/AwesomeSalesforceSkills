# Examples — Azure Salesforce Integration Patterns

## Example 1 — "React to Closed-Won opportunities in an Azure Function"

**Context:** A Sales Cloud org wants to start a downstream provisioning
workflow in Azure (create the customer in the billing system, kick off
onboarding emails) every time an Opportunity is set to Closed Won.
Volume is around 800 events / day with peaks of 50 in a minute. The
provisioning workflow must not lose events even if the Function is
slow or the Service Bus side is briefly unavailable.

**Problem:** Reaching for an Apex `@future` callout to the Function URL
is the obvious path, but a bulk update of 50 opportunities in one
transaction will fan into 50 callouts, exhaust the asynchronous-Apex
governor budget, and provide no replay if the Function fails mid-batch.
There is also no DLQ, so failures get logged to email-the-admin Apex
exception emails.

**Solution:**

```text
1. Create a high-volume Platform Event:        Opportunity_Won__e
   Fields: Opportunity_Id__c, Account_Id__c, Amount__c, Close_Date__c
2. Record-triggered Flow (after-save) on Opportunity:
     when StageName = 'Closed Won' and IsClosed = true
     publish Opportunity_Won__e
3. Setup → Azure Service Bus Connector:
     SAS connection string for the namespace
     Outbound Connection: maps Opportunity_Won__e → topic 'opportunity-won'
4. Azure side: Function with Service Bus topic trigger,
     subscription 'provisioning-sub', max delivery 5,
     dead-letter on max-delivery to 'opportunity-won/$DeadLetterQueue'
```

**Why it works:** The high-volume Platform Event channel survives
subscriber slowness (the Service Bus Connector listener is the
subscriber here). Service Bus's at-least-once delivery + DLQ replaces
the retry / fault-handling code that the Apex `@future` path would
require. The Apex transaction that closes the Opportunity does not
make a callout, so governor exposure stays at zero.

---

## Example 2 — "Real-time pricing call from a screen flow"

**Context:** A guided selling screen flow needs to fetch a price from a
proprietary pricing engine hosted as an Azure Function behind APIM. The
agent is on the screen waiting; latency budget is 2 seconds; the call
must succeed before the flow can advance.

**Problem:** The Service Bus pattern is wrong here — it is async by
construction. A direct callout from Flow without a Named Credential
ends up storing a Function Key in custom metadata or worse.

**Solution:**

```text
1. Create an External Credential 'AzureAD_PricingEngine' with:
     Authentication Protocol = OAuth 2.0
     Authentication Flow Type = Client Credentials with Client Secret Flow
     Identity Type = Named Principal
     Token Endpoint URL = https://login.microsoftonline.com/<tenant>/oauth2/v2.0/token
     Scope = api://<app-id>/.default
2. Create a Named Credential 'AzureAPIM_Pricing':
     URL = https://<your-apim>.azure-api.net
     External Credential = AzureAD_PricingEngine
     Allowed Namespaces = (your namespace, locked down)
3. Screen flow → HTTP Callout action:
     Endpoint Path = /pricing/quote
     Method = POST
     Connection = AzureAPIM_Pricing
     Sample response captured during action authoring
4. Map the action output → screen variables → next screen
```

**Why it works:** The token never appears in flow metadata; OAuth 2.0
client-credentials means no human is in the loop and the secret
rotates centrally. The Allowed Namespaces lock prevents another package
from reusing the credential for an unintended endpoint. The HTTP
Callout action surfaces the response shape to Flow as typed variables
without an Apex shim.

---

## Anti-Pattern — "Just store the Azure Function key in a Custom Metadata Type"

**What practitioners do:** Create a `Azure_Config__mdt` with a
`Function_Key__c` Long Text field and read it from Apex with
`Azure_Config__mdt.getInstance('PROD').Function_Key__c`. Then
hand-build the HTTP request with a `x-functions-key` header.

**What goes wrong:** Custom Metadata is checked into version control on
the way to production. Anyone with `View All Data` or
`View Setup and Configuration` can read the secret in the running org.
The key cannot be rotated without a deployment; secrets show up in
ApexLog if anyone logs the request. None of the OAuth 2.0 token
hygiene happens.

**Correct approach:** Always use a Named Credential with an External
Credential. For Azure-hosted endpoints, prefer OAuth 2.0
client-credentials against Azure AD. Only fall back to Function Keys
for low-stakes endpoints (no PII, dev-only), and even then put the key
in the External Credential's Per-User or Named Principal parameter, not
in custom metadata.
