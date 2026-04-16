# Well-Architected Notes — Slack Workflow Builder

## Relevant Pillars

- **Security** — Slack workflows can expose Salesforce-derived data to everyone in a channel. Apply least-privilege Flow design, narrow queries, and channel governance so Workflow Builder does not become an unaudited data export path.
- **Reliability** — Two platforms participate in each run: Slack executes the workflow while Salesforce executes the Flow. Token, permission, or deployment issues surface as step failures; operators need clear ownership between Slack admins and Salesforce admins.
- **Operational Excellence** — Publish/run history in Slack and debug logs in Salesforce must be linked in runbooks. Changes to connector allowlists, Flow API names, or input contracts should be versioned like any cross-system integration.

## Architectural Tradeoffs

**Slack Workflow Builder vs Salesforce-owned automation:** Workflow Builder is ideal when the **human trigger lives in Slack** (shortcut, reaction, channel event) and Salesforce work is short and idempotent. When the **system of record event** originates in Salesforce at high volume, implementing automation in Salesforce Flow (often asynchronous) reduces coupling and clarifies failure handling.

**Thin autolaunched wrapper vs duplicating logic:** Calling a large record-triggered flow from Slack is impossible without refactoring. A thin autolaunched flow that delegates to subflows or Apex keeps Slack mapping stable while allowing CRM paths to evolve.

## Anti-Patterns

1. **Treating Workflow Builder as iPaaS** — Chaining many connector steps without retries, idempotency keys, or compensation flows creates brittle production behavior. For complex orchestration, use an integration tier or Salesforce-first patterns from Integration Patterns guidance.

2. **Skipping bulk testing** — A workflow tested with single clicks may still fail under imports or message storms. Always validate bulk scenarios when the Flow performs DML or callouts.

3. **Mixing up directions** — Teams assign “Slack integration” tickets without clarifying Slack→Salesforce vs Salesforce→Slack. Document which product surface owns the trigger to avoid building the wrong automation.

## Official Sources Used

- Guide to Slack Workflow Builder — https://slack.com/help/articles/360035692513 (Slack product behavior, publishing, activity logs)
- Slack connectors for Workflow Builder — https://slack.com/help/articles/20155812595219 (connector authentication and approval model)
- Connect the Salesforce for Slack App to a Salesforce Org — https://help.salesforce.com/s/articleView?id=sf.slack_apps_digital_hq_setup.htm (prerequisite org connection)
- Flow Reference: Slack Actions in Salesforce Flow — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_actions_slack.htm (disambiguates Salesforce Flow actions that *send to Slack* from Slack-initiated **Run a Flow**)
- Integration Patterns — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html (system boundaries, synchronous vs asynchronous tradeoffs)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (trusted, easy, adaptable solution quality)
