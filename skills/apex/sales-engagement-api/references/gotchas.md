# Gotchas — Sales Engagement API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Invocable Action Returns Success=False Without Throwing an Exception

**What happens:** When `assignTargetToSalesCadence` is called for a target that is already enrolled in an active cadence, the action does not throw an Apex exception. It returns an `Invocable.Action.Result` where `isSuccess()` is `false` and `getErrors()` contains an error code. Code that only wraps the call in a try/catch block will never detect this failure and will assume the enrollment succeeded.

**When it occurs:** Any time the invocable action call is made without inspecting the returned `List<Invocable.Action.Result>` per record. Common in trigger or batch code where developers treat invocable actions like database operations and only handle exceptions.

**How to avoid:** Always iterate the result list after calling `Invocable.Action.invoke()` and check `result.isSuccess()` for each position. Log or surface the errors from `result.getErrors()`. Add a pre-flight SOQL check on `ActionCadenceTracker` for active enrollments before calling the action, which also surfaces duplicates before they reach the action layer.

---

## Gotcha 2: Standard Apex Triggers Cannot Be Placed on ActionCadenceTracker

**What happens:** Attempting to deploy an Apex trigger with `trigger MyTrigger on ActionCadenceTracker (before insert, after update)` results in a deployment error. The error message is not always intuitive; it can surface as an "entity is not trigger-able" compile error or a deployment failure depending on the API version.

**When it occurs:** Any time a developer tries to react to enrollment events using the standard Salesforce trigger framework rather than CDC. This is a very common first instinct because triggers are the default reactive mechanism in Apex.

**How to avoid:** Use Change Data Capture. Enable CDC on `ActionCadenceTracker` in Setup, then create an Async Apex Trigger on `ActionCadenceTrackerChangeEvent`. This is the only supported Apex mechanism for reacting to tracker record changes. Document this constraint in the architecture decision record so it is not re-attempted later.

---

## Gotcha 3: Cadence Structure Is Fully Read-Only via API — Including Apex

**What happens:** Queries against `ActionCadence`, `ActionCadenceStep`, and `ActionCadenceStepVariant` return live data that reflects the current state of cadences as built in the Cadence Builder UI. However, DML operations (insert, update, delete) on these objects are blocked. Attempts to create cadence content via Apex or the Metadata API will fail.

**When it occurs:** When a stakeholder requests that a deployment pipeline or Apex code "set up" cadence content as part of a release. The team discovers at deploy time — not design time — that the cadence cannot be scripted.

**How to avoid:** Treat cadence structure as UI-owned configuration, not deployable metadata. Build cadences manually in the Cadence Builder UI in each target environment (sandbox to production). Use the SOQL-queryable `ActionCadence` object only to look up cadence IDs by name at enrollment time. Communicate this constraint early in the project.

---

## Gotcha 4: Invocable Action Calls Do Not Execute in Standard Unit Tests Without a Licensed Org

**What happens:** Unit tests that call `Invocable.Action.createCustomAction('apex', 'assignTargetToSalesCadence').invoke(inputs)` return empty result lists or throw null pointer exceptions in orgs or scratch orgs that do not have the Sales Engagement license provisioned. The test passes or fails inconsistently depending on environment.

**When it occurs:** In CI pipelines that run tests against a scratch org without the Sales Engagement add-on, or in developer sandboxes without the SE license.

**How to avoid:** Wrap the invocable action call behind a service interface. In tests, inject a stub implementation that returns controlled `Invocable.Action.Result` objects. This makes tests deterministic regardless of license state and documents the enrollment contract in the stub's interface. Alternatively, test against a Developer Edition org or sandbox provisioned with Sales Engagement.

---

## Gotcha 5: CDC Events for ActionCadenceTracker May Arrive After Significant Latency Under Load

**What happens:** Change Data Capture events are delivered asynchronously through the event bus. Under high enrollment volume or when the event bus is under stress, `ActionCadenceTrackerChangeEvent` delivery can lag behind actual record state changes by seconds to minutes. Downstream processes that query `ActionCadenceTracker` state immediately after receiving a CDC event may read stale data.

**When it occurs:** In orgs with high cadence enrollment throughput, near end-of-batch processing windows, or during platform maintenance periods.

**How to avoid:** Do not assume that the state in the CDC event payload is the current state of the record. When the event-triggered Queueable queries `ActionCadenceTracker` for enriched data, it will read the current (post-all-changes) state, which is typically correct. Avoid designing workflows that depend on sub-second precision of cadence state transitions.
