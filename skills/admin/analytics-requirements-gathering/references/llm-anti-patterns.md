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
- Dataset aggregates exceed what a report can display

Standard Reports and Dashboards are sufficient when:
- Single-object or simple 2-object report
- No external data
- Standard sharing settings provide correct row-level security
```

**Detection hint:** Answer recommends "custom report type" or "summary report" for a use case that involves external data, 3+ object joins, or complex row-level security.

UNVERIFIED (2026-10-03): the object-count threshold above ("more than 2 objects") is a rule of thumb, not a documented limit; check custom report type limits for the specific case.

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

---

## Anti-Pattern 6: Treating App Sharing as Row-Level Security

**What the LLM generates:** "Share the Analytics app with the Sales Reps group so each rep sees their own pipeline."

**Why it happens:** In standard Salesforce, folder and record sharing blur together in casual training text. In CRM Analytics, app sharing and dataset row-level security are separate layers.

**Correct pattern:**

```
App share (WaveApplication.shares): who can open the app and its assets
  accessLevel: View | EditAllContents | Manage
Row security (dataset predicate or sharing inheritance): which rows each user sees
  'OwnerId' == "$User.Id"
A dataset with no row-level security shows every row to everyone who can open it.
```

**Detection hint:** An audience requirement satisfied only by an app share, with no predicate or sharing-inheritance decision.

---

## Anti-Pattern 7: Planning Refresh Cadence Without the Run Budget

**What the LLM generates:** "Refresh each dataset hourly so dashboards stay current," for six datasets, without counting runs.

**Why it happens:** The model treats refresh frequency as free. CRM Analytics caps dataflow and recipe runs at 60 per rolling 24 hours (runs under two minutes excepted), and at the limit no job runs.

**Correct pattern:** Add a refresh budget to the requirements: each scheduled job, its expected duration, and its frequency, summed against 60. Prefer event-based schedules that run once after the local sync.

**Detection hint:** Several hourly schedules in one requirements document with no run count.

---

## Anti-Pattern 8: Forgetting the Two Internal Users

**What the LLM generates:** A data source matrix and predicate design that never mentions the Integration User or the Security User.

**Why it happens:** These users are internal to CRM Analytics and rarely appear in generic requirements templates.

**Correct pattern:** Check every extracted field against the Integration User (a job fails on an unreadable field). List every custom User field a predicate references so the Security User can be granted read access (otherwise queries error). Never delete either user.

**Detection hint:** Requirements that name custom User fields in predicates, or sensitive source fields, with no access task for the internal users.

