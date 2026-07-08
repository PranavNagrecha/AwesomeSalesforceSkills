# Well-Architected Notes — Case Management Setup

## Relevant Pillars

- **Operational Excellence** — Case management setup directly determines how efficiently a support team can triage, route, and resolve customer issues. Misconfigured escalation rules, missing auto-response rules, or broken thread handling create manual work, missed SLAs, and degraded customer experience. Operational Excellence requires that every case reach the correct owner via the correct channel, with appropriate notifications, without human intervention. It also requires that the configuration keep working: Salesforce frames case management as an ongoing practice — "not a 'set it and forget it' process" — where rule entries, queue membership, and SLA thresholds are reviewed on a cadence and where leaders have reports and dashboards showing routing and SLA attainment. A setup with no named owner and no review interval is operationally incomplete regardless of how correct it was on day one.
- **Reliability** — Email-to-Case and Web-to-Case are customer-facing inbound channels. Silent failure modes (truncated email bodies, dropped Web-to-Case submissions at the 50,000 limit, orphaned cases from deleted queues) are reliability risks that are invisible until a customer escalates. Reliability requires monitoring these limits and testing failure paths explicitly.
- **Security** — Web-to-Case forms are publicly accessible. Without validation, they are an open vector for spam, garbage data, and potential injection of malicious content into the case body. Case team access grants record visibility independent of org sharing — this access channel must be managed deliberately.

## Architectural Tradeoffs

**Escalation rules vs. Flow/Apex for time-based re-routing:** Native escalation rules are declarative and zero-code but have a one-hour engine cadence and support only one active rule. Flow or Apex time-based actions can achieve sub-hour precision and more complex logic but require development and maintenance overhead. For SLA requirements where 30-minute precision matters, native escalation rules are insufficient.

**Web-to-Case vs. API-based form submission:** The built-in Web-to-Case endpoint is simple but has a 50,000 pending-request hard limit and no native validation. An Experience Cloud site or a custom form that POSTs directly to the REST API (creating cases via the sObject API) bypasses the Web-to-Case queue, allows server-side validation, and scales without the pending-request constraint. For high-volume scenarios (product launches, public forms), API-based submission is architecturally superior.

**Entitlements via automation vs. manual application:** Entitlement templates on products require Classic. In Lightning, automation (Flow triggered on case creation) is necessary to apply entitlements at scale. Relying on agents to manually attach entitlements introduces SLA gaps — cases without entitlements have no milestone tracking.

**Queue pull vs. Omni-Channel push:** Queues are shared work lists reps pull from — Salesforce describes them as lists "from which specific reps can jump in to solve certain types of cases." That model is cheap to configure, requires no capacity modeling, and lets experienced reps self-select. It also lets hard cases sit unclaimed and gives no mechanism to balance load. Omni-Channel pushes work to a rep based on availability, skill set, and workload, which enforces balance and enables true skills-based routing at the cost of presence configuration, capacity models, and ongoing tuning. Choose pull when the team is small and homogeneous; choose push when case complexity varies by skill or when unclaimed work is a measurable problem. The queue remains the input either way — Omni-Channel replaces the pull, not the queue.

**A single active rule as an architectural constraint, not an inconvenience:** Assignment, auto-response, and escalation rules each permit exactly one active rule for cases. This is not a limit to be worked around; it is a forcing function that keeps case routing centralized and auditable. Orgs that fight it — by pushing routing logic into Flow or Apex so that each business unit can own its own automation — trade a single ordered, first-match-wins rule that any admin can read for a distributed set of automations whose combined behavior nobody can predict. The constraint is worth preserving. Model variation as ordered entries inside the one rule, and treat activation as a governed change with a named rollback target.

**AI-predicted field values as a routing input:** Einstein Case Classification predicts checkbox, picklist, and lookup field values on a case from the org's closed-case history, when the case is created. (Its sibling app on the same help topic, Einstein Case Wrap-Up, predicts when a chat with the customer ends — a distinct app, not a second timing mode of Classification.) Where routing criteria depend on fields agents fill by hand (Type, Priority, Reason), prediction removes the gap between case creation and correct routing. It also inherits the quality of the closed-case corpus and places a model in the path of every inbound case. The tradeoff is accuracy-versus-latency-to-route: manual triage is slower but auditable; prediction is immediate but requires monitoring of prediction quality and a routing design that degrades safely when confidence is low. A catch-all assignment rule entry is the safety net either way. Prerequisites and enablement belong to `agentforce/agentforce-service-ai-setup`, not to this skill.

## Anti-Patterns

1. **Configuring auto-response rules without verifying the assignment rule layer** — Auto-response rules have no independent trigger. Treating them as standalone causes repeated misconfiguration, because every "why isn't the auto-response firing" investigation must start at the assignment rule layer. Design documentation and team onboarding should explicitly call out this dependency.

2. **Escalation rule maintenance in production without reactivation impact analysis** — Deactivating an escalation rule for any maintenance reason, then reactivating it, can generate a bulk escalation wave for all open cases that aged past threshold during the inactive period. Performing this operation in production without sandbox testing first is an operational risk that has caused unintended manager notifications and case re-assignments at scale.

3. **Relying on Web-to-Case without monitoring the pending request count** — The 50,000 limit is a silent drop ceiling. Orgs that add public-facing forms (support pages, product registration, warranty claims) without establishing operational monitoring for this counter eventually experience submission loss during traffic spikes. This is a reliability gap, not just a configuration detail.

4. **Activating rules in production as an ungoverned Setup action** — Activating an assignment, auto-response, or escalation rule deactivates the rule already occupying that slot, with no confirmation and no partial state. An admin activating a test rule to "see if the criteria work" has replaced production routing org-wide. The mitigation is procedural, not technical: inventory the active rule in each slot, name rules with a version marker so the incumbent is identifiable, rehearse the swap in a sandbox against every inbound channel, and activate the replacement directly rather than deactivating the incumbent first. Rollback should be one activation of a rule that still exists, not a rebuild from memory.

5. **Treating go-live as the end of case management work** — Rule entries stop matching as picklist values evolve, queues retain members who left the company, and SLA thresholds drift from the contracts they were derived from. Salesforce is explicit that case management is not a set-and-forget process. A configuration handed over without a named owner per rule slot, a review cadence, and dashboards that surface routing and SLA attainment to leaders will degrade silently — and the degradation will surface as a customer escalation rather than an admin alert.

## Official Sources Used

- Salesforce Help: Set Up Email-to-Case — https://help.salesforce.com/s/articleView?id=sf.setting_up_email_to_case.htm
- Salesforce Help: Email-to-Case Limits — https://help.salesforce.com/s/articleView?id=sf.cases_email_limitations.htm
- Salesforce Help: Set Up Web-to-Case — https://help.salesforce.com/s/articleView?id=sf.setting_up_web-to-case.htm
- Salesforce Help: Assignment Rule Limits — https://help.salesforce.com/s/articleView?id=sf.creating_assignment_rules.htm
- Salesforce Help: Auto-Response Rules — https://help.salesforce.com/s/articleView?id=sf.creating_auto-response_rules.htm
- Salesforce Help: Escalation Rules — https://help.salesforce.com/s/articleView?id=sf.creating_escalation_rules.htm
- Salesforce Help: Set Up Entitlements and Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_setup.htm
- Salesforce Help: Case Teams Overview — https://help.salesforce.com/s/articleView?id=sf.caseteam_overview.htm
- Salesforce Help: Case Management Best Practices — https://help.salesforce.com/s/articleView?id=000390829&language=en_US&type=1
- Salesforce Help: Cases (Service Cloud) — https://help.salesforce.com/s/articleView?id=service.cases_intro.htm&language=en_US&type=5
- Salesforce Help: Automate Cases with Rules — https://help.salesforce.com/s/articleView?id=service.cases_rules_home.htm&language=en_US&type=5
- Salesforce Help: Set Up Auto-Response Rules — https://help.salesforce.com/s/articleView?id=service.creating_auto-response_rules.htm&language=en_US&type=5
- Salesforce Help: Limits for Assignment, Auto-Response, and Escalation Rules — https://help.salesforce.com/s/articleView?id=service.rules_limits.htm&language=en_US&type=5
- Salesforce Help: Use Case Feed in Salesforce Classic — https://help.salesforce.com/s/articleView?id=service.case_interaction_overview.htm&language=en_US&type=5
- Salesforce Help: Route Work with Omni-Channel — https://help.salesforce.com/s/articleView?id=service.omnichannel_intro.htm&language=en_US&type=5
- Salesforce Help: Omni-Channel Skills-Based Routing — https://help.salesforce.com/s/articleView?id=omnichannel_skills_based_routing.htm&language=en_US&type=5
- Salesforce Help: Autofill Case Fields with Einstein Case Classification Apps — https://help.salesforce.com/s/articleView?id=service.cc_service_what_is.htm&language=en_US&type=5
- Trailhead: Service Cloud for Lightning Experience — Manage Cases — https://trailhead.salesforce.com/content/learn/modules/service_lex/service_lex_case_manage
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
