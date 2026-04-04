# Gotchas — Platform Selection Guidance

Non-obvious platform behaviors that cause real production problems when platform feature choices are made without full knowledge of their constraints.

---

## 1. Custom Settings Data Is NOT Deployable via Metadata API by Default

Custom Settings records (their actual data values) are not included in Metadata API retrieve/deploy operations or change sets. The Custom Settings *type definition* (field schema) deploys as metadata, but the values in each record do not. This means every sandbox refresh or new org requires the values to be seeded separately — via Apex scripts, data loader, or custom deployment tooling.

This is the primary reason Custom Metadata Types are preferred for deployable configuration. CMT records deploy as metadata files alongside the type definition.

**Impact:** Teams that choose Custom Settings for configuration data discover this limitation the first time they try to deploy to a new sandbox or production. The workaround — seeding data via anonymous Apex in a post-deploy script — adds friction to every release. If the team uses a CI/CD pipeline, this becomes a recurring manual step unless custom tooling is built to automate it.

**Rule:** If the configuration data needs to be consistent across orgs and deployments without manual intervention, do not use Custom Settings. Use Custom Metadata Types.

---

## 2. LWC Cannot Consume Aura Application Events — Partial Migrations Break Event Chains

LWC components cannot register as handlers of Aura application events (`e.namespace:EventName`). If an org has a cross-component communication pattern built on Aura application events, migrating only the publisher component to LWC will silently break all Aura consumers — they will stop receiving events with no runtime error that clearly points to the event chain.

The reverse is also true: an Aura component cannot subscribe to a custom DOM event from a LWC sibling at the application level.

**Impact:** Teams that attempt incremental LWC migrations on a component-by-component basis, without redesigning the event communication layer first, end up with broken event wiring that is difficult to diagnose.

**Rule:** Before migrating any component that participates in cross-component Aura events, design the Lightning Message Service (LMS) channel replacement for the full event chain. Migrate all participating components together, or use the LMS channel from the LWC publisher while Aura consumers temporarily subscribe to LMS (Aura supports LMS since Spring '21).

---

## 3. Platform Events and CDC Have Different Retention Windows — External Replay Depends on Getting This Right

Platform Events retain for 72 hours (the replay window). CDC events retain for 72 hours by default; this extends to 7 days with Salesforce Shield Event Monitoring.

This distinction matters when designing integrations with external subscribers. If an external ERP or middleware goes offline for more than 72 hours, any Platform Events published during that window are lost. The subscriber cannot replay them.

**Impact:** Integration designs that assume "the subscriber can always catch up by replaying" will fail if the subscriber is offline for more than the retention window. This is especially dangerous in CDC-based sync patterns where missed events mean the external system is permanently out of sync.

**Rules:**
- If the integration requires more than 72 hours of replay tolerance, evaluate Salesforce Shield for the extended CDC window.
- If Platform Events are used and an extended replay window is critical, design a fallback: a scheduled reconciliation job that re-publishes or re-syncs any records that the subscriber may have missed.
- Document the retention assumption explicitly in the integration architecture document.

---

## 4. OmniStudio DataRaptors Are Not SOQL-Equivalent — They Have Their Own Query Model and Limitations

OmniStudio DataRaptors perform data reads, writes, and transforms declaratively, but they are not a drop-in replacement for SOQL. DataRaptors operate on a different query model: they read from a single object per Extract step, do not support arbitrary JOIN-like multi-object queries in a single operation, and have their own field mapping and transformation layer.

**Impact:** Teams that choose OmniStudio expecting DataRaptors to behave like SOQL with extra UI steps encounter limitations when trying to query data that requires relationship traversal or conditional joins. Complex cross-object reads require multiple DataRaptor steps chained together, or delegation to an Integration Procedure with multiple steps — adding design complexity.

**Rules:**
- Do not assume DataRaptors can replace arbitrary SOQL queries. Validate the data access requirements against DataRaptor capabilities before committing to an OmniScript design.
- For complex multi-object data retrieval, prefer Integration Procedures with multiple Read steps, or delegate to an Apex REST callout.
- If the team does not have OmniStudio-trained resources, the complexity of DataRaptor design often negates the declarative benefit; evaluate Standard Flow + Apex as an alternative.

---

## 5. Custom Metadata Types Cannot Store Relationship Lookups to Non-CMT sObjects

Custom Metadata Type records can have relationship fields that point to other Custom Metadata Type records (metadata relationships), but they cannot have standard lookup or master-detail relationship fields pointing to standard sObjects like Account, User, or Queue.

**Impact:** Teams that design routing rules or configuration that needs to reference a Salesforce record ID (e.g., a Queue ID, a User ID, a Pricebook ID) cannot store that reference as a proper relationship field in Custom Metadata. They must store the ID as a text field, which means:
- No lookup validation (bad ID goes undetected until runtime)
- ID is org-specific and will break when deploying across orgs unless the ID is updated post-deploy

**Rule:** If configuration data needs to reference a Salesforce record (Queue, User, Group, Pricebook), either store the developer name or API name of the referenced record and resolve it at runtime via SOQL, or evaluate whether a Custom Object is a better fit for this use case.

---

## 6. Outbound Messaging Has Delivery Guarantees That Platform Events Do Not Auto-Replicate

Outbound Messaging (legacy, tied to Workflow Rules) has a built-in retry mechanism — Salesforce retries delivery to the endpoint for up to 24 hours on failure. Platform Events do not automatically retry to external endpoints. The replay window (72 hours) allows a subscriber to re-read missed events, but only if the subscriber actively initiates the replay.

**Impact:** Teams migrating from Outbound Messaging to Platform Events sometimes assume the retry behavior transfers. It does not. External subscribers that go offline or experience errors will miss events unless they implement replay logic using the `replayId` mechanism.

**Rule:** When migrating from Outbound Messaging to Platform Events, explicitly design the subscriber replay strategy. Test failure scenarios where the external endpoint is unavailable for an extended period. If guaranteed delivery is a hard requirement, evaluate middleware (MuleSoft, Boomi) that can provide delivery guarantee semantics on top of Platform Events.
