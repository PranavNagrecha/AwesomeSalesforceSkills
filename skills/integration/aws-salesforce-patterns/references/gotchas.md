# Gotchas — AWS Salesforce Integration Patterns

Non-obvious behaviors that cause real production problems when integrating
Salesforce with AWS managed services.

---

## Gotcha 1: AppFlow connection version-locks the Salesforce API

**What happens.** When you create an AppFlow connection on Salesforce
API v58, the connection stays bound to v58 for its entire lifetime.
Newly added Salesforce fields (custom fields you build six months
later) do **not** show up on existing flows — they're filtered out by
the locked-in API version.

**When it occurs.** Six to twelve months after the initial AppFlow setup,
when someone adds a custom field and is surprised it's not flowing.

**How to avoid.** Create a fresh AppFlow connection when adding fields
that must flow, then re-point the flow at the new connection. Or
manually re-map the field. There is no in-place upgrade path. (Source:
[AWS AppFlow Salesforce connector docs](https://docs.aws.amazon.com/appflow/latest/userguide/salesforce.html)
under "API Version".)

---

## Gotcha 2: AppFlow Bulk API 2.0 silently drops compound fields

**What happens.** Compound fields — `Address` (BillingAddress, ShippingAddress
on Account/Contact), `Name` on Person Accounts, geolocation compound types
— are not transferable when AppFlow uses the Bulk API 2.0 path. The flow
runs successfully and reports records transferred; the compound columns
are simply absent in the destination.

**When it occurs.** API Preference is `Automatic` (which auto-switches to
Bulk 2.0 above ~1 M source records), or explicitly set to `Bulk`.

**How to avoid.** If compound fields are required, force API Preference
to `Standard` (REST) and accept the timeout risk on large runs — split
across multiple smaller flows by `LastModifiedDate` window if needed.
(Source: [AWS AppFlow Salesforce connector docs](https://docs.aws.amazon.com/appflow/latest/userguide/salesforce.html)
under "Compound Fields".)

---

## Gotcha 3: OAuth refresh-token policy default kills the flow on first refresh

**What happens.** When you bring your own connected app for AppFlow JWT
flow (or any non-AWS-managed OAuth), the connected-app default for
"Refresh Token Policy" is **"Refresh token is valid until first use"**.
The flow works on day 1 — then the first time the access token expires
and AppFlow refreshes, the refresh token is invalidated and every
subsequent run fails authentication.

**When it occurs.** 1–24 hours after the flow's first run, depending on
the connected app's access-token lifetime.

**How to avoid.** In the connected app, set Refresh Token Policy to
**"Refresh token is valid until revoked"** *before* the AppFlow
connection authorizes against it. The AWS-managed connected app uses
the right policy by default — the gotcha is bring-your-own-app.

---

## Gotcha 4: Event Relay is one-way (Salesforce → AWS only)

**What happens.** Teams configure Event Relay assuming it gives them
bidirectional event flow with EventBridge — and then realize the AWS
side has no way to push events back into Salesforce.

**When it occurs.** Discovery hits during architecture review, often
weeks into the build.

**How to avoid.** For the AWS → Salesforce direction, configure
**EventBridge API Destinations** (a separate AWS feature) to POST to a
Salesforce REST endpoint or Pub/Sub publish. That's a second
configuration in a second tool, not part of Event Relay. Plan and budget
for both sides explicitly when the architecture demands bidirectional.

---

## Gotcha 5: Apex → Lambda callouts blow the per-transaction governor on bulk operations

**What happens.** A trigger that calls Lambda for each opportunity in a
batch — with no bulkification — hits the **100 callouts per transaction**
governor and the **120-second wall-clock per callout** limit (cumulative
maximum 120 s for synchronous Apex). Bulk DML operations lose every
record after the 100th.

**When it occurs.** Anonymous-Apex one-off load, Data-Loader bulk update,
or any Salesforce process publishing many records at once.

**How to avoid.** Bulkify: send all record IDs in a single payload, let
the Lambda return a map of results, apply them to the in-memory record
collection before the trigger returns. Use `templates/apex/HttpClient.cls`
which already implements bulk-batch semantics. For asynchronous fan-out,
use Event Relay instead and let EventBridge do the per-event dispatch on
the AWS side.

---

## Gotcha 6: AppFlow's "schedule-triggered" flows cap at 1 run per minute

**What happens.** Teams configure a schedule-triggered flow expecting
sub-minute granularity (every 30 seconds, every 15 seconds) and find
the Lambda firing at most once per minute regardless of the schedule
expression.

**When it occurs.** Real-time-ish use cases that don't need true
event-driven (otherwise use Event Relay) but want tighter than minute
cadence.

**How to avoid.** If sub-minute is required, the right path is **event-driven** (CDC trigger in AppFlow, or Event Relay → EventBridge) — not a tighter schedule. AppFlow's schedule cap is documented and not negotiable. (Source: [AWS AppFlow Salesforce connector docs](https://docs.aws.amazon.com/appflow/latest/userguide/salesforce.html) under "Trigger Modes".)

---

## Gotcha 7: AppFlow → Salesforce upsert needs an external-id field, not the Salesforce ID

**What happens.** Teams configure an AppFlow flow with Salesforce as
destination, set the operation to "Upsert", and map the source's primary
key to the Salesforce `Id` field. The flow runs and only updates existing
records — every "new" record fails silently.

**When it occurs.** Loading data from a non-Salesforce system that has
its own primary keys (rather than Salesforce IDs).

**How to avoid.** Define an **external-id field** on the target Salesforce
object (custom field with `Unique` + `External ID` checked), map the
source's primary key to that, and AppFlow will upsert correctly.
Salesforce `Id` is not a valid external-id target for upsert.
