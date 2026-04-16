# Well-Architected Notes — MuleSoft Anypoint Architecture

## Relevant Pillars

### Security

API Manager policy enforcement is the governance layer for all MuleSoft APIs. Policies are only enforced when: (1) the API Instance is in Active status, and (2) the Mule application has Autodiscovery configured with the correct Instance ID. Security configurations that appear complete in API Manager but fail either condition run with no enforcement. Anypoint Security Edge and Tokenization are only available on CloudHub runtimes — verify feature compatibility before finalizing runtime model selection.

### Operational Excellence

Runtime model selection directly determines operational burden. CloudHub 1.0 and 2.0 are MuleSoft-managed — infrastructure operations, upgrades, and availability are MuleSoft's responsibility. Runtime Fabric delegates Kubernetes cluster management to the customer. Teams without Kubernetes operations capability selecting RTF will face unplanned operational burden. Document the runtime model rationale and operations ownership explicitly before deployment.

### Reliability

Post-deployment API policy validation is mandatory. A successfully deployed Mule application with a misconfigured or Inactive API Instance will pass all integration tests that do not test policy enforcement. Reliability requires testing that policy enforcement is actually active — call the API without credentials and confirm rejection before marking deployment complete.

### Performance Efficiency

CloudHub 2.0 private spaces allow VPC-level isolation without sacrificing MuleSoft-managed scalability. Runtime Fabric adds customer-managed cluster scaling responsibility. For performance-sensitive deployments, confirm that autoscaling policies are configured correctly for the selected runtime model.

---

## WAF Mapping

| WAF Area | Guidance |
|---|---|
| Security | API Manager Active status + Autodiscovery required for policy enforcement; verify Anypoint Security feature compatibility with runtime model |
| Operational Excellence | Document runtime model selection rationale and operations ownership before deployment |
| Reliability | Post-deployment validation must include API policy rejection tests, not just HTTP 200 connectivity tests |
| Performance Efficiency | Select runtime model appropriate to scaling needs; CloudHub managed scaling vs. RTF customer-managed cluster scaling |

---

## Cross-Skill References

- `integration/api-led-connectivity` — For designing the Experience/Process/System API layer pattern
- `integration/mulesoft-salesforce-connector` — For Salesforce Connector configuration within Mule applications
- `integration/hybrid-integration-architecture` — For decisions about MuleSoft vs. Salesforce-native integration

---

## Official Sources Used

- MuleSoft Anypoint Platform Runtime Models: https://docs.mulesoft.com/runtime-manager/
- MuleSoft CloudHub 2.0 Overview: https://docs.mulesoft.com/cloudhub-2/
- MuleSoft Runtime Fabric Overview: https://docs.mulesoft.com/runtime-fabric/latest/
- API Manager — Apply Policies: https://docs.mulesoft.com/api-manager/2.x/latest-tasks-policy-mule4
- API Autodiscovery (Mule 4): https://docs.mulesoft.com/api-manager/2.x/api-auto-discovery-new-concept
- Anypoint Exchange: https://docs.mulesoft.com/exchange/
