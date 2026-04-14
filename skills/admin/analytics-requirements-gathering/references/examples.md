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

**What goes wrong:** Standard Reports cannot join more than two objects efficiently, cannot use external data, and have limited row-level security customization. Practitioners build standard Reports, then realize they cannot meet the requirements, and must migrate to CRM Analytics mid-project.

**Correct approach:** Always complete a CRM Analytics vs standard Reports decision step at the start of requirements gathering. Use the decision criteria: cross-object joins, external data, predictive needs, complex row-level security, and large dataset aggregation are the primary indicators for CRM Analytics.
