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
- The batched processing granularity of the time-based engine is acceptable for most SLA windows (4 hours, 8 hours, 24 hours). For sub-hourly SLAs (15-minute response, for example), the declarative engine is not suitable. UNVERIFIED (2026-09-04): the frequently-quoted ~1-hour interval has no fetchable official source — see `references/gotchas.md` Gotcha 1; design for "batched", and measure the interval before quoting it.

**Business hours vs. 24/7 escalation:**
- 24/7 escalation is appropriate for P1/critical cases in always-on environments. Business-hours escalation is appropriate for standard cases at regionally-staffed orgs.
- Mixing both within one rule (24/7 for P1, business-hours for P2/P3) is supported by using separate entries with different business hours settings.

## Anti-Patterns

1. **Creating separate escalation rules for each case type** — Salesforce allows only one active escalation rule per org. Attempting to have a "Sales" rule and a "Service" rule active simultaneously causes the second activation to silently deactivate the first. Use multiple rule entries within a single active rule to differentiate by case type.

2. **Assuming "Use Business Hours" without configuring the hours** — The default business hours record is 24/7. Enabling "Use Business Hours" on a rule entry without explicitly restricting business hours in Setup > Business Hours has no meaningful effect. This is a common source of weekend escalation noise.

3. **Not validating escalation action targets** — Escalation notifications sent to inactive users, empty queues, or invalid roles fail silently. There is no delivery failure notification. Audit action targets periodically against active users and populated queues.

## Official Sources Used

- Metadata API Developer Guide, `EscalationRules` section — `EscalationRule`, `RuleEntry`, and `EscalationAction` field tables, the declarative sample definition, the `.escalationRules` suffix and `escalationRules` folder, API 27.0+, and wildcard support in package.xml (supports every element name, enum value, and the package.xml / file-layout claims in `references/metadata-examples.md`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `RuleEntry` field table — "Specify only if businessHoursSource is set to Static" and "Specify either formula or criteriaItems, but not both fields" (supports the `businessHoursSource` / `businessHours` pairing check and the criteria-vs-formula check in `scripts/check_escalation_rules.py`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `FilterItem` — the `field` / `operation` / `value` shape and the `FilterOperation` enum (`equals`, `notEqual`, `contains`, `startsWith`, and the rest) used in every `criteriaItems` block here — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference, `BusinessHours` object — "Escalation rules are run only during these hours", and the statement that holidays associated with business hours suspend both the hours and the escalation rules using them (supports the business-hours dependency in `SKILL.md` and Gotchas 3 and 10) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference, `Case` object, `IsEscalated` field — boolean with Create / Update / Filter / Group / Sort, "A case's escalated state does not affect how you can use a case… You can set this flag via the API" (supports Gotcha 11 and the monitoring caveat in `references/metadata-examples.md`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference, `Case` object, `BusinessHoursId` field — a writable reference to the calendar (supports `businessHoursSource` = `Case` and the null-fallback in `references/examples.md` Example 2) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce App Limits Cheat Sheet — searched for an escalation limit and found none; this is why the "5 actions per entry" ceiling is marked UNVERIFIED in `SKILL.md` rather than asserted — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Metadata API Developer Guide, `EscalationRules` metadata type reference page (canonical HTML entry point for the section above) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_escalationrules.htm
- Salesforce Well-Architected Overview (framing for the Reliability and Operational Excellence notes above) — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
