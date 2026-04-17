# Examples — Data Loader and Tools

## Example 1: Choosing Between Data Import Wizard and Data Loader for a Lead Import

**Context:** A marketing ops admin needs to import 8,500 new leads from a trade show list (CSV) into a Salesforce Production org. The org uses Lightning Experience. The admin wants to deduplicate by email address. No scheduling is needed.

**Problem:** The admin defaults to Data Loader because it is familiar, but encounters confusion setting up an external ID upsert field for email-based deduplication.

**Solution:**

Use Data Import Wizard instead. It handles email-based dedup for Leads natively without requiring a custom external ID field:

1. Go to Setup → Data Import Wizard → Launch Wizard.
2. Select **Leads** → **Add new and update existing records**.
3. Choose **Match by: Email**.
4. Upload the CSV.
5. Map fields on the mapping screen (wizard auto-maps common column headers like "First Name", "Last Name", "Email", "Company").
6. Click **Start Import**.
7. Monitor progress at Setup → Bulk Data Load Jobs.

```text
CSV column mapping for Data Import Wizard (Leads):
  "First Name"    → First Name
  "Last Name"     → Last Name
  "Email"         → Email
  "Company"       → Company
  "Phone"         → Phone
  "Lead Source"   → Lead Source
```

**Why it works:** Data Import Wizard supports email-based deduplication for Leads out of the box. The 8,500 record count is well within the 50,000 record limit. No Java runtime, no desktop install, and no field mapping file to maintain.

**When this example breaks:** If the CSV has more than 50,000 rows, the wizard silently truncates at 50,000. Switch to Data Loader upsert with an external ID field (e.g., a custom `External_Email__c` field with External ID checked, or use the `Email` standard field as a dedup key via Data Loader's upsert operation pointed at a Contact external ID — Leads require a custom external ID field for Data Loader upsert).

---

## Example 2: Automating a Nightly Opportunity Export on Windows

**Context:** A revenue ops team needs a daily CSV extract of all open Opportunities (StageName != 'Closed Won' and != 'Closed Lost') deposited to a shared drive for downstream reporting. Volume is approximately 200,000 records.

**Problem:** Running the export manually via the GUI every night is error-prone and requires someone to be present.

**Solution:**

Use Data Loader CLI batch mode on Windows with Windows Task Scheduler.

**Step 1 — Create an encryption key and encrypted password:**
```bat
cd "C:\Program Files\Salesforce\Data Loader\bin"
encrypt.bat -g mykey.key
encrypt.bat -e MyPassword mykey.key
```
Save the encrypted password string; you will reference it in config.

**Step 2 — Create `ExportOpportunities-process-conf.xml`:**
```xml
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN"
  "http://www.springframework.org/dtd/spring-beans.dtd">
<beans>
  <bean id="ExportOpportunities"
        class="com.salesforce.dataloader.process.ProcessRunner"
        singleton="false">
    <description>Nightly export of open Opportunities</description>
    <property name="name" value="ExportOpportunities"/>
    <property name="configOverrideMap">
      <map>
        <entry key="sfdc.endpoint"       value="https://login.salesforce.com"/>
        <entry key="sfdc.username"       value="dataloader@example.com"/>
        <entry key="sfdc.password"       value="ENCRYPTED_PASSWORD_HERE"/>
        <entry key="sfdc.debugMessages"  value="false"/>
        <entry key="process.operation"   value="extract"/>
        <entry key="sfdc.entity"         value="Opportunity"/>
        <entry key="dataAccess.type"     value="csvWrite"/>
        <entry key="dataAccess.name"     value="C:\exports\opportunities_nightly.csv"/>
        <entry key="sfdc.extractionSOQL" value="SELECT Id, Name, StageName, Amount, CloseDate, AccountId FROM Opportunity WHERE IsClosed = false"/>
        <entry key="sfdc.useBulkApi"     value="true"/>
        <entry key="sfdc.bulkApiSerialMode" value="false"/>
      </map>
    </property>
  </bean>
</beans>
```

**Step 3 — Run from command line to test:**
```bat
dataloader.bat process "C:\exports\config" ExportOpportunities
```

**Step 4 — Schedule via Windows Task Scheduler:**
- Create a task that runs `dataloader.bat process "C:\exports\config" ExportOpportunities` at 02:00 AM daily.
- Set the task to run under a service account with the appropriate Salesforce permissions.

**Why it works:** Data Loader CLI batch mode reads configuration from `process-conf.xml`, encrypts credentials, and supports Bulk API 2.0 for the 200K+ record volume. The output CSV path is fixed and predictable for downstream consumption.

**macOS alternative:** Use Salesforce CLI with a cron job instead:
```bash
# In crontab -e:
0 2 * * * /usr/local/bin/sf data export bulk \
  --sobject Opportunity \
  --query "SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity WHERE IsClosed = false" \
  --output-file /exports/opportunities_nightly.csv \
  --target-org prod-org
```

---

## Example 3: Replacing Workbench for Ad-Hoc SOQL in a Developer Sandbox

**Context:** A developer uses Workbench to run SOQL queries and test REST API endpoints in a scratch org. They want to know the official replacement workflow.

**Problem:** Workbench is on a sunset trajectory; official Salesforce guidance points away from it. Building workflows around it creates fragile dependencies.

**Solution:**

Use one of the officially supported alternatives depending on use case:

**For SOQL queries:**
```bash
# Salesforce CLI — query from terminal
sf data query \
  --query "SELECT Id, Name, StageName FROM Opportunity WHERE CloseDate = THIS_QUARTER" \
  --target-org my-scratch-org \
  --result-format csv > results.csv

# For large result sets (bulk query):
sf data export bulk \
  --sobject Opportunity \
  --query "SELECT Id, Name FROM Opportunity" \
  --output-file results.csv \
  --target-org my-scratch-org
```

**For REST Explorer (equivalent to Workbench REST Explorer tab):**
```bash
# Salesforce CLI REST calls
sf org request rest /services/data/v66.0/sobjects/Account/describe \
  --target-org my-scratch-org

# Or use VS Code Salesforce Extensions → Org Browser / REST Explorer panel
```

**Why it works:** Salesforce CLI is officially supported, cross-platform, version-controlled friendly, and maintained actively by Salesforce. Unlike Workbench, CLI commands can be captured in scripts and shared via source control.

---

## Anti-Pattern: Using Salesforce Inspector in Production for Data Exports

**What practitioners do:** Developers install Salesforce Inspector Reloaded in a production org Chrome browser and use it to export customer data to CSV files for quick reporting or data cleanup tasks.

**What goes wrong:** Salesforce Inspector and Salesforce Inspector Reloaded are open-source Chrome extensions maintained by the community — they are NOT official Salesforce products. Using them in production orgs:

- Bypasses standard data governance and audit trail controls
- May violate data residency and PII handling policies (data is extracted through the browser)
- Creates security risk if the extension is compromised in a future version
- Provides no error.csv for failed rows and no resumability for large exports

**Correct approach:** Use Data Loader (with logging) or Salesforce CLI for all production data exports. Both tools are official, auditable, and provide structured success/error output. Reserve Salesforce Inspector for developer sandbox field-name lookup only, not data extraction.
