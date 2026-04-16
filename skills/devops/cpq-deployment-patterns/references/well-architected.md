# Well-Architected Notes — CPQ Deployment Patterns

## Relevant Pillars

### Operational Excellence

CPQ deployments have two distinct steps: metadata deployment and data deployment. Both steps must be present in the CI/CD pipeline and executed in order. Metadata-only deployments succeed silently while leaving CPQ configuration missing in the target org — this is a failure mode that appears successful until a sales rep tries to generate a quote.

### Reliability

Post-deployment test quote generation is a mandatory validation step. CPQ configuration can be structurally correct (all records deployed) but logically incorrect (Price Rules produce wrong prices). Reliability requires testing business-critical pricing scenarios after every deployment.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Operational Excellence | Two-step pipeline: metadata first, data second; validate with test quotes |
| Reliability | Test CPQ quote generation for each major pricing scenario after deployment |
| Security | External ID fields on CPQ objects must have FLS set appropriately to prevent unauthorized cross-org data exposure |
| Performance | CPQ Quote Calculation Sequence order affects deployment load time; load in dependency order to minimize rollback risk |

---

## Cross-Skill References

- `devops/cpq-deployment-administration` — For CPQ sandbox administration between deployment cycles
- `data/deployment-data-dependencies` — For general data record deployment with cross-org ID mapping
- `devops/package-development-strategy` — For CPQ package type selection if building CPQ extensions

---

## Official Sources Used

- Salesforce Help: CPQ Quote Calculation Sequence — https://help.salesforce.com/s/articleView?id=sf.cpq_quote_calc_sequence.htm
- Salesforce Help: Integrating Salesforce CPQ and Salesforce Billing — https://help.salesforce.com/s/articleView?id=sf.cpq_billing_integrate.htm
- SFDMU (Salesforce Data Move Utility): https://github.com/forcedotcom/SFDMU
