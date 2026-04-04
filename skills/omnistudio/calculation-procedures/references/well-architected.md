# Well-Architected Notes — Calculation Procedures

---

## Relevant Pillars

### Reliability

Calculation Procedures execute synchronously. Any runtime error in a procedure or its referenced matrix will fail the calling OmniScript action or Integration Procedure step immediately. Reliability work here means: ensuring active versions exist before deployment, guarding against null variable state from type mismatches, and testing with boundary inputs before activation. Sub-procedure activation order is a reliability risk in multi-environment deployments.

### Scalability

Calculation Procedures with many sequential steps and multiple Decision Matrix lookups add latency to synchronous OmniScript and Integration Procedure flows. Very large matrix row sets (thousands of rows) affect lookup performance at runtime. Design mitigation: decompose large procedures into focused sub-procedures, keep matrix columns lean (only the inputs and outputs actually needed), and avoid looping constructs (`IsLoopingEnabled`) unless the use case genuinely requires iteration — looping significantly increases execution time.

---

## Architectural Tradeoffs

**Calculation Procedure vs. Apex class:** A Calculation Procedure is a no-code artifact that business analysts can read and (with appropriate permissions) edit. An Apex class is more testable with unit tests but requires a developer and a deployment for every change. Use a Calculation Procedure when the logic changes on a business cycle (quarterly rates, annual eligibility rules). Use Apex when the logic is deeply procedural, requires bulkification, or must integrate with complex transaction logic.

**Calculation Matrix vs. Custom Settings/Metadata:** Custom Metadata Types are deployment artifacts — every data change requires a deployment or a special partial deployment. A Calculation Matrix allows data changes (new rows, new versions) through the UI with no deployment. Use Custom Metadata for configuration that belongs in source control; use Calculation Matrix for business-owned lookup data that changes independently of code.

**Single large procedure vs. sub-procedures:** A single monolithic procedure is simpler to deploy and trace. Sub-procedures allow product-line teams to version their logic independently and reduce the blast radius of a single change. Choose sub-procedures when different business owners control different calculation branches, or when a calculation component is genuinely reusable across multiple parent procedures.

---

## Anti-Patterns

1. **Hardcoding rate data in Assignment steps** — Encoding business rates directly in Assignment step literals means every rate change requires a new procedure version. Rates and rules belong in a Calculation Matrix where business users can manage them. Procedure versions should capture logic changes, not data changes.

2. **Single monolithic procedure with deeply nested Condition branches** — Procedures with 30+ steps and multi-level Condition nesting are difficult to debug, version, and hand off. The built-in test execution panel cannot efficiently test all branches in a single run. Decompose into focused sub-procedures with clear input/output contracts.

3. **Missing activation validation in deployment runbooks** — Deploying Calculation Procedures and Calculation Matrices to production without explicitly verifying `IsActive = true` on the correct versions is a leading cause of post-release failures. Activation is a data operation that is not captured in standard change sets; it must be a documented, verified step in every release process.

---

## Official Sources Used

- Salesforce Industries Developer Guide (local import: `knowledge/imports/salesforce-industries-dev-guide.md`) — ExpressionSet object, ExpressionSetVersion object, CalculationMatrix object, CalculationMatrixVersion object, CalculationMatrixRow object, step type reference, and migration service documentation
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Reliability, Scalability, and Trusted pillar framing
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm — OmniStudio integration patterns and component design
