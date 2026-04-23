---
name: event-relay-configuration
description: "Use when forwarding Salesforce Platform Events or Change Data Capture to AWS EventBridge via Event Relay. Covers Named Credential + Connection setup, channel selection, event filter design, replay handling, retry/back-off, IAM, and monitoring. Does NOT cover consuming external events in Salesforce (see pub-sub-api or salesforce-connect)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "event relay aws eventbridge"
  - "forward platform events to aws"
  - "salesforce to eventbridge cdc"
  - "event relay setup"
  - "event relay retry"
tags:
  - integration
  - event-relay
  - pub-sub
  - aws
  - eventbridge
inputs:
  - Platform Events or CDC channel to forward
  - AWS account + region for EventBridge
  - Throughput and retry requirements
outputs:
  - Event Relay configuration (Named Credential, Connection, Relay Config)
  - IAM / permission design
  - Filter strategy
  - Monitoring and replay runbook
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Event Relay Configuration (Salesforce → AWS EventBridge)

## Purpose

Event Relay is the managed bridge from Salesforce Pub/Sub API to Amazon
EventBridge. It replaces the DIY pattern of "Apex callout to an AWS Lambda
in an after-insert trigger on a Platform Event" with a no-code, reliable,
at-least-once pipe. Teams that pick Event Relay without understanding IAM,
filters, replayId handling, and channel selection typically under-spec
reliability and over-spec cost. This skill codifies the decisions.

## When To Use

- Forwarding a Platform Event or CDC stream to AWS EventBridge for
  downstream consumers (Lambda, Step Functions, SQS, partners).
- Replacing Apex-to-SQS shims.
- Hybrid event bus where Salesforce is one producer among many.

## Recommended Workflow

1. **Confirm Event Relay fits.** If the target is not AWS, Event Relay is
   not the tool — consider Named Credential + Apex, or Pub/Sub API
   direct-consumer.
2. **Pick the channel.** Standard Platform Event, High-Volume Platform
   Event, or CDC channel. High-Volume is strongly preferred for relay.
3. **Create AWS Connection (Named Credential).** IAM role trust policy
   scoped to the Salesforce AWS account/region; least-privilege
   `events:PutEvents` on the target bus.
4. **Create the Event Relay Config.** Associate the channel with the
   Connection; configure replay from `LATEST`, `EARLIEST`, or specific
   replayId.
5. **Design the filter.** Event Relay supports filtering before relay —
   shrink what's forwarded to reduce downstream noise and cost.
6. **Monitor.** Event Relay emits metrics; wire them to your ops stack.
   Alert on consecutive failures and lag.
7. **Plan replay.** Document how to pause, change replayId, and resume
   without creating duplicates downstream.

## Channel Selection

| Channel | Use When | Notes |
|---|---|---|
| Platform Event (standard volume) | Low throughput, human-scale | Not ideal for relay; storage limits are tight |
| High-Volume Platform Event | Most relay use cases | 72-hour retention |
| Change Data Capture | Field-level change notifications | Consumer must tolerate deltas |

## IAM Design

- Trust: Salesforce AWS account principal with external id check.
- Permissions: `events:PutEvents` on the target bus only.
- Region pinning: Connection is region-specific.
- Rotate the external id per relay to avoid confused deputy.

## Filters

- Field-based SOQL-like filters on event payload.
- Always filter out test/QA events from prod relays.
- Avoid regex / deep JSON path; keep filters simple for performance.

## Replay / Resume

- `LATEST` (default): new events only.
- `EARLIEST`: all retained events — spikes load on resume.
- Specific replayId: safest for controlled resume after outage.
- Keep a watermark downstream so you can point relay to the right id.

## Reliability

- At-least-once delivery; consumers MUST be idempotent.
- Max 3 days retention upstream; if the relay is paused longer, events are
  lost.
- Event Relay auto-resumes on transient errors; persistent errors require
  manual intervention.

## Monitoring

- Salesforce Setup → Event Relay Configs shows state.
- AWS EventBridge metrics on the bus confirm receipt.
- Alert thresholds: lag > 5 min, failures > 0 for N consecutive windows.

## Anti-Patterns (see references/llm-anti-patterns.md)

- Use Event Relay with standard Platform Events at high volume.
- Forward every field of a CDC event without filtering.
- Assume "exactly-once" delivery.
- No replayId watermark.

## Official Sources Used

- Event Relay — https://help.salesforce.com/s/articleView?id=sf.event_relay.htm
- Pub/Sub API — https://developer.salesforce.com/docs/platform/pub-sub-api/overview
- Platform Events High-Volume — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_high_volume.htm
- AWS EventBridge — https://docs.aws.amazon.com/eventbridge/
