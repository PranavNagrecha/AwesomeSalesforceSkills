# LLM Anti-Patterns — Salesforce Connect External Objects

Common mistakes AI coding assistants make when generating or advising on Salesforce Connect and External Objects.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating External Objects Like Standard Objects in SOQL

**What the LLM generates:** SOQL queries against External Objects using features not supported: `SELECT COUNT(Id) FROM External_Object__x GROUP BY Field__c`, aggregate functions, or complex WHERE clauses that External Objects cannot process.

**Why it happens:** LLMs apply standard SOQL patterns to External Objects without recognizing the significant query limitations imposed by the OData or custom adapter backend.

**Correct pattern:**

```text
External Object (__x) SOQL limitations:
- No aggregate functions (COUNT, SUM, AVG, MIN, MAX)
- No GROUP BY or HAVING
- No SOQL subqueries
- Limited WHERE clause operators (depends on adapter capabilities)
- No ORDER BY on non-indexed external fields (adapter-dependent)
- JOIN queries limited to indirect lookups
- SOQL for-update (FOR UPDATE) not supported
- Relationship queries limited in depth

Supported patterns:
  SELECT ExternalId, Name__c, Status__c FROM External_Object__x
  WHERE Status__c = 'Active' LIMIT 100

For complex queries: query the external system directly via callout,
not through the External Object SOQL interface.
```

**Detection hint:** Flag SOQL against `__x` objects using COUNT, SUM, GROUP BY, subqueries, or FOR UPDATE. These are not supported on External Objects.

---

## Anti-Pattern 2: Recommending External Objects for High-Frequency Queries

**What the LLM generates:** "Use Salesforce Connect to show real-time inventory data on every Account page view" without noting that every External Object query makes a real-time callout to the external system, adding latency and consuming external API resources.

**Why it happens:** LLMs present External Objects as transparent data access without highlighting the per-query callout overhead. Every SOQL query against an External Object triggers a synchronous HTTP callout to the external system.

**Correct pattern:**

```text
External Object performance characteristics:
- Every query = real-time HTTP callout to external system
- Latency: depends entirely on external system response time (typically 200ms-2s)
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

## Anti-Pattern 3: Ignoring the Indirect Lookup Requirement for Relationships

**What the LLM generates:** "Create a lookup from Contact to the External Object using the standard lookup field type" when External Objects require indirect lookups (matching an External ID on the Salesforce object to a field on the External Object) instead of standard ID-based lookups.

**Why it happens:** Standard lookups use Salesforce record IDs (18-character). External Objects do not have Salesforce IDs — they have external IDs from the source system. LLMs apply standard relationship patterns without accounting for this difference.

**Correct pattern:**

```text
External Object relationship types:

1. Indirect Lookup (Salesforce object -> External Object):
   - Salesforce parent object must have an External ID field (unique)
   - External Object must have a field containing matching values
   - Relationship is based on value matching, not Salesforce ID

2. External Lookup (External Object -> Salesforce object):
   - External Object field contains the Salesforce record's External ID
   - Points from external data to internal Salesforce records

3. Cross-org External Lookup:
   - External Object in one org -> standard object in another org
   - Uses the Cross-Org adapter

Standard lookup (Id-based): NOT supported for External Objects
Master-detail: NOT supported for External Objects
```

**Detection hint:** Flag standard lookup or master-detail relationship recommendations between Salesforce objects and External Objects. Check for missing indirect lookup configuration.

---

## Anti-Pattern 4: Not Evaluating Salesforce Connect Licensing Costs

**What the LLM generates:** "Use Salesforce Connect with the OData adapter to virtualize your database" without mentioning that Salesforce Connect requires a separate license and specifying which adapter type is needed.

**Why it happens:** Licensing details are frequently omitted from training data. LLMs recommend features without cost context.

**Correct pattern:**

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

**Correct pattern:**

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
