---
name: lwc-mobile-offline-and-briefcase
description: "Use when designing LWCs that must work offline in the standard Salesforce Mobile App, and when configuring Briefcase Builder rules to prime records onto user devices. Covers form-factor detection (`@salesforce/client/formFactor`), Lightning Data Service offline-cache behavior, Briefcase priming-rule design, conflict resolution on reconnect, and the legacy SmartStore / IndexedDB picture for context. Triggers: 'briefcase builder rule design', 'lwc not working offline', 'how do I prime records to user devices', 'sync conflict on reconnect', 'offline draft persistence in lwc'. NOT for Field Service Mobile offline priming (use admin/fsl-mobile-app-setup or architect/fsl-offline-architecture — FSL has its own priming pipeline). NOT for general LWC mobile container patterns / device APIs (use lwc/lwc-offline-and-mobile)."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
triggers:
  - "how do I make my lwc work offline in the salesforce mobile app"
  - "briefcase builder rule for our service team users"
  - "users can't see records on their phone when they're offline"
  - "sync conflict appears every time the technician reconnects"
  - "lightning data service caches records but my custom lwc doesn't"
  - "how do I detect offline state from inside a lwc"
  - "draft form data is lost when the salesforce mobile app goes offline"
  - "picklist values are blank in the offline lwc"
  - "record types not appearing on offline mobile create form"
tags:
  - lwc-mobile-offline-and-briefcase
  - briefcase-builder
  - offline-priming
  - lds-offline-cache
  - mobile-conflict-resolution
inputs:
  - "Container: standard Salesforce Mobile App (iOS/Android), not FSL Mobile"
  - "User population needing offline access (which permission set / profile / group)"
  - "Records and parent-child hierarchy that must be available offline"
  - "Whether the LWC reads, writes, or both during offline use"
  - "Acceptable staleness for cached data (minutes? hours? a workday?)"
outputs:
  - "Briefcase priming rule configuration (objects, filter, parent/child relationships)"
  - "LWC implementation that detects offline state and degrades gracefully"
  - "Conflict-resolution UX strategy for write-on-reconnect"
  - "Test plan covering airplane-mode scenarios and reconnect flows"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
---

# LWC Mobile Offline and Briefcase

Activate this skill when an LWC must operate inside the standard Salesforce Mobile App with intermittent or no connectivity, and when a Briefcase Builder priming rule needs to be designed so that the records the LWC depends on are actually present on the device. The skill is about the *handshake* between Briefcase priming, LDS cache behavior, and offline-aware component code — not about general mobile UI patterns.

If the target is Field Service Mobile (the dispatcher/technician app), this is the wrong skill — FSL Mobile has its own offline priming pipeline that is configured separately and shares almost no implementation surface with Briefcase Builder. Use `admin/fsl-mobile-app-setup` instead.

---

## Before Starting

Gather this context before designing the priming rule or writing any LWC:

- **Which mobile app.** "Standard Salesforce Mobile App" (Lightning-based, available on App Store / Play Store, what most internal users see) is what Briefcase Builder targets. FSL Mobile, the Communities mobile experience, and the legacy Mobile Classic app are all different surfaces with different offline mechanisms.
- **Edition and license.** Briefcase Builder is generally available since Winter '21 and is included with Sales Cloud, Service Cloud, and most platform licenses. Verify under Setup → Briefcase Builder; if the node is missing, it's a licensing problem, not a config one.
- **Realistic offline duration.** A 30-minute commute is not the same problem as a full-shift field visit. Sub-hour use cases lean on LDS-only caching; multi-hour use cases require an explicit Briefcase rule. Above ~24 hours, conflict resolution becomes the dominant design problem, not data availability.
- **Record volume per user.** Briefcase has soft limits on records primed per user (Salesforce documents 400 records per object per user as a guideline, with a hard ceiling that varies by edition). A rule that primes "all open opportunities for the user" is fine for an AE with 20 active deals; the same rule is broken for a service rep with 5,000 open cases.
- **Read vs write.** A read-mostly offline UX (reps reviewing notes before a meeting) is straightforward; an offline-write UX (reps logging visit outcomes that will sync later) needs explicit conflict-resolution design and draft persistence.
- **Picklist / record type / profile dependencies.** Picklist value entries, record types, and dependent picklists are loaded lazily by LDS and are NOT primed by Briefcase Builder — they live in metadata and must be brought offline through a different mechanism (LDS metadata cache, which is opportunistic). This is the #1 source of "why is my offline form blank" tickets.

---

## Core Concepts

### Concept 1 — Three offline data layers, only one of which is configurable

When a user opens an LWC in the Salesforce Mobile App offline, data may come from any of three layers, in priority order:

1. **Briefcase-primed records.** Records explicitly listed in a Briefcase Builder rule for the user's assigned Briefcase. These are deterministic — if the rule says "all Accounts where Owner = current user," every matching Account is on the device after the last sync.
2. **LDS recently-viewed cache.** Records the user *opened* on the device in the last few hours. The Salesforce Mobile App caches the LDS payload for recently visited records and serves it offline as a courtesy. This is opportunistic and not configurable. Don't design an offline UX that depends on it.
3. **In-flight draft state.** Form-state held in component memory or `localStorage` by the LWC itself. Survives backgrounding but is lost if the app is force-quit unless you persist it explicitly.

Briefcase Builder is the only layer the admin/architect can directly control. The LDS cache is a backup; component-side draft persistence is the LWC author's responsibility.

The distinction matters because a typical "it works on my phone" demo shows recently-viewed-cache behavior — the demo user just opened the record, so it's cached. The same flow fails for a different user who hasn't visited that record. The fix is a Briefcase rule, not "test harder."

### Concept 2 — Briefcase Builder priming-rule shape

A Briefcase definition has three configuration surfaces:

- **Audience.** Which users get this Briefcase. Configured by Permission Set / Permission Set Group assignment. A user can belong to multiple Briefcases (the union of their primed records is what lands on the device).
- **Priming rule.** A SOQL-flavored filter on a root object — e.g., `Account WHERE OwnerId = $User.Id AND Account_Status__c = 'Active'`. The filter supports the standard SOQL operators and the special `$User.Id` token.
- **Related objects.** Optional child records to include for each primed root record. Defined as a parent → child traversal, e.g., from each Account include up to N Contacts and up to N open Opportunities. Each related object can have its own filter.

The thing that surprises most admins: only **certain object types are primable**. The supported list (per Salesforce docs) includes the common standard objects (Account, Contact, Opportunity, Case, Lead, Task, Event) and most custom objects, but excludes BigObjects, External Objects, ContentDocument blobs, AttachedContentDocument joins, and several setup/configuration object types. A rule referencing an unsupported object simply does nothing — the rule saves, the sync runs, no records appear, and there is no error message in Setup.

Limits to internalize:

- A user gets soft-limit guidance of ~400 records per object per Briefcase (consult Salesforce docs for the current published number — this has evolved).
- A user can have multiple Briefcases assigned simultaneously.
- The full Briefcase syncs at intervals controlled by the Mobile App; users do not get a "force sync now" button by default. The interval has tightened in recent releases but is not user-controllable.

### Concept 3 — LDS offline behavior vs. imperative Apex

Lightning Data Service (`@wire`, `lightning-record-form`, `lightning-record-edit-form`, `getRecord`, `getRecords`, `getRecordCreateDefaults`) is offline-aware. When the device is offline:

- `@wire(getRecord, ...)` returns the cached record if one exists, with the same shape as an online response. The component does not need any conditional offline branch — it just gets data.
- A user-initiated `lightning-record-edit-form` save while offline queues the change as a *pending action*. The Mobile App shows a queued-changes indicator. On reconnect, queued actions are submitted in order. This is the primary write path that "works offline" with no extra LWC code.
- `getRecord` for a record NOT in any cache layer returns an error, which the component must handle. Don't crash; show a "not available offline" empty state.

Imperative Apex (`@AuraEnabled` methods called from `import myMethod from '@salesforce/apex/Foo.bar'`) is **not offline-aware by default**. An imperative call while offline rejects with a network error. There is no automatic queuing, no automatic retry — the LWC author must catch the error and decide what to do (queue locally, show a friendly empty state, refuse the action).

Decision rule of thumb:

| If the LWC needs… | Use |
|---|---|
| Record CRUD on standard or custom sObjects | LDS (`lightning-record-form`, `getRecord`, `updateRecord`, `createRecord`) |
| A computed value or aggregation | Imperative Apex *with explicit offline handling* — pre-compute and cache the result on the record itself if the value matters offline |
| A custom picklist dependency map | LDS `getPicklistValues` — opportunistic offline only; design a fallback |
| External system data | Imperative Apex; assume offline = "not available" |

The rule simplifies: **lean on LDS for everything that LDS can model, and treat every imperative Apex call as online-only unless you've engineered otherwise.**

### Concept 4 — Conflict resolution on reconnect

When a user makes offline edits to a record that someone else (or another device of the same user) also edited, Salesforce Mobile applies a default last-write-wins reconciliation: the queued offline change overwrites the server value when the queued action runs.

Three problems this creates:

1. **Silent data loss for the *other* edit.** The dispatcher edited the case while the rep was in the field; rep's reconnect overwrites the dispatcher's change with no warning.
2. **Validation rule failure on sync.** Server-side validation rules fire at sync time, not at offline-edit time. A rep can fill in an offline form that violates a VR; the queued action fails on reconnect; the rep is now hours away with broken state and no recovery UI by default.
3. **Required-field added since the user went offline.** Admin adds a required field while the rep is offline; rep's queued change doesn't populate it; sync fails with a non-obvious error.

The Mobile App surfaces sync failures in a "Pending Changes" / "Sync Issues" UI, but it is opaque to the rep without coaching. For UX-critical offline write paths, the LWC should:

- Persist a draft separately from the LDS pending action (so the user can re-edit if sync fails).
- Display a "queued" indicator after a successful offline save.
- On reconnect, listen for sync errors via the standard Mobile App pending-action surface and offer a retry/edit path.

For high-stakes records (regulated industries, financial transactions, anything where silent overwrite is unacceptable), choose a *conflict-detection* pattern: before the offline edit form opens, capture `LastModifiedDate` on the record; on save, include that timestamp; if the queued action sees a later `LastModifiedDate` at sync time, route to a conflict-resolution screen instead of overwriting. This requires a custom Apex endpoint and explicit handling — it is the most expensive offline UX to build correctly.

---

## Recommended Workflow

1. **Confirm the scenario truly needs Briefcase.** If the offline window is < 1 hour and users will have already opened the records of interest, LDS recently-viewed cache is sufficient and a Briefcase rule is overhead. If the window is > 1 hour or users need data they haven't viewed yet, proceed.
2. **Audit LDS-vs-Imperative for your component.** Use the bundled `scripts/check_lwc_mobile_offline_and_briefcase.py` to walk your LWC bundles and flag imperative Apex calls — each is an offline failure point that needs explicit handling. Convert to LDS where possible; mark the rest with a "not available offline" affordance.
3. **Design the Briefcase priming rule on paper first.** Identify the root object, the filter (use `$User.Id` for owner-scoped rules), and the parent→child traversal. Estimate records-per-user under realistic conditions; if you exceed the published per-object soft limit, narrow the filter rather than splitting into multiple Briefcases.
4. **Verify object-type supportability.** Confirm every object in the rule appears in the Briefcase-supported list per Salesforce docs. ContentDocument blobs, BigObjects, and most setup objects are excluded. Substitute with a flat field on the parent object if the offline UX needs that data.
5. **Build the LWC with offline branches.** Wire LDS reads through `@wire(getRecord, ...)` rather than imperative methods. For writes, use `lightning-record-edit-form` (auto-queues on offline). For computed/aggregated values, pre-compute server-side and store on the record itself so LDS can serve them offline.
6. **Test with airplane mode, not "lost connection" simulation.** Open the Salesforce Mobile App, navigate to the LWC, enable airplane mode, exercise read and write paths, then disable airplane mode and verify the queued action lands. Repeat for force-quit-and-relaunch. Most "offline support" bugs surface at the second step, not the first.
7. **Document the conflict-resolution behavior for ops.** If your write path uses last-write-wins (the default), make sure the user-facing rollout doc says so. If you've built a conflict-detection branch, document the recovery UI and train on it.

---

## Review Checklist

- [ ] Briefcase priming rule has been designed and the audience permission set assigned to test users.
- [ ] Records-per-user estimate is below the published soft limit for every object in the rule.
- [ ] Every object referenced in the rule is on Salesforce's Briefcase-supported list.
- [ ] All imperative Apex calls in the LWC have an offline-error path (not just `.catch(noop)`).
- [ ] LDS reads (`@wire(getRecord)`) handle the "not in cache" error with an empty state.
- [ ] Forms used offline rely on `lightning-record-edit-form` or explicit `createRecord` / `updateRecord` queuing.
- [ ] Picklist values, record types, and dependent picklists have been verified to load offline (via LDS metadata cache or a fallback).
- [ ] Tested on a real device with airplane mode, including reconnect and sync-failure scenarios.
- [ ] Conflict-resolution UX (last-write-wins or detection) is documented for end users.

---

## Salesforce-Specific Gotchas

Surface-level highlights — see `references/gotchas.md` for the full list:

1. **Picklist values do not Briefcase-prime.** Custom picklists fall under metadata, not records, and rely on LDS metadata cache that is opportunistic.
2. **Record types are loaded lazily.** A user who hasn't opened a "create new Account" form recently may see no record-type options when offline, even though the Briefcase contains Account records.
3. **Long text and rich-text blobs may be truncated in cache.** Briefcase prioritizes structural fields; large blob fields can be skipped.
4. **`ContentDocument` files are not primed.** Files attached to records are pointers, not blobs, in offline cache. The file itself is not on the device.
5. **`@salesforce/client/formFactor` is `'Large'` even on tablets in landscape.** Don't use it as a proxy for "is mobile" — it's three values (`Large`, `Medium`, `Small`) and the breakpoints do not map to network state.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Briefcase priming rule design | Root object + filter + child traversal, with records-per-user estimate |
| Offline-aware LWC implementation | Component using LDS for cacheable paths and explicit error handling for imperative Apex |
| Conflict-resolution strategy | Last-write-wins (default) or detection-based (custom), with end-user UX documented |
| Airplane-mode test plan | Read/write/reconnect/force-quit scenarios with expected outcomes |

---

## Related Skills

- `lwc/lwc-offline-and-mobile` — broader LWC mobile container patterns, mobile-capability APIs, form-factor responsiveness; complement to this skill, not replacement
- `lwc/lwc-imperative-apex` — when offline analysis turns up unavoidable imperative calls, this skill covers the patterns
- `admin/fsl-mobile-app-setup` — for the Field Service Mobile equivalent (different priming pipeline entirely)
- `architect/fsl-offline-architecture` — architecture-level design for FSL offline use cases
- `apex/fsl-mobile-app-extensions` — custom-metadata and Apex patterns for FSL extensions
