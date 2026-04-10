# Well-Architected Notes — CPQ Test Automation

## Relevant Pillars

- **Reliability** — CPQ test automation directly supports reliability by verifying that price rules, discount schedules, contracting flows, and order generation behave correctly across deployments. Without CPQ-engine-invoked tests, regressions in managed package upgrade interactions go undetected until production. The four-layer test strategy (Apex unit, CPQ API, Selenium UI, LWC Jest) provides defense in depth across all CPQ behavior surfaces.

- **Operational Excellence** — Reliable CPQ test classes are a prerequisite for automated CI/CD pipelines that include CPQ-heavy orgs. Tests that skip the calculation engine produce false-green pipelines that ship broken pricing logic. Following the ServiceRouter invocation pattern ensures test results are meaningful signals, not noise.

- **Security** — CPQ test classes that use `@testSetup` and proper data isolation prevent unintended cross-test data contamination. Running with realistic data (real product structures, real pricebook entries) also surfaces security-related validation behaviors (sharing rules, field-level security) that mock data misses.

- **Performance** — CPQ calculation engine calls within tests consume governor limits. Tests that over-call `SBQQ.ServiceRouter.calculateQuote()` (e.g., calling it once per quote line rather than once per quote) will hit CPU time and SOQL limits before covering meaningful scenarios. Batching quote line inserts before a single engine call is the correct pattern.

- **Scalability** — CPQ test classes that share a `@testSetup` data set scale better than classes where every test method creates its own full prerequisite graph. As the number of CPQ test methods grows, `@testSetup` amortizes the expensive prerequisite DML across all methods.

## Architectural Tradeoffs

**ServiceRouter invocation vs. DML-only tests:** The key tradeoff is test fidelity against simplicity. ServiceRouter tests are more complex to write and slower to execute (they invoke the full managed package engine), but they are the only tests that actually exercise price rule logic. DML-only tests are simpler and faster but have zero coverage of CPQ's core pricing behaviors. For any org where price rules are configured, DML-only tests for pricing are an architectural liability.

**CPQ API layer vs. UI test layer:** CPQ API tests (ServiceRouter) cover pricing and contracting logic but cannot test option constraints, guided selling UX, or configurator flows that are rendered and enforced in the CPQ UI. Selenium / UTAM tests can reach the UI layer but are slower, more brittle, and harder to maintain. The recommended split is: use CPQ API tests for all pricing and contracting coverage; use UI tests only for constraint and configurator behaviors that have no Apex-accessible equivalent.

**Full CPQ package dependency vs. isolation:** CPQ test classes are architecturally dependent on the managed package being installed. This is not optional. The design tradeoff is accepting this hard dependency (and managing it through scratch org provisioning and CI pipeline configuration) vs. attempting to isolate CPQ logic behind Apex interfaces — which breaks down as soon as any SBQQ type is referenced in the production code under test.

## Anti-Patterns

1. **DML-Only Price Rule Coverage** — Writing test classes that insert quote lines and assert pricing field values without invoking `SBQQ.ServiceRouter.calculateQuote()`. This produces tests with 100% code coverage metrics but zero behavioral coverage of price rules. The anti-pattern is invisible in coverage reports and only reveals itself when a price rule regression reaches production.

2. **Hardcoded Standard Pricebook IDs** — Embedding a specific Pricebook2 ID in test data setup instead of calling `Test.getStandardPricebookId()`. This makes test classes org-specific, breaking CI pipelines and scratch org workflows. The Salesforce Well-Architected framework's reliability pillar requires tests to be environment-agnostic; hardcoded IDs are a direct violation of this principle.

3. **Omitting CPQ Package from Scratch Org Provisioning** — Designing a DX workflow that provisions scratch orgs without installing the CPQ managed package, then attempting to deploy CPQ test classes. This produces non-compilable deployments and breaks the "deploy early, test often" principle that underpins Operational Excellence in the Salesforce Well-Architected framework.

## Official Sources Used

- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
- Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_ref_guide.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce CPQ Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_guide.htm
- Salesforce Help: Important Fields for CPQ Test Classes (KA-000390047) — https://help.salesforce.com/s/articleView?id=000390047&type=1
- Salesforce Developers Blog: Automating Salesforce CPQ Testing — https://developer.salesforce.com/blogs/2019/01/automating-salesforce-cpq-testing.html
