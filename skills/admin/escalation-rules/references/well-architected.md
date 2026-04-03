# Well-Architected Notes — Escalation Rules

## Relevant Pillars

### Reliability

Escalation rules are a reliability mechanism: they ensure that cases do not fall through the cracks when agents are unavailable, overloaded, or miss an SLA. A well-configured escalation rule provides a backstop that fires regardless of individual agent behavior.

Key reliability design considerations:
- Use multiple rule entries to cover different case types and priorities; a single catch-all entry with loose criteria may not provide appropriate SLA coverage for high-priority cases.
- Validate escalation action targets (users, queues) regularly — a notification sent to an inactive user or an empty queue silently fails to reach anyone.

### Operational Excellence

Escalation rules are a form of operational automation. They reduce the need for manual SLA monitoring and enable support teams to act on breaches rather than discover them after the fact.

Best practices for operational excellence:
- Document the escalation rule configuration alongside your SLA commitments so support managers understand the automation behavior.
- Review and update escalation rule entries when SLA policies change — stale rules that reference obsolete priorities or case types create confusion and gaps.
- Align escalation thresholds with business hours to avoid off-hours noise that desensitizes the team.

## Architectural Tradeoffs

**Declarative escalation (Escalation Rules) vs. programmatic escalation (Apex/Flow):**
- Escalation Rules are zero-maintenance, no-code, and native to Case management. They are the right choice for straightforward time-based case notification and reassignment.
- Escalation Rules cannot conditionally branch, call external APIs, or perform complex record updates. If your escalation logic requires multi-step orchestration, conditional logic based on related records, or cross-object updates, consider a Scheduled Flow or Apex Schedulable.
- The ~1-hour processing granularity of the time-based engine is acceptable for most SLA windows (4 hours, 8 hours, 24 hours). For sub-hourly SLAs (15-minute response, for example), the declarative engine is not suitable.

**Business hours vs. 24/7 escalation:**
- 24/7 escalation is appropriate for P1/critical cases in always-on environments. Business-hours escalation is appropriate for standard cases at regionally-staffed orgs.
- Mixing both within one rule (24/7 for P1, business-hours for P2/P3) is supported by using separate entries with different business hours settings.

## Anti-Patterns

1. **Creating separate escalation rules for each case type** — Salesforce allows only one active escalation rule per org. Attempting to have a "Sales" rule and a "Service" rule active simultaneously causes the second activation to silently deactivate the first. Use multiple rule entries within a single active rule to differentiate by case type.

2. **Assuming "Use Business Hours" without configuring the hours** — The default business hours record is 24/7. Enabling "Use Business Hours" on a rule entry without explicitly restricting business hours in Setup > Business Hours has no meaningful effect. This is a common source of weekend escalation noise.

3. **Not validating escalation action targets** — Escalation notifications sent to inactive users, empty queues, or invalid roles fail silently. There is no delivery failure notification. Audit action targets periodically against active users and populated queues.

## Official Sources Used

- Salesforce Help: Set Up Case Escalation Rules — https://help.salesforce.com/s/articleView?id=sf.customize_escalation.htm
- Salesforce Help: Business Hours — https://help.salesforce.com/s/articleView?id=sf.businesshours.htm
- Metadata API Developer Guide: EscalationRules Metadata Type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_escalationrules.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
