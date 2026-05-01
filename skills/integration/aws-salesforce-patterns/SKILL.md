---
name: aws-salesforce-patterns
description: "AWS integration patterns for Salesforce — pick between Amazon AppFlow, Event Relay → EventBridge, Amazon S3 ingestion paths, and direct Apex → Lambda callouts. Decision matrix + AppFlow deep dive (Salesforce as source / destination, OAuth Authorization-Code vs JWT, REST vs Bulk 2.0 API, 15 GB / run cap). NOT for the Event Relay setup details themselves (see integration/event-relay-configuration), NOT for MuleSoft, NOT for in-AWS architecture (Lambda code style, EventBridge bus topology)."
category: integration
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "salesforce to aws integration which service should I use"
  - "amazon appflow salesforce connector setup oauth"
  - "should I use appflow or event relay for cdc"
  - "salesforce s3 file integration ingestion paths"
  - "apex callout to aws lambda pattern"
  - "amazon connect service cloud voice integration"
tags:
  - aws
  - amazon-appflow
  - amazon-connect
  - amazon-s3
  - integration-pattern
  - decision-matrix
inputs:
  - "Direction of data flow (Salesforce → AWS, AWS → Salesforce, or bidirectional)"
  - "Latency requirement (real-time event, scheduled batch, on-demand)"
  - "Volume estimate (records / day; total bytes / run)"
  - "Whether Change Data Capture is already enabled in the source org"
outputs:
  - "Recommendation: which AWS integration service (AppFlow / Event Relay / S3 connector / Apex callout / Service Cloud Voice + Connect)"
  - "Auth model decision (OAuth Authorization Code vs JWT Bearer Flow vs IAM role)"
  - "Specific limits the chosen path will hit and how to budget around them"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-01
---

# AWS Salesforce Integration Patterns

When a Salesforce org needs to talk to AWS — read S3 files, sync records to a
data lake, react to a contact event with a Lambda, route a call through Amazon
Connect — there are five distinct managed paths and a sixth do-it-yourself
fallback. Picking the wrong one costs operational debt: a custom Apex callout
where AppFlow would have handled it, or AppFlow where Event Relay's at-least-once
durability is the actual requirement.

This skill is the **decision layer**. It will not re-derive the Event Relay
setup steps — that lives in `integration/event-relay-configuration`. It will not
explain MuleSoft (different decision tree).

---

## Before Starting

- Confirm whether the integration is **Salesforce → AWS**, **AWS → Salesforce**, or **bidirectional**. The first two have very different recommended paths; bidirectional usually means stitching two unidirectional flows.
- Check whether **Change Data Capture** is already enabled in the source org. AppFlow's event-driven trigger and Event Relay both need it — turning it on retroactively means a backfill plan.
- Note the **volume budget**. AppFlow caps at 15 GB / 7.5 M records per single run (Salesforce as source, ~2 KB / record); above that you split across flows or move to Event Relay + downstream batch.
- Get the **AWS account id and region** of the consuming services. Cross-region traffic costs and PrivateLink availability vary by region.

---

## Core Concepts

### The five managed AWS integration paths

1. **Amazon AppFlow (Salesforce connector)** — managed bidirectional sync. Salesforce can be source, destination, or both. Scheduled / on-demand / event-driven (CDC) triggers. AWS-managed connected app for OAuth, or bring-your-own connected app for JWT. *Right when you want declarative record-level sync without writing code.*
2. **Event Relay → Amazon EventBridge** — Salesforce streams Platform Events and CDC events to an EventBridge bus on your AWS account. At-least-once delivery, replay, 72-hour buffer. *Right for event-driven architectures where you want AWS-side fan-out (multiple Lambdas, Step Functions, etc.) reacting to Salesforce events.*
3. **Amazon S3 ingestion (Data Cloud connector or Files Connect)** — Data Cloud's S3 connector ingests structured files into Data Model Objects; Files Connect surfaces S3 as external file references inside Salesforce. *Right when the source of truth is files in a data lake.*
4. **Apex → Lambda callout** — Salesforce makes an HTTP request to a Lambda Function URL or API Gateway endpoint via Named Credential. *Right when you need a synchronous response inside a transaction (validation, enrichment, screen-flow callout).*
5. **Service Cloud Voice + Amazon Connect** — telephony integration. Amazon Connect routes the call; contact flows can invoke Lambda; Salesforce records the contact + transcript. *Right for voice channel; not a generic data-integration path.*

### Why the choice usually comes down to two axes

- **Direction × Latency.** Real-time event-driven from Salesforce → Event Relay. Scheduled batch in either direction → AppFlow. Synchronous request-response from Salesforce → Apex callout to Lambda. AWS-side data lake to Salesforce → S3 → Data Cloud or AppFlow source-from-S3.
- **Code budget.** AppFlow and Event Relay are zero-Apex. Lambda callouts and custom S3 work require code, error handling, monitoring, and tests on the Salesforce side.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| React to a Salesforce record change in AWS within seconds | **Event Relay** → EventBridge | At-least-once, replay, no Apex code. Configure once. |
| Nightly sync of accounts/contacts to Redshift | **AppFlow scheduled flow** | Field mapping in console, built-in retry, no Apex. |
| Bulk-import 50 M rows from S3 into Data Cloud | **Data Cloud S3 connector** | Native ingestion to DMOs; AppFlow caps below this volume. |
| Inline credit-check during opportunity save | **Apex callout** to Lambda Function URL | Need synchronous response inside transaction. |
| Phone agent answers a Service Cloud case | **Service Cloud Voice + Amazon Connect** | Telephony is the channel — generic data-integration paths don't apply. |
| Salesforce reads a small JSON file from S3 once a day | **Apex callout with Named Credential** OR a daily AppFlow flow | Either works; pick AppFlow if you want zero-code, Apex if you need the data inside a custom transaction. |
| Bidirectional account sync with a partner CRM hosted on AWS | **AppFlow source + AppFlow destination** | Two flows; let AppFlow handle field mapping in both directions. |
| Stream high-volume Platform Events to multiple AWS services | **Event Relay → EventBridge → fan-out** | EventBridge handles fan-out natively; one rule per target. |

---

## Common Patterns

### Pattern A — Event-driven sync via Event Relay

**When to use.** Real-time reaction in AWS to a Salesforce change. The
canonical example is "when an Opportunity moves to Closed-Won, kick off
Lambda + Step Functions to provision downstream resources."

**How it works.** Configure the Pub/Sub API channel, define a Relay Config
that points at the AWS event-bus partner-source, accept the source in
EventBridge, attach rules. Salesforce delivers events at-least-once with a
72-hour replay window. See `integration/event-relay-configuration` for the
full setup recipe.

**Why not the alternative.** A Platform-Event-trigger Apex class doing the
HTTP callout to AWS works but reinvents at-least-once delivery,
back-pressure handling, and retries. Event Relay is a managed equivalent.

### Pattern B — Scheduled batch sync via AppFlow

**When to use.** Hourly / nightly snapshot of Salesforce records to a data
lake, warehouse, or another SaaS. Or pull-from-S3 to upsert Salesforce
records by external id.

**How it works.** AppFlow connection (OAuth Authorization-Code is the
recommended starting auth — AWS manages the connected app on its side; JWT
when you need server-to-server with no interactive consent). Pick API
Preference (`Automatic` is right for most loads — REST under 1 M source
records, Bulk 2.0 above; `Bulk` only if compound fields are not in scope).
Cap is **15 GB or ~7.5 M records per single run**; split larger workloads.

**Why not the alternative.** Hand-rolled Apex Batch + ScheduledApex works
but needs monitoring, retry, and CDC-style change detection. AppFlow is
the managed version of all of that.

### Pattern C — Apex callout to Lambda

**When to use.** Inside a transaction you need an external decision —
fraud check, real-time enrichment, currency conversion. Synchronous,
small payload, sub-second latency required.

**How it works.** Define a Named Credential with the Lambda Function URL
(or API Gateway). Use `HttpClient` from `templates/apex/HttpClient.cls`.
Wrap with circuit-breaker + timeout. Test class uses `MockHttpResponseGenerator`
from `templates/apex/tests/`.

**Why not the alternative.** AppFlow is async. Event Relay is async. If
you need the answer before the trigger commits, only a callout works.
Use `templates/apex/HttpClient.cls` rather than reimplementing — there's
a documented pattern for retry, circuit-breaker, and observable logging.

---

## Recommended Workflow

1. **State the integration in one sentence.** Direction, latency, volume, payload type. If you can't fill all four, gather more context before recommending.
2. **Walk the Decision Guidance table top-to-bottom.** First match wins. If two rows match, the more constrained one (specific volume / specific latency) takes precedence over the generic one.
3. **Confirm the auth model.** OAuth Authorization-Code (default for AppFlow), JWT Bearer Flow (server-to-server, AppFlow or custom), Named Credential + IAM (Apex → Lambda), or Connected App + IAM Role for cross-account EventBridge (Event Relay).
4. **Budget against limits.** AppFlow 15 GB / run; Event Relay's 72-hour replay window; Apex callout governor (100 callouts / transaction, 120 s wall-clock per callout).
5. **Pick the related skill for implementation depth.** Cite it in the recommendation rather than re-deriving the setup.

---

## Review Checklist

- [ ] Direction (Salesforce → AWS, AWS → Salesforce, bidirectional) named explicitly in the recommendation.
- [ ] Latency requirement (real-time / scheduled / on-demand) named.
- [ ] Volume estimate compared against the path's hard limit.
- [ ] Auth model named (Authorization-Code / JWT / IAM / Named Credential).
- [ ] Cross-account / cross-region considerations called out where relevant.
- [ ] If recommending Event Relay, link to `integration/event-relay-configuration` for setup; do not re-derive.
- [ ] If recommending Apex callout, point at `templates/apex/HttpClient.cls` rather than inlining example code.

---

## Salesforce-Specific Gotchas

1. **AppFlow connection version-locks the Salesforce API.** A connection created on API v58 stays on v58 — newly added Salesforce fields *do not* auto-import on existing flows. Either rebuild the flow on a new connection or manually re-map. ([AWS AppFlow Salesforce connector docs](https://docs.aws.amazon.com/appflow/latest/userguide/salesforce.html))
2. **AppFlow Bulk API 2.0 silently drops compound fields.** Address (`BillingAddress`), Name (`Name` on a person account), and Geolocation compound fields are not transferable on the Bulk path. If you need them, force `Standard` API preference and accept the timeout risk on big runs. ([AWS docs](https://docs.aws.amazon.com/appflow/latest/userguide/salesforce.html))
3. **Event Relay does not push back to Salesforce.** It is one-way (Salesforce → AWS). Reverse direction needs EventBridge API Destinations writing to a Salesforce REST endpoint, configured separately on the AWS side.
4. **OAuth refresh-token policy must be "Valid until revoked"** when bringing your own connected app to AppFlow. The default "Refresh token is valid until first use" silently kills the flow as soon as the first refresh occurs.
5. **Apex callouts to a Lambda Function URL** count against the 100-callout governor and the 120-second wall-clock — bulkify them through a single batched payload rather than per-record.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Decision recommendation | One paragraph naming the chosen path, the auth model, the cited limit, and the linked skill for implementation depth. |
| Configuration checklist | Numbered list of the AWS-side and Salesforce-side prerequisites for the chosen path. |
| Risk register | Any limit the design will get within 50 % of, plus the mitigation. |

---

## Related Skills

- `integration/event-relay-configuration` — full Event Relay setup recipe; this skill points at it rather than duplicating.
- `apex/apex-callout-patterns` — Named Credential + circuit-breaker + bulkified callouts; cite when recommending Pattern C.
- `architect/hybrid-integration-architecture` — broader integration topology decisions; consult before picking an AWS path if MuleSoft / Heroku / private VPC are also options.
- `standards/decision-trees/integration-pattern-selection.md` — the master integration decision tree; AWS paths are one branch.
