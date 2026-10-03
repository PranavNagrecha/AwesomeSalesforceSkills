# LLM Anti-Patterns — Data Cloud vs CRM Analytics Decision

Common mistakes AI coding assistants make when advising on Data Cloud versus CRM Analytics platform boundaries. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Declaring the two products “the same category”

**What the LLM generates:** “Both are Salesforce analytics products; pick whichever is cheaper this quarter.”

**Why it happens:** Training data bundles all “Einstein” and “Tableau CRM” naming with BI keywords and underweights the customer data platform responsibilities that Data Cloud carries in current positioning.

**Correct pattern:**

```
Data Cloud is the harmonization, identity, and activation layer in a Data 360 architecture. CRM Analytics is the analytics and visualization layer that can consume CRM data and, when applicable, Data Cloud entities through supported connectivity—treat them as complementary unless requirements are CRM-only.
```

**Detection hint:** Response lacks the words harmonize, DMO, identity, activation, or dataset in a structured comparison.

---

## Anti-Pattern 2: “CRM Analytics can ingest anything Data Cloud can”

**What the LLM generates:** Step-by-step instructions to replicate every external connector inside CRM Analytics recipes so Data Cloud is unnecessary.

**Why it happens:** Assistants generalize from ETL-like features in analytics tools without checking that identity rulesets, activation targets, and lakehouse-scale ingestion are separate platform concerns.

**Correct pattern:**

```
If requirements include governed cross-source profiles, identity resolution, or segment activation, Data Cloud remains the owning platform. CRM Analytics may visualize harmonized outputs but does not replace those platform services.
```

**Detection hint:** Proposed architecture has zero mention of identity resolution rulesets or activation targets while claiming full parity with Data Cloud.

---

## Anti-Pattern 3: Skipping the DMO layer in Direct Data discussions

**What the LLM generates:** “Connect CRM Analytics directly to Data Cloud streams for live dashboards.”

**Why it happens:** Colloquial use of “Data Cloud data” ignores that supported analytics paths are documented around harmonized Data Model Objects and product-specific connectors—not arbitrary stream tables.

**Correct pattern:**

```
Anchor the design in Data Model Objects (DMOs) and the official CRM Analytics ↔ Data Cloud Direct Data guidance; document which subject areas and DMOs are in scope before promising datasets.
```

**Detection hint:** Text references “streams” or “lake” interchangeably with what analysts query, without naming DMOs or citing Direct Data documentation.

---

## Anti-Pattern 4: Recommending Data Cloud for CRM-only bar charts

**What the LLM generates:** “Enable Data Cloud for every org so all reports are faster.”

**Why it happens:** Overselling the flagship SKU without requirements triage.

**Correct pattern:**

```
When all metrics are native CRM objects, no activation is needed, and no external behavioral feeds exist, CRM Analytics on CRM data is typically sufficient. Introduce Data Cloud when multi-source harmonization, identity, or activation enters the roadmap.
```

**Detection hint:** Recommendation includes Data Cloud without listing a non-CRM source, activation channel, or identity use case.

---

## Anti-Pattern 5: Licensing word salad

**What the LLM generates:** “Buy Einstein and you get both.”

**Why it happens:** Marketing names change across releases; bundles differ by edition.

**Correct pattern:**

```
Call out that licensing and permission models are product-specific: verify current Salesforce SKU mapping for Data Cloud entitlements versus CRM Analytics Permission Set Licenses with your account team—never infer entitlements from names alone.
```

**Detection hint:** Absolute statements about bundles with no caveat to verify org-specific entitlements.

---

## Anti-Pattern 6: Pricing Data 360 like a per-seat analytics licence

**What the LLM generates:** A cost comparison that multiplies analyst seats for CRM Analytics and does the same for Data Cloud, then picks the cheaper column.

**Why it happens:** Most analytics products in training data are licensed per user. Data 360 documents usage as credit consumption shown in a digital wallet, so volume and processing frequency drive cost.

**Correct pattern:** Price CRM Analytics by its licences and Data 360 by expected consumption from a measured proof of concept. Record a consumption owner and a review cadence in the decision record. Mark any credit rate you did not read from the contract as unverified.

**Detection hint:** A cost table with a "per user" row for Data Cloud and no consumption line.

---

## Anti-Pattern 7: Designing SOQL dashboards over calculated insights

**What the LLM generates:** A Lightning component or report plan that runs `SELECT ... FROM` a calculated insight object, or sums a currency field across a DMO with SOQL.

**Why it happens:** DMOs look like sObjects, so the model assumes full SOQL support. The SOQL reference says calculated insight objects cannot be queried with SOQL, aggregate queries over Data 360 objects do not support currency fields, and results are capped at 12 MB.

**Correct pattern:** Query calculated insights through the Data 360 query paths (SQL, CRM Analytics, or a BI tool over the JDBC driver). Use SOQL on DMOs only for record lookups and small non-currency aggregates.

**Detection hint:** SOQL naming a calculated insight object, or `SUM()` on a currency field of a DMO.

