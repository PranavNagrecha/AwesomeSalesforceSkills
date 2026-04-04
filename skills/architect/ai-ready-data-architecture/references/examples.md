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
2. **Embedded tables:** Fee schedule information is stored as HTML tables within Rich Text fields. The RAG retrieval pipeline strips HTML but does not reconstruct table semantics, leaving "0.25% | 0.50% | 1.00%" with no column headers.
3. **No metadata tagging:** Articles have no product, audience, or topic category metadata. The retrieval system returns all 800 articles as candidates for any query, including irrelevant ones, which injects noise into the grounding context.

**Solution:**
1. **Article decomposition:** The 8,000-word guide is split into 12 focused articles: one per account type, one for fee schedules (prose format, not table), one for eligibility rules, one for tax treatment, one per FAQ category. Each article is capped at 600–800 words.

2. **Prose conversion of tables:** Fee schedules are rewritten as structured prose: "The standard advisory fee for balances under $100,000 is 1.00% annually. For balances between $100,000 and $500,000 the fee is 0.50% annually. For balances above $500,000 the fee is 0.25% annually." This format chunks and embeds cleanly.

3. **Metadata taxonomy:** A data category taxonomy is defined: Product (5 values), Audience (3 values: Retail, Advisor, Internal), Topic (10 values: Fees, Eligibility, Tax, Onboarding, etc.). All 800 articles are tagged. Agentforce is configured to pre-filter by Audience=Retail for customer-facing queries.

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
