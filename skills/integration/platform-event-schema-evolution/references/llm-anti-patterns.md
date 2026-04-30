# LLM Anti-Patterns — Platform Event Schema Evolution

Common mistakes AI coding assistants make when generating or advising on Platform Event schema changes.

## Anti-Pattern 1: Recommending in-place rename

**What the LLM generates:** "Rename `Customer_Id__c` to `Account_Number__c` and redeploy."

**Why it happens:** Treats Platform Event fields like database columns where rename is a metadata operation.

**Correct pattern:** Salesforce metadata "rename" deletes the old field and creates a new one. For published events, use the dual-publish pattern (new event v2, dual-publish from publishers, migrate subscribers, retire v1).

**Detection hint:** Any "rename" instruction on a Platform Event field with no mention of v2 or dual-publish.

---

## Anti-Pattern 2: Treating high-volume events like fire-and-forget

**What the LLM generates:** "Make the change. Subscribers will pick up the new schema on the next event."

**Why it happens:** Mental model of fire-and-forget messaging.

**Correct pattern:** High-volume events have a 72-hour replay window. Subscribers reconnecting may receive pre-change events. Subscriber code must tolerate the older schema for the full window.

**Detection hint:** Any rollout plan that doesn't reference a wait period after the publisher change.

---

## Anti-Pattern 3: Hardcoding Pub/Sub schema IDs in client code

**What the LLM generates:**

```python
SCHEMA_ID = "abcdef..."  # Order_Created__e
def decode(event_bytes):
    return decoder(SCHEMA_ID).decode(event_bytes)
```

**Why it happens:** Treats schema ID as constant.

**Correct pattern:** Each event carries the schema ID it was published under. Decoders must call `GetSchema(unknown_id)` and cache by ID.

```python
schemas: dict[str, Schema] = {}
def decode(event_bytes, schema_id):
    if schema_id not in schemas:
        schemas[schema_id] = client.GetSchema(schema_id)
    return schemas[schema_id].decode(event_bytes)
```

**Detection hint:** A constant or single global SCHEMA_ID adjacent to a Pub/Sub decoder.

---

## Anti-Pattern 4: Suggesting to make a field required to enforce data quality

**What the LLM generates:** "Mark `Customer_Id__c` as required so all publishers must populate it."

**Why it happens:** Database-style data-quality reflex.

**Correct pattern:** Required-on-publish breaks any existing publisher (Apex, Flow, REST) that doesn't supply the field. For data-quality, validate in the subscriber and reject malformed events; don't enforce at publish time.

**Detection hint:** Any "make this required" recommendation on a Platform Event without a publisher inventory step.

---

## Anti-Pattern 5: Ignoring CDC's separate schema model

**What the LLM generates:** Applying Platform Event evolution rules to a Change Data Capture event ("OpportunityChangeEvent").

**Why it happens:** Both look like sObjects-as-events.

**Correct pattern:** CDC events derive schema from the underlying sObject. They evolve when the sObject schema evolves; subscribers must tolerate added/removed fields per the CDC contract. Direct Platform Event versioning patterns don't apply. Refer to apex/change-data-capture-apex.

**Detection hint:** A "v2 event" plan applied to a CDC event name (`*ChangeEvent`).
