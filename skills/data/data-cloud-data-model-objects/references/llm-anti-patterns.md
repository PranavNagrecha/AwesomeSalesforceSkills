# LLM Anti-Patterns — Data Cloud Data Model Objects

Common mistakes AI coding assistants make when generating or advising on Data Cloud DMO design and management.

---

## Anti-Pattern 1: Using SOQL to Query DMO Objects

**What the LLM generates:** `SELECT Id, ssot__Email__c FROM ssot__Individual__dlm WHERE ssot__CreatedDate__c = TODAY` — submitted as a SOQL query in Developer Console or Apex.

**Why it happens:** LLMs associate Data Cloud object API names (ssot__ prefix, __dlm suffix) with standard Salesforce objects and assume SOQL applies. The naming convention looks similar to managed package objects that do support SOQL.

**Correct pattern:** DMOs are columnar store objects in the Data Cloud data lake. They require the Data Cloud Query API with ANSI SQL: `POST /services/data/v{version}/ssot/queryapis/queryjobs` with an ANSI SQL body. SOQL does not work against DMO objects.

**Detection hint:** If SOQL contains DMO API names (ssot__ prefix with __dlm suffix), it will fail or return empty results.

---

## Anti-Pattern 2: Attempting to Modify System XMD

**What the LLM generates:** `PATCH /services/data/{version}/wave/datasets/{id}/xmds/system` with a modified XMD JSON body to rename field labels.

**Why it happens:** LLMs may retrieve System XMD as a reference and then attempt to PATCH it, not modeling the immutability constraint.

**Correct pattern:** System XMD is platform-generated and immutable. PATCH against System XMD returns HTTP 403. Target Main XMD instead: `PATCH /services/data/v{version}/wave/datasets/{id}/xmds/main`.

**Detection hint:** Any REST call PATCHing `/xmds/system` will be rejected.

---

## Anti-Pattern 3: Treating DMO Relationships as a Foreign Key Graph Like CRM Objects

**What the LLM generates:** Entity relationship diagrams or code that creates multiple relationship types between the same two DMOs (e.g., both "primary" and "secondary" relationships from Purchase DMO to Individual DMO using the same field pair).

**Why it happens:** LLMs model relationships from the CRM object model (lookup, master-detail, junction) which supports multiple relationship types. The Data Cloud DMO relationship model is more constrained.

**Correct pattern:** Data Cloud allows only one data relationship per field pair between two DMOs. Complex many-to-many or multi-type relationships must be modeled using different field pairings or through a transform that produces a new intermediate DMO.

**Detection hint:** If a design shows two relationships between the same two DMOs using the same field pair, the second relationship will fail to create.

---

## Anti-Pattern 4: Using Streaming Transforms for Cross-DLO Joins

**What the LLM generates:** A streaming transform configuration that joins a web event DLO with a product catalog DLO to enrich event records in near-real-time.

**Why it happens:** LLMs conflate streaming and batch transforms, not modeling the single-source restriction on streaming transforms.

**Correct pattern:** Streaming transforms support only one source DLO and cannot perform joins. Cross-DLO joins require batch transforms (scheduled interval). For near-real-time enrichment that requires joining multiple sources, the design must use a batch transform with a short scheduling interval, accepting the latency tradeoff.

**Detection hint:** If a streaming transform configuration references more than one DLO as a source, it will fail at configuration time.

---

## Anti-Pattern 5: Omitting Mandatory Identity DMO Mappings When Onboarding a New Data Source

**What the LLM generates:** A data stream configuration that maps all business-relevant fields (purchase amount, product, date) to a custom DMO but does not map identity-relevant fields (email, customer ID) to the mandatory identity DMOs.

**Why it happens:** LLMs focus on the business data fields and miss the identity infrastructure layer, not knowing that identity resolution is gated on specific standard DMO mappings.

**Correct pattern:** Any data source that contains customer identity fields (email, phone, address, external customer ID) must map those fields to the mandatory identity DMOs: Contact Point Email, Contact Point Phone, Contact Point Address, Party Identification, and Individual. Omitting these mappings means the data source cannot contribute to unified profiles — with no error to indicate why.

**Detection hint:** If a data stream onboarding plan shows all fields mapping to a custom DMO but none mapping to the five mandatory identity DMOs, and the source contains customer identity data, identity resolution coverage for that source will be zero.

---

## Anti-Pattern 6: Confusing Data Cloud Harmonization with the Marketing Cloud "Harmonization Center"

**What the LLM generates:** In response to "harmonize my data in Data Cloud," instructions to open the Harmonization Center in the Connect & Mix tab and configure naming-convention patterns, classification rules, and harmonized dimensions.

**Why it happens:** Two unrelated Salesforce features share the word "harmonize." The Harmonization Center is a real feature — but it belongs to Marketing Cloud Intelligence (formerly Datorama), not Data Cloud / Data 360. LLMs pattern-match on the word and pull in the wrong product's UI.

**Correct pattern:** In Data Cloud / Data 360, harmonizing data means mapping DLO fields to standardized Customer 360 Data Model DMO fields (the Transform and Model lifecycle stage). It has no "Harmonization Center." Only reach for the Harmonization Center's naming-convention and classification-rule mechanics when the context is explicitly Marketing Cloud Intelligence / Datorama analytics.

**Detection hint:** If Data Cloud DMO guidance mentions "Harmonization Center," "Connect & Mix," "harmonized dimensions," or "classification rules," it has drifted into the wrong product.
