# LLM Anti-Patterns — Data Cloud Data Streams

Common mistakes AI coding assistants make when generating or advising on Data Cloud Data Streams.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Mapping Only to Individual DMO and Declaring the Stream Ready for Identity Resolution

**What the LLM generates:** The assistant walks through creating a data stream, maps the source fields to the Individual DMO (`Individual ID`, `First Name`, `Last Name`), and then says "the data stream is now ready for identity resolution." It does not mention Contact Point DMO or Party Identification DMO mappings.

**Why it happens:** Training data likely contains many partial examples that focus on the Individual DMO as the central object. The Contact Point DMO mapping requirement is a platform-specific constraint that is easy to omit when generalizing the workflow. LLMs tend to stop once a "person record" is mapped, assuming that is sufficient.

**Correct pattern:**

```
Required mappings per data stream for identity resolution:
1. Individual DMO:
   - Source primary key → Individual ID (primary key)
   - First name field   → First Name
   - Last name field    → Last Name

2. Contact Point Email DMO (or Phone/Address/App, or Party Identification DMO):
   - Email field        → Email Address
   - Source primary key → Individual ID (foreign key, links to Individual DMO)

Both mappings must be present before an identity resolution ruleset can be created.
```

**Detection hint:** Search the generated response for "identity resolution" — if it appears without a corresponding mention of "Contact Point" or "Party Identification", the response is likely incomplete.

---

## Anti-Pattern 2: Instructing the Use of Ingestion API for Record Deletion

**What the LLM generates:** The assistant describes a bidirectional sync integration where creates, updates, and deletes from the source system are all sent to the Data Cloud Ingestion API. It shows a delete payload structure, often resembling: `{"data": [{"id": "123"}], "mode": "delete"}`.

**Why it happens:** Many LLMs generalize from CRUD APIs (REST, SOAP, Bulk API) where delete operations are supported. The Ingestion API's append/upsert-only constraint is a Data Cloud-specific limitation that runs counter to the general pattern. LLMs trained on broad API documentation will assume delete is always available.

**Correct pattern:**

```
Ingestion API supported operations:
  - mode: "append"   → inserts new records, no deduplication
  - mode: "upsert"   → insert or update based on primary key

Ingestion API does NOT support:
  - mode: "delete"   → not supported; will return an error

For record deletions, use:
  - Data Cloud bulk delete facility (admin UI or Bulk Delete API)
  - Route deletions through the standard pipeline, not the Ingestion API
```

**Detection hint:** Search the generated payload or integration code for the string `"delete"` in an Ingestion API context. Any occurrence is incorrect.

---

## Anti-Pattern 3: Mapping the External ID to the Party Identification ID Field

**What the LLM generates:** When explaining how to ingest loyalty IDs or ERP customer numbers via the Party Identification DMO, the assistant maps the external ID value to the `Party Identification ID` field: `loyalty_id → Party Identification ID`.

**Why it happens:** The field name `Party Identification ID` sounds like "the ID that identifies the party" — i.e., the external identifier. In reality, it is the DMO's internal system-generated primary key, not a field for external values. The actual field for external identifiers is `Identification Number`. LLMs frequently conflate these without knowing the platform-specific distinction.

**Correct pattern:**

```
Party Identification DMO field mapping:
  External ID value (e.g., loyalty_id)   → Identification Number
  ID type label (e.g., "Loyalty ID")     → Identification Type
  Source person primary key              → Individual ID (foreign key)

DO NOT map external IDs to:
  Party Identification ID  ← this is a system-generated key, not an external ID field
```

**Detection hint:** Search for `Party Identification ID` in the mapping table. If an external source field is mapped to it, the mapping is incorrect.

---

## Anti-Pattern 4: Presenting Calculated Insights as Real-Time Metrics

**What the LLM generates:** The assistant describes a use case where a segment fires immediately after a customer makes a purchase (e.g., "customers who made a purchase in the last 5 minutes") and recommends building a Calculated Insight to compute this metric, implying the insight will update in near-real-time.

**Why it happens:** The name "Calculated Insights" sounds dynamic and computational. LLMs do not always distinguish between batch-processed analytics and real-time stream processing. They may conflate Calculated Insights with Streaming Insights or assume that all Data Cloud metrics update continuously.

**Correct pattern:**

```
Calculated Insights:
  - SQL-defined batch metrics
  - Run on a configured schedule (e.g., daily, every 12 hours)
  - NOT updated incrementally as records flow in
  - Suitable for: RFM scoring, LTV calculations, aggregated purchase history

Streaming Insights:
  - Near-real-time processing of Web SDK / Mobile SDK events
  - Suitable for: behavioral signals, in-session activity, real-time triggers
  - Cannot be created from batch DLO data

For use cases requiring sub-hour freshness, use Streaming Insights — not Calculated Insights.
```

**Detection hint:** If the response recommends a Calculated Insight for a use case described as "real-time", "immediate", or "within minutes", flag it for review.

---

## Anti-Pattern 5: Assuming More Than 2 Identity Resolution Rulesets Can Be Created Per Org

**What the LLM generates:** The assistant designs a multi-BU Data Cloud implementation where each of three business units has its own identity resolution ruleset (e.g., "BU1 Ruleset", "BU2 Ruleset", "BU3 Ruleset") and presents this as a valid architecture.

**Why it happens:** LLMs trained on general multi-tenancy and multi-BU patterns assume that configuration objects can be created in multiples. The 2-ruleset-per-org limit is a specific and non-obvious Data Cloud platform constraint. Without explicit training data on this limit, the LLM will recommend as many rulesets as logically seem needed.

**Correct pattern:**

```
Identity Resolution Ruleset limit: 2 per org (hard platform limit)

Design rulesets to cover all required business units and data sources within this limit:
  - Option A: One ruleset covering all sources with multiple match rules (email + phone)
  - Option B: Two rulesets with different primary match keys if BU populations are disjoint

Multi-BU implementations must be designed at the org level.
Individual BU teams should not independently create rulesets without org-level coordination.
```

**Detection hint:** Count the number of rulesets proposed in the architecture. If the count exceeds 2, the design is invalid for a single Data Cloud org.

---

## Anti-Pattern 6: Referencing DMO Relationships for Identity-Resolved Data in SOQL

**What the LLM generates:** The assistant writes a SOQL query that attempts to join a standard CRM object (e.g., Contact) to a Data Cloud DMO using a relationship field, expecting to traverse an identity-resolved relationship from SOQL.

**Why it happens:** Data Cloud DMOs appear in the Salesforce platform schema to some extent, and LLMs may assume standard SOQL JOIN semantics apply. In reality, identity resolution-based relationships between CRM objects and DMOs are not supported in SOQL. Only direct DMO relationships are available via SOQL, and these are limited.

**Correct pattern:**

```
SOQL limitation:
  - Direct DMO-to-CRM-object relationships via SOQL: limited support
  - Identity resolution-based relationships (Unified Individual → source Contact): NOT supported in SOQL

Alternatives:
  - Use Data Cloud query API (SELECT from DMOs using Data Cloud SQL)
  - Use Data Cloud Segments with activation to push unified profile data back to CRM
  - Use Data Cloud Einstein Studio or Tableau CRM for cross-DMO analytics
```

**Detection hint:** Any SOQL query that references a DMO object or attempts to traverse a "unified" relationship is suspect. Cross-check against Data Cloud query API documentation.
