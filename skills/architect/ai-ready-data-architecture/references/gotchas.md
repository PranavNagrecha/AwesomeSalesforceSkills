# Gotchas — AI-Ready Data Architecture

Non-obvious pitfalls when designing Salesforce data architectures for AI features.

---

## Gotcha 1: Einstein Scoring Silently Degrades Without Warning When Fill Rates Drop

Einstein predictive scoring models are retrained periodically, but there is no native alerting when model confidence degrades due to declining data quality. If a picklist field that was a strong predictor in the original model begins receiving inconsistent values after a process change (e.g., a new picklist value is added that absorbs traffic from two previously meaningful values), the model silently re-weights that field downward on the next training cycle. Scores may still be generated and displayed — they just become less accurate.

**What to do:** Build a monthly data quality monitoring report that tracks fill rates and picklist distribution for all fields known to be predictive inputs. Flag any field where value distribution shifts by more than 10 percentage points month-over-month. Treat Einstein score confidence ratings in the setup UI as a lagging indicator, not a proactive signal.

---

## Gotcha 2: Data Cloud Activation Mismatches Fail Silently

When Data Cloud activates a segment or calculated insight back to Salesforce CRM objects, field type mismatches between the Data Cloud attribute and the CRM target field cause individual record updates to fail without surfacing a bulk error. A Number field in Data Cloud mapped to a Text field in Salesforce CRM will often write successfully but strip precision (e.g., `1250.75` becomes `"1250.75"`, breaking downstream numeric SOQL comparisons). A Date/Time in UTC mapped to a Date-only field loses time-of-day information.

**What to do:** Before production activation, run a dry-activation on a 100-record test segment. Validate the activated field values in the target CRM object using SOQL. Confirm data types match — not just that activation completes without an error in the Data Cloud activation log.

---

## Gotcha 3: Rich Text Fields in Salesforce Knowledge Store HTML That Pollutes Vector Embeddings

Salesforce Knowledge's Body field is a Rich Text Area. When content is authored in the Knowledge editor, the platform stores HTML markup (`<p>`, `<ul>`, `<li>`, `<strong>`, `&amp;`, `&#160;` for non-breaking spaces, etc.) inside the field value. If this raw HTML is passed to an embedding model, the model treats markup tokens as part of the semantic content. The resulting embeddings cluster articles by their HTML structure rather than their semantic content — articles that both happen to use heavily nested lists will be more similar to each other than articles on the same topic but formatted differently.

**What to do:** Strip HTML before embedding. A server-side transformation step must parse the Rich Text field, extract plain text, and normalize whitespace before passing content to the embedding pipeline. BeautifulSoup (Python) or a Salesforce Apex `String.stripHtmlTags()` call can handle this. Build the stripping step into the Data Cloud ingestion transform, not as a post-hoc fix.

---

## Gotcha 4: Einstein Feature Store Fields Are Not Queryable in Real-Time Decision Logic

Einstein scoring fields on CRM records (e.g., `EinsteinScore__c`, `EinsteinScoreReason1__c`, `EinsteinScoreReason2__c`) are updated asynchronously by the Einstein scoring service. The update can lag the triggering event by minutes to hours depending on org load. Trigger-based Apex or synchronous Flow that reads these fields immediately after a record save will frequently read stale values — including null before the first score is ever written.

An anti-pattern seen in the field: a before-save Flow that gates record routing logic on the Einstein score value. If the score is null (because it has not yet been written), the Flow branches to a default path that is incorrect for scored records. This creates a race condition where early-pipeline records are routed differently from re-scored records.

**What to do:** Einstein score fields should be consumed in asynchronous contexts only: reports, list views, dashboard components, scheduled jobs, and Agentforce prompt context. Never use them in synchronous record-save logic. If routing logic requires a score-influenced decision, use a scheduled Apex job or Flow scheduled path that runs after the scoring cycle completes.

---

## Gotcha 5: Data Cloud Harmonized Data Model Requires Consistent `primaryKey` Mapping Across All Ingested Data Streams

Data Cloud's identity resolution depends on a consistent `primaryKey` value being passed in every data stream for the same individual or account. If one data stream passes Salesforce `ContactId` as the primary key and another passes email address, Data Cloud will not automatically unify those records unless email address is also configured as an identity attribute for the `ContactId`-keyed stream — or vice versa.

This is a frequent mistake during Data Cloud onboarding: the CRM connector correctly passes Salesforce IDs, while a custom-built commerce data stream passes customer email as the key. The result is two unresolved identity graphs — Einstein recommendations built on the unified profile see only half the customer's history.

**What to do:** Before connecting any new data stream, define the identity resolution strategy explicitly: which fields represent the same real-world person or account across all data sources. Add all candidate identity attributes (email, phone, CRM ID, loyalty ID) to the identity resolution ruleset. Test unification with a known set of records that have overlapping identities before activating the stream in production.

---

## Gotcha 6: Knowledge Article Sync Lag Can Ground Agentforce on Outdated Policy Content

Agentforce grounding via Data Cloud knowledge base does not update instantaneously when a Knowledge article is updated in Salesforce CRM. The article must be re-synced to Data Cloud, re-chunked, and re-embedded before the updated content is available for retrieval. Depending on the Data Cloud connector sync schedule, this lag can be 4–24 hours. During this window, Agentforce may ground responses on the previous version of the article.

For policy-sensitive content (pricing, legal terms, compliance procedures), this lag is operationally significant. A price change published in Knowledge at 9 AM may not be available to the Agentforce knowledge base until the next evening sync.

**What to do:** For policy-critical articles, configure the Data Cloud Knowledge connector to run on a near-real-time or hourly schedule rather than daily. Establish a process where Knowledge article authors flag policy-critical updates, triggering a manual connector sync via the Data Cloud connector admin UI. Document the lag SLA for AI grounding in the operational runbook so stakeholders have calibrated expectations.
