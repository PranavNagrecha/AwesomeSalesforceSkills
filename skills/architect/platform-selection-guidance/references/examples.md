# Examples — Platform Selection Guidance

---

## Example 1: Routing-Rules Configuration — CMT vs Custom Settings vs Custom Object

### Scenario

A service team needs to store routing rules that determine which queue receives a case based on the case's origin, language, and product category. There are approximately 60 routing combinations. The rules change infrequently but must be consistent across all sandboxes and production. The team uses a CI/CD pipeline with SFDX.

### Candidates Evaluated

| Feature | Pros | Cons |
|---|---|---|
| Custom Metadata Types | Deploys via Metadata API; queryable in SOQL and Flow; no per-user variant needed; works with SFDX source format | Cannot handle relationships to records (metadata relationships only reach objects, fields, entity particles, or other custom metadata types); limited to ~5,000 records (UNVERIFIED 2026-10-03) |
| Custom Settings (List) | Familiar to legacy teams | Not deployable as data via standard Metadata API; values must be seeded via Apex scripts or data tools; no hierarchy support; legacy pattern |
| Custom Object | Full CRUD; relationships possible; audit trail | Requires data migration scripts for every sandbox refresh; no formula access; adds storage overhead; no advantage over CMT for this volume |

### Decision

**Custom Metadata Types.**

Rationale: The 60 routing rules easily fit within CMT practical volume. The rules need to ship with each release and be identical across production and all sandboxes — this is exactly the CMT deployment model. The team's SFDX pipeline can include CMT records as source-tracked metadata. Custom Settings were rejected because their data values do not deploy via Metadata API without workarounds. A Custom Object was rejected because the volume does not justify the storage and data deployment overhead, and formula access to routing values is used in a validation rule.

### Implementation reference

See `admin/custom-metadata-types` for type design and field structure. See `apex/custom-metadata-in-apex` for the Apex reader pattern.

---

## Example 2: UI Upgrade Decision — Aura Component with Complex Event Wiring to LWC

### Scenario

A financial services org has a case detail sidebar built as an Aura component. It fires an Aura application event (`e.c:CaseContextChanged`) that is consumed by three other Aura components on the same Lightning page. The team wants to rebuild this in LWC for performance and to enable Experience Cloud deployment. An Experience Cloud community is being planned.

### Assessment

| Concern | Finding |
|---|---|
| Aura application event model | `e.c:CaseContextChanged` broadcasts to all registered handlers. LWC does not support Aura application events. The event must be redesigned. |
| LWC equivalent | LWC custom events bubble up the DOM. A Lightning Message Service (LMS) channel can replace the cross-component broadcast pattern. |
| Incremental migration risk | The three consuming components also need to migrate. Migrating only the publisher component while consumers remain Aura will break the event chain. |
| Experience Cloud | LWC is fully supported. The migrated components will work in the Experience Cloud site without additional wiring. |

### Decision and Migration Path

1. Design a Lightning Message Service channel to replace the Aura application event. This is the LWC-native cross-component messaging mechanism.
2. Build the new LWC sidebar publisher component first, publishing to the LMS channel instead of the Aura application event.
3. Build LWC replacements for all three consumer components, subscribing to the LMS channel.
4. Deploy all components and switch the Lightning page to use the LWC versions.
5. Retire the Aura components once the LWC page is stable in production.

**Do not attempt to migrate one component at a time while keeping Aura components in the event chain.** The Aura application event is not visible to LWC components; a partial migration would silently break consumers.

### Risk Register

| Risk | Mitigation |
|---|---|
| LMS channel message schema differs from original Aura event payload | Map all payload fields during component design; add integration tests before go-live |
| Team unfamiliarity with LMS | Include LMS channel design in sprint planning; allocate spike time |
| Experience Cloud page layouts need updating | Schedule page layout migration as part of the same sprint as component deployment |

---

## Example 3: Integration Pattern Selection — CDC vs Platform Events for External ERP Sync

### Scenario

A manufacturing org syncs its Salesforce Order records to an external ERP. The ERP needs to know when Order Status, Quantity, and Ship Date fields change so it can update fulfillment queues. Currently the integration uses Outbound Messaging tied to a Workflow Rule (now retired).

### Candidates Evaluated

| Pattern | Assessment |
|---|---|
| Platform Events | Publisher would need to explicitly publish an event on every relevant field change; subscriber cannot tell which fields changed from the event payload alone; requires field-level change tracking logic in the event publisher |
| Change Data Capture | Salesforce automatically emits a change event for every Order record change; the event payload includes `changedFields` — the ERP subscriber can filter for the three relevant fields without any custom publisher logic |
| Outbound Messaging | Legacy — tied to retired Workflow Rules; do not extend |

### Decision

**Change Data Capture.**

Rationale: The ERP needs field-level delta information. CDC events include `changedFields` automatically — no custom publisher logic required. The subscriber filters on the three fields of interest. Platform Events were rejected because they would require custom logic to detect and publish field-level changes, duplicating what CDC provides natively. Outbound Messaging is not a viable option with Workflow Rules retired.

### Implementation notes

- Enable CDC for the Order object in Setup > Integrations > Change Data Capture.
- The ERP subscriber connects via Pub/Sub API or CometD.
- Correction (2026-10-03): earlier text said to configure Shield Event Monitoring for a 7-day CDC retention window (standard 72 hours). The Change Data Capture Developer Guide stores change events for up to three days and documents no extension; plan a reconciliation extract for outages longer than that.
- Test replay behavior: if the ERP goes offline, verify the subscriber can replay missed events within the retention window.

---

## Example 4: Decision Record for Storing Case Routing Thresholds and Publishing Changes to a Data Lake

**Context:** A Service Cloud Enterprise Edition org routes cases by product, language, and severity using 140 threshold rows. Thresholds change about once a month through the release pipeline. One value, the overflow queue, differs for the night-shift supervisor profile. The routing code also calls a partner API with a key that is currently stored in a list custom setting. A data lake wants every change to `Case` and `CaseComment`, and a separate fraud service wants only cases flagged high risk. The org has an Experience Cloud help site with guest access.

**Decision record (machine-readable form):**

```yaml
adr: PLT-014
title: Configuration storage and event pattern for case routing
status: accepted
date: 2026-10-03
decisions:
  - id: D1
    need: 140 routing thresholds that ship with each release
    choice: Custom Metadata Type Routing_Threshold__mdt
    deployable_members:            # package.xml member forms (Metadata API, CustomObject and CustomMetadata)
      CustomObject: Routing_Threshold__mdt
      CustomMetadata: [Routing_Threshold.EMEA_Sev1, Routing_Threshold.EMEA_Sev2, "..."]
    why: records deploy as metadata; queries do not count against the SOQL query limit
    rejected:
      - option: list custom setting
        reason: data values do not deploy; tests cannot see the data without SeeAllData or setup
      - option: custom object
        reason: changes go through releases, not runtime edits; no need for record-level audit
  - id: D2
    need: overflow queue that differs for one profile
    choice: hierarchy Custom Setting Routing_Override__c (org default + one profile row)
    why: only hierarchy custom settings resolve org, profile, and user values; seeded by a post-deploy step
    stores: queue DeveloperName, not the queue Id (custom metadata cannot look up records)
  - id: D3
    need: partner API key
    choice: Named Credential Partner_Routing_API with an External Credential
    why: unprotected custom settings are readable by every profile, including the guest user
    action: rotate the existing key, which has been readable by the guest profile
  - id: D4
    need: data lake receives every Case and CaseComment change
    choice: Change Data Capture on Case and CaseComment (2 of the 5 entities allowed without an add-on)
    retention: up to three days; nightly reconciliation by SystemModstamp covers longer outages
  - id: D5
    need: fraud service receives high-risk cases only
    choice: custom platform event High_Risk_Case__e published by a record-triggered flow
    why: application-level event with only the fields the fraud service needs
allocation_check:   # Platform Events Developer Guide default delivery allocation, Enterprise Edition
  daily_delivery_allocation: 25,000 events per 24 hours, shared by CDC and high-volume platform events
  estimate: {data_lake_cdc: 14,000, fraud_events: 600, total: 14,600}
  headroom: about 10,400 events; add-on not needed today, revisit at 20,000
consequences:
  - post-deploy step seeds Routing_Override__c in every new sandbox
  - CDC subscriber stores its last replay ID durably and alerts at 48 hours of lag
```

**Why it works:** each store matches how its values change and who must see them, the secret leaves readable configuration, the record reference is stored by name so it survives deployment, and the event design is sized against the shared delivery allocation before anyone builds it.

