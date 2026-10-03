# Gotchas — Platform Selection Guidance

Non-obvious platform behaviors that cause real production problems when platform feature choices are made without full knowledge of their constraints.
Each gotcha names its source. Claims no fetched source confirms carry an inline `UNVERIFIED (date):` marker. Each gotcha ends with a **How to avoid** line.

---

## Gotcha 1: Custom Settings Data Is NOT Deployable via Metadata API by Default

**What happens:** Custom Settings records (their actual data values) are not included in Metadata API retrieve/deploy operations or change sets. The Custom Settings *type definition* (field schema) deploys as metadata, but the values in each record do not. This means every sandbox refresh or new org requires the values to be seeded separately — via Apex scripts, data loader, or custom deployment tooling.

This is the primary reason Custom Metadata Types are preferred for deployable configuration. CMT records deploy as metadata files alongside the type definition; the Metadata API Developer Guide (`CustomMetadata`) lists them in `package.xml` as `<TypeName>.<RecordName>` members under the `CustomMetadata` type. The Apex Developer Guide ("Custom Settings") confirms a custom setting can be included in a package and that custom settings data is copied into sandboxes.

**When it occurs:** The first deployment to a new sandbox, scratch org, or production after the configuration was built.

**Impact:** Teams that choose Custom Settings for configuration data discover this limitation the first time they try to deploy to a new sandbox or production. The workaround — seeding data via anonymous Apex in a post-deploy script — adds friction to every release. If the team uses a CI/CD pipeline, this becomes a recurring manual step unless custom tooling is built to automate it.

**How to avoid:** If the configuration data needs to be consistent across orgs and deployments without manual intervention, do not use Custom Settings. Use Custom Metadata Types.

---

## Gotcha 2: LWC Cannot Consume Aura Application Events — Partial Migrations Break Event Chains

**What happens:** LWC components cannot register as handlers of Aura application events (`e.namespace:EventName`). If an org has a cross-component communication pattern built on Aura application events, migrating only the publisher component to LWC will silently break all Aura consumers — they will stop receiving events with no runtime error that clearly points to the event chain.

The reverse is also true: an Aura component cannot subscribe to a custom DOM event from a LWC sibling at the application level. The LWC Developer Guide ("Lightning Web Components and Aura Components Working Together") says Aura components can contain Lightning web components but not the reverse. The *Lightning Aura Components Developer Guide* (Spring '26, local corpus `knowledge/imports/lightning.md`, "Application Event Propagation") says that to communicate across the DOM within a Lightning page, or between Visualforce, Lightning pages and LWC, you should use Lightning Message Service instead of application events.

**When it occurs:** Component-by-component LWC migrations of a page whose components talk through application events.

**Impact:** Teams that attempt incremental LWC migrations on a component-by-component basis, without redesigning the event communication layer first, end up with broken event wiring that is difficult to diagnose.

**How to avoid:** Before migrating any component that participates in cross-component Aura events, design the Lightning Message Service (LMS) channel replacement for the full event chain. Migrate all participating components together, or use the LMS channel from the LWC publisher while Aura consumers temporarily subscribe to LMS through `lightning:messageChannel` (UNVERIFIED 2026-10-03: the "since Spring '21" date in earlier text was not confirmed).

---

## Gotcha 3: Platform Events and CDC Retention Windows Are Fixed — External Replay Depends on Getting This Right

**What happens:** High-volume platform events are retained for 72 hours and legacy standard-volume events for 24 hours (Platform Events Developer Guide, "Event Retention in the Event Bus"). Change events are stored for up to three days (Change Data Capture Developer Guide). Correction (2026-10-03): earlier text said CDC retention "extends to 7 days with Salesforce Shield Event Monitoring". The CDC guide states only the three-day window; the one seven-day figure in its Shield section is how often an event bus tenant secret can be generated or rotated.

**When it occurs:** Subscriber outages longer than the window, often over a long weekend.

This distinction matters when designing integrations with external subscribers. If an external ERP or middleware goes offline for more than 72 hours, any Platform Events published during that window are lost. The subscriber cannot replay them.

**Impact:** Integration designs that assume "the subscriber can always catch up by replaying" will fail if the subscriber is offline for more than the retention window. This is especially dangerous in CDC-based sync patterns where missed events mean the external system is permanently out of sync.

**How to avoid:**
- If the integration requires more replay tolerance than the window, do not count on a licence to extend it; design a reconciliation path (Bulk API 2.0 extract by `SystemModstamp`) for gaps longer than the window.
- If Platform Events are used and an extended replay window is critical, design a fallback: a scheduled reconciliation job that re-publishes or re-syncs any records that the subscriber may have missed.
- Document the retention assumption explicitly in the integration architecture document.

---

## Gotcha 4: OmniStudio DataRaptors Are Not SOQL-Equivalent — They Have Their Own Query Model and Limitations

**What happens:** OmniStudio DataRaptors perform data reads, writes, and transforms declaratively, but they are not a drop-in replacement for SOQL. DataRaptors operate on a different query model: they read from a single object per Extract step, do not support arbitrary JOIN-like multi-object queries in a single operation, and have their own field mapping and transformation layer.

UNVERIFIED (2026-10-03): the DataRaptor query-model details in this gotcha were not checked against the OmniStudio documentation in this pass.

**When it occurs:** OmniScript designs scoped before the data access requirements are known.

**Impact:** Teams that choose OmniStudio expecting DataRaptors to behave like SOQL with extra UI steps encounter limitations when trying to query data that requires relationship traversal or conditional joins. Complex cross-object reads require multiple DataRaptor steps chained together, or delegation to an Integration Procedure with multiple steps — adding design complexity.

**How to avoid:**
- Do not assume DataRaptors can replace arbitrary SOQL queries. Validate the data access requirements against DataRaptor capabilities before committing to an OmniScript design.
- For complex multi-object data retrieval, prefer Integration Procedures with multiple Read steps, or delegate to an Apex REST callout.
- If the team does not have OmniStudio-trained resources, the complexity of DataRaptor design often negates the declarative benefit; evaluate Standard Flow + Apex as an alternative.

---

## Gotcha 5: Custom Metadata Types Cannot Store Relationship Lookups to Records

**What happens:** Custom Metadata Type records can have metadata relationship fields, but they cannot have standard lookup or master-detail relationship fields pointing to records like an Account, User, or Queue. The Metadata API Developer Guide (`CustomField`, `metadataRelationshipControllingField`) describes metadata relationships to an entity definition (an object), a field definition, an entity particle, or another custom metadata type, not to data records.

**When it occurs:** Routing and assignment configuration that needs to point at a specific queue, user, or price book.

**Impact:** Teams that design routing rules or configuration that needs to reference a Salesforce record ID (e.g., a Queue ID, a User ID, a Pricebook ID) cannot store that reference as a proper relationship field in Custom Metadata. They must store the ID as a text field, which means:
- No lookup validation (bad ID goes undetected until runtime)
- ID is org-specific and will break when deploying across orgs unless the ID is updated post-deploy

**How to avoid:** If configuration data needs to reference a Salesforce record (Queue, User, Group, Pricebook), either store the developer name or API name of the referenced record and resolve it at runtime via SOQL, or evaluate whether a Custom Object is a better fit for this use case.

---

## Gotcha 6: Outbound Messaging Has Delivery Guarantees That Platform Events Do Not Auto-Replicate

**What happens:** Outbound Messaging (legacy; the Metadata API Developer Guide, `WorkflowOutboundMessage`, describes outbound messages as workflow and approval actions) has a built-in retry mechanism. *Integration Patterns and Practices* says Salesforce retries for up to 24 hours with an exponential interval from 15 seconds to 60 minutes, extendable to seven days through Salesforce Support, after which failed messages wait in a queue for manual retry. The same guide says platform events are published to the bus once with no Salesforce-side retry.

**When it occurs:** Migrations from outbound messaging to platform events that keep the subscriber unchanged. Platform Events do not automatically retry to external endpoints. The replay window (72 hours) allows a subscriber to re-read missed events, but only if the subscriber actively initiates the replay.

**Impact:** Teams migrating from Outbound Messaging to Platform Events sometimes assume the retry behavior transfers. It does not. External subscribers that go offline or experience errors will miss events unless they implement replay logic using the `replayId` mechanism.

**How to avoid:** When migrating from Outbound Messaging to Platform Events, explicitly design the subscriber replay strategy. Test failure scenarios where the external endpoint is unavailable for an extended period. If guaranteed delivery is a hard requirement, evaluate middleware (MuleSoft, Boomi) that can provide delivery guarantee semantics on top of Platform Events.

---

## Gotcha 7: Public Custom Settings Are Readable by Every Profile, Including Guest

**What happens:** A team stores an API key or integration password in a hierarchy custom setting because it is "configuration". The Apex Developer Guide ("Custom Settings") warns that protection applies only to custom settings marked protected and installed as part of a managed package; otherwise they are public and readable for all profiles, including the guest user. It says not to store secrets, PII, or private data there and to use named credentials or encrypted fields instead.

**When it occurs:** Orgs with an Experience Cloud site and secrets in unpackaged custom settings.

**How to avoid:** Keep secrets in named credentials and external credentials. Treat any existing secret in an unpackaged custom setting as exposed and rotate it.

---

## Gotcha 8: Custom Settings Data Is Invisible to Apex Tests by Default

**What happens:** Code that reads a hierarchy custom setting passes in the sandbox UI and fails in tests. The Apex Developer Guide ("Isolation of Test Data from Organization Data in Unit Tests" and "Custom Settings") says test methods cannot see pre-existing custom settings data unless the test uses `SeeAllData=true`, and recommends creating the data in test setup. The same section says objects used to manage the org and metadata objects stay accessible, which is why metadata-based configuration is easier to test. UNVERIFIED (2026-10-03): custom metadata types are not named in that list, so confirm in a test before relying on it.

**When it occurs:** Every deployment that runs tests touching configuration stored in custom settings.

**How to avoid:** If the configuration is stored in custom settings, create the records in `@TestSetup`. Prefer custom metadata for configuration that every test needs.

---

## Gotcha 9: Custom Metadata Records Cannot Be Changed With DML

**What happens:** An admin screen or Apex job tries to `insert` or `update` custom metadata records and fails. The Apex Developer Guide ("Deploy Apex Using Metadata API", "Metadata") says Apex deploys records of custom metadata types through `Metadata.Operations.enqueueDeployment()`, which is asynchronous. Protected custom metadata can only be accessed by Apex in the same namespace.

**When it occurs:** Designs where business users maintain thresholds or routing tables at runtime, many times a day.

**How to avoid:** Use custom metadata for configuration that changes through releases or occasional admin edits. Use a custom object (with history tracking) when users change values frequently or need record-level audit. Custom metadata queries do not count against the SOQL query limit in a transaction (*Salesforce Developer Limits and Allocations Quick Reference*), which is one reason it wins for read-heavy configuration.

---

## Gotcha 10: Event Delivery Allocations Are Shared Between Platform Events and CDC

**What happens:** An org adds CDC for an ERP sync and a platform-event feed for a data lake, each sized separately, and hits the delivery limit. The Platform Events Developer Guide ("Default Platform Event Allocations for Event Publishing and Delivery") gives a default delivery allocation of 50,000 events per 24 hours in Performance and Unlimited Editions (25,000 in Enterprise), counted per subscribed client and shared between high-volume platform events and CDC. Deliveries to Apex triggers, flows, and processes do not count. The Change Data Capture Developer Guide limits entity selection to five entities without an add-on licence.

**When it occurs:** Any design with more than one external subscriber, or more than five CDC entities.

**How to avoid:** Count subscribers times events per day across both features before choosing. Use stream filters (delivery counts after filtering, per the same guide) and custom channels to send each subscriber only what it needs. Budget the platform event add-on when the numbers exceed the default.

