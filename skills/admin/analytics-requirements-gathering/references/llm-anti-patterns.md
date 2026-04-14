# LLM Anti-Patterns — Analytics Requirements Gathering

Common mistakes AI coding assistants make when generating or advising on CRM Analytics requirements gathering. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Standard Reports When CRM Analytics Is Needed

**What the LLM generates:** "Create a custom report type joining Opportunity, Account, and Territory. Add a dashboard with summary charts." — recommending standard Reports for cross-object use cases that require CRM Analytics.

**Why it happens:** Standard Salesforce Reports are the dominant pattern in training data for Salesforce reporting. LLMs don't reliably model when cross-object joins, external data, or large-scale aggregation exceed standard Reports capabilities.

**Correct pattern:**
```
CRM Analytics is required when:
- More than 2 objects must be joined in a single view
- External data (Snowflake, S3, BigQuery) must be included
- Predictive scoring or trend forecasting is needed
- Row-level security requires custom SAQL predicates
- Dataset aggregates exceed 2,000 report rows

Standard Reports and Dashboards are sufficient when:
- Single-object or simple 2-object report
- No external data
- Standard sharing settings provide correct row-level security
```

**Detection hint:** Answer recommends "custom report type" or "summary report" for a use case that involves external data, 3+ object joins, or complex row-level security.

---

## Anti-Pattern 2: Treating Object Sync as a Ready-to-Query Dataset

**What the LLM generates:** "Enable Opportunity sync in CRM Analytics Data Manager, then you can query the Opportunity data in your lenses."

**Why it happens:** LLMs conflate "connecting to a data source" with "having a queryable dataset." They don't model the intermediate dataflow/recipe step required to create a CRM Analytics dataset from a synced object.

**Correct pattern:**
```
Object sync only = data in storage layer (not queryable as a dataset)
To create a queryable dataset from a synced object:
1. Enable object sync in Data Manager
2. Create a dataflow or recipe that reads the synced object
3. Run the dataflow/recipe to create a named dataset
4. The named dataset is now available in lens/dashboard Studio
```

**Detection hint:** Instructions skip from "enable sync" to "query in a lens" without a recipe or dataflow step.

---

## Anti-Pattern 3: Omitting Data Source Type from Requirements

**What the LLM generates:** Analytics requirements that list "data sources: Opportunity, Account, Billing data" without specifying whether Billing data is a Salesforce object, external connector, Data Cloud DMO, or CSV upload.

**Why it happens:** LLMs treat "data source" as a generic concept and don't model that CRM Analytics has four distinct connection mechanisms with different setup requirements and refresh capabilities.

**Correct pattern:**
```
Requirements must specify data source type for each source:
- Opportunity: Salesforce object sync → recipe → dataset
- Account: Salesforce object sync → recipe → dataset
- Billing data: Snowflake external connector → recipe → dataset
  Named Credential required, incremental refresh watermark needed
```

**Detection hint:** Requirements list data sources by name only, without specifying the connection type (Salesforce object / external connector / Data Cloud / CSV).

---

## Anti-Pattern 4: Not Documenting Audience-Specific Row-Level Security

**What the LLM generates:** An analytics requirements document that lists one dashboard design for all users, without specifying what data each user role can see.

**Why it happens:** LLMs default to the "one dashboard for everyone" mental model unless explicitly asked about access control. They don't proactively ask about row-level security requirements.

**Correct pattern:**
```
Audience matrix must document per role:
- Sales Rep: sees only own opportunities (predicate: 'OwnerId' == "$User.Id")
- Sales Manager: sees team's opportunities (sharing inheritance)
- VP: sees all data (no predicate / admin profile)
- Finance: sees all opportunities but only financial fields (field-level security + predicate)
```

**Detection hint:** Requirements document has no audience matrix or row-level security specification.

---

## Anti-Pattern 5: Missing Transformation Requirements

**What the LLM generates:** Requirements that say "use the Account and Opportunity objects" without specifying how they should be joined, what fields are computed, or how dates should be transformed into fiscal periods.

**Why it happens:** LLMs treat data retrieval as a simple SELECT operation. They don't model that CRM Analytics recipes require explicit transformation specifications for joins, computed fields, and date dimensions.

**Correct pattern:**
```
Transformation requirements:
- Join: Account + Opportunity on AccountId (left join, keep all Opportunities)
- Computed field: FiscalQuarter__c = derive from CloseDate using fiscal year offset
- Rename: Account.Name → AccountName, Opportunity.Name → OpportunityName
- Computed field: Revenue_Tier = case when Amount < 10000 then 'Small' when Amount < 100000 then 'Mid' else 'Large'
```

**Detection hint:** Requirements document lists source objects but has no join specifications, computed field definitions, or field rename/normalization requirements.
