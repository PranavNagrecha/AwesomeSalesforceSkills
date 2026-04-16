# Well-Architected Notes — AI Training Data Preparation

## Relevant Pillars

### Reliability

Data preparation is the reliability foundation of any Einstein ML model. A model trained on leaky or incomplete data produces unreliable predictions that erode trust in the product. The fill-rate audit and leakage detection steps in this skill directly address reliability by ensuring the training dataset represents the actual feature space the model will encounter at prediction time.

### Performance Efficiency

Model accuracy is directly constrained by data quality. Einstein Discovery's silent field-dropping means that performance problems (low accuracy, poor recall) are often rooted in data preparation gaps rather than model configuration issues. Addressing fill rates and class balance before training prevents wasted iteration on model settings.

## WAF Alignment

| WAF Area | Guidance |
|---|---|
| Trustworthy AI | Leakage detection prevents artificially inflated accuracy metrics — models that perform well in training but fail in production undermine user trust in AI features |
| Data Quality | Fill-rate thresholds (70% for Einstein Discovery, 200-record minimums for EPB) are platform-enforced quality gates |
| Operational Excellence | Documenting outcome field design and leakage audit results creates an audit trail for model review and regulatory compliance |

## Cross-Skill References

- `data/analytics-data-preparation` — XMD metadata management affects which fields are available in CRM Analytics datasets used by Einstein Discovery
- `admin/analytics-dataset-management` — Dataset scheduling and row limits affect training data freshness
- `agentforce/einstein-discovery-development` — Story creation and REST API integration that consumes this skill's data preparation work

## Official Sources Used

- Einstein Discovery — Determine Data Requirements: https://help.salesforce.com/s/articleView?id=sf.bi_edd_data_requirements.htm
- Einstein Prediction Builder Considerations: https://help.salesforce.com/s/articleView?id=sf.einstein_prediction_considerations.htm
- CRM Analytics REST API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.bi_dev_guide_rest.meta/bi_dev_guide_rest/bi_rest_overview.htm
