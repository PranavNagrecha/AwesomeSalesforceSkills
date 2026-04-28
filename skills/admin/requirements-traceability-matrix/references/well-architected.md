# Well-Architected Notes — Requirements Traceability Matrix

## Relevant Pillars

The RTM is a delivery-governance artifact, not a runtime system. The Well-Architected pillars apply through the *quality of the delivery and operations process*, not through org-level configuration.

- **Operational Excellence** — The RTM is the operational record of "what we agreed to build, what we built, what we tested, what shipped." It is the canonical artifact every release gate, Steerco, and audit consumes. A maintained RTM means delivery is observable; a stale RTM means leadership is making decisions on fiction.
- **Reliability** — Forward and backward traceability are reliability controls for the delivery process. Forward traceability ensures every approved requirement was delivered (no silent drops). Backward traceability ensures no scope was added without an approval trail (no silent additions). Together they make the delivery process repeatable and auditable across releases and phases.

The other three pillars (Security, Performance, Scalability, User Experience) are out of scope for this skill — the RTM does not change platform behavior. Where regulatory traceability adds a `compliance_control_id` column, the linkage to Security pillar is indirect: the matrix does not implement the control, it documents that the control was implemented and tested.

## Architectural Tradeoffs

The key tradeoffs a delivery team faces:

- **Spreadsheet vs CSV-in-Git** — Spreadsheet RTMs are easier to start but rot quickly because they lack version control, review gates, and automated checks. CSV-in-Git requires more setup (a checker script, a CI hook, a markdown generator) but produces a durable artifact that survives team turnover. For any Salesforce program past three sprints, CSV-in-Git is the only sustainable choice.
- **Lightweight vs regulated schema** — A greenfield project with no audit posture can ship a 10-column RTM. A regulated project (HIPAA, SOX, GxP, FedRAMP) needs `compliance_control_id` and `evidence_link` columns plus per-row evidence artifacts. Adding regulated columns to a non-regulated project creates noise; omitting them on a regulated project creates audit findings.
- **Update cadence** — Updating at release gates is easier but produces stale data. Updating per-sprint requires more discipline but keeps the matrix current. The right cadence is per-sprint with a release-gate audit pass on top.
- **Hand-tracing vs automated linkage** — Manually populating `defect_ids` by walking defect → story → requirement does not scale past sprint 3. A nightly automation job that reads the defect tracker and updates the RTM scales but requires the agile and defect tools to expose APIs (Jira, Azure DevOps, GUS all do).

## Anti-Patterns

1. **RTM as a snapshot, not a process** — Building the RTM once at project kickoff and never updating it produces an artifact that lies by the second sprint. The RTM is a continuous artifact; if it is not being updated weekly, it is decaying.

2. **RTM as a delivery report, not a scope record** — Teams use the RTM to show "what we shipped" and exclude dropped or deferred requirements. This destroys the audit trail and prevents leadership from seeing the cumulative scope decisions across the program. Dropped requirements are first-class rows.

3. **One-row-per-story instead of one-row-per-requirement** — When a requirement maps to multiple stories, teams often add one row per story. This breaks the unique key on `req_id`, makes coverage queries unreliable, and obscures the requirement-level rollup. Always: one row per requirement, pipe-delimited story IDs.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/well-architected/adaptable/resilient
- Salesforce Trailhead — Business Analyst Skills (requirements management and traceability practices) — https://trailhead.salesforce.com/credentials/businessanalyst
