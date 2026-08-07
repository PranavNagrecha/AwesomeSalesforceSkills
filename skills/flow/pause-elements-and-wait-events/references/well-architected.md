# Well-Architected Notes — Pause Elements and Wait Events

## Relevant Pillars

- **Reliability** — The primary pillar for this skill. Paused interviews must resume correctly even under failure conditions (faulting on resume, flow version changes, org limit pressure). Fault paths, timeout watchdog alarms, and version activation discipline are reliability controls. An interview that silently never resumes is a business process failure.
- **Performance** — Paused interviews consume zero CPU and governor limits while suspended, which is a performance advantage over polling patterns. However, the Alarm minimum fire time (~15 minutes) and platform event delivery latency (seconds, but asynchronous) must be understood when designing time-sensitive flows.
- **Operational Excellence** — Long-running suspended interviews must be observable and manageable. Designs that do not include monitoring hooks, timeout bounds, or cleanup routines become operational liabilities as volumes grow. The admin UI (Paused and Failed Flow Interviews) is the primary observability surface.
- **Scalability** — The org-wide concurrent paused interview limit is the primary scalability constraint. High-volume use cases must account for this ceiling. Designs that use Pause elements for bulk-triggered scenarios (e.g., mass record creates) can exhaust the pool and block all other flows.

## Architectural Tradeoffs

### Pause Element vs. Scheduled Path

Scheduled Paths on record-triggered flow Start elements are simpler, do not consume async interview storage, and do not require an auto-launched flow. They are correct for single-point future execution with no state continuity requirement. Pause elements are correct when state must be preserved across time windows, when multiple future time points must be handled in one interview, or when the resume trigger is an external event rather than a time offset. Choosing a Pause element for a use case a scheduled path covers adds unnecessary complexity and storage cost.

### Pause Element vs. Apex Scheduled Jobs

For very high-volume time-based processing (thousands of records), Apex scheduled jobs or Batchable Apex are more scalable than per-record paused flow interviews. Each paused interview is a separate persisted unit; Apex batch processes can handle bulk volumes in a single execution context. Pause elements offer faster implementation, no code, and declarative readability — the tradeoff is lower volume ceiling.

### Platform Event Resume vs. Polling

Platform event resume reacts within seconds and consumes no governor limits during the wait. Polling (via scheduled flows or Apex) wastes query limits and introduces latency up to the polling interval. The tradeoff is that platform event-driven designs require the external system to publish a well-structured event and require careful resume condition design to avoid cross-contamination. Polling is simpler to implement but operationally expensive at scale.

## Anti-Patterns

1. **Using Pause elements in record-triggered flows instead of scheduled paths** — Record-triggered flows have Scheduled Paths built into the Start element specifically for single-point future execution. Adding an auto-launched sub-flow with a Pause element to achieve the same outcome is an over-engineered solution that adds async interview storage cost and deployment complexity. Reserve Pause elements for multi-window or event-driven scenarios.

2. **No timeout watchdog on Platform Event waits** — A Platform Event wait event with no companion Alarm wait event can result in interviews paused indefinitely if the expected event is never published (external system failure, misconfigured filter, event message lost). Since Spring '24 there is no interview-count limit to backstop this, so nothing fails loudly: the interviews simply accumulate, consume Data Storage forever, and cannot be cleaned up without admin intervention. Removing the limit made this anti-pattern quieter, not safer. Every Platform Event wait event should have a companion Alarm wait event that fires at a defined maximum wait duration and routes to an error-handling path.

3. **Deploying high-volume Pause-based flows without storage validation** — When a flow uses a Pause element and is triggered by bulk operations (e.g., a data migration that creates 10,000 records), every record creates a paused interview simultaneously. Do **not** reject such a design on interview-count grounds: the per-org cap was removed in Spring '24, and even before removal it was 50,000, so 10,000 concurrent interviews was always within budget. The real questions are Data Storage consumption, whether every interview has a resume path that actually fires, and what the resume storm does to limits when 10,000 interviews wake at once. Validate those, not a count ceiling.

## Official Sources Used

- Flow Elements: Wait (Pause) — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_pause.htm&type=5
- Flow Wait Conditions — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_pause_conditions.htm&type=5
- Flow Resume Event: Platform Event Message — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_pause_events_platform.htm&type=5
- Paused Flow Interview Considerations — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_design_pause.htm&type=5
- General Flow Limits — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_limit.htm&type=5
- Wait for Conditions Element — https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_wait_for_conditions.htm&type=5
- Have Unlimited Paused and Waiting Flows (Spring '24 release notes, release=248) — https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_mgmt_remove_paused_interview_limit.htm&language=en_US&release=248&type=5
- Paused Flow Interview Considerations — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_design_pause.htm&language=en_US&type=5
- Flow Usage-Based Entitlements (the pre-removal 50,000 pending-schedules-and-paused-interviews allocation and the "Your org has too many waiting flow interviews" exception) — https://help.salesforce.com/s/articleView?id=platform.flow_considerations_usage_entitlements.htm&language=en_US&type=5
- Sample Flow That Pauses Until a Platform Event Message Is Received — https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_wait_examples_platformevent.htm&type=5
- Salesforce Well-Architected: Reliability — https://architect.salesforce.com/well-architected/reliable
- Salesforce Well-Architected: Performance — https://architect.salesforce.com/well-architected/performant
