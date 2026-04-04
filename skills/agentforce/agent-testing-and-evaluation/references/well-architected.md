# Well-Architected Notes — Agent Testing and Evaluation

## Relevant Pillars

- **Reliability** — Testing is the primary mechanism for ensuring an Agentforce agent behaves predictably across utterance variations, conversational contexts, and after configuration changes. Without a structured test suite covering topic routing, action sequences, and regression baselines, reliability is accidental rather than engineered. A reliable agent has documented, passing tests for every topic before it is activated, and those tests are re-run after every change.

- **Operational Excellence** — Post-deploy monitoring closes the loop that pre-deploy testing opens. Enhanced Event Logs, containment rate dashboards, and escalation rate trends are the operational instruments that surface gaps in the test suite that pre-production testing did not catch. Operational Excellence requires treating anomalies in production metrics as inputs to the test suite — every production failure mode should produce a new test case.

- **Security** — Testing surfaces unintended agent behavior that could expose sensitive data or bypass intended scope restrictions. Out-of-scope utterance tests confirm the agent declines gracefully rather than hallucinating an in-scope topic and invoking unauthorized actions. Instruction adherence tests validate that data-handling constraints in topic instructions are respected in agent responses.

## Architectural Tradeoffs

**Deterministic test gates vs. probabilistic quality signals:** Topic and action tests are deterministic and suitable as hard pipeline gates. Instruction adherence tests use an LLM judge and have inherent variance. Mixing them in the same gate tier causes flaky pipelines. Keep them in separate tiers with different gate policies.

**Test coverage breadth vs. run time:** Testing API runs are asynchronous and each invocation adds latency. A test suite with hundreds of cases will block a CI pipeline noticeably. The tradeoff: run the full regression suite on release branches but run a smaller smoke suite (happy path only, ~10 cases per topic) on every feature branch merge. Document the tiering policy explicitly.

**Pre-production testing vs. production monitoring:** No pre-production test suite can fully represent the diversity of real user utterances. The architecture that maximizes reliability combines automated pre-production tests (high confidence, low coverage) with post-deploy analytics from real conversations (high coverage, lagging signal). Neither is sufficient alone.

## Anti-Patterns

1. **Happy-path-only test suite** — building a test suite that covers only the canonical, clearly in-scope utterance for each topic. This gives full pass rates in CI while leaving topic boundary failures and edge-case routing errors undiscovered until production. The fix: require boundary utterances and out-of-scope utterances in every topic's test case set before promotion.

2. **Testing without a saved baseline** — running test suites but not persisting the results, then applying topic or action changes and re-running. Without a baseline, a regression cannot be distinguished from a pre-existing failure, and newly broken cases go undetected. The fix: save the full Testing API result payload as a versioned artifact and diff it against the new run after every change.

3. **Relying on Testing API alone for end-to-end validation** — assuming that 100% test pass rate means the agent is production-ready, without running live sessions in sandbox to validate action execution. The fix: treat Testing API as a routing/reasoning validator and layer live functional testing on top before every production promotion.

## Official Sources Used

- Agentforce Developer Guide — Testing API overview, AiEvaluationDefinition metadata reference, Connect API test execution
  URL: https://developer.salesforce.com/docs/einstein/genai/guide/testing-api.html

- Agentforce Developer Guide — Build Tests in Metadata API
  URL: https://developer.salesforce.com/docs/einstein/genai/guide/testing-api-build-tests.html

- Agentforce Developer Guide — Use Test Results to Improve Your Agent
  URL: https://developer.salesforce.com/docs/einstein/genai/guide/testing-api-use-results.html

- Agentforce Developer Guide — Run Tests in Connect API
  URL: https://developer.salesforce.com/docs/einstein/genai/guide/testing-api-connect.html

- Salesforce Developers Blog — Automate Multi-Turn Agent Testing with Conversation History in Agentforce
  URL: https://developer.salesforce.com/blogs/2025/11/automate-multi-turn-agent-testing-with-conversation-history-in-agentforce

- Salesforce Developers Blog — Test Your Agentforce Agents with Custom Evaluation Criteria
  URL: https://developer.salesforce.com/blogs/2025/10/test-your-agentforce-agents-with-custom-evaluation-criteria

- Salesforce Well-Architected Overview — architecture quality framing (Reliability, Operational Excellence pillars)
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
