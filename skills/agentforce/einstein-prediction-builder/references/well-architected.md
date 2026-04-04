# Well-Architected Notes — Einstein Prediction Builder

## Relevant Pillars

- **Trusted** — The model must be built on clean, unbiased training data with leakage fields excluded. Score-based decisions made by sales reps, service agents, or automated Flows carry real business consequences. A model built on leakage data or an imbalanced outcome set will produce scores that are statistically misleading and erode user trust in AI tooling. Auditing top factor fields via EinsteinModelFactor__c before go-live is a trust gate, not an optional step.
- **Adaptable** — Predictions become stale as business patterns change. An adaptable EPB implementation includes a documented retrain cadence, a model comparison process before promoting a new version, and monitoring for score distribution drift over time. The implementation should not treat the first trained model as permanent.
- **Easy** — Score fields and the "Einstein Prediction" Lightning component are designed for low-friction end-user adoption. The score (0–100) is interpretable by non-technical users. Well-architected implementations surface score + top reasons (via the component or a custom formula) on the record page without requiring users to navigate to separate reports.

## Architectural Tradeoffs

**Auto field selection vs. practitioner-guided exclusion:** Einstein auto-selects predictor fields based on correlation, which is fast but can introduce leakage. Practitioner review and explicit exclusion of leakage fields adds a setup step but is non-negotiable for model validity. The tradeoff is speed-of-setup vs. model reliability in production.

**Single prediction vs. segments:** A single prediction definition with no segments trains on the full record population and applies one model to all records. Segments allow per-segment field configurations, which improves accuracy for distinct sub-populations at the cost of increased configuration complexity and more outcome data required per segment. Use segments when there are demonstrably different predictor signals across sub-populations (e.g., Enterprise vs. SMB, Inbound vs. Outbound).

**EPB vs. Einstein Discovery:** EPB is the right choice for binary yes/no outcomes on CRM objects, requires no CRM Analytics license, and has a point-and-click setup. Einstein Discovery supports continuous (regression) and multi-class outcomes, supports prescriptive improvement suggestions, and integrates with Data Cloud and CRM Analytics datasets — but requires a CRM Analytics or Tableau CRM license and more data preparation overhead. Choose EPB for simple binary scoring embedded in the CRM UI; choose Einstein Discovery for advanced analytics and prescriptive use cases.

## Anti-Patterns

1. **Training without reviewing leakage fields** — Accepting Einstein's auto-selected predictor fields without reviewing them for outcome-time leakage. This produces training metrics that look excellent but a model that fails in production because the fields that drove accuracy are not available at the time of actual scoring. Always review and exclude fields that are set at or after the outcome event.

2. **Activating with imbalanced training data and no exclusion filter** — Proceeding to activation when the outcome field has fewer than 5–10% positive outcomes and no exclusion filter to undersample the majority class. The resulting model learns to predict "No" for almost every record, achieving high raw accuracy (matching the base rate) but near-zero utility. Imbalanced data must be addressed before activation either through outcome field cleanup, exclusion filters, or acknowledgment that the model will have low positive-class recall.

3. **No retrain cadence or model drift monitoring** — Activating a prediction and never returning to retrain or review model accuracy. As business conditions change, the model's internal assumptions diverge from reality. There is no automatic alert when model accuracy degrades — monitoring must be built into operational governance. Treat a trained EPB model like production code: it requires ongoing ownership, not one-time deployment.

## Official Sources Used

- Einstein Prediction Builder documentation — https://help.salesforce.com/s/articleView?id=sf.bi_edd_home.htm&type=5
- Einstein Prediction Builder: Build a Prediction (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.bi_edd_create.htm&type=5
- EinsteinModelFactor Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_einsteinmodelfactor.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Einstein Platform Services Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
