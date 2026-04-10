# Examples — MCAE Prospect Data Migration

## Example 1: Importing Prospects From a Legacy CRM With Custom Field Mapping

**Context:** A B2B company is migrating from HubSpot to MCAE. The marketing team has exported 45,000 contact records from HubSpot as a CSV. The records include standard fields (email, first name, last name, company, phone) plus two custom fields that the team uses for lead routing: `Lead Source Detail` (a text field) and `Product Interest` (a picklist). The Salesforce admin has already created corresponding custom fields on the Salesforce Lead object.

**Problem:** The first import attempt succeeded (no import errors), but when the team checked imported prospects in MCAE, both custom field columns were blank on every record. The CSV clearly contained values for those columns. The import log showed the correct record count but no indication that data was dropped.

**Solution:**

The root cause was that the custom fields existed on the Salesforce Lead object but had not yet been:
1. Created as MCAE custom prospect fields (Admin > Configure Fields > Prospect Fields > Add Custom Field)
2. Mapped bidirectionally in the Salesforce Connector (Admin > Connectors > Salesforce > Edit > Map Fields)

Steps taken to resolve:

```
1. Navigate to MCAE Admin > Configure Fields > Prospect Fields
2. Add Custom Field: Label = "Lead Source Detail", Type = Text, Salesforce Field = Lead.Lead_Source_Detail__c
3. Add Custom Field: Label = "Product Interest", Type = Dropdown, Salesforce Field = Lead.Product_Interest__c
4. Navigate to Admin > Connectors > Edit Salesforce Connector > Map Fields
5. Confirm Lead Source Detail and Product Interest appear in the field mapping list
6. Set sync direction to bidirectional for both fields
7. Save the connector configuration
8. Re-import the CSV using Prospects > Import > Import Prospects
9. On the field mapping screen, map "Lead Source Detail" column → MCAE "Lead Source Detail" field
10. Map "Product Interest" column → MCAE "Product Interest" field
11. Submit import; verify custom field values on spot-checked records after completion
```

**Why it works:** MCAE's import field mapping UI only surfaces fields that have been fully created and connector-mapped. Until those prerequisites are met, the column has no target and the data is silently discarded. Running the full connector setup before the import ensures the fields appear in the mapping UI and the values are written correctly.

---

## Example 2: Discovering That Engagement History Cannot Be Migrated

**Context:** A company is consolidating its marketing operations from Eloqua into MCAE. Eloqua has three years of engagement history per contact: email opens, click-throughs, webinar attendance flags, and a composite engagement score. The demand generation manager asks whether this history can be imported into MCAE so that current nurture programs don't start from zero.

**Problem:** The project team initially plans to include open count, click count, last activity date, and engagement score as columns in the migration CSV. After researching the MCAE import field mapping UI, they discover these fields do not exist as importable prospect fields. They then investigate the Pardot API v5 to determine if VisitorActivity records can be created programmatically.

**Solution:**

```
Investigation findings (to document in the migration scope document):

1. MCAE CSV list import supports prospect profile fields only.
   Engagement data (opens, clicks, form fills, page views) is not a prospect field —
   it is stored as VisitorActivity records linked to a prospect.

2. The Pardot API v5 VisitorActivity endpoint is read-only.
   POST to /api/v5/visitorActivities is not supported.
   There is no create or upsert operation for visitor activities in the API.

3. No Salesforce-supported workaround exists for backfilling engagement history.

Migration plan adjustment:
- Remove open count, click count, last activity date, and engagement score from the CSV.
- Document the engagement history gap in the migration scope sign-off.
- Plan a re-engagement email campaign to run 2 weeks after go-live, targeting all imported 
  prospects. This generates initial MCAE engagement signals and begins rebuilding scores.
- Suppress all score-gated automation rules for 60 days post-migration.
  Score threshold rules will fire incorrectly (sending or suppressing prospects) because 
  all imported prospects have score = 0 regardless of their actual engagement history.
```

**Why it works:** Documenting the limitation before the migration prevents the team from discovering it mid-project. The re-engagement campaign approach is the accepted practice for rebuilding signal in MCAE after a prospect import — it is faster and more accurate than attempting any workaround because it generates real engagement data against real MCAE assets.

---

## Anti-Pattern: Attempting to Import Engagement History via a CSV Workaround

**What practitioners do:** A practitioner exports Eloqua or HubSpot engagement metrics (open count, click rate, last sent date) into the migration CSV. They create MCAE custom prospect fields named "Historical Opens" and "Historical Clicks" and map the CSV columns to those fields during import. They argue this preserves engagement signal for scoring purposes.

**What goes wrong:** MCAE prospect score is calculated automatically based on native MCAE activity — tracked email sends, form submissions, page views, and custom redirects. The score is not a custom field that can be written directly. Creating custom fields named "Historical Opens" does store the values, but those values have no connection to the MCAE scoring engine. Scoring rules in MCAE will not read a custom field named "Historical Opens" and adjust the score accordingly — they respond only to actual tracked activity events. The imported "historical" values sit unused and mislead the team into thinking prospect scores reflect actual engagement, when in reality the score is still zero.

**Correct approach:** Accept that engagement scores restart from zero for all imported prospects. Suppress score-gated automation rules during a defined warm-up period (typically 30–90 days). Run a re-engagement campaign targeting all imported prospects immediately after migration to generate real MCAE activity. Build scoring rules in MCAE that reward the types of engagement you care about going forward. Scores will reflect genuine, verifiable MCAE-tracked activity rather than imported approximations.
