# Gotchas — Azure Salesforce Integration Patterns

Non-obvious behaviors that cause real production problems when integrating
Salesforce with Azure. Each entry is **what / when / how**: what goes
wrong, when it bites, how to avoid it.

## 1. Service Bus Connector listener silently drops messages on standard PE channels

**What:** The Salesforce-side Message Listener for the Azure Service Bus
Connector subscribes to a Salesforce Platform Event channel that the
listener publishes onto. If that channel is **standard** (not
high-volume), Salesforce only retains 24 hours of events and does not
handle slow subscribers gracefully.

**When:** It bites when the receiving Apex / Flow that consumes the
Platform Event slows down for any reason — a long-running batch on the
same org, a sandbox refresh window, an upstream Service Bus DLQ replay
flooding the listener. You see "missing" Salesforce-side reactions to
Service Bus messages with no errors anywhere.

**How:** Configure the Platform Event channel as **High Volume** at
creation time. You cannot convert a standard channel to high-volume
after the fact — the field is immutable.

## 2. Function Keys in Custom Metadata are a one-way door

**What:** Function Keys (`x-functions-key` header) are easy to start
with because Azure Functions accepts them out of the box. Teams put
them in a Custom Metadata Type and call from Apex. Once 30 callers
exist, retrofitting Named Credentials means re-touching every caller.

**When:** It bites at the first secret rotation or the first auditor
who reads "where do you store secrets?" in a SOC 2 review. It also
bites when someone with `View Setup and Configuration` extracts the
key from the running org.

**How:** Start with a Named Credential + External Credential from the
first call, even when the endpoint is dev-only. The cost of doing it
right on call #1 is negligible; the cost on call #30 is a refactor
ticket and a security incident.

## 3. Azure AD SCIM provisioning can grant Salesforce permissions

**What:** The Azure AD Salesforce Enterprise gallery app supports
mapping AAD attributes onto User fields, including `ProfileId` and
indirect Permission Set assignments via SCIM extensions. Whoever
configures the gallery app on the AAD side decides who has Modify All
Data in Salesforce.

**When:** It bites when an Azure AD admin who has never logged into
Salesforce changes a SCIM mapping during a tenant-wide cleanup.
Salesforce-side change-management does not see this; Setup Audit Trail
sees the resulting User update but not the AAD config change.

**How:** Lock the SCIM mapping in the gallery app to **lifecycle
attributes only** — `username`, `email`, `firstname`, `lastname`,
`isActive`, `userType`. Govern Profiles and Permission Sets entirely
from Salesforce-side rules (Permission Set Groups, validation rules,
or a Salesforce-resident provisioning admin process).

## 4. Power Platform's Salesforce connector throttles at the M365 tenant level

**What:** A Power Automate flow you built has its own per-flow request
budget, but the underlying Salesforce connector quotas are tenant-wide
across all Power Automate / Logic Apps / Power Apps usage in the same
M365 tenant.

**When:** It bites when an unrelated team's badly-built citizen flow
saturates the connector quota. Your business-critical Power Automate
flow starts seeing 429 responses or long delays. The Salesforce side
sees nothing — it is not a Salesforce-side limit.

**How:** For any high-business-impact flow, use a **dedicated
connection** and a **dedicated service account** so quota tracking is
explicit. Document the flow in M365 governance and request capacity
reservation if your tenant has Power Platform per-flow plans.

## 5. Data Cloud Azure Blob ingestion races partial files

**What:** The Data Cloud Azure Blob connector reads files at rest on a
schedule (15-minute minimum cadence on standard ingestion). If a
producer writes the same file path repeatedly (overwriting), the
ingestion job can read a half-written file.

**When:** It bites when an upstream pipeline rewrites
`opportunities.parquet` every 5 minutes "for freshness". You see Data
Lake Object rows that look truncated, or Calculated Insights that are
intermittently wrong with no error anywhere.

**How:** Use **immutable file naming** with a date+UUID suffix
(`opportunities/2026-05-01/run-3a8e9f.parquet`) and treat the storage
container as append-only. Configure ingestion to read the whole prefix
and let the connector handle de-duplication via the watermark.

## 6. OAuth 2.0 client-credentials needs the right Refresh-Token Policy

**What:** Salesforce's Connected App default Refresh-Token Policy is
"first use", which expires the refresh token after the first refresh
exchange. Server-to-server flows (Apex callout to Azure with
client-credentials) do not behave like that — they expect a stable
machine credential.

**When:** It bites the first time the access token expires after the
Connected App is moved from setup to production. The next callout
fails with `invalid_grant`, and there is no human to re-consent.

**How:** Set the Connected App's **Refresh-Token Policy to "Refresh
token is valid until revoked"** for every server-to-server flow. Pair
with a Permission Set Group that grants only the API scopes the flow
actually needs. Same gotcha as the AWS-side JWT Bearer flow.
