# Examples — Custom Index Requests

## Example 1: Requesting a Custom Index for a Lead Routing Query

**Scenario:** A high-growth SaaS company has 4 million Lead records. A real-time lead routing automation runs a SOQL query every 5 seconds: `SELECT Id, OwnerId FROM Lead WHERE LeadSource__c = 'Inbound Web' AND Status = 'Open'`. Query Plan shows TableScan. Average query time has grown to 8 seconds, causing routing delays.

**Problem:** `LeadSource__c` is a custom field. `Status` is a standard field. Neither has a selective index on the combination. The filter matches ~15% of records (600K of 4M), which is above the 10% threshold for a standard custom index.

**Solution:**
1. Add more selective WHERE conditions to reduce the match rate. Add `AND CreatedDate = LAST_N_DAYS:30` to limit to recent leads. This reduces the result set from 600K to ~40K (1% of 4M) — well within selectivity thresholds.
2. Run the Query Plan again. It now shows an index on `CreatedDate` being used.
3. If further optimization is needed, open a Salesforce Support case requesting a two-column index on (`LeadSource__c`, `CreatedDate`) for the Lead object.

**Support case content:**
- Org ID: 00D5x...
- Object: Lead (4.2M records)
- Fields: LeadSource__c and CreatedDate
- SOQL: `SELECT Id, OwnerId FROM Lead WHERE LeadSource__c = 'Inbound Web' AND CreatedDate = LAST_N_DAYS:30`
- Query Plan output: [attached screenshot]
- Field distribution: 'Inbound Web' = 8% of records; LAST_N_DAYS:30 on CreatedDate = ~3% of records
- Query frequency: ~12,000 times per day
- Business impact: Lead routing latency affecting sales team SLA

**Why it works:** The date filter reduces selectivity to a level where the standard index on `CreatedDate` is sufficient. The Support case for a two-column index is a backup if the date index alone is insufficient.

---

## Example 2: Skinny Table for a High-Frequency Dashboard Query

**Scenario:** A manufacturing org's flagship executive dashboard runs a report on the Opportunity object (3.8M records) every 5 minutes. The query always returns the same 6 fields filtered by `CloseDate >= THIS_QUARTER`. A Full sandbox shows the query takes 45 seconds against 3.8M records even with the standard index on CloseDate.

**Problem:** The query is selective (CloseDate = current quarter ≈ 8% of 3.8M = 304K records) and the index is being used, but the query is still slow because the Opportunity table is wide (150+ fields). Each index lookup must perform a full row read to retrieve the 6 fields.

**Solution:** Request a skinny table from Salesforce Support. The skinny table would include only the 6 fields the dashboard needs (OwnerId, CloseDate, StageName, Amount, AccountId, RecordTypeId) plus the indexed CloseDate. Salesforce maintains the skinny table in sync with the main Opportunity table.

**Support case content:**
- Org ID: 00D3y...
- Object: Opportunity (3.8M records)
- Fields for skinny table: Id, OwnerId, CloseDate, StageName, Amount, AccountId, RecordTypeId
- Primary filter: `CloseDate >= THIS_QUARTER`
- Query frequency: ~288 times per day (every 5 minutes, 24 hours)
- Business impact: Executive dashboard timing out in 45s; dashboard loads only after manual refresh

**Why it works:** The skinny table eliminates the wide-row I/O cost. The query optimizer reads from the narrow skinny table rather than the 150+ field Opportunity table, reducing per-row I/O by ~95%.
