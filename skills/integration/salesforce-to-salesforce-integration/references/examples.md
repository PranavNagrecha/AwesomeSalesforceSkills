# Examples — Salesforce-to-Salesforce Integration

## Example 1: Replacing Native S2S With API-Based Sync

**Context:** A company has native S2S enabled between their Sales org and Service org (enabled two years ago). It was working fine at low volume but now causes SOAP API limit errors as the business has grown to 5,000+ record shares per day.

**Problem:** Native S2S consumes SOAP API calls on both orgs. At 5,000 records/day, each S2S share counts as a SOAP API call against both orgs' daily limits. The orgs are hitting API limits and some shares are failing silently.

**Solution:**
Design a REST API-based cross-org sync to replace S2S:
1. Create Connected App in Service org (target) with OAuth2 Client Credentials flow
2. Create Named Credential in Sales org (source) pointing to Service org instance URL
3. Implement a Scheduled Apex job that runs every 2 hours: queries recently modified Accounts in Sales org, calls Service org REST API to upsert matching records using `External_ID__c` as idempotency key
4. Note: native S2S cannot be disabled — it will continue to exist but new sync traffic is routed through the API-based mechanism; the old PartnerNetworkConnections should be deactivated where possible

**Why it works:** API-based sync with Scheduled Apex gives full control over call frequency, batch size, and error handling. It does not consume SOAP API limits at the same rate as native S2S.

---

## Example 2: Salesforce Connect Cross-Org for Read-Only Inventory Access

**Context:** A Manufacturing org needs to display live inventory availability from a separate Inventory Management Salesforce org on the Opportunity record page in the Sales org, without copying all inventory data to the Sales org.

**Problem:** The team considers syncing all Inventory records to the Sales org via nightly batch, but there are 2M inventory line items that change constantly. A nightly sync would be stale by midday and storage costs are significant.

**Solution:**
Use Salesforce Connect Cross-Org adapter:
1. Create Connected App in Inventory org with REST API scope
2. Create External Data Source in Sales org: Type = Salesforce, URL = Inventory org instance
3. Create External Objects in Sales org mapping to Inventory org's custom objects
4. Add External Object related list to Opportunity record page
5. Users see live inventory availability queried on demand from Inventory org

**Why it works:** No data replication — inventory data is always current, fetched live on page load. No storage cost in Sales org. The Salesforce Connect Cross-Org adapter handles authentication and query translation automatically.

---

## Anti-Pattern: Enabling Native S2S Without Understanding Irreversibility

**What practitioners do:** They enable the native Salesforce-to-Salesforce feature in a sandbox to test it, then enable it in production without reading the documentation about irreversibility.

**What goes wrong:** The S2S feature cannot be deactivated once enabled. If the business later decides to use a different cross-org architecture, the S2S objects (PartnerNetworkConnection, PartnerNetworkRecordConnection) persist in the org forever, causing confusion for future developers.

**Correct approach:** Never enable native S2S without an explicit business decision that accepts its permanent nature. If testing is needed, use a developer edition org for evaluation. In production, prefer API-based sync which can be modified or removed freely.
