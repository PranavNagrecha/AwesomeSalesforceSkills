# Well-Architected Notes — Email-to-Case Configuration

## Relevant Pillars

- **Reliability** — Email-to-Case is a critical inbound channel. Misconfigured threading means customer replies create duplicate cases, causing agents to work in parallel on the same issue. Unverified routing addresses silently drop inbound email. Both failures are invisible to the customer and degrade support reliability. On-Demand mode relies on Salesforce infrastructure availability; Standard mode adds a local agent as a reliability dependency.
- **Security** — Standard Email-to-Case keeps email content inside the corporate network before case creation, which matters for orgs with strict data classification requirements. On-Demand routes email through Salesforce infrastructure. The choice must be deliberate and documented. Auto-response rule loops can expose the org's case creation endpoint to abuse if an external sender can trigger unbounded case creation.
- **Operational Excellence** — Routing address verification, mail server forwarding rules, threading tests, and auto-response loop prevention must all be validated before go-live and documented in the org runbook. Multiple routing addresses per org must be inventoried so that changes to mail server configuration do not silently break specific channels.
- **Performance** — Standard Email-to-Case consumes API calls per email. High-volume orgs using Standard mode must account for this in API budget planning. On-Demand uses Apex Email Services and does not consume API calls, making it the more scalable choice for high-volume inbound channels.

## Architectural Tradeoffs

**On-Demand vs Standard:** On-Demand is simpler to operate, requires no local infrastructure, does not consume API calls, and scales with Salesforce's email infrastructure. The tradeoff is that email content routes through Salesforce infrastructure before case creation. Standard keeps email internal but adds an agent server as a single point of failure and consumes API calls. Choose Standard only when data residency or content classification policy explicitly requires it.

**Single vs multiple routing addresses:** A single routing address is simpler to maintain but cannot differentiate inbound channels at creation time. Multiple routing addresses allow per-channel defaults and queue routing but multiply the number of mail server forwarding rules, verification records, and monitoring points. Design for the minimum number of routing addresses that meets the business's channel differentiation requirement.

**Auto-response on Email-to-Case vs outbound email on case creation:** Auto-response rules are simple and require no automation. However, they depend on assignment rule execution and cannot be triggered selectively (e.g., only for certain case origins). Flow-based outbound email actions give more control over when and to whom the confirmation is sent, at the cost of additional automation to maintain.

## Anti-Patterns

1. **Unverified routing addresses in production** — Creating routing addresses and completing mail server forwarding without verifying the Salesforce-side address results in silent case creation failures. All inbound email is delivered but no cases are created. This is an operational excellence anti-pattern: there is no monitoring, no alert, and no user-facing error. Always verify routing addresses before configuring mail server forwarding rules.

2. **Assuming On-Demand and Standard are equivalent in all scenarios** — Treating the mode choice as a cosmetic preference rather than an infrastructure and security decision causes post-go-live surprises: attachment rejections under On-Demand for files that worked under Standard, or data residency audit findings when email content was expected to remain internal. Document the mode selection rationale in the org's architecture decision record.

3. **Relying on email threading without end-to-end testing through the production mail gateway** — Testing threading in sandbox bypasses the corporate email gateway. Production gateways often modify email content in ways that strip Lightning thread tokens. Discovering this failure after go-live means all customer replies have been creating new cases — sometimes for days — before the issue is detected. End-to-end gateway testing is a reliability requirement, not an optional step.

## Official Sources Used

- Salesforce Help: Set Up Email-to-Case — https://help.salesforce.com/s/articleView?id=sf.setting_up_email_to_case.htm
- Salesforce Help: Email-to-Case Limits and Limitations — https://help.salesforce.com/s/articleView?id=sf.email_to_case_limits.htm
- Salesforce Help: Auto-Response Rules — https://help.salesforce.com/s/articleView?id=sf.creating_auto-response_rules.htm
- Salesforce Help: Assignment Rules — https://help.salesforce.com/s/articleView?id=sf.creating_assignment_rules.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
