# Well-Architected Notes — AI Training Data Preparation

## Relevant Pillars

### Reliability

Data preparation is the reliability foundation of any Einstein ML model. A model trained on leaky or incomplete data produces unreliable predictions that erode trust in the product. The fill-rate audit and leakage detection steps in this skill directly address reliability by ensuring the training dataset represents the actual feature space the model will encounter at prediction time.

### Performance Efficiency

Model accuracy is directly constrained by data quality. Performance problems (low accuracy, poor recall) are often rooted in data preparation gaps rather than model configuration: sparse fields, unusable categoricals, and rare outcomes. Addressing fill rates and class balance before training prevents wasted iteration on model settings.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Trustworthy AI | Leakage detection prevents artificially inflated accuracy metrics — models that perform well in training but fail in production undermine user trust in AI features |
| Data Quality | Einstein Studio enforces 400 to 20 million rows and 3 to 50 columns; the 70% fill rate and 200-record EPB figures are review thresholds, UNVERIFIED as platform rules (2026-10-03) |
| Operational Excellence | Documenting outcome field design and leakage audit results creates an audit trail for model review and regulatory compliance |

## Cross-Skill References

- `data/analytics-data-preparation` — XMD metadata management affects which fields are available in CRM Analytics datasets used by Einstein Discovery
- `admin/analytics-dataset-management` — Dataset scheduling and row limits affect training data freshness
- `agentforce/einstein-discovery-development` — Story creation and REST API integration that consumes this skill's data preparation work

## Official Sources Used

Read for this revision (2026-10-03):

- Data Cloud guide, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/data_cloud.pdf. Use AI Models: Create Predictive AI Models From Scratch (400 to 20 million rows, 3 to 50 columns, regression and binary classification, steps that can't be edited after creation), Address Data Issues (outliers, incorrect values, high cardinality, ordinal variables, collinearity, missing values), Evaluate Model Quality (AUC, R-squared, "too high" accuracy), Glossary for Predictive AI (leakage, cardinality and 100 categories, Unspecified nulls, correlation, importance, k-fold), Einstein Studio Model Builder Guidelines and Limits.
- Metadata API Developer Guide, Version 67.0: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf. AIApplication, MLDataDefinition (includedFields, excludedFields, filters, fields that can't be updated), MLFilter, MLPredictionDefinition (type values, status, pushbackField).
- Analytics Platform Setup Guide, Spring '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/bi_admin_guide_setup.pdf. CRM Analytics Plus permission sets covering Einstein Discovery; "Story Creation and Prediction Limits" pointer to Einstein Discovery Limits (limits not listed in the PDF).
- Einstein Discovery REST API Developer Guide, Spring '26 (local corpus): `knowledge/imports/bi-dev-guide-rest-sdd.md`. Story `sourceType` values (AnalysisSetup, AnalyticsDataset, LiveDataset, Report).
- Salesforce Object Reference, Summer '26: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf. Case.IsEscalated (groupable boolean used in the audit example).

Listed in the original version and not re-read:

- Einstein Discovery, Determine Data Requirements: https://help.salesforce.com/s/articleView?id=sf.bi_edd_data_requirements.htm (Salesforce Help does not fetch; source of the 400-row and 70% figures, now marked UNVERIFIED).
- Einstein Prediction Builder Considerations: https://help.salesforce.com/s/articleView?id=sf.einstein_prediction_considerations.htm (Salesforce Help does not fetch; source of the 200/200 figure, now marked UNVERIFIED).
- CRM Analytics REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
