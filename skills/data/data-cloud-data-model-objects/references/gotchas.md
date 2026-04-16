# Gotchas — Data Cloud Data Model Objects

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: DMOs Do Not Support SOQL

DMOs are columnar store objects in the Data Cloud data lake, not Salesforce CRM objects. SOQL queries against DMO API names either fail with an error or return empty results. All DMO data access requires the Data Cloud Query API using ANSI SQL syntax. This surprises practitioners who assume that because DMOs appear in Data Cloud Setup alongside familiar Salesforce concepts, they work like standard objects.

**Fix:** Use `POST /services/data/v{version}/ssot/queryapis/queryjobs` with ANSI SQL to query DMO data. Never use SOQL for DMO queries.

---

## Gotcha 2: System XMD Is Immutable — PATCH Returns 403

The XMD (extended metadata) layer has three types: System (auto-generated, immutable), Main (org-customizable), and User (per-user preference). Attempting to PATCH the System XMD via the REST API returns HTTP 403. Many practitioners mistakenly target the System XMD because they retrieve it for reference and then attempt to update it.

**Fix:** Always target Main XMD for updates: `PATCH /services/data/v{version}/wave/datasets/{id}/xmds/main`. Retrieve System XMD only for reference; never attempt to modify it.

---

## Gotcha 3: Only One Data Relationship Per Field Pair Between DMOs

Data Cloud enforces a limit of one data relationship per field pair between two mapped DMOs. You cannot create two separate relationships between the same pair of fields on the same two DMOs. If a more complex mapping is needed, it must use a different field pairing or be modeled through a transform that produces an intermediate DMO.

**Fix:** Document all planned DMO relationships before implementation. If two entities need multiple relationship types, model them as separate DMOs or use a transform to produce the join result as a new DMO.

---

## Gotcha 4: Streaming Transforms Cannot Join Multiple DLOs

Streaming transforms in Data Cloud execute near-real-time on incoming DLO records. However, they are restricted to a single source DLO — they cannot perform joins across multiple DLOs. This means complex enrichments that require data from two or more sources (e.g., joining a purchase event DLO with a product catalog DLO) cannot be done in a streaming transform. They must be batch transforms.

**Fix:** Use batch transforms (scheduled interval) for any enrichment that requires joining two or more DLOs. Use streaming transforms only for single-DLO enrichments where near-real-time processing is needed.

---

## Gotcha 5: Omitting Identity-Relevant Fields from Mandatory DMO Mapping Silently Disables Identity Resolution

If a data stream is ingested but the identity-relevant fields (email, phone, external ID) are not mapped to the five mandatory DMOs, identity resolution simply has no data to match against. The ingestion succeeds, the DLO receives records, and no error is raised — but the data is invisible to identity resolution. The result is a unified profile count of zero for data from that source, with no diagnostic error message explaining why.

**Fix:** As part of data stream configuration, always verify that identity-relevant fields are mapped to Individual, Party Identification, Contact Point Email, Contact Point Phone, or Contact Point Address DMOs before running identity resolution.
