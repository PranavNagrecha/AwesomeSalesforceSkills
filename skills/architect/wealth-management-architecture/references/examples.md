# Examples — Wealth Management Architecture

## Example 1: Enabling AI Portfolio Insights via IndustriesSettings Metadata Deployment

**Context:** A wealth management firm is upgrading their FSC org to surface AI-powered portfolio analysis and client engagement insights in the advisor workspace. The feature is confirmed available under the firm's FSC license. The Salesforce admin toggled every visible setting in Setup but the AI insight components still do not appear on the advisor page.

**Problem:** The `enableWealthManagementAIPref` flag is not surfaced as a standard Setup toggle — it lives in the `IndustriesSettings` metadata type and must be deployed via Metadata API. Clicking through Setup UI will never activate it. The missing deployment means the advisor workspace components that depend on this flag render as blank panels with no error message.

**Solution:**

```xml
<!-- force-app/main/default/settings/Industries.settings-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<IndustriesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableWealthManagementAIPref>true</enableWealthManagementAIPref>
    <enableDealManagement>true</enableDealManagement>
</IndustriesSettings>
```

Deploy with Salesforce CLI:

```bash
sf project deploy start \
  --source-dir force-app/main/default/settings/Industries.settings-meta.xml \
  --target-org <alias>
```

Retrieve the current state first to avoid overwriting other active flags:

```bash
sf project retrieve start \
  --metadata "IndustriesSettings" \
  --target-org <alias>
```

**Why it works:** `IndustriesSettings` is a settings metadata type — it represents the entire settings singleton for the Industries namespace. Retrieving before deploying ensures only the target flags are changed. The AI preference flag requires API v63.0+, so confirm the CLI and `sfdx-project.json` `sourceApiVersion` are set to `63.0` or higher before deploying.

---

## Example 2: Enrolling Financial Account Transactions in Compliant Data Sharing with Existing Data

**Context:** A regional wealth management firm is going live with CDS for regulatory compliance. Account and Opportunity are already enrolled. The team now needs to enroll `FinServ__FinancialAccountTransaction__c` (a custom extension mapped to the custodian feed) in CDS. The object has 2.3 million existing records from three months of custodian imports.

**Problem:** Activating CDS on the object type without immediately running the sharing recalculation batch causes all 2.3 million existing transaction records to have no sharing entries. Advisors will see zero transaction history after activation. This does not generate errors — it silently removes record access.

**Solution:**

1. Schedule a maintenance window during off-hours.
2. Enroll the object in CDS via Setup > Compliant Data Sharing > Object Activation.
3. Immediately after activation, queue the sharing recalculation batch. In Apex:

```apex
// Queue CDS sharing recalculation for Financial Account Transaction
// Use the FSC-provided invocable or the platform sharing recalculation job
Database.executeBatch(
    new FinServ.CompliantDataSharingRecalcBatch(
        'FinServ__FinancialAccountTransaction__c'
    ),
    200
);
```

4. Monitor batch completion via Apex Jobs in Setup. Confirm the job processes all 2.3 million records before the maintenance window closes.
5. Run a spot-check query to confirm sharing entries exist:

```soql
SELECT COUNT() FROM FinServ__FinancialAccountTransaction__Share
WHERE RowCause = 'CompliantDataSharing__c'
```

**Why it works:** CDS enrollment creates the access-control infrastructure but does not back-fill it. The recalculation batch walks all existing records and creates the correct `Share` entries based on current advisor assignments. Without this step, the object's existing records are inaccessible even to the advisors who own the accounts.

---

## Anti-Pattern: Routing Nightly Custodian Batch Through REST Composite API

**What practitioners do:** Use the Salesforce REST Composite API to insert or update `FinServ__FinancialAccountTransaction__c` records from a nightly custodian feed. This is familiar to developers who know the REST API and the Composite endpoint supports up to 25 sub-requests per call.

**What goes wrong:** A 500K-record nightly feed requires 20,000 Composite API calls with 25 records each. Each call consumes governor limits including DML rows, CPU time, and heap. At scale, calls begin timing out and hitting the per-org daily API call limit (varies by edition, commonly 100K–1M). Failed records are silently dropped unless the caller implements retry logic. The feed also competes with advisor-initiated transactions during the evening overlap window.

**Correct approach:** Use Bulk API 2.0 ingest jobs for all custodian feeds exceeding a few thousand records. Create one job per object type per feed, upload CSV or JSON payloads in chunks up to 150 MB, then poll for job completion. Failed rows are returned in a separate result set for dead-letter processing — no records are silently lost. The Bulk API path does not consume the same per-transaction governor limits as the REST path.
