# Flow Transactional Boundaries — Salesforce Well-Architected Mapping

Salesforce Well-Architected defines three pillars directly impacted by how Flow work is bounded across transactions: **Reliability**, **Performance**, and **Security** (running-user and sharing implications). This skill's recommendations map as follows.

## Reliability

Well-Architected Reliability requires that the system behave predictably under partial failure, bulk load, and integration concurrency. Transactional boundaries determine what "partial failure" means.

- **Same-transaction work fails together.** When a Before-Save or After-Save flow is paired with an Apex trigger, any exception from either rolls back everything in the transaction. This is DESIRABLE when the work is semantically one unit (create a parent and its line items as one atomic save). It is UNDESIRABLE when the post-processing is enrichment that should not block the primary save.
- **New-transaction work fails independently.** Scheduled Paths, Platform Event subscribers, and Orchestration Background Steps commit or fail in their own transaction. The originating save has already committed. This is DESIRABLE when enrichment or fan-out must not jeopardize the primary save; UNDESIRABLE when the business process must be all-or-nothing.
- **Idempotency is mandatory at every new-transaction boundary.** A retry may re-run the async path. Design writes so that re-applying them produces the same result (e.g., check `if (Case.EnrichedAt__c == null)` before updating).
- **Fault paths on async boundaries are non-negotiable.** A Scheduled Path without a fault path is a time bomb. When it fails, the user has already moved on and the only evidence is a debug log.

## Performance

Well-Architected Performance asks that work happen at the lowest cost and most appropriate latency for the user and the platform.

- **Before-Save is the lowest-cost boundary for same-record enrichment.** No extra DML. No re-trigger. Folded into the platform's existing save. This is the canonical "cheapest place to do the work" answer and should be the default for same-record rules.
- **Async boundaries double the per-transaction budget.** Synchronous limits (100 SOQL, 150 DML, 10,000 ms CPU, 6 MB heap) become async limits (200 SOQL, no CPU wall for schedulable / 60,000 ms for queueable, 12 MB heap) when work crosses to a new async transaction. Routing heavy work async is often the only way to stay under limits at scale.
- **Pause elements do NOT reduce work, they only defer it.** A Pause does not save CPU; it just moves the remaining work to a later transaction. Do not use Pause as a performance mitigation; use it when the business genuinely waits on an external event.
- **Subflows do not isolate cost.** A subflow runs in the parent transaction. If a subflow is proposed as a performance improvement, the improvement must come from algorithmic changes (collections, bulk patterns), not the boundary itself.
- **The save-to-user-return path should be as thin as possible.** Heavy post-save work should live in a Scheduled Path, Platform Event subscriber, or Queueable. The user's page should return in < 2 seconds for a good UX; every element on the synchronous path is time the user is waiting.

## Security

Well-Architected Trusted (Security) requires that all work happen in the correct user context with the correct sharing and permission semantics. Transactional boundaries change running-user context.

- **Same-transaction flows run as the user who triggered the save.** A record-triggered flow on Case `Update` runs as the user updating the Case. DML is attributed to them, sharing rules apply to them, and audit fields (`LastModifiedBy`) reflect them.
- **Scheduled Paths run as the user who caused the originating save.** The same running-user context is preserved across the scheduled path dispatch, which is usually what you want.
- **Platform Event subscribers run as the Automated Process user by default.** When a PE-triggered flow fires, the running user is the Automated Process user (not the publishing user) unless explicitly overridden with `Run as` settings. Sharing visibility changes accordingly.
- **Orchestration Background Steps run as the Automated Process user.** Interactive Steps run as the assignee.
- **Resumed Pause interviews run as the resuming actor.** If the user resumes, it's the user. If the scheduler resumes (timer elapsed), it's the Automated Process user.

Implications:
- Document "Who is the running user at this boundary?" next to every async/pause/orchestration boundary.
- Review Get Records and Update Records after each new-transaction boundary for sharing safety. A record visible to the initiator may not be visible to the Automated Process user.
- For sensitive queries on resumed interviews, consider re-checking FLS and sharing explicitly in the flow logic, or switch to Orchestration for an explicit per-step user.

## Observability (cross-cutting)

Transactional boundaries are also observability boundaries.

- Debug Logs capture one transaction each. A scheduled path failure is in a DIFFERENT debug log than the originating save. The team must know WHERE to look.
- Orchestration Work Guide is the only UI that stitches cross-step state together.
- Platform Event publishing and subscription have separate monitoring (Event Monitoring, Pub/Sub API telemetry).

Recommendation: pair every new-transaction boundary with a durable log record (custom error-log object, ApplicationLogger template in `templates/apex/`) so that cross-transaction failures are discoverable without debug logs.

## Related Frameworks

- `templates/apex/ApplicationLogger.cls` — canonical logger for cross-transaction fault capture.
- `standards/decision-trees/async-selection.md` — the tree for picking the right async mechanism.
- `skills/flow/fault-handling/SKILL.md` — fault connector and FaultMessage conventions.

## Official Sources Used

- Salesforce Help — "Flow Triggers: Before Save vs. After Save": https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_types.htm
- Salesforce Help — "Scheduled Paths in Record-Triggered Flows": https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_scheduled_path.htm
- Salesforce Developer Documentation — "Execution Governors and Limits": https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_gov_limits.htm
- Salesforce Help — "Pause Element" (Flow Builder reference): https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_pause.htm
- Salesforce Help — "Flow Orchestration Overview": https://help.salesforce.com/s/articleView?id=sf.orchestrator_overview.htm
- Salesforce Architects — "Well-Architected: Resilient": https://architect.salesforce.com/well-architected/trusted/resilient
- Salesforce Architects — "Well-Architected: Performant": https://architect.salesforce.com/well-architected/trusted/performant
- Salesforce Architects — "Well-Architected: Secure": https://architect.salesforce.com/well-architected/trusted/secure
