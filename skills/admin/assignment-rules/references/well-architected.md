# Well-Architected Notes — Assignment Rules

## Relevant Pillars

- **Operational Excellence** — Assignment rules are a core operational mechanism. A well-configured rule reduces manual ownership decisions, ensures consistent routing, and makes queue workloads visible to managers. Poorly ordered rule entries or missing catch-all entries create operational noise (mis-routed records, late response).
- **Reliability** — Rules that depend on API callers passing the correct header create a reliability risk: one missed header means records silently bypass routing. Design for reliability by auditing integration touchpoints and making header inclusion a code review requirement.
- **Scalability** — Native assignment rules scale to 3,000 entries per rule without code. For round-robin or capacity-based routing at volume, Omni-Channel is the scalable choice over Apex triggers that may hit CPU limits under bulk insert.

## Architectural Tradeoffs

**Declarative vs Apex routing:** Assignment rules are the correct first choice for criteria-based routing — they require no deployment risk, no testing infrastructure, and are maintainable by admins. Apex is only warranted when the routing logic cannot be expressed as field-value criteria (e.g., true round-robin, machine-learning-based scoring) or when the assignment must react to external service responses.

**Queue vs direct user assignment:** Queue assignment is more resilient to staff changes. Adding or removing a user from a queue does not require changing the assignment rule. Direct user assignment creates a single point of failure if the assigned user goes on leave — every rule entry targeting that user must be updated. Prefer queue assignment with Omni-Channel for flexible capacity management.

**Assignment rules vs Flow:** Record-triggered Flows can also set OwnerId during before-save execution, and they run before assignment rules in the order of operations. If a Flow sets OwnerId and the assignment rule also runs, the assignment rule's result will override the Flow's OwnerId set in before-save — unless the user/API caller does not opt in to the rule. This interaction must be explicitly tested.

## Anti-Patterns

1. **Multiple overlapping assignment mechanisms without explicit priority** — Using both a before-save Flow that sets OwnerId and an active assignment rule on the same object creates unpredictable ownership. The rule fires after before-save, so the rule result typically wins. Document and test which mechanism is authoritative.
2. **Targeting individual users instead of queues for team routing** — Hard-coding individual user IDs in rule entries creates maintenance overhead. Every time a rep changes territory, quits, or goes on leave, an admin must update the assignment rule. Queues with Omni-Channel or queue + human acceptance provide resilience.
3. **No catch-all rule entry** — Rules with only specific criteria entries will not match every record. Unmatched records go to the Default Lead Owner or retain the API user as owner — silently. Always add a final entry with no criteria as a catch-all to a known default queue.

## Official Sources Used

- Salesforce Help: Set Up Lead Assignment Rules — https://help.salesforce.com/s/articleView?id=sf.customizestandard_leadrules.htm&type=5
- Salesforce Help: Set Up Case Assignment Rules — https://help.salesforce.com/s/articleView?id=sf.cases_assignment.htm&type=5
- Metadata API Developer Guide: AssignmentRules Metadata Type — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_assignmentrule.htm
- Object Reference: AssignmentRule sObject — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_assignmentrule.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
