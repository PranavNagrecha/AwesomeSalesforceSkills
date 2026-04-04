# Well-Architected Notes — Queues and Public Groups

## Relevant Pillars

- **Operational Excellence** — Queues and public groups are operational infrastructure. Clear naming conventions, documented membership ownership, and regular membership audits keep support and sales operations running predictably. Poorly maintained queues (deactivated members, deleted queues with orphaned records) create operational blind spots.
- **Scalability** — Public group nesting and sharing rule design directly affect sharing recalculation performance. Flat group structures and bounded sharing rule counts keep the platform responsive as record volumes and team sizes grow. Queue-based work distribution scales better than individual-user assignment when team size fluctuates.
- **Reliability** — Queue email misconfiguration or deleted queues create silent failures: records enter a queue, no one is notified, and work stalls. Validate queue email addresses and membership coverage during any team restructuring.
- **Security** — Public groups are an access-granting mechanism. Overly broad group membership (e.g., adding all users to a group that has a wide sharing rule) can inadvertently open access beyond intent. Group membership should be reviewed with the same rigor as permission sets.

## Architectural Tradeoffs

**Flat vs nested group membership:** Nested public groups are convenient for modeling org hierarchies but multiply the cost of sharing recalculation. The tradeoff is between maintenance simplicity (nesting mirrors the org chart) and platform performance (flat groups recalculate faster). In orgs with more than 500,000 records on a shared object, prefer flat groups and accept the manual maintenance overhead.

**Queue email vs Omni-Channel presence:** Queue email provides a simple team notification with zero configuration overhead. Omni-Channel routing provides capacity-aware, agent-availability-based distribution with real-time presence. The tradeoff is setup complexity vs routing intelligence. Omni-Channel requires additional licenses (in some editions) and admin configuration; queue email requires only an email alias. Choose based on SLA requirements and team size.

**Queue-based routing vs user assignment:** Queue-based routing provides flexibility (any available agent picks up work) at the cost of reporting clarity (ownership attribution is delayed until acceptance). Direct user assignment provides clear accountability from record creation but requires knowing which agent to target at routing time. Omni-Channel combines the flexibility of queues with automated agent selection.

## Anti-Patterns

1. **Using queues for objects that do not support them** — Creating a queue and attempting to assign Accounts, Contacts, or Opportunities to it is unsupported. The queue may appear in Setup, but the object's OwnerId cannot be set to a Queue Id. Use public groups and sharing rules for access on these objects instead.

2. **Using a public group as a substitute for a queue** — Public groups do not own records. Trying to "assign" a record to a public group by setting OwnerId to the group's Id is not a valid operation for most objects and produces an error. If record ownership routing is the goal, create a queue.

3. **Unconstrained group nesting in high-volume orgs** — Building a hierarchy of five or more nested groups for a sharing rule that covers a large object creates a sharing recalculation risk. Any membership change can trigger a multi-hour async job. Design groups to be as flat as possible, especially for Opportunity, Case, and high-record-count custom objects.

## Official Sources Used

- Salesforce Help: Set Up and Use Queues — https://help.salesforce.com/s/articleView?id=sf.queues_overview.htm&type=5
- Salesforce Help: Create and Edit Groups — https://help.salesforce.com/s/articleView?id=sf.group_creating.htm&type=5
- Salesforce Help: Sharing Rules — https://help.salesforce.com/s/articleView?id=sf.security_sharing_rules_managing.htm&type=5
- Salesforce Help: Queue Fields (Group sObject) — https://help.salesforce.com/s/articleView?id=sf.queues_fields.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Record Access Under the Hood (Salesforce Architects) — local knowledge: knowledge/imports/salesforce-record-access-under-the-hood.md
