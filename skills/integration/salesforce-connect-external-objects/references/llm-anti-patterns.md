# LLM Anti-Patterns — Salesforce Connect External Objects

Common mistakes AI coding assistants make when generating or advising on Salesforce Connect and External Objects.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating External Objects Like Standard Objects in SOQL

**What the LLM generates:** SOQL queries against External Objects using features not supported: `SELECT COUNT(Id) FROM External_Object__x GROUP BY Field__c`, aggregate functions, or complex WHERE clauses that External Objects cannot process.

**Why it happens:** LLMs apply standard SOQL patterns to External Objects without recognizing the significant query limitations imposed by the OData or custom adapter backend.

**Correct pattern:**

```text
External Object (__x) SOQL limitations (SOQL and SOSL Reference v67.0):
- Not supported: AVG, SUM, MIN, MAX, COUNT(fieldName), GROUP BY, HAVING
- COUNT() is supported; OData adapters need Request Row Counts enabled
- Not supported: LIKE, INCLUDES, EXCLUDES, toLabel(), TYPEOF, FOR VIEW,
  FOR REFERENCE, WITH
- Subqueries ARE supported, but a subquery involving external objects
  returns at most 1,000 rows
- Up to 4 joins per query; each join is a separate round trip
- OData adapters: no ORDER BY in relationship queries; NULLS FIRST/LAST ignored

Supported patterns:
  SELECT ExternalId, Name__c, Status__c FROM External_Object__x
  WHERE Status__c = 'Active' LIMIT 100

For complex aggregation: aggregate in the external system and expose the
result, or replicate the needed subset into Salesforce.
```

An earlier version of this entry said subqueries and all aggregate functions are unsupported and that joins are limited to indirect lookups. The SOQL Reference contradicts all three.

**Detection hint:** Flag SOQL against `__x` objects using SUM, AVG, MIN, MAX, COUNT(field), GROUP BY, HAVING, LIKE, or WITH.

---

## Anti-Pattern 2: Recommending External Objects for High-Frequency Queries

**What the LLM generates:** "Use Salesforce Connect to show real-time inventory data on every Account page view" without noting that every External Object query makes a real-time callout to the external system, adding latency and consuming external API resources.

**Why it happens:** LLMs present External Objects as transparent data access without highlighting the per-query callout overhead. Every SOQL query against an External Object triggers a synchronous HTTP callout to the external system.

**Correct pattern:**

```text
External Object performance characteristics:
- Every query = real-time HTTP callout to external system
- Latency: depends entirely on external system response time (UNVERIFIED 2026-10-03: the 200ms-2s range is an estimate, not a documented figure)
- No caching by default (every page load triggers a new callout)
- External system must handle the query load from all Salesforce users
- Connection failures cause errors on the Salesforce page

Use External Objects when:
- Data must remain in the external system (cannot be replicated)
- Access is infrequent (not on every page load for all users)
- Latency of 1-3 seconds is acceptable
- External system can handle the query throughput

Consider alternatives for high-frequency access:
- Replicate data into Salesforce using ETL/middleware (MuleSoft, Informatica)
- Use Platform Cache to cache frequently accessed external data
- Use Heroku Connect for near-real-time bidirectional sync
```

**Detection hint:** Flag External Object recommendations for page layouts, list views, or reports that all users access frequently. Check for missing latency and throughput assessment.

---

## Anti-Pattern 3: Getting the external object relationship type or direction wrong

**What the LLM generates:** "Create a lookup from Contact to the External Object using the standard lookup field type", or an external lookup on the external object that points at a Salesforce parent.

**Why it happens:** Standard lookups use Salesforce record IDs. External rows are identified by the External ID values from the source system, and the two special lookup types differ by which side is the parent. Models apply standard relationship patterns or mix up the direction.

**Correct pattern:**

```text
External Object relationship types (Apex Developer Guide v67.0):

1. Indirect lookup: child EXTERNAL object -> parent standard or custom object
   - Matches the child's field values against a parent field named in
     referenceTargetField
   - That parent field must have externalId = true and unique = true

2. External lookup: child standard, custom, or external object -> parent
   EXTERNAL object
   - Matches on the parent external object's External ID standard field
   - Child records store and display the parent's External ID values

3. Cross-org: external objects backed by another Salesforce org (SfdcOrg adapter)
```

An earlier version of this entry reversed the direction of indirect and external lookups. UNVERIFIED (2026-10-03): it also said standard Id-based lookups and master-detail relationships are not supported for external objects; the fetched guides do not state either way.

**Detection hint:** Flag standard lookup or master-detail relationship recommendations between Salesforce objects and External Objects. Check for missing indirect lookup configuration.

---

## Anti-Pattern 4: Not Evaluating Salesforce Connect Licensing Costs

**What the LLM generates:** "Use Salesforce Connect with the OData adapter to virtualize your database" without mentioning that Salesforce Connect requires a separate license and specifying which adapter type is needed.

**Why it happens:** Licensing details are frequently omitted from training data. LLMs recommend features without cost context.

**Correct pattern:** UNVERIFIED (2026-10-03): the license names below are not in any fetched Salesforce guide; confirm with the account team before quoting them.

```text
Salesforce Connect licensing:

OData 2.0 / OData 4.0 adapter:
- Requires Salesforce Connect OData license
- Per-user or per-org pricing (check current Salesforce pricing)
- Included with some Salesforce editions (verify with account executive)

Cross-Org adapter:
- Requires Salesforce Connect Cross-Org license
- Connects two Salesforce orgs via External Objects

Custom Adapter (Apex-based):
- Requires Salesforce Connect Custom Adapter license
- Uses Apex DataSource classes to connect to any external system
- Most flexible but most development effort

Before recommending Salesforce Connect:
1. Verify the license is available or budgeted
2. Evaluate whether Heroku Connect or ETL replication is more cost-effective
3. Consider the total cost: license + development + external system hosting
```

**Detection hint:** Flag Salesforce Connect recommendations that do not mention licensing requirements. Check for missing cost comparison with alternative approaches.

---

## Anti-Pattern 5: Expecting Full Reporting Support on External Objects

**What the LLM generates:** "Create reports and dashboards on External Object data" without noting that External Objects have significant reporting limitations compared to standard objects.

**Why it happens:** LLMs treat External Objects as equivalent to custom objects for reporting purposes. The limitations are Salesforce-specific and not well-represented in training data.

**Correct pattern:** UNVERIFIED (2026-10-03): the reporting limits below come from an earlier version of this skill and are not in the fetched guides; test each one in a sandbox.

```text
External Object reporting limitations:

NOT supported:
- Cross-object report types with External Objects
- Dashboard components based on External Object reports
- Report formulas referencing External Object fields
- Bucket fields on External Object columns
- Reporting snapshots (Analytic Snapshots)
- Joined reports with External Object data

LIMITED support:
- Standard tabular and summary reports on a single External Object
- Basic filters on External Object fields
- Row-level detail (each row triggers a callout)

Alternatives for External Object reporting:
1. Replicate data to a Salesforce custom object for full reporting
2. Use CRM Analytics (Tableau) with a direct connection to the external source
3. Use Heroku Connect to replicate and report on Salesforce-native data
```

**Detection hint:** Flag reporting or dashboard recommendations that include External Object data without noting limitations. Check for cross-object report types involving `__x` objects.

---

## Anti-Pattern 6: Using plain DML on external objects in Apex

**What the LLM generates:**

```apex
SalesOrder__x order = new SalesOrder__x(Status__c = 'Submitted');
insert order;
```

**Why it happens:** External objects look like sObjects, so the model writes ordinary DML.

**Correct pattern:** The Apex Developer Guide says Apex "can't execute standard insert(), update(), or create() operations on external objects". Use the asynchronous methods and keep the locator, or `insertImmediate` in portal-user context:

```apex
SalesOrder__x order = new SalesOrder__x(Status__c = 'Submitted');
Database.SaveResult sr = Database.insertAsync(order);
String locator = Database.getAsyncLocator(sr);
```

**Detection hint:** `insert`, `update`, `upsert`, or `delete` statements whose target variable is an `__x` type.

---

## Anti-Pattern 7: Proposing a trigger on an external object

**What the LLM generates:** `trigger OrderSync on SalesOrder__x (after update) { ... }`.

**Why it happens:** Triggers are the default reaction pattern for record changes.

**Correct pattern:** Apex triggers are not available for external objects. For OData 4.0 connections, write the trigger on the change event object (for example `Products__ChangeEvent`); otherwise react in the source system or middleware.

**Detection hint:** `trigger <name> on <Object>__x`.

