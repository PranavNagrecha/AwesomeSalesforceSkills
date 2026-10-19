# Examples — SOQL Query Optimization

## Example 1: Fixing a Non-Selective Query on a 2M-Row Custom Object

**Context:** `Loan_Application__c` holds 2.1 million rows (live plus Recycle Bin). A nightly batch `start` method runs:

```soql
SELECT Id, Applicant_Name__c, Status__c, Loan_Amount__c
FROM Loan_Application__c
WHERE Status__c = 'Pending Review'
AND Assigned_Officer__c = null
```

The job started timing out after the object passed 1.5 million rows.

**Diagnosis:**

1. `GET /services/data/v67.0/query/?explain=<the query>` returns one plan, `leadingOperationType: TableScan`, `relativeCost` above 1.0, with a note that `Status__c` is unindexed.
2. `SELECT Status__c, COUNT(Id) FROM Loan_Application__c GROUP BY ROLLUP(Status__c)` shows 'Pending Review' = 98,000 rows.
3. Custom-index threshold for 2.1M rows: 10% of 1,000,000 + 5% of 1,100,000 = 100,000 + 55,000 = 155,000. 98,000 is under it.
4. `Assigned_Officer__c = null` cannot drive the query: index tables leave out null rows by default.

**Solution:**

- Ask Customer Support for a custom index on `Status__c`, attaching the GROUP BY output and the arithmetic above.
- Replace the null test with a positive value the batch can index on: a `Queue_State__c` picklist set to `Unassigned` by the assignment automation (the LDV guide's "use values such as NA" advice).

```soql
SELECT Id, Applicant_Name__c, Status__c, Loan_Amount__c
FROM Loan_Application__c
WHERE Status__c = 'Pending Review'
AND Queue_State__c = 'Unassigned'
```

- After the index exists, capture the plan again: `leadingOperationType: Index` on `Status__c`, `relativeCost` under 1.0.

**Why it works:** One filter is now indexed and under its threshold, so it can drive the query; the second filter no longer depends on null rows that the index does not hold.

---

## Example 2: Report Timeout Caused by a Formula Filter

**Context:** An Opportunity report (3.8M rows) filters on `Days_Since_Last_Activity__c`, a formula `TODAY() - LastActivityDate`. It times out for managers.

**Problem:** The formula uses TODAY, so it is non-deterministic and cannot be indexed. Filtering on it always scans.

**Solution A — filter on the source field:**

```soql
SELECT Id, Name, OwnerId, StageName, Amount
FROM Opportunity
WHERE OwnerId IN :teamIds
AND LastActivityDate < LAST_N_DAYS:30
```

`OwnerId` is indexed by default; scoping by owner gives the optimizer a selective, indexed driver. Check the plan, because `LastActivityDate` is not in the default index list.

**Solution B — store the value:** A scheduled job writes `Last_Activity_Bucket__c` (a Text field, which can be an External ID or receive a custom index) each night. The report filters on the stored bucket. Freshness drops to nightly, which is usually acceptable for this report.

---

## Example 3: Capturing the Plan in CI Before Code Merges

**Context:** A team wants every selector query that runs from trigger code checked before merge.

```bash
# One query per line in selectors.txt; fail the build when any plan is not selective.
while IFS= read -r q; do
  enc=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote_plus(sys.argv[1]))' "$q")
  curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$INSTANCE_URL/services/data/v67.0/query/?explain=$enc" \
  | python3 -c 'import json,sys; p=json.load(sys.stdin)["plans"][0]; print(p["leadingOperationType"], p["relativeCost"]); sys.exit(1 if p["relativeCost"] > 1.0 else 0)' \
  || { echo "NOT SELECTIVE: $q"; exit 1; }
done < selectors.txt
```

**Why it works:** The `explain` resource returns plans sorted most to least optimal, so `plans[0]` is the plan that runs, and `relativeCost` above 1.0 means the query is not selective. Run it against a Full sandbox or production so row counts are realistic. The resource is Beta.

---

## Anti-Pattern: Adding LIMIT to a Non-Selective Query to Fix Timeouts

**What practitioners do:** Add `LIMIT 200` to a timing-out query.

```soql
SELECT Id, Status__c FROM Case WHERE Custom_Category__c = 'Urgent' LIMIT 200
```

**What goes wrong:** The filter is still unindexed, so the optimizer still has to find matching rows without an index. LIMIT changes how many rows come back, not how they are found.

**Correct approach:** Make the filter selective and indexed first. The documented exception is a Last_N_Days query with ORDER BY on an indexed field and a LIMIT under 100,000 (Gotcha 3).

---

## Anti-Pattern: OR Across Non-Indexed Custom Fields

```soql
SELECT Id, Name FROM Contact
WHERE Lead_Source_Detail__c = 'Webinar'
OR Campaign_Origin__c = 'Q1-2025'
```

**What goes wrong:** All fields in an OR must be indexed for any index to be used. Neither is, so the query scans Contact.

**Correct approach:** Index both and confirm each is under its threshold, or split into two queries and merge them in a `Map<Id, Contact>`.
