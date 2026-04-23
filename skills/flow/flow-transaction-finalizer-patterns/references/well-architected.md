# Well-Architected Notes — Flow Transaction Finalizer Patterns

## Relevant Pillars

- **Reliability** — "commit before notify" is the defining pattern for
  trustworthy downstream effects.
- **Operational Excellence** — finalizers make success/failure observable.
- **Scalability** — async handoff keeps critical-path transactions small.

## Architectural Tradeoffs

- **Flow-native vs Apex:** Flow-native (scheduled path, platform event)
  keeps ownership with admins; Apex Queueable with Finalizer gives
  strongest durability but requires dev skills.
- **Same-txn speed vs post-commit safety:** pre-commit steps are fast but
  risk firing on rolled-back data; post-commit is slower but correct.
- **Platform Event vs Queueable:** events suit fan-out; queueables suit
  chained, multi-step work with explicit result handling.

## Official Sources Used

- Flow Scheduled Paths — https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule.htm
- Publish-After-Commit — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_publish_after_commit.htm
- Queueable Finalizer — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueable_finalizer.htm
