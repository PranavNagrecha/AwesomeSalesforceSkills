# LLM Anti-Patterns — Change Data Capture Integration

Common mistakes AI coding assistants make when generating or advising on Change Data Capture Integration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming `changedFields` Is Available in CometD

**What the LLM generates:** Code or guidance that reads `ChangeEventHeader.changedFields` from a CometD subscription and uses it to build delta logic, implying the field is present in CometD event payloads.

**Why it happens:** The LLM conflates Pub/Sub API and CometD documentation. Both use `ChangeEventHeader` in their payload structures, so the LLM generalizes the field availability incorrectly.

**Correct pattern:**
```
changedFields, nulledFields, and diffFields are ONLY available in:
  - Pub/Sub API (gRPC) subscribers
  - Apex trigger subscribers

They are NOT present in CometD (Streaming API) event messages.
CometD delivers the current values of all fields that are returned in the payload,
but does not include header-level field change bitmaps.
```

**Detection hint:** Flag any code that reads `ChangeEventHeader.changedFields` in a CometD-based subscriber (identified by `/cometd/` in the URL or use of Bayeux/EMP Connector patterns).

---

## Anti-Pattern 2: Treating Gap Events as Normal Change Events

**What the LLM generates:** A CDC subscriber that processes `changeType` values like `GAP_CREATE` or `GAP_UPDATE` as if they were `CREATE` or `UPDATE`, attempting to read field values from the payload body.

**Why it happens:** The LLM either does not know gap events exist, or it strips the `GAP_` prefix without explaining that gap events have no field body data — only header metadata (`recordIds`, `changeType`, `commitTimestamp`).

**Correct pattern:**
```python
change_type = header["changeType"]
if change_type.startswith("GAP_"):
    # No field data available — fetch current record state from REST API
    for record_id in header["recordIds"]:
        fetch_and_reconcile(record_id)
else:
    # Normal change event — process field values
    process_fields(event_payload)
```

**Detection hint:** Look for subscriber code that reads field values from the event body without first checking for the `GAP_` prefix on `changeType`. Also flag code that `strip("GAP_")` manipulates the changeType string to reuse normal processing logic.

---

## Anti-Pattern 3: Stateless Replay — Reconnecting with `-1` Every Time

**What the LLM generates:** A subscriber implementation that always passes `-1` (tip) as the replay ID on startup, with no mechanism to persist or recover the last processed position.

**Why it happens:** The LLM focuses on getting the subscription working and omits durability requirements. `-1` is the simplest value to use and is commonly seen in tutorial examples.

**Correct pattern:**
```
Always persist the replay ID to durable external state after each
successfully processed event batch. On startup:
  1. Load the stored replay ID.
  2. If a stored ID exists and is within the 72-hour window: pass it to resume.
  3. If no stored ID: use -2 (all retained) for initial catch-up.
  4. If the stored ID is outside the retention window: trigger a full
     Bulk API re-sync, then subscribe at -1 (tip).
Never use -1 as the default startup replay ID in a production integration.
```

**Detection hint:** Flag any subscriber implementation that hardcodes `-1` as the replay ID without a comment explaining why tip-only is acceptable for the use case.

---

## Anti-Pattern 4: Recommending > 5 Entity Selections Without Mentioning the Add-On

**What the LLM generates:** Instructions to enable CDC for 8 or 10 standard objects via Setup > Change Data Capture, without noting that the default limit is 5 entities across all channels and that exceeding it requires purchasing the CDC add-on.

**Why it happens:** The LLM is unaware of the per-org entity selection cap or assumes it applies only to a specific edition. The limit is 5 entities for all editions (Performance, Enterprise, Developer) with no edition-based exception.

**Correct pattern:**
```
The default entity selection limit is 5 objects (standard + custom combined)
across all channels (including custom channels). This applies to all editions.
If you need more than 5 entities:
  - Purchase the Change Data Capture add-on (removes the entity cap).
  - Evaluate whether all entities truly need CDC, or whether some can use
    outbound messaging or polling.
Audit the current selection count with:
  SELECT COUNT() FROM PlatformEventChannelMember (Tooling API)
```

**Detection hint:** Flag any guidance that lists more than 5 CDC entities without referencing the allocation limit or the add-on requirement.

---

## Anti-Pattern 5: Ignoring 72-Hour Retention in Recovery Design

**What the LLM generates:** A reconnection or disaster-recovery plan that assumes replay is always possible from any stored replay ID, without acknowledging that events older than 72 hours are permanently purged.

**Why it happens:** The LLM is aware that CDC supports replay but does not model the time boundary. It may also conflate CDC retention with Salesforce Shield event monitoring (which has different retention for Platform Events).

**Correct pattern:**
```
CDC event retention is exactly 72 hours. After that, events are purged permanently.
Salesforce Shield does NOT extend CDC retention (Shield extends Platform Event
monitoring storage, not CDC event bus retention).

Every CDC integration must define a fallback for gaps > 72 hours:
  1. Detect that stored replay ID is outside the retention window (error on subscribe).
  2. Trigger a full Bulk API 2.0 re-sync of all affected objects.
  3. After re-sync completes, re-subscribe at tip (-1).
  4. Log the incident and alert on subscriber downtime before it exceeds 72 hours.
```

**Detection hint:** Flag recovery or reconnection designs that reference only replay ID resumption without a fallback for the out-of-window case. Also flag any claim that Shield extends CDC retention.

---

## Anti-Pattern 6: Confusing Custom Platform Event Channels with CDC Channels

**What the LLM generates:** Instructions to create a `PlatformEventChannel` for a custom Platform Event (e.g., `My_Business_Event__e`) and describe it as a CDC channel, or vice versa — treating CDC entity channels and Platform Event channels as the same construct.

**Why it happens:** Both Platform Events and CDC use `PlatformEventChannel` metadata type in the API, and LLMs conflate the two when generating Metadata API configuration.

**Correct pattern:**
```
PlatformEventChannel is used for BOTH Platform Events and CDC custom channels,
but the channelType must match:
  - CDC custom channels: channelType = "data"
  - Platform Event channels: channelType = "event"

CDC channels use PlatformEventChannelMember with selectedEntity pointing to
an sObject (e.g., Account, Order, MyCustomObject__c).

Platform Event channels use PlatformEventChannelMember pointing to a
Platform Event object (e.g., My_Event__e).

Do not mix channelTypes or entity types across the two.
```

**Detection hint:** Flag any Metadata API configuration that assigns a Platform Event API name (ending in `__e`) as a `selectedEntity` in a channel marked `channelType = data`, or an sObject name in a `channelType = event` channel.
