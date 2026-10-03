# Examples — AI-Ready Data Architecture

Real-world patterns for designing Salesforce data architectures that reliably support AI features.

---

## Example 1: Improving Einstein Opportunity Scoring Fill Rates

**Scenario:** A B2B SaaS company enables Einstein Opportunity Scoring on their Enterprise Edition org. After 30 days, scoring is active but the model's accuracy score in the setup UI shows "Low Confidence" and reps report that scores do not match their intuition.

**Problem:** The data quality audit reveals that three of the highest-signal predictor fields — `Industry`, `AnnualRevenue`, and `NumberOfEmployees` on the Account — have fill rates of 28%, 19%, and 14% respectively. These are the fields Einstein most commonly uses to personalize opportunity scoring in B2B orgs. Because the model cannot build meaningful clusters from sparse data, it falls back to global averages and produces near-identical scores for all open opportunities.

Additionally, the `LeadSource` field on Opportunity has 40+ active picklist values, many of which are legacy migration artifacts (e.g., "Legacy Import Q4 2019", "Migrated — unknown"). This picklist noise makes it impossible for the model to distinguish meaningful acquisition channel signals.

**Solution:**
1. **Fill rate remediation:** A Flow on the Account object is updated to make `Industry` required on edit for existing records and required on create for new records. A data cleanup task is assigned to Sales Ops to populate `AnnualRevenue` and `NumberOfEmployees` for the top 200 open-pipeline accounts using a SOQL-exported CSV and Data Loader import.

2. **Picklist curation:** `LeadSource` values are consolidated from 40+ to 12 canonical values. A Flow migration runs on existing records, mapping legacy values to canonical equivalents. The picklist is set to Restricted so new values cannot be added without admin approval.

3. **Validation:** After 60 days and an Einstein model refresh cycle, fill rates on the three Account fields reach 74%, 61%, and 58%. Einstein's model confidence score improves from Low to High. Rep feedback improves: the score now reliably distinguishes high-momentum from stalled deals.

**Why it works:** Einstein's feature selection algorithm weights fields by their predictive power relative to their availability. A field with 20% fill rate has low availability, so even if it is highly correlated with outcomes, it cannot be weighted heavily without introducing selection bias. Increasing fill rates to 60%+ allows the model to use those signals across the full pipeline population.

---

## Example 2: Structuring Knowledge Articles for Agentforce RAG Grounding

**Scenario:** A financial services company deploys Agentforce for Service to handle customer-facing questions about their wealth management products. The agent is grounded on the company's Salesforce Knowledge base of 800 articles. In UAT, testers find that the agent frequently gives incomplete answers, sometimes combines facts from unrelated products, and occasionally hallucmates policy details that are not in any article.

**Problem:** A review of the Knowledge base reveals three structural problems:
1. **Monolithic articles:** The flagship product guide is a single 8,000-word article covering account types, fee schedules, eligibility rules, tax treatment, and FAQs. When chunked, individual chunks lack enough context to stand alone as grounding material.
2. **Embedded tables:** Fee schedule information is stored as HTML tables within Rich Text fields. The RAG retrieval pipeline strips HTML but does not reconstruct table semantics, leaving "0.25% | 0.50% | 1.00%" with no column headers. (UNVERIFIED 2026-10-03: how the native Data Library search index treats HTML tables is not documented in the fetched guides; the problem is observed in custom pipelines.)
3. **No metadata tagging:** Articles have no product, audience, or topic category metadata. The retrieval system returns all 800 articles as candidates for any query, including irrelevant ones, which injects noise into the grounding context.

**Solution:**
1. **Article decomposition:** The 8,000-word guide is split into 12 focused articles: one per account type, one for fee schedules (prose format, not table), one for eligibility rules, one for tax treatment, one per FAQ category. Each article is capped at 600–800 words.

2. **Prose conversion of tables:** Fee schedules are rewritten as structured prose: "The standard advisory fee for balances under $100,000 is 1.00% annually. For balances between $100,000 and $500,000 the fee is 0.50% annually. For balances above $500,000 the fee is 0.25% annually." This format chunks and embeds cleanly.

3. **Metadata taxonomy:** A data category taxonomy is defined: Product (5 values), Audience (3 values: Retail, Advisor, Internal), Topic (10 values: Fees, Eligibility, Tax, Onboarding, etc.). All 800 articles are tagged. Agentforce is configured to pre-filter by Audience=Retail for customer-facing queries, using the data library's "Filter by Knowledge Data Categories" setting (Generative AI guide, "Setting Up Data Libraries").

**Why it works:** RAG retrieval quality depends on chunk coherence and retrieval precision. Short, focused articles produce chunks that are semantically complete — each chunk can answer a narrow question without requiring context from adjacent chunks. Metadata pre-filtering reduces the candidate pool from 800 to ~150 articles per query, dramatically improving precision and reducing the chance of contradictory grounding content entering the prompt context.

---

## Example 3: Data Cloud Field Mapping for AI Activation

**Scenario:** A retail company connects their Salesforce CRM to Data Cloud with the goal of building a unified customer profile for personalized product recommendations powered by Einstein. After ingesting Account and Contact data, the Data Cloud team finds that calculated insights on purchase history are returning incorrect values and the AI recommendation model is under-performing.

**Problem:** The root cause is inconsistent field naming and semantic duplication across the source data:
- `Account.Phone`, `Contact.Phone`, and the external POS system's `customer_phone` field are all mapped to three different Contact Point Phone fields in Data Cloud's canonical schema because their API names are different. Identity resolution treats them as independent contact points, creating duplicate individual profiles.
- `Account.AnnualRevenue` (Salesforce) and `customer_ltv` (external commerce platform) represent similar but not identical concepts. Both are mapped to the same canonical revenue field, causing calculated insights to combine incompatible values.
- `CreatedDate` and `LastModifiedDate` are used inconsistently across ingestion sources as the event timestamp. Some Data Cloud data streams use `CreatedDate`, others use `LastModifiedDate`. Calculated insights on purchase recency are computed against inconsistent time references.

**Solution:**
1. **Phone normalization:** A pre-ingestion transformation in the Data Cloud data stream normalizes all phone fields to E.164 format before ingestion. Data Cloud's identity resolution then correctly merges the three contact points into a single canonical phone number per customer.
2. **Revenue field separation:** `AnnualRevenue` and `customer_ltv` are mapped to separate calculated insight fields with documented semantic definitions. A unified `CustomerValue__c` calculated insight is defined as a weighted formula combining both signals with documented business logic.
3. **Timestamp standardization:** All data streams are updated to use a single canonical `EventTimestamp` field. Source timestamps are preserved in a separate `SourceCreatedDate` field for auditability.

**Why it works:** Data Cloud's harmonized data model depends on field-level consistency across sources. When the same real-world concept appears under different API names or with different semantic meanings, automated mapping creates silent errors that propagate into every downstream calculated insight and AI model feature. Standardizing before ingestion — rather than attempting to fix downstream — is always less expensive and more reliable.

---

## Example 4: AI-Readiness Assessment Record for a Service Agent and Case Scoring

**Context:** An insurer (Service Cloud Unlimited Edition, Data Cloud provisioned, Einstein for Service add-on) wants an Agentforce Service Agent to answer policy questions from Knowledge and a Prediction Builder model that predicts claim escalation on `Case`. Pricing tables change mid-month. Some article fields were moved to Shield-encrypted text last year.

**Evidence: fill rates for candidate predictor fields.** The SOQL guide says `COUNT(fieldName)` ignores nulls while `COUNT()` and `COUNT(Id)` do not, so one aggregate query per object gives the fill rate for every field at once:

```soql
SELECT COUNT(Id) total,
       COUNT(Type) type_filled,
       COUNT(Reason) reason_filled,
       COUNT(Product_Line__c) product_filled,
       COUNT(Policy_Tier__c) tier_filled
FROM Case
WHERE CreatedDate = LAST_N_DAYS:365 AND IsClosed = true
```

**Evidence: which Knowledge fields can ground the agent.** Field types come from the Knowledge object's field list; the Generative AI guide supports Text, Text Area, Text Area (Long), and Text Area (Rich), and not Text (Encrypted) or URL.

**Assessment record (machine-readable form):**

```yaml
assessment: AIR-003
date: 2026-10-03
scope:
  - feature: Agentforce Service Agent, Answer Questions with Knowledge
    licences: [Einstein for Service add-on, Data Cloud]
  - feature: Prediction Builder model on Case (escalation)
    output: AIRecordInsight records plus the prediction field the model writes (Object Reference)
data_library:
  source: Knowledge only        # a library takes Knowledge OR file uploads, not both
  identifying_fields: [Title, Summary]
  content_fields: [Answer__c (Text Area Rich), Coverage_Details__c (Text Area Long)]
  excluded_fields:
    - Claim_Contact_Line__c: Text (Encrypted), not supported for grounding; stays protected by design
    - Policy_PDF_Link__c: URL, not supported; the PDFs go into a second, file-upload library (<= 100 MB each)
  filters: [Use Public Knowledge Articles, data category Audience = Customer]
  freshness: Knowledge reindexed daily after initial indexing
policy_values:
  decision: premiums and deductibles come from a flow action that reads Rate_Card__c live
  reason: daily reindex means grounded text can be a day old; deterministic values must not depend on it
predictors:   # fill rate = <field>_filled / total from the query above
  Type: 0.97
  Reason: 0.88
  Product_Line__c: 0.64     # below the 70% working threshold (heuristic, UNVERIFIED)
  Policy_Tier__c: 0.31      # remediate before training or drop
remediation:
  - Product_Line__c: populate from the related policy record with a before-save flow; backfill closed cases by batch
  - Policy_Tier__c: drop from the first model version; revisit after 6 months of capture
data_cloud_streams:
  - name: Claims_Events
    category: Engagement     # cannot be changed after ingestion
    identity_attributes: [Policy_Number__c, Email]
quality_gate:
  completeness: pass after Product_Line__c backfill
  consistency: Reason picklist reduced from 41 to 14 values
  timeliness: Data Cloud stream hourly; Knowledge reindex daily (accepted)
  volume: closed Case history 3 years (Help-only minimums not relied on)
  circularity: escalation prediction field excluded from model inputs
```

**Why it works:** each claim in the record traces to a documented behavior (field-type support, single-source libraries, daily reindex, immutable stream categories, `COUNT(fieldName)` null handling). The two heuristic thresholds are labeled as heuristics, and policy values that must be exact are served by a live action rather than by grounded text.

