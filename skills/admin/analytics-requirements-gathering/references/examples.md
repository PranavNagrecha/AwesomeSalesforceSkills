# Examples — Analytics Requirements Gathering

## Example 1: Sales Analytics Requirements — CRM Analytics vs Reports Decision

**Context:** A VP of Sales asks for "a sales performance dashboard." The project team is unsure whether to use CRM Analytics or standard Reports.

**Problem:** Without a structured requirements session, the developer builds a CRM Analytics dashboard. The stakeholder later reveals they only needed Opportunity reports grouped by Owner — no cross-object joins, no external data, no predictions. CRM Analytics was unnecessary and the license cost was not justified.

**Solution:**
Requirements gathering reveals:
- Data sources: Opportunities (standard object only)
- Grouping: by Owner, by Stage, by Close Quarter
- External data: None
- Predictive needs: None
- Audience: All sales reps see their own data; VPs see all

Decision record: Standard Reports and Dashboards with Owner-based row-level security (sharing settings) can serve this need without CRM Analytics. CRM Analytics is not required.

**Why it works:** A structured requirements session with a CRM Analytics vs Reports decision framework prevents over-engineering. The decision record documents the rationale for auditability.

---

## Example 2: Revenue Analytics with External Snowflake Data — Requirements Mapping

**Context:** A finance team needs a CRM Analytics dashboard combining Salesforce Opportunity data with billing data from a Snowflake data warehouse.

**Problem:** Requirements are gathered at the object level only ("we need Opportunity and Billing data"). The developer builds a recipe assuming the Snowflake table has a matching field to join on Account. The Snowflake table uses a different Account identifier format (internal billing ID vs Salesforce AccountId). The join produces zero matches.

**Solution:**
Requirements document captures the data source matrix:
- Salesforce: Opportunity (Amount, Stage, CloseDate, AccountId), Account (Name, Industry, Region__c)
- External: Snowflake table `billing.invoices` (columns: account_billing_id, invoice_amount, invoice_date)
- Join key issue noted in requirements: Salesforce AccountId ≠ Snowflake account_billing_id; requires a mapping table or a lookup field on the Account object that stores the Snowflake billing ID
- Transformation requirement: a mapping recipe step that looks up BillingID__c on Account and joins to the Snowflake table on that field
- Named Credential needed for Snowflake connector: documented as out-of-scope for requirements but flagged as pre-requisite

**Why it works:** Field-level requirements (not just object names) expose the join key mismatch before development starts, saving a full recipe rebuild.

---

## Anti-Pattern: Recommending Standard Reports When CRM Analytics Is Actually Needed

**What practitioners do:** They default to "create a standard Report type" without assessing whether cross-object joins, external data, predictive features, or audience-specific views are required.

**What goes wrong:** Standard Reports cannot use external data and have limited row-level security customization. UNVERIFIED (2026-10-03): the claim that standard Reports "cannot join more than two objects efficiently" is not grounded in the guides read for this pass; check custom report type limits for the specific case. Practitioners build standard Reports, then realize they cannot meet the requirements, and must migrate to CRM Analytics mid-project.

**Correct approach:** Always complete a CRM Analytics vs standard Reports decision step at the start of requirements gathering. Use the decision criteria: cross-object joins, external data, predictive needs, complex row-level security, and large dataset aggregation are the primary indicators for CRM Analytics.

---

## Example 3: The Requirements Package as a Structured Artifact

**Context:** The finance dashboard from Example 2 is approved for build. The developer asks for a single artifact that holds sources, fields, refresh, and audiences, so nothing is re-elicited mid-build.

**Solution:** Capture the package as YAML in the project repository. Each key traces to a question in the SKILL.md table.

```yaml
platform_decision:
  choice: CRM Analytics
  reason: "Joins Salesforce Opportunity data with Snowflake billing data; external data cannot feed standard Reports"
  license: CRM Analytics Plus   # 10 billion row allocation; 2 concurrent dataflow runs in production
sources:
  - name: Opportunity
    type: salesforce_local_sync      # lands as a connected object; needs a recipe to become a dataset
    fields: [Id, AccountId, Amount, StageName, CloseDate, OwnerId]
    integration_user_access_checked: true
    refresh: eventdriven              # after the local sync, one counted run per day
  - name: Account
    type: salesforce_local_sync
    fields: [Id, Name, Industry, Region__c, Billing_Id__c]
    integration_user_access_checked: true
    refresh: eventdriven
  - name: billing.invoices
    type: external_connection         # counts against org limits; confirm with the integration owner
    fields: [account_billing_id, invoice_amount, invoice_date]
    refresh: daily
transformations:
  - join: "Opportunity LOOKUP Account on AccountId = Id"   # keep every Opportunity
  - join: "Account LOOKUP billing.invoices on Billing_Id__c = account_billing_id"
  - computed: "FiscalQuarter from CloseDate, fiscal year starts February"
datasets:
  - name: Finance_Revenue
    estimated_rows: 2500000
    row_security:
      mechanism: predicate
      predicate: "'Region__c' == \"$User.Sales_Region__c\""
      security_user_needs_read_on: [User.Sales_Region__c]
audiences:
  - role: Finance Analyst
    app_access: EditAllContents
    rows: own region
  - role: CFO
    app_access: View
    rows: all regions   # needs a predicate branch or a separate dataset; decide before build
refresh_budget:
  counted_runs_per_day_existing: 9
  counted_runs_per_day_added: 2
  limit: 60
```

**Why it works:** Every build decision the developer needs is in one reviewed file. The `security_user_needs_read_on` line prevents the predicate query error described in gotcha 6, and the refresh budget shows the plan fits the 60-run limit. The deployable form of the audience section is in `metadata-examples.md`.

