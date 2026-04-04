# Examples — SOQL Query Optimization

## Example 1: Fixing a Non-Selective Query on a 2M-Record Custom Object

**Context:** A financial services org has a `Loan_Application__c` custom object with 2.1 million records. A nightly batch job runs the following SOQL query to pull pending applications:

```soql
SELECT Id, Applicant_Name__c, Status__c, Loan_Amount__c
FROM Loan_Application__c
WHERE Status__c = 'Pending Review'
AND Assigned_Officer__c = null
```

The job consistently times out after the org grew past 1.5 million records.

**Problem:**

- `Status__c` is a custom picklist field with no index.
- `Assigned_Officer__c` is a custom lookup field. Lookups are standard indexed, but the `= null` filter is not served by the index because index tables exclude null rows by default.
- Query Plan tool shows cost of 4.2 — a full-table scan.

**Diagnosis steps:**

1. Open Developer Console > Debug > Open Query Plan.
2. Paste the query. Cost = 4.2. Plan type: "TableScan". No index candidates listed.
3. Run a selectivity check: `SELECT Status__c, COUNT(Id) FROM Loan_Application__c GROUP BY Status__c`. Result: 'Pending Review' = 180,000 records (8.6% of total). That is selective for a custom index.
4. For the null filter: Salesforce standard index on `Assigned_Officer__c` excludes null rows by default.

**Solution:**

Step 1 — Request a custom index on `Status__c` via Salesforce Support. Provide: object API name (`Loan_Application__c`), field API name (`Status__c`), and the query pattern. Selectivity evidence: 8.6% match rate on target value.

Step 2 — Request a null-inclusive index on `Assigned_Officer__c` via the same Support case.

Step 3 — After indexes are confirmed active in production, re-run Query Plan. Expected: cost < 1.0, plan type uses the custom index.

Step 4 — Rewrite query to ensure both filters remain indexed:

```soql
SELECT Id, Applicant_Name__c, Status__c, Loan_Amount__c
FROM Loan_Application__c
WHERE Status__c = 'Pending Review'
AND Assigned_Officer__c = null
ORDER BY CreatedDate ASC
LIMIT 2000
```

**Why it works:** With a custom index on `Status__c` (selective at 8.6%) and a null-inclusive index on `Assigned_Officer__c`, the optimizer can use both indexes. The AND combination cost drops below 1.0 because each individual filter is below the 10%/333,333 threshold for custom indexes.

---

## Example 2: Debugging a Report Timeout Caused by a Formula Field Filter

**Context:** A sales operations team has a report on the `Opportunity` object (3.8M records) that filters by a formula field `Days_Since_Last_Activity__c`. The formula references `LastActivityDate` (a standard field on the object) and returns a numeric count. The report consistently times out for managers.

**Problem:**

`Days_Since_Last_Activity__c` is a non-deterministic formula field because it references `TODAY()` in its calculation (e.g., `TODAY() - LastActivityDate`). Non-deterministic formula fields cannot be indexed. Filtering on them always produces a full-table scan regardless of the selectivity of the computed value.

Query Plan for `WHERE Days_Since_Last_Activity__c > 30` shows cost = 6.1, TableScan.

**Solution:**

Option A — Replace the formula field filter with a filter on `LastActivityDate` directly:

```soql
SELECT Id, Name, OwnerId, StageName, Amount
FROM Opportunity
WHERE LastActivityDate < LAST_N_DAYS:30
AND IsClosed = false
```

`LastActivityDate` is not a standard indexed field, but `OwnerId` and `IsClosed` combined with a date range can be selective. Verify with Query Plan.

Option B — Create a stored numeric field `Days_Without_Activity__c` (Number type, non-formula). Populate it via a nightly scheduled Flow or batch Apex that sets the value from `LastActivityDate`. Request a custom index on this field. This converts the non-indexable formula into an indexable stored field.

```soql
SELECT Id, Name, OwnerId, StageName, Amount
FROM Opportunity
WHERE Days_Without_Activity__c > 30
AND IsClosed = false
```

Query Plan after custom index: cost < 1.0.

**Why it works:** Stored fields have deterministic values and can receive custom indexes. The formula field approach trades real-time computation for a nightly refresh cycle — acceptable for most reporting use cases where overnight freshness is sufficient.

---

## Anti-Pattern: Adding LIMIT to a Non-Selective Query to Fix Timeouts

**What practitioners do:** When a query times out on a large object, developers add `LIMIT 200` hoping it will prevent the timeout.

```soql
SELECT Id, Status__c FROM Case WHERE Custom_Category__c = 'Urgent' LIMIT 200
```

**What goes wrong:** LIMIT does not change the query optimizer's access strategy. If `Custom_Category__c` is non-indexed, Salesforce still performs a full-table scan to find any records matching the filter — it just stops returning results after 200. On a 5M-record object, the scan still touches millions of rows before it can return the first 200 qualifying records. The timeout occurs during the scan phase, before LIMIT is applied.

**Correct approach:** Make the query selective first (index the filter field, or restructure to use an indexed field). Then LIMIT is useful for pagination, not for performance rescue.

---

## Anti-Pattern: OR Across Non-Indexed Custom Fields

**What practitioners do:** Building a single flexible query that covers multiple filter paths using OR.

```soql
SELECT Id, Name FROM Contact
WHERE Lead_Source_Detail__c = 'Webinar'
OR Campaign_Origin__c = 'Q1-2025'
```

**What goes wrong:** Neither `Lead_Source_Detail__c` nor `Campaign_Origin__c` has a custom index. For OR conditions, all branches must be indexed for any index to be used. Since neither field is indexed, the optimizer performs a full-table scan of the entire Contact object.

**Correct approach:** Either request custom indexes on both fields (and verify each is selective), or decompose into two separate queries and merge results in Apex using a `Map<Id, Contact>` to deduplicate.
