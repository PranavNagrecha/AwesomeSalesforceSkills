# Well-Architected Notes — Event Relay Configuration

## Relevant Pillars

- **Reliability** — Primary pillar. Event Relay removes the two things that
  actually break streaming integrations: a process you have to host and a replay
  position you have to checkpoint. Salesforce owns both. What it does *not* remove
  is at-least-once delivery semantics, an unordered stream, and a recovery path
  whose fallback (`relayOption`) can replay up to three days of the event bus. The
  reliability work moves from "keep the consumer alive" to "make the consumer
  idempotent on a business key," which is a better place for it to live.

- **Operational Excellence** — The relay is a two-party asset. Half of its
  configuration is Salesforce metadata under source control; the other half — the
  partner event source association, the event bus, the rule, and the IAM
  credential — lives in an AWS account owned by a different team, is not in your
  repository, and changes without your deployment pipeline noticing. Every runbook
  for this integration is therefore a joint runbook, and the credential has an
  expiry date that nothing in Salesforce will warn you about.

- **Security** — Authentication is AWS Signature Version 4 through an
  `ExternalCredential`/`NamedCredential` pair, so no key material sits in the
  deployable artifact. The two-sided handshake means Salesforce never holds
  standing write access to an arbitrary EventBridge bus: the AWS account owner
  opts in by associating a bus with the pending partner event source. Deploying the
  configuration requires Customize Application; reading it requires View Setup and
  Configuration.

- **Performance** — The cost is not compute, it is allocation. Every relayed event
  counts against the org's daily event delivery allocation, per subscribed client,
  and that allocation is shared between high-volume platform events and Change Data
  Capture events. A relay added alongside existing subscribers is additive, not
  shared.

## Architectural Trade-offs

**Event Relay vs a Pub/Sub API consumer.** The relay gives up control and gains
operations. You cannot filter, transform, enrich, or batch in flight; whatever the
channel carries goes to EventBridge as-is, and all shaping happens in an
EventBridge rule or the target. A Pub/Sub API consumer can do all of that and gives
you explicit replay-id control, at the cost of a long-lived process, its
checkpointing, its deployment, and its on-call rotation. Choose the relay when the
transformation belongs on the AWS side anyway — which is most of the time when the
target is Lambda or Step Functions.

**Event Relay vs an Apex callout on a trigger.** An Apex trigger on the platform
event can call out directly and needs no AWS partner source at all. It also
consumes Apex governor limits, has to handle retries and backoff itself, and
couples the Salesforce transaction to the availability of an HTTP endpoint. Notably,
Apex trigger subscribers do *not* count against the event delivery allocation
("Published event messages that are delivered to non-API subscribers, such as Apex
triggers, flows, and Process Builder processes, don't count against the delivery
allocation"), so for a low-volume, high-value stream the Apex path can be cheaper in
allocation terms and more expensive in everything else.

**`LATEST` vs `EARLIEST` recovery.** This is a trade between duplicate processing
and gap risk, and it is decided by the *downstream* system's idempotency, not by a
preference for completeness. `EARLIEST` is safe when the EventBridge target upserts
on a business key and merely noisy when it replays three days. It is an incident
when the target appends rows, sends notifications, or moves money. Where neither
option is acceptable, the answer is not a third relay setting — it is a
reconciliation job that compares state between the two systems on a schedule.

**One relay per event type.** The platform forces this: a channel holds exactly one
event type. The consequence is that an integration spanning custom events and CDC
is at least two relays, two channels, and two partner event sources, each with its
own state, its own feedback row, and its own AWS-side association. Budget for that
multiplicity at design time rather than discovering it during deployment.

**Where the transformation lives.** Because the relay cannot transform, the shape
of the platform event *is* the contract with AWS. Adding a field to the event
changes what every EventBridge consumer sees. Design the event payload as a public
interface — include the natural key the consumer will deduplicate on — rather than
as an internal notification you can freely reshape.

## Anti-Patterns

1. **Deploying with `<state>RUN</state>`.** The only valid create-time state is
   `STOP`, and the relay cannot usefully run before the AWS side has associated a
   bus. Model activation as a separate post-deploy step.

2. **Treating the Salesforce metadata as the whole integration.** A pending partner
   event source with no associated bus produces silent success on the Salesforce
   side and zero events on the AWS side. Every plan needs an AWS-side owner and an
   AWS-side step.

3. **Choosing `EARLIEST` for safety.** It replays up to the full three-day event
   bus retention, not "what you missed," and it only engages in the rare case where
   the relay cannot resume from its last position at all.

4. **Stopping a relay during an incident.** `STOPPED` deletes
   `LastRelayedEventTime` and the error fields — the exact diagnostics you were
   about to read — and drops everything published while stopped. `PAUSED` preserves
   both. Write "pause, never stop" into the runbook.

5. **Alerting on `Status` alone.** `ERROR` self-clears, and a wedged relay reports
   `RUNNING`. Alarm on `LastRelayedEventTime` staleness against the stream's known
   cadence.

6. **Presenting the relay as free.** It is a subscribed client and consumes the
   daily event delivery allocation per client. Baseline with
   `PlatformEventUsageMetric` before switching it on, and retire the subscriber it
   replaces in the same change.

7. **Building a consumer that assumes exactly-once, ordered delivery.** The relay
   inherits the event bus's at-least-once, unordered semantics and adds its own
   recovery behaviour on top. Idempotency on a payload-carried business key is the
   only durable answer.

8. **Letting the region drift between the two places it is configured.** The
   `AwsRegion` `AuthParameter` on the external credential sets the SigV4 signing
   scope; the named credential's `DefaultEndpoint` sets the host. A mismatch
   authenticates nothing and is invisible in the metadata diff.

## Official Sources Used

- Metadata API Developer Guide — EventRelayConfig (`destinationResourceName` with `callout:` prefix, `eventChannel`, `relayOption` JSON contract, `state` enum and create-time restriction, updatable-fields rule, Customize Application requirement, sample XML) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_eventrelayconfig.htm
- Metadata API Developer Guide — PlatformEventChannel (`channelType` / `eventType` valid pairs, one-type-per-channel rule, `__chn` suffix, Customize Application requirement) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_platformeventchannel.htm
- Metadata API Developer Guide — PlatformEventChannelMember — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_platformeventchannelmember.htm
- Metadata API Developer Guide — ExternalCredential (`AwsSv4` authentication protocol, `AuthParameter` with `AwsRegion` / `AwsService`, `AuthProtocolVariant` `AwsSv4_STS`, `AwsStsPrincipal`, sample XML) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_externalcredential.htm
- Metadata API Developer Guide — NamedCredential (`SecuredEndpoint` type, `DefaultEndpoint` / `DefaultAuth` parameters, sample XML) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_namedcredential.htm
- Object Reference for the Salesforce Platform — EventRelayConfig (read-only, View Setup and Configuration to query) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventrelayconfig.htm
- Object Reference for the Salesforce Platform — EventRelayFeedback (`Status` picklist semantics, `LastRelayedEventTime`, `RemoteResource` partner-source format, error fields) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_eventrelayfeedback.htm
- Platform Events Developer Guide — Default Platform Event Allocations for Event Publishing and Delivery, and Event Delivery Usage Combined for All Subscribers — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
- Platform Events Developer Guide — Monitor Platform Event Publishing and Delivery Usage (`PlatformEventUsageMetric`, Enhanced Usage Metrics in API 58.0 and later) — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_usage_metrics.htm
- Salesforce Developers — Event Relay — https://developer.salesforce.com/docs/platform/event-relay/overview
- Salesforce Well-Architected — Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

<!-- UNVERIFIED: the AWS-side navigation path "Amazon EventBridge console →
     Integration → Partner event sources" and the pending→active association
     step are AWS console behaviour, not Salesforce behaviour, and were not
     verified against docs.aws.amazon.com in this pass. The existence of the
     pending partner event source and its name format ARE verified, from
     EventRelayFeedback.RemoteResource. Confirm the AWS console labels before
     handing the runbook to an AWS admin. -->
<!-- UNVERIFIED: no maximum number of event relays per org was found in the
     Metadata API guide, the Object Reference, or the Platform Events Developer
     Guide's allocations chapter. If a cap exists it is not stated in those
     sources, so this package makes no claim about one. -->
