# Well-Architected Notes — Case Management Setup

## Relevant Pillars

- **Operational Excellence** — Case management setup directly determines how efficiently a support team can triage, route, and resolve customer issues. Misconfigured escalation rules, missing auto-response rules, or broken thread handling create manual work, missed SLAs, and degraded customer experience. Operational Excellence requires that every case reach the correct owner via the correct channel, with appropriate notifications, without human intervention.
- **Reliability** — Email-to-Case and Web-to-Case are customer-facing inbound channels. Silent failure modes (truncated email bodies, dropped Web-to-Case submissions at the 50,000 limit, orphaned cases from deleted queues) are reliability risks that are invisible until a customer escalates. Reliability requires monitoring these limits and testing failure paths explicitly.
- **Security** — Web-to-Case forms are publicly accessible. Without validation, they are an open vector for spam, garbage data, and potential injection of malicious content into the case body. Case team access grants record visibility independent of org sharing — this access channel must be managed deliberately.

## Architectural Tradeoffs

**Escalation rules vs. Flow/Apex for time-based re-routing:** Native escalation rules are declarative and zero-code but have a one-hour engine cadence and support only one active rule. Flow or Apex time-based actions can achieve sub-hour precision and more complex logic but require development and maintenance overhead. For SLA requirements where 30-minute precision matters, native escalation rules are insufficient.

**Web-to-Case vs. API-based form submission:** The built-in Web-to-Case endpoint is simple but has a 50,000 pending-request hard limit and no native validation. An Experience Cloud site or a custom form that POSTs directly to the REST API (creating cases via the sObject API) bypasses the Web-to-Case queue, allows server-side validation, and scales without the pending-request constraint. For high-volume scenarios (product launches, public forms), API-based submission is architecturally superior.

**Entitlements via automation vs. manual application:** Entitlement templates on products require Classic. In Lightning, automation (Flow triggered on case creation) is necessary to apply entitlements at scale. Relying on agents to manually attach entitlements introduces SLA gaps — cases without entitlements have no milestone tracking.

## Anti-Patterns

1. **Configuring auto-response rules without verifying the assignment rule layer** — Auto-response rules have no independent trigger. Treating them as standalone causes repeated misconfiguration, because every "why isn't the auto-response firing" investigation must start at the assignment rule layer. Design documentation and team onboarding should explicitly call out this dependency.

2. **Escalation rule maintenance in production without reactivation impact analysis** — Deactivating an escalation rule for any maintenance reason, then reactivating it, can generate a bulk escalation wave for all open cases that aged past threshold during the inactive period. Performing this operation in production without sandbox testing first is an operational risk that has caused unintended manager notifications and case re-assignments at scale.

3. **Relying on Web-to-Case without monitoring the pending request count** — The 50,000 limit is a silent drop ceiling. Orgs that add public-facing forms (support pages, product registration, warranty claims) without establishing operational monitoring for this counter eventually experience submission loss during traffic spikes. This is a reliability gap, not just a configuration detail.

## Official Sources Used

- Salesforce Help: Set Up Email-to-Case — https://help.salesforce.com/s/articleView?id=sf.setting_up_email_to_case.htm
- Salesforce Help: Email-to-Case Limits — https://help.salesforce.com/s/articleView?id=sf.cases_email_limitations.htm
- Salesforce Help: Set Up Web-to-Case — https://help.salesforce.com/s/articleView?id=sf.setting_up_web-to-case.htm
- Salesforce Help: Assignment Rule Limits — https://help.salesforce.com/s/articleView?id=sf.creating_assignment_rules.htm
- Salesforce Help: Auto-Response Rules — https://help.salesforce.com/s/articleView?id=sf.creating_auto-response_rules.htm
- Salesforce Help: Escalation Rules — https://help.salesforce.com/s/articleView?id=sf.creating_escalation_rules.htm
- Salesforce Help: Set Up Entitlements and Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_setup.htm
- Salesforce Help: Case Teams Overview — https://help.salesforce.com/s/articleView?id=sf.caseteam_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
