# Gotchas — Platform Events Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `EventBus.publish` Needs Result Handling

**What happens:** The publish call is made and nobody checks the returned result, so failures disappear into the background.

**When it occurs:** Teams treat event publication like `System.enqueueJob()` with no follow-up.

**How to avoid:** Inspect the returned save results and route failures into a real logging or alerting path.

---

## Apex Event Triggers Are Not External Replay Managers

**What happens:** Architects try to solve external consumer replay recovery inside Apex trigger code.

**When it occurs:** Platform Events and Pub/Sub API responsibilities are blurred.

**How to avoid:** Keep durable external subscriber replay state in middleware or the Pub/Sub client. An Apex trigger has its own, narrower replay control — `EventBus.TriggerContext.setResumeCheckpoint()` over the events in the current batch — and that is not a substitute for an external consumer's committed Replay ID.

---

## Publishing In Loops Creates Operational Noise

**What happens:** One event is published per record inside a loop.

**When it occurs:** Developers port synchronous trigger habits directly into event publication code.

**How to avoid:** Build a list of events and publish once. It is simpler to monitor and safer at scale.

---

## CDC And Platform Events Sound Similar But Drive Different Contracts

**What happens:** Consumers are built against a custom event when they really need row-change semantics, or vice versa.

**When it occurs:** There is no explicit decision about business event versus data-change event.

**How to avoid:** Make the decision rule explicit during design and document why CDC or Platform Events was chosen.

---

## The Default Publish Behaviour Survives A Rollback — And Spends A Different Meter

**What happens:** A service publishes an event, the transaction then hits a validation rule and rolls back, and the downstream system fulfils an order that does not exist. Separately, a batch that publishes 200 times per transaction never trips the DML limit and the team concludes publishing is free.

**When it occurs:** `publishBehavior` was omitted from the `__e` object definition. *"If you don't specify this field, the default value used is `PublishImmediately`"* (`api_meta` L42228–42229), and `PublishImmediately` means *"The event message is published when the publish call executes, regardless of whether the transaction succeeds"* (`api_meta` L42225–42227). Only `PublishAfterCommit` is *"published only after a transaction commits successfully. If the transaction fails the event message isn't published"* (`api_meta` L42222–42224).

The two behaviours are also metered separately. `PublishAfterCommit` calls count as one DML statement each (`apexdev` L19635, `apexrefguide` L214525–214527). `PublishImmediately` calls do **not** touch the DML meter — they draw on a *"Maximum number of `EventBus.publish` calls for platform events configured to publish immediately: 150 / 150"* (`apexdev` L19598), readable at runtime with `Limits.getPublishImmediateDML()` and `Limits.getLimitPublishImmediateDML()` (`apexrefguide` L220763–220780).

**How to avoid:** Write `<publishBehavior>` explicitly in every `__e` object file. Choose `PublishAfterCommit` for any event that asserts a committed fact ("Order Approved"), and `PublishImmediately` only for signals that must survive the rollback — a failure or audit event whose whole point is to escape a doomed transaction. Then instrument the right meter: `Limits.getDMLStatements()` for after-commit, `Limits.getPublishImmediateDML()` for immediate.

---

## `EventBus.publish` Never Throws For A Rejected Event

**What happens:** A publish is wrapped in `try/catch`, the catch block never fires, and the team believes every event shipped. Some of them were rejected by the bus.

**When it occurs:** Any time the return value is discarded. *"`EventBus.publish()` can publish some passed-in events, even when other events can't be published due to errors. The `EventBus.publish()` method doesn't throw exceptions caused by an unsuccessful publish operation. It's similar in behavior to the Apex `Database.insert` method when called with the partial success option."* (`apexrefguide` L214561–214565). The one exception is a type error: publishing an sObject that is not a platform event *"returns a `System.UnexpectedException`"* (`apexrefguide` L214569–214571).

**How to avoid:** Capture `List<Database.SaveResult>` and loop it by index against the event list you passed in — the results are positional, and that index is the only link back to the record the event described. Do not use `SaveResult.getId()` as the message identity: *"The Id field value isn't included in the event message delivered to subscribers. It isn't used to identify an event message, and isn't always unique."* (`apexrefguide` L214565–214567).

---

## `isSuccess() == true` Only Means "Queued"

**What happens:** The publisher logs a clean run, and the message never reaches a subscriber. Nothing in the publishing transaction ever learns this.

**When it occurs:** Publishing is treated as synchronous. *"If the `isSuccess()` method returns true, the publish request is queued in Salesforce and the event message is published asynchronously."* (`apexrefguide` L214510–214513). The final asynchronous outcome arrives only through an Apex publish callback: `EventBus.EventPublishFailureCallback.onFailure()` is called *"when the final result of the asynchronous publish operation becomes available"* (`apexrefguide` L157451–157455).

**How to avoid:** For any event whose loss is a business incident, publish with the two-argument form `EventBus.publish(events, callback)` (`apexrefguide` L214727–214729) and implement `onFailure`. Correlate the callback back to your data by pre-populating `EventUuid` with `SObjectType.newSObject(recordTypeId, loadDefaults)` — documented for exactly this purpose (`apexrefguide` L194227–194229) — and by reading `EventBus.getOperationId(saveResult)`, which returns `null` when the request failed to be enqueued synchronously (`apexrefguide` L214482–214486).

---

## API 67.0 Silently Moves Publishing Into User Mode

**What happens:** A class that published fine is bumped to a newer API version and starts failing for some running users, with no code change.

**When it occurs:** On the `-meta.xml` version bump. *"Prior to API version 67.0, this method ran with `AccessLevel.SYSTEM_MODE` access. Starting with API version 67.0, it runs with `AccessLevel.USER_MODE` access. The user will be the automated process user unless you set a user using the `PlatformEventSubscriberConfig`."* (`apexrefguide` L214529–214531, repeated for every `publish` overload). Under user mode the running user needs create access to the event; under system mode it did not.

**How to avoid:** When bumping a publisher class to 67.0 or later, grant Create (and Read) on the `__e` object, in the permission set of every publishing persona, or decide deliberately to bypass with `EventBus.publishWithAccessLevel(events, AccessLevel.SYSTEM_MODE)` (`apexrefguide` L214745–214753) and record why — a `without sharing` class does not help here, since sharing and object/field permissions are separate mechanisms; only user mode versus system mode decides whether Create on the event is checked. Note `publishWithAccessLevel`'s `accesslevel` parameter *"Can't be null"* (`apexrefguide` L214708–214711).

**Production symptom (S2-F-13, `.sfskills/builds/tier2-webhook/reports/MOCK-DEPLOY-M1.md` run 8):** a validate-only deploy with tests running as a Standard User holding the build's permission set rejected every `EventBus.publish` of a custom `Tier2_Escalation__e`, captured into the service's own failure log as a `Database.SaveResult` error reading `"Tier2_Escalation__e publish rejected: Access to entity 'Tier2_Escalation__e' denied"`. Neither the org's shipped permission set nor any other in the deployment granted Create on the event. The Queueable the publish was meant to trigger downstream still enqueued regardless — a publish rejection does not stop unrelated code in the same method — so the failure mode in production is a spurious failure-log row per escalation and an event that never reaches any subscriber, silently, for every subscriber, until someone reads the failure log. General grounding in the offline corpus for user-mode object-permission enforcement: *"Apex runs in user mode by default, which means that user permissions on objects and field-level security are respected. A user cannot run code that tries to access fields or objects that are hidden from the user."* (`apexdev` L11735-11737); *"Apex generally runs in user context by default, meaning that the current user's permissions and field-level security (FLS) are enforced during code execution. To ignore the FLS and object permissions of the current user, you must explicitly set a database operation or query to run in system mode."* (`apexdev` L11760-11763). UNVERIFIED (2026-09-12): the platform-event-specific sentence "publishing an event requires Create permission on the event object" is not stated verbatim in the Apex Developer Guide or in `api_meta.txt` — neither file discusses object permissions on `__e` objects by name. It is consistent with, and already carried above by, the `apexrefguide` L214529–214531 citation on this same gotcha; the Platform Events Developer Guide, which would state the publish-specific rule directly, is not in the offline corpus and its host cannot be fetched.

---

## The Subscriber Trigger's Default Batch Is 2,000, Not 200

**What happens:** A subscriber written like an ordinary trigger blows a governor limit as soon as event volume rises, and every event in the failed batch is retried into the same wall.

**When it occurs:** The trigger batch size for platform events is not the standard 200. *"The Apex trigger batch size for platform events and Change Data Capture events is 2,000."* (`apexdev` L19862, footnote to the trigger batch size row). `PlatformEventSubscriberConfig.batchSize` accepts *"from 1 through 2,000 ... The default batch size is 2,000 for platform event triggers"* (`api_meta` L96412–96417).

**How to avoid:** Size the handler for 2,000, or lower `batchSize` deliberately in a `PlatformEventSubscriberConfig` — but not to 1: *"We don't recommend setting the batch size to 1 to process one event at a time. Small batch sizes can slow down the processing of event messages."* (`api_meta` L96416–96419). For CPU-heavy work, chunk inside the handler and checkpoint per chunk rather than shrinking the batch. Depth on tuning lives in `apex/apex-event-bus-subscriber`.

---

## Exceeding The Retry Budget Stops The Subscription Entirely

**What happens:** A subscriber throws `EventBus.RetryableException` on every attempt for a failure that is not actually transient. The subscription eventually stops receiving events — including the healthy ones behind it — and nobody notices until a downstream system reports a gap.

**When it occurs:** `EventBusSubscriber.Status` reaches `Error`: *"The subscriber was disconnected and stopped receiving published events. A trigger reaches this state when it exceeds the number of maximum retries with the `EventBus.RetryableException`. Trigger assertion failures and unhandled exceptions don't cause the error state. We recommend limiting the retries to fewer than nine times to avoid reaching this state. When you fix and save the trigger, or for a managed package trigger, if you redeploy the package, the trigger resumes automatically from the tip, starting from new events."* (`object_reference` L131382–131390). Resuming "from the tip" means the backlog that accumulated while it was in `Error` is skipped, not replayed.

**How to avoid:** Guard every throw with the retry count: `EventBus.TriggerContext.currentContext().retries` is *"The number of times the trigger was retried due to throwing the `EventBus.RetryableException`"* (`apexrefguide` L157805–157810). Cap below nine, and on exhaustion log and consume rather than throwing again. Classify the failure first — only retry things like `StatusCode.UNABLE_TO_LOCK_ROW`; a missing parent record or a malformed payload will fail identically nine times. Alert on `SELECT Status, Retries, LastError FROM EventBusSubscriber WHERE Topic = '<Event>__e'`.

---

## `setResumeCheckpoint` Rejects Any Replay ID Outside The Current Batch

**What happens:** A handler stores the last processed `ReplayId` in a static or a custom setting, passes it to `setResumeCheckpoint()` on the next invocation, and the trigger throws.

**When it occurs:** *"The method throws an `EventBus.InvalidReplayIdException` if the supplied Replay ID is not valid — the replay ID is not in the current trigger batch of events, in the `Trigger.new` list."* (`apexrefguide` L157888–157892). The checkpoint is a within-invocation bookmark, not a durable cursor: *"When the trigger stops execution before all events in `Trigger.New` are processed, either because of an uncaught exception or intentionally, the trigger is invoked again. The new execution starts with the event message in the stream after the one with the checkpointed Replay ID."* (`apexrefguide` L157866–157874).

**How to avoid:** Only ever pass a `ReplayId` taken from an event in the batch you are currently handling, and only after that event's work has actually been done — the guide's own snippet is `EventBus.TriggerContext.currentContext().setResumeCheckpoint(event.replayId);` (`apexrefguide` L157895–157896). Checkpointing before the work is the bug that looks like it works: the trigger fails, resumes past the checkpoint, and the events silently never get processed.

UNVERIFIED (2026-09-05): whether a checkpoint set before an `EventBus.RetryableException` is honoured on the retry (so the retry resumes past it) or discarded (so the retry replays the whole batch) is not stated in the Apex Reference Guide or the Apex Developer Guide. It is described in the Platform Events Developer Guide, which is not in the offline corpus and whose host cannot be fetched. Do not rely on combining the two mechanisms in the same code path until you confirm it; use one or the other per handler.

---

## Delivered Events Are Not Rows You Can Query Back

**What happens:** Someone writes `SELECT Id FROM Order_Approved__e` to reconcile what was published, or tries to `update` an event in the subscriber trigger.

**When it occurs:** The `__e` type is treated as an sObject with a table behind it. The message is a stream entry, not a record: the `Id` on `Database.SaveResult` *"isn't included in the event message delivered to subscribers ... and isn't always unique"* (`apexrefguide` L214565–214567), and the durable identity is `EventUuid` plus the stream position `ReplayId`. The event bus retains messages for a bounded window — the `EventSubscriptionReplayPreset` `EARLIEST` option *"sends new events and any other events less than 72 hours old"* (`api_meta` L86612–86616), and a committed Replay ID *"can be invalid if it's older than the event retention window"* (`api_meta` L86619–86622).

**How to avoid:** Reconcile against your own durable artifacts — the publisher's log rows and the subscriber's idempotency receipts (`Processed_Event__c` in `references/code-examples.md`) — not against the event object. Persist `EventUuid` at consumption time; it is the value the publish callbacks hand back (`EventBus.SuccessResult.getEventUuids()` / `FailureResult.getEventUuids()`, `apexrefguide` L157596–157650), so it is the one key that joins publisher and subscriber records.

UNVERIFIED (2026-09-05): the exact retention window per event type (and whether standard-volume and high-volume differ) is stated only in the Platform Events Developer Guide's allocations page. The App Limits cheat sheet in the corpus lists "Platform Event Allocations" as a section heading with no values (`salesforce_app_limits_cheatsheet` L1244–1253). The 72-hour figure above is the Metadata API's own wording for the `EARLIEST` replay preset, which is the only retention number in the corpus.

---

## `StandardVolume` Is A Trap In Older Object Files

**What happens:** A retrieved `__e` definition from an older org is redeployed and the deployment errors, or an event created years ago behaves differently from a new one.

**When it occurs:** `CustomObject.eventType` has two values: *"`HighVolume` — For a high-volume platform event. `StandardVolume` — Deprecated. Creating a platform event with this event type is supported and returns an error."* (`api_meta` L42091–42097). Existing standard-volume events keep working but need migrating.

**How to avoid:** New events always get `<eventType>HighVolume</eventType>`. Migrate existing standard-volume events with the `PlatformEventMigration` metadata type (`api_meta` L96225–96330), and read its precondition first: *"Before starting a migration, ensure all publish activity has stopped and all subscribers, including triggers and flows, are done processing ... While the migration is running, publishes won't work and you'll be unable to create new triggers or flows until the migration finishes."* (`api_meta` L96293–96296, L96380–96384). That is an outage window, not a background task.

---

## The Subscriber Runs As Automated Process Unless You Say Otherwise

**What happens:** Records created by the subscriber are owned by a system entity, the trigger cannot send email, and the debug logs the team enabled for the integration user are empty during the incident they are trying to debug.

**When it occurs:** No `PlatformEventSubscriberConfig` exists for the trigger. *"By default, the platform event trigger runs as the Automated Process entity."* Setting `user` gives you: *"Records are created or modified as this user. Records with `OwnerId` fields have their `OwnerId` fields populated to this user when created or modified. Debug logs for the trigger execution are created by this user. You can send email from the trigger, which isn't supported with the default Automated Process user."* (`api_meta` L96453–96462).

**How to avoid:** Ship a `PlatformEventSubscriberConfig` alongside every `__e` trigger that writes records, names an owner, sends notifications, or will ever need a debug log. Deploy it last — it *"references an Apex trigger, which depends on a platform event ... If the referenced trigger and platform event don't exist in the org, include their definitions in the package. Otherwise, the deployment fails."* (`api_meta` L96482–96499). The XML is in `references/code-examples.md`, Artifact 5.
