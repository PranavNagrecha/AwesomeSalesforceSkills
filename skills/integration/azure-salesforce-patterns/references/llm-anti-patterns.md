# LLM Anti-Patterns — Azure Salesforce Integration Patterns

Mistakes AI coding assistants commonly make when asked about
Salesforce↔Azure integration. Each entry is **what / why / correct /
detection** so the consuming agent can self-check.

## 1. Generating an Apex `@future` callout when Service Bus Connector applies

**What the LLM generates:** Boilerplate Apex with `@future(callout=true)`
to POST a JSON payload to an Azure Function URL on every Opportunity
Closed-Won, with no retry and a hard-coded function key.

**Why:** Public training data overweights "Apex callout to webhook" as
the canonical Salesforce-to-cloud pattern. The native Azure Service
Bus Connector is recent and underrepresented in the corpus, and most
LLM examples never mention it.

**Correct pattern:**

```text
- Publish Opportunity_Won__e high-volume Platform Event
- Setup → Azure Service Bus Connector outbound mapping → topic
- Function side: Service Bus topic trigger
```

**Detection:** Search Apex output for `@future(callout=true)` paired
with a hostname containing `azurewebsites.net` or `*.azure-api.net`.
Ask: "Is this transactional or fire-and-forget?" If fire-and-forget,
suggest Service Bus Connector.

## 2. Hard-coding the Function Key in Custom Metadata or Apex

**What the LLM generates:**

```apex
String key = Azure_Config__mdt.getInstance('PROD').Function_Key__c;
req.setHeader('x-functions-key', key);
```

…or worse, `final String KEY = 'abc123==';` in the class body.

**Why:** Function-Key auth is the simplest Azure mechanism and shows up
first in Microsoft Quickstarts. LLMs reach for the simplest example.
Salesforce-side Named Credentials require more setup and feel
disproportionate for a one-line example.

**Correct pattern:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:AzureAPIM_Pricing/pricing/quote');
req.setMethod('POST');
req.setHeader('Content-Type', 'application/json');
// Auth applied by the External Credential
```

The Named Credential `AzureAPIM_Pricing` has an attached External
Credential using OAuth 2.0 client-credentials.

**Detection:** Grep for `setHeader('x-functions-key'` or
`Function_Key__c`. Either is a smell.

## 3. Treating the Power Platform Salesforce connector as an integration backbone

**What the LLM generates:** A Power Automate flow that polls Salesforce
every minute via the connector to do high-volume sync work, paired
with claims that "Power Automate scales like serverless".

**Why:** Power Automate is the Microsoft-side default for "automate
across these apps" and LLMs follow that framing. The reality —
tenant-wide quota tied to all M365 Power Platform usage — is
operational knowledge that does not appear in product docs.

**Correct pattern:** Treat Power Platform connectors as the **citizen
automation** path: low volume, employee-productivity flows, manual
triggers and approvals. Anything event-volume-shaped goes through
Service Bus Connector or Apex callouts. Document the boundary in
governance.

**Detection:** A Power Automate flow polling Salesforce more than once
per 5 minutes, or a recurrence trigger with high frequency, is the
tell.

## 4. Suggesting Apex Bulk API to load Azure Blob files when the consumer is analytics

**What the LLM generates:** A pipeline that reads Parquet from Azure
Blob, converts to CSV in Apex (somehow), and uploads via Bulk API 2.0
into custom CRM objects — then asks Calculated Insights to query
those custom objects.

**Why:** "Bulk API" is the canonical Salesforce mass-load answer and
LLMs default to it. The Data Cloud Azure Blob connector is recent and
the destination shape (DLO → DMO) is unfamiliar to general-purpose
LLMs.

**Correct pattern:** If the downstream consumer is Data Cloud
(Calculated Insights, segments, activations), use the **Data 360 Azure
Blob Storage connector** to ingest into Data Lake Objects, then
promote to Data Model Objects. Custom CRM objects are the wrong
destination shape for analytics-grade volumes.

**Detection:** Output mentions both "Bulk API 2.0" and
"Calculated Insights" in the same design — that combination is almost
always a smell.

## 5. Mixing Azure AD SAML and OIDC Auth Provider as if interchangeable

**What the LLM generates:** "Use Azure AD SSO; configure either SAML
2.0 or OpenID Connect — they are equivalent."

**Why:** Both are listed under SSO in Microsoft and Salesforce docs.
LLMs flatten "either works" into "they are interchangeable". They are
not — JIT provisioning, claim-to-User-field mapping, and SCIM
companion behavior differ.

**Correct pattern:** Pick **SAML 2.0** when the requirement is "let
users log in" and SCIM-based provisioning suffices.
Pick **OIDC via Auth Provider** when you need richer JIT (claims into
User fields beyond standard SCIM) or when the org also wants to use
Azure AD as an IdP for a connected app federation use case (Apex
callout exchanging Azure AD tokens for Salesforce session). Document
the choice; do not present them as interchangeable.

**Detection:** Output that contains "SAML or OIDC, either works" with
no follow-up about JIT mapping or claim flow.
