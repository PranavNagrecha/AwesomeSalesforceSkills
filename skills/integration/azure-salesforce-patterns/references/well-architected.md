# Well-Architected Notes — Azure Salesforce Integration Patterns

## Relevant Pillars

- **Security** — Auth model selection drives the security envelope.
  OAuth 2.0 client-credentials against Azure AD (the recommended path
  for Apex → Function callouts) keeps tokens short-lived and rotates
  centrally. Function Keys, the Microsoft default, end up in custom
  metadata or environment files; treat them as the regression. The
  Service Bus Connector's SAS connection string is a long-lived secret
  — store it only in the connector's encrypted setup field, never in
  custom metadata or Apex source.
- **Reliability** — The Service Bus Connector is the only Azure
  integration path with built-in at-least-once delivery, DLQ, and
  replay. AppFlow has no Azure equivalent, so Power Platform's
  Salesforce connector is the citizen-automation alternative — but its
  throttle is shared at the M365 tenant level, which makes it
  unreliable for backbone work. Apex callouts have neither retry nor
  replay; the calling transaction must implement its own idempotency.
  Lean on Service Bus Connector for any flow where losing an event
  has business impact.
- **Operational Excellence** — Managed paths (Service Bus Connector,
  Data Cloud Azure Blob ingestion, Azure AD gallery app) reduce
  operational debt to "watch the dashboard". Custom Apex → Function
  callouts plus a parallel Power Automate flow doing duplicate work
  equals "watch four places: Salesforce debug logs, Apex exception
  emails, Function App Insights, Power Platform run history". Pick
  managed unless a constraint forces you off it.

## Architectural Tradeoffs

- **Service Bus Connector vs Apex callout (Salesforce → Azure).**
  Service Bus is right when the contract is event-level and async;
  Apex callout is right when the response must come back inside the
  same transaction. The split is *whether the Salesforce-side
  transaction needs the answer before commit*.
- **Service Bus Connector vs Power Platform connector.** Both can
  carry events from Salesforce to Azure-side compute. Service Bus is
  the integration backbone (durable, dedicated, no tenant-wide
  throttle); Power Platform is citizen automation (shared throttle,
  governed on the M365 side, easy for non-developers). Pick by
  governance owner and volume, not by what is faster to demo.
- **Data Cloud Azure Blob vs Apex Bulk into custom objects.** Both
  ingest files; Data Cloud writes to Data Lake Objects (correct shape
  for analytics, identity resolution at scale), Apex Bulk writes to
  custom CRM objects (correct shape only for transactional CRM data).
  For data-lake-to-analytics bridging, the destination shape decides.
- **Azure AD SAML vs OIDC.** SAML is the mature, common path with the
  best gallery-app drift detection. OIDC via Auth Provider is correct
  when you need richer JIT (claims to User fields beyond SCIM) or
  when downstream Apex needs to consume Azure AD-issued tokens.

## Anti-Patterns

1. **"We can just use Power Automate for everything."** Power Platform
   connectors share a tenant-wide throttle with every other Power
   Platform user in the M365 tenant. Treat them as citizen automation,
   not as the integration backbone — anything event-volume-shaped
   needs Service Bus Connector or Apex with a Named Credential.
2. **"Function Keys are fine, we'll rotate later."** The migration from
   Function Keys + Custom Metadata to Named Credential + External
   Credential is cheap on call #1 and expensive on call #30. Do it on
   call #1.
3. **"Just hand-roll the SAML config; gallery apps are heavyweight."**
   The Azure AD Salesforce gallery app provides drift detection and
   SCIM provisioning that hand-rolled SAML cannot match. Use the
   gallery app and lock the SCIM mapping to lifecycle attributes.

## Official Sources Used

- Azure Service Bus Connector — Feature Support — https://help.salesforce.com/s/articleView?id=001121997&type=1
- Azure Service Bus Connector — Message Listener — https://help.salesforce.com/s/articleView?id=001121869&type=1
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Data 360 Integration Patterns — Azure Blob Storage — https://architect.salesforce.com/docs/architect/data360/guide/data360_integration_patterns.html
- Named Credentials and External Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Salesforce Well-Architected — Trusted (Secure) — https://architect.salesforce.com/well-architected/trusted/secure
- REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/intro_what_is_rest_api.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
