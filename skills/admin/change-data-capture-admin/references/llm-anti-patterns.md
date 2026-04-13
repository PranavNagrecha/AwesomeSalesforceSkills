# LLM Anti-Patterns — Change Data Capture Admin

Common mistakes AI coding assistants make when generating or advising on Change Data Capture Admin.
These patterns help the consuming agent self-check its own output.

---

### Anti-Pattern 1: Recommending Enrichment on Standard Per-Object Channels

**What LLMs do:** When asked to add enriched fields to a CDC subscription for Account, LLMs generate `EnrichedField` configuration targeting the standard `AccountChangeEvent` per-object channel member, such as creating a `PlatformEventChannelMember` for `/data/AccountChangeEvent` with `EnrichedField` children.

**Why:** Training data contains many examples of `PlatformEventChannelMember` and `EnrichedField` usage without the constraint that enrichment only works on custom multi-entity channels. The platform does not return an error during deployment, so this pattern is never corrected in training feedback loops.

**Correct approach:** Enrichment is only supported on `PlatformEventChannelMember` records in custom channels (channel names ending in `__chn`). Create a `PlatformEventChannel` metadata record first, assign the entity to it via `PlatformEventChannelMember`, then add `EnrichedField` children to that custom channel member. Route the subscriber to the custom channel path.

```xml
<!-- Correct: EnrichedField on a custom channel member -->
<PlatformEventChannelMember>
    <eventChannel>Account_Enriched__chn</eventChannel>
    <selectedEntity>Account</selectedEntity>
    <enrichedFields>
        <name>Industry</name>
    </enrichedFields>
</PlatformEventChannelMember>
```

**Detection:** If generated metadata sets `eventChannel` to any value ending in `ChangeEvent` (e.g., `AccountChangeEvent`, `Contact__ChangeEvent`) and also includes `enrichedFields` children, the configuration is incorrect.

---

### Anti-Pattern 2: Directing Admins to Modify DataCloudEntities Channel Members

**What LLMs do:** When asked to remove a "duplicate" entity selection or clean up unused channel members, LLMs generate Tooling API or Metadata API instructions to delete `PlatformEventChannelMember` records from the `DataCloudEntities` channel, treating it the same as any other custom channel.

**Why:** LLMs have no awareness that the `DataCloudEntities` channel is Data Cloud-managed and has special ownership semantics. The channel appears like any other custom channel in Tooling API results.

**Correct approach:** Never modify `PlatformEventChannelMember` records belonging to the `DataCloudEntities` channel directly. These are owned by Data Cloud and must be managed through CRM Data Stream configuration in the Data Cloud UI. Before any cleanup action, always filter audit results to exclude this channel:

```soql
SELECT QualifiedApiName, PlatformEventChannel.MasterLabel
FROM PlatformEventChannelMember
WHERE PlatformEventChannel.MasterLabel != 'DataCloudEntities'
```

**Detection:** If generated instructions include DELETE or update operations on `PlatformEventChannelMember` without first filtering out the `DataCloudEntities` channel, flag for human review.

---

### Anti-Pattern 3: Using the Setup UI as the Authoritative CDC Audit Source

**What LLMs do:** When asked to audit which objects have CDC enabled, LLMs instruct users to navigate to **Setup > Integrations > Change Data Capture** and review the Selected Entities list as the complete inventory.

**Why:** The Setup UI is the most prominently documented path in official documentation for enabling CDC, so LLMs anchor to it as the canonical view of CDC configuration state.

**Correct approach:** The Setup UI only shows entities selected on the default `ChangeEvents` channel. Custom channels and the `DataCloudEntities` channel are invisible there. Always use Tooling API for a complete audit:

```soql
SELECT QualifiedApiName, PlatformEventChannelId,
       PlatformEventChannel.MasterLabel, PlatformEventChannel.ChannelType
FROM PlatformEventChannelMember
ORDER BY PlatformEventChannel.MasterLabel, QualifiedApiName
```

**Detection:** If generated audit instructions reference only the Setup UI path and do not include a Tooling API query, the audit is incomplete.

---

### Anti-Pattern 4: Ignoring Edition-Based Delivery Limits When Designing Channel Topology

**What LLMs do:** When designing a CDC architecture for multiple subscribers, LLMs recommend that all consumers subscribe directly to the default `ChangeEvents` channel or to individual per-object channels, without accounting for how this multiplies delivery allocation consumption.

**Why:** LLMs understand that CDC has delivery limits but do not consistently apply the per-subscriber multiplication effect (N subscribers each consuming the full event count) when evaluating the impact of a multi-subscriber design.

**Correct approach:** Calculate total expected delivery consumption as `(events per day) × (number of distinct subscribers)`. Compare against the org's edition allocation (50K/25K/10K per 24h). If the result approaches the limit, recommend:
1. Custom channels with server-side entity filtering so subscribers only receive relevant events.
2. A single bridge subscriber that fans out to Kafka or another message bus, reducing Salesforce-side subscriber count to 1.
3. Purchasing the CDC add-on for monthly volume pricing if sustained high volumes are required.

**Detection:** If a multi-subscriber design is proposed without any mention of delivery allocation math or mitigation, request a delivery consumption estimate before accepting the design.

---

### Anti-Pattern 5: Conflating Admin-Side CDC Configuration with Subscriber-Side Setup

**What LLMs do:** When asked to "set up CDC for Account," LLMs generate a combined response that mixes admin configuration (Setup UI entity selection) with subscriber implementation (Apex trigger class with `handleChangeRequest`, CometD connection code, or Pub/Sub API gRPC stubs), presenting both as equally in scope for the admin performing the task.

**Why:** CDC documentation covers both the admin and developer/integration sides in the same guide, and LLMs do not apply the organizational skill boundary that separates platform configuration from subscriber implementation.

**Correct approach:** Admin-side CDC setup is limited to entity selection, channel configuration, enrichment setup, and delivery monitoring. Subscriber implementation (Apex triggers, CometD clients, Pub/Sub API gRPC clients, replay ID management, gap event handling) is out of scope for an admin task and belongs to `integration/change-data-capture-integration` or the relevant Apex skill. When generating admin guidance, stop after channel configuration is validated and reference the integration skill explicitly for subscriber setup.

**Detection:** If generated output includes `CometD`, `replayId`, `handleChangeRequest`, `PlatformStreamingClient`, or gRPC subscription code in response to an admin-framed CDC question, the scope boundary has been violated.
