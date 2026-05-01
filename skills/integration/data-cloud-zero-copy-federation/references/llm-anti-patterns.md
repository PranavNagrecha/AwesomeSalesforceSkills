# LLM Anti-Patterns — Data Cloud Zero Copy Federation

Common mistakes AI coding assistants make when generating or advising on Data Cloud Zero Copy Federation. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending federation as a no-cost replacement for ingestion

**What the LLM generates:** Advice such as "use federation — it's zero copy so there's no cost or storage impact." The recommendation skips any mention of source-warehouse compute billing or derived-storage growth.

**Why it happens:** The "zero copy" name implies "zero cost" by association. LLMs latch onto the marketing phrase and miss the per-query cost on the source warehouse.

**Correct pattern:**

```
Federation removes Data Cloud raw-storage cost but bills source-warehouse
compute on every query. For frequently-queried hot subsets, layer a
query-acceleration cache. Model source-side cost ceilings (Snowflake
credits, BigQuery on-demand bytes) before recommending federation.
```

**Detection hint:** Search the response for "no cost", "free", "zero cost", or "no storage" near "federation" / "zero copy". If those phrases appear without a paired source-cost caveat, the answer is wrong.

---

## Anti-Pattern 2: Mapping a federated DLO to the Individual DMO without materializing identity-resolution keys

**What the LLM generates:** Configuration steps that federate a customer table from Snowflake / BigQuery, map it to `Individual`, and proceed straight to identity-resolution rule definition without any mention of acceleration caches or key materialization.

**Why it happens:** The mental model "DLO → DMO → IR" is symmetrical for ingested and federated objects in the docs. The LLM treats them as interchangeable. The performance and correctness implications of running IR over a federated source are not explicit in most public docs.

**Correct pattern:**

```
For federated DLOs that participate in identity resolution:
  1. Enable a query-acceleration cache on the DLO.
  2. Materialize the columns IR rules will read (typically email, phone,
     normalized customer ID).
  3. Leave non-key columns federated.
  4. Run IR with a small sample first; verify cluster sizes against a
     known-duplicate test set before scaling.
```

**Detection hint:** If the response wires a federated DLO into the `Individual` DMO and configures match rules without using the words "cache", "materialize", or "accelerat*", the answer is incomplete.

---

## Anti-Pattern 3: Generating cross-connector segment SQL or rule logic

**What the LLM generates:** A segment definition that joins a Snowflake DLO with a BigQuery DLO using SQL-style JOIN syntax, with a confident "Data Cloud will optimize this" framing.

**Why it happens:** SQL-bias. The model sees two tables and produces a join. It does not know that the Data Cloud query engine cannot push joins across two source warehouses and will fall back to a slow local join.

**Correct pattern:**

```
Cross-connector joins are an architectural smell. Pick one:
  (a) Pre-join at source — author a view in Snowflake / BigQuery that
      already incorporates the other side via a cross-cloud share.
  (b) Physically ingest the smaller side so only one connector remains
      in the join path.
Both options keep pushdown intact.
```

**Detection hint:** Look for any segment / CI / activation rule that names DLOs from two different connectors in the same join. Flag for redesign.

---

## Anti-Pattern 4: Treating federation latency as Data-Cloud-internal

**What the LLM generates:** When asked "why is segment compile slow?" the model recommends Data Cloud-side optimizations (rebuild segment, reduce dimension count) without checking whether a federated DLO is in the predicate path.

**Why it happens:** The model defaults to the platform it knows (Data Cloud) and doesn't trace the query path into the source warehouse. Source-warehouse query logs are not in its context.

**Correct pattern:**

```
Slow federated-segment debugging starts on the source warehouse:
  1. Identify federated DLOs in the segment's predicate path.
  2. Pull the source-warehouse query log for the federation principal.
  3. Confirm pushdown happened (filters / projections appear in the
     source SQL).
  4. Check source-warehouse compute saturation, not Data Cloud's.
  5. Apply a query-acceleration cache to the hot path if pushdown is
     working but cost is the issue.
```

**Detection hint:** Slow-segment recommendations that do not mention "source warehouse", "pushdown", or "Snowflake / BigQuery / Databricks query log" are missing the federation-aware diagnostic path.

---

## Anti-Pattern 5: Hallucinating supported source platforms

**What the LLM generates:** Confident statements that Data Cloud federation supports Postgres, MySQL, Oracle, MongoDB, MSSQL, or arbitrary JDBC sources with the same Zero Copy semantics.

**Why it happens:** The four supported lakehouse platforms (Snowflake, Databricks, BigQuery, Redshift) are routinely confused with the broader connector ecosystem. The model pattern-matches "external warehouse" to whatever warehouses it has seen in its training set.

**Correct pattern:**

```
Lakehouse Federation / Zero Copy supports Snowflake, Databricks,
BigQuery, and Amazon Redshift today (verify in the current release
notes — additions appear over time). Other relational sources require
physical ingestion via Ingestion API, MuleSoft Direct, or a
custom connector — not federation.
```

**Detection hint:** Any list of federation source platforms that includes Postgres, MySQL, Oracle, MongoDB, or generic JDBC is wrong as of Spring '25. Reject and consult the Data Cloud connectors release notes.

---

## Anti-Pattern 6: Not surfacing source-side governance as a debugging path

**What the LLM generates:** When the user reports "segments are missing records," the model investigates Data Cloud-side filters, identity resolution, and segment criteria but does not consider source-side row-access policies.

**Why it happens:** Source-side governance is invisible from inside Data Cloud Setup. The model's diagnostic search space is bounded by the surface it can "see."

**Correct pattern:**

```
For federated-DLO data-loss symptoms, include the source-warehouse
governance layer in the diagnostic checklist:
  - Snowflake: row-access policies and dynamic data masking on the
    federation principal.
  - Databricks: Unity Catalog row filters and column masks.
  - BigQuery: authorized views and column-level IAM.
  - Redshift: row-level security policies on the federated user.
Test by logging in as the federation principal in the source console
and running the predicate directly.
```

**Detection hint:** Any "missing data" diagnostic that does not at least name the source-side governance layer is incomplete for federated DLOs.
