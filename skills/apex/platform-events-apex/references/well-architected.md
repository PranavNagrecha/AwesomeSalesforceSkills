# Well-Architected Notes — Platform Events Apex

## Relevant Pillars

### Scalability

Platform Events are a decoupling mechanism that lets producers and consumers evolve independently. They are valuable when synchronous transaction coupling would otherwise limit scale.

Tag findings as Scalability when:
- a synchronous integration should be broken into published work
- events are published one-at-a-time inside loops
- consumers are tightly coupled to publisher transaction timing

### Reliability

Event-driven systems are only reliable when publication failures, subscriber failures, and replay expectations are all visible.

Tag findings as Reliability when:
- publish results are ignored
- subscriber processing is heavy and fragile inside the trigger
- external replay requirements are undocumented

## Architectural Tradeoffs

- **Platform Events vs CDC:** CDC is lower-friction for record-change propagation; Platform Events are better for explicit business messages.
- **Thin subscriber trigger vs rich subscriber trigger:** thin triggers are easier to operate and test.
- **Immediate consistency vs eventual consistency:** events reduce coupling but require consumers to tolerate delayed processing.

## Anti-Patterns

1. **Custom event used where CDC already expresses the need** — duplication without architectural gain.
2. **Subscriber trigger doing heavyweight orchestration inline** — brittle and hard to retry.
3. **No publication monitoring** — event-driven failures become invisible until downstream systems complain.

## Official Sources Used

- Apex Reference Guide, `EventBus` Class (`apexrefguide` L214410–214560) — `publish(SObject)` / `publish(List<SObject>)` / `publish(events, callback)` signatures, the `Database.SaveResult` contract, and the statement that `EventBus.publish()` does not throw for an unsuccessful publish (supports "Publication Success Is Not No Exception Thrown" in SKILL.md and the `EventBus.publish` Never Throws gotcha). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apex_ref_guide.pdf
- Apex Reference Guide, `EventBus` Namespace (`apexrefguide` L157140–157900) — `EventPublishSuccessCallback` / `EventPublishFailureCallback` / `SuccessResult` / `FailureResult` / `TestBroker.deliver()` / `TestBroker.fail()` / `TriggerContext.retries`, `lastError`, `setResumeCheckpoint`, `getResumeCheckpoint`, and `InvalidReplayIdException` (supports Artifacts 3, 4 and 6 in references/code-examples.md and the checkpoint gotcha).
- Apex Developer Guide, Apex Transactions and Governor Limits (`apexdev` L19598, L19635, L19862) — the 150-call `EventBus.publish` limit for publish-immediately events, publish-after-commit counting as a DML statement, and the 2,000-event trigger batch size for platform events and CDC (supports the two-meter gotcha and the batch-size gotcha). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide, `CustomObject` (`api_meta` L42091–42097, L42206–42230) — `eventType` (`HighVolume`, deprecated `StandardVolume`) and `publishBehavior` (`PublishAfterCommit` / `PublishImmediately`, default `PublishImmediately`) (supports Artifact 1 and the default-publish-behaviour gotcha). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide, `PlatformEventSubscriberConfig` (`api_meta` L96385–96520) — `batchSize` range and default, `user` and the Automated Process default, `numPartitions` / `partitionKey`, the sample definition and the dependency-ordered `package.xml` (supports Artifact 5, Artifact 7 and the deploy-order table).
- Metadata API Developer Guide, `PlatformEventMigration` (`api_meta` L96225–96384) and `ManagedEventSubscription` (`api_meta` L86600–86640) — standard-to-high-volume migration preconditions, and the `LATEST` / `EARLIEST` replay presets with the "less than 72 hours old" retention wording (supports the `StandardVolume` gotcha and the retention correction in references/llm-anti-patterns.md).
- Object Reference for the Salesforce Platform, `EventBusSubscriber` (`object_reference` L131272–131430) — `Status` values including the `Error` state reached by exceeding the `RetryableException` retry budget, the "fewer than nine" recommendation, `Retries`, `LastError`, `LastProcessed` / `LastPublished` replacing `Position` / `Tip` at API 66.0, and `Tip` always -1 for high-volume events (supports the retry-budget gotcha and the verification SOQL). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce Developer Limits and Allocations Quick Reference (`salesforce_app_limits_cheatsheet` L102, L152, L417, L1244–1253) — the same publish limits as the Apex guide; its "Platform Event Allocations" section is a heading with no numeric values, which is why event-retention and delivery allocations carry UNVERIFIED markers in this package.
