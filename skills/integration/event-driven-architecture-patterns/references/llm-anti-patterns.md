# LLM Anti-Patterns — Event-Driven Architecture Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce event-driven architecture selection. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending CDC for Custom Domain Events Without a DML Trigger

**What the LLM generates:** When asked "how do I notify an external system when an order is approved in Salesforce," the LLM recommends enabling Change Data Capture for the Order object and subscribing to `/data/Order__ChangeEvent`.

**Why it happens:** CDC and Platform Events are often discussed together in Salesforce documentation and training content. LLMs conflate "streaming event from Salesforce" with CDC without checking whether the event source requires a DML operation.

**Correct pattern:**

```
If the event represents a business milestone (approval, batch completion, workflow decision)
that does not map 1:1 to a single DML operation on a single record → Platform Events.

If the event represents "this record's fields changed" and the trigger IS the DML → CDC.
```

CDC cannot be published manually. It fires only from Salesforce DML (insert, update, delete, undelete) on an enabled entity. Recommending CDC for a non-DML-triggered event is architecturally incorrect.

**Detection hint:** If the recommended event mechanism is CDC but the described trigger is a business process, batch job, approval step, or external system event rather than a record DML — flag this as an anti-pattern.

---

## Anti-Pattern 2: Treating Streaming API (PushTopic) as Equivalent to CDC for External Sync

**What the LLM generates:** "You can use the Streaming API with a PushTopic on the Account object to stream Account changes to your ERP. Set the replay ID to -1 to get all retained events."

**Why it happens:** PushTopic streaming and CDC are both CometD-based channels in older Salesforce documentation. LLMs trained on pre-2020 content associate "real-time record changes" with PushTopic because it predates CDC as the primary mechanism for this use case.

**Correct pattern:**

```
For external system record synchronization (ERP, data warehouse, MDM):
→ Use CDC for the following reasons:
   - Automatic changedFields tracking (no custom SELECT list maintenance)
   - 72-hour retention (vs 24 hours for PushTopic)
   - Higher throughput ceiling
   - Gap events with structured recovery path

Use PushTopic only for legacy integrations already using it.
```

**Detection hint:** If the proposed solution uses PushTopic for external system record sync with no mention of the 24-hour retention limit or the CDC alternative — flag this recommendation.

---

## Anti-Pattern 3: Ignoring the CDC Entity Allocation Limit

**What the LLM generates:** A CDC rollout plan that enables Change Data Capture for 10 or more Salesforce objects across a standard Enterprise org without mentioning the entity allocation limit.

**Why it happens:** LLMs often generate technically correct CDC setup steps without applying the platform's licensing and allocation constraints. The 5-entity free tier is a platform limit that is easy to overlook when describing a conceptually simple configuration step.

**Correct pattern:**

```
Before recommending CDC across multiple objects:
1. Count the total entities requiring CDC coverage.
2. If count > 5 for a standard Enterprise or Professional edition org:
   → Document the need for a Change Data Capture add-on license.
   → OR propose a tiered rollout where CDC covers top-priority objects
     and Platform Events with Apex publisher covers lower-priority objects.
```

**Detection hint:** Any CDC recommendation that covers more than 5 objects without mentioning the entity allocation limit or add-on licensing requirement is missing a critical constraint.

---

## Anti-Pattern 4: Recommending Platform Events as a Direct Drop-In Replacement for Outbound Messages

**What the LLM generates:** "Instead of Outbound Messages, use Platform Events — publish from a Flow and have the external system subscribe via the Pub/Sub API. This is the modern approach."

**Why it happens:** Platform Events are the documented strategic successor to Outbound Messages, and LLMs correctly associate this migration direction. However, they miss the delivery-model difference: Outbound Messages deliver SOAP directly with acknowledgment-based retry. Platform Events are pub/sub with at-most-once delivery to the subscriber's connection window (within the 72-hour replay window). If the external endpoint requires SOAP, Platform Events alone do not satisfy the delivery requirement.

**Correct pattern:**

```
If external endpoint requires SOAP:
→ Maintain Outbound Message (if Workflow Rule is grandfathered in) OR
→ Platform Event + Apex subscriber that makes a SOAP callout via Named Credential

If external endpoint can consume JSON (REST/webhook):
→ Platform Event published from Flow or Apex
→ External subscriber via Pub/Sub API or CometD

Never recommend Platform Events as a direct replacement without confirming the
external endpoint's protocol requirements.
```

**Detection hint:** If the recommendation replaces an Outbound Message with Platform Events without asking about the receiver's protocol or without adding a SOAP callout layer — flag this gap.

---

## Anti-Pattern 5: Assuming All Standard Objects Support CDC

**What the LLM generates:** "Enable CDC on the Task and Event objects to sync Activity changes to your external calendar system."

**Why it happens:** LLMs generalize from the fact that CDC supports "standard and custom objects" to mean all standard objects, without applying the specific exclusions documented in the CDC Developer Guide. Task and Event have partial or restricted CDC support — Task change events exist but with restrictions; full Activity history is not available through CDC.

**Correct pattern:**

```
Before recommending CDC for any specific object:
1. Check the CDC Developer Guide's supported objects list at:
   https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/cdc_object_support.htm
2. For Task, Event, and activity-related objects — explicitly state the restriction
   and recommend an alternative (polling via REST, Platform Events on milestone updates).
3. Do not assume all custom objects support CDC — only custom objects explicitly
   enabled in Setup are in scope.
```

**Detection hint:** If CDC is recommended for Task, Event, or any object listed with restrictions in the CDC Developer Guide without calling out the limitation — flag this recommendation.

---

## Anti-Pattern 6: Recommending PushTopic for Browser Clients Using LWC

**What the LLM generates:** "Create a PushTopic for Order updates and subscribe from your LWC component using CometD to display real-time updates in the browser."

**Why it happens:** PushTopic was historically the recommended mechanism for real-time browser updates before the `empApi` LWC wire adapter and Platform Events became the standard. LLMs trained on older documentation or Stack Overflow answers reproduce the PushTopic pattern for in-browser use cases.

**Correct pattern:**

```
For real-time updates in Lightning Web Components (LWC):
→ Use Platform Events + empApi wire adapter
→ Example: subscribe to /event/MyEvent__e using the lightning/empApi module

PushTopic CometD from within an LWC is not supported via empApi.
empApi only supports Platform Event and CDC channels, not PushTopic channels.
```

**Detection hint:** Any LWC code that imports `lightning/empApi` and uses a `/topic/` channel path (PushTopic) rather than `/event/` (Platform Event) is an anti-pattern — `empApi` does not support PushTopic channels.
