# Gotchas — High Volume Sales Data Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Sharing Recalculation Cost Is Non-Linear with Skewed Ownership

**What happens:** When a sharing rule is added or modified, the platform recalculates visibility for every record owned by affected users. If one user owns 100K records, that single user's set dominates the entire recalculation job duration, blocking other sharing operations.

**When it occurs:** Any time a sharing rule is created, edited, or deleted, or when a role hierarchy change affects users who own large record sets. Also triggered by territory realignment operations.

**How to avoid:** Keep per-user ownership below 10,000 records on Account and Opportunity. Monitor ownership distribution quarterly. Use queues for integration-created records rather than assigning to a single service account.

---

## Gotcha 2: Report Detail Row Limit Silently Truncates Pipeline Data

**What happens:** Salesforce reports cap at 2,000 detail rows in the browser. A pipeline report that matches 50,000 Opportunities returns only the first 2,000 rows in detail view. Summary rows may aggregate more, but dashboard snapshots based on filtered reports inherit the truncation silently -- no error, no warning.

**When it occurs:** When sales managers build "all open pipeline" reports without selective date or stage filters on high-volume Opportunity tables. The report appears to work but understates pipeline by the truncated amount.

**How to avoid:** Always include selective filters on indexed fields (CloseDate range, StageName) that keep expected result sets well under 2,000 detail rows. For executive dashboards, use analytic snapshots or CRM Analytics datasets that pre-aggregate the full record set.

---

## Gotcha 3: Custom Indexes Can Be Dropped Without Notification

**What happens:** Custom indexes requested through Salesforce Support are metadata additions that are not version-controlled in the org's metadata API. During major version upgrades, org splits, or sandbox refreshes, custom indexes may not carry over. The org continues to function but queries that depended on the index become non-selective.

**When it occurs:** After sandbox refresh from production (sandboxes do not always inherit custom indexes), after org migrations, or after Salesforce infrastructure changes during major releases.

**How to avoid:** Maintain a register of all custom indexes and skinny tables with the fields, objects, and Support case numbers. After every sandbox refresh, verify indexes using the Query Plan tool in Developer Console. Include index verification in the post-refresh runbook.

---

## Gotcha 4: Big Object Async SOQL Returns Results to a Target Object, Not Inline

**What happens:** Developers write SOQL against a Big Object expecting synchronous results like standard SOQL. Async SOQL instead requires specifying a target sObject where results are written, and the query executes in the background. There is no way to query a Big Object and get inline results in Apex at runtime.

**When it occurs:** When architects design Lightning page components or triggers that need to read archived data from Big Objects in real time. The page load expects data that will not arrive for minutes.

**How to avoid:** For any UI or synchronous use case, maintain a lightweight summary custom object populated during the archival ETL. Reserve Big Object reads for batch analytics, compliance audits, and scheduled reporting.

---

## Gotcha 5: Skinny Tables Exclude Formula and Encrypted Fields

**What happens:** A skinny table is requested for a wide Opportunity object to speed up reports. The report includes formula fields like `Expected_Revenue__c` (Amount * Probability). The skinny table cannot include formula fields, roll-up summaries, or fields using Shield Platform Encryption. The report either does not benefit from the skinny table for those columns or falls back to the full table.

**When it occurs:** When the most frequently filtered or displayed columns in slow reports are formula-based. Common in sales orgs where pipeline value, weighted amount, and days-in-stage are all formula fields.

**How to avoid:** Before requesting a skinny table, audit which report columns are formulas. Consider replacing critical formula fields with workflow-updated or Flow-updated regular fields that store the calculated value. This makes them eligible for skinny table inclusion and indexing.
