# Gotchas — LWC Mobile Offline and Briefcase

Non-obvious Salesforce Mobile App + Briefcase Builder + LDS-offline behaviors that cause real production problems. Each entry corresponds to a real "why doesn't my offline LWC work" support pattern.

---

## Gotcha 1: Picklist values are blank in offline create/edit forms

**What happens:** A user opens an offline `lightning-record-edit-form` for an Account. The form renders, but the `Industry` picklist shows no options — just an empty dropdown. Saving the form with no industry selected violates a validation rule on reconnect, and the queued save fails silently from the user's perspective.

**When it occurs:** The user has not opened a "create new Account" or "edit Account" form recently enough for LDS to have cached the picklist values. Picklist values are loaded via the `getPicklistValues` adapter, which uses the LDS metadata cache — opportunistic, not guaranteed. Briefcase Builder primes record data only; metadata (picklist values, layouts, record types) flows separately and is not configurable.

**How to avoid:**
- Pre-warm the metadata cache by including a hidden component that calls `getPicklistValues` for the relevant fields on app launch — when the device is online — so the values are cached before the user goes offline.
- For genuinely offline-first scenarios with critical picklist dependencies, render a custom picklist sourced from a Custom Metadata record that you read with LDS (`getRecord` on the CMT), since CMT records can be primed via standard cache pathways.
- Document for end users that "first-time use of an offline form" requires being online once.

---

## Gotcha 2: Record types are not Briefcase-primed

**What happens:** A multi-record-type Account object has 4 record types. The Briefcase rule primes 100 Accounts to the device. When the user tries to *create* a new Account offline, the record-type picker is blank — none of the 4 record types appear. The user can't proceed.

**When it occurs:** Record types are metadata, not records. Briefcase Builder primes record rows; record-type definitions live in Setup metadata. The Salesforce Mobile App caches record-type information opportunistically (when the user has recently created a record of that type), but it is not part of any Briefcase definition.

**How to avoid:**
- For offline create flows, restrict the LWC to a single hard-coded record type via the form's `record-type-id` attribute. The user doesn't see a picker; they always create as the same record type. This works offline because no metadata lookup is needed.
- If multiple record types are required, pre-warm by ensuring the user has created at least one record of each type while online — this caches the record-type metadata.
- Avoid `lightning-record-edit-form` without a record-type-id when offline write is a requirement.

---

## Gotcha 3: Long-text and rich-text fields can be truncated in offline cache

**What happens:** A custom `Description__c` long-text field on Case is set to a 32,000-character limit. Reps see the full description while online, but only the first ~5,000 characters when offline. Long descriptions are silently truncated in the cache view.

**When it occurs:** The Salesforce Mobile App offline cache prioritizes storage efficiency. Long-text and rich-text fields have soft per-record cache limits that vary by platform and version; the published guidance has shifted over time, so treat any specific number as approximate. Briefcase priming includes these fields but the cache layer truncates long values.

**How to avoid:**
- Don't put critical, must-be-read-fully content in long-text fields if it must be offline-available. Split into shorter fields or summarize the most important content into a separate `Summary__c` short-text field.
- Test offline read flows on a real device with realistic field values, not lorem-ipsum 200-character samples.
- Document for stakeholders that long descriptions may be truncated offline; offer a "tap to view full text on reconnect" affordance.

---

## Gotcha 4: `ContentDocument` files are pointers, not blobs, in offline cache

**What happens:** A user attaches a 5 MB PDF to a Case. Briefcase primes the Case. The user goes offline and opens the case — they can see the file's title and metadata, but tapping the file shows a loading spinner that never resolves. The blob itself is not on the device.

**When it occurs:** Briefcase Builder primes record data — fields, IDs, relationships. `ContentDocument` rows are records and *can* be primed (subject to the supported-object list), but the underlying file body lives in `ContentVersion.VersionData`, which is BLOB content stored separately. The mobile app does not download `VersionData` as part of standard Briefcase priming.

**How to avoid:**
- For documents critical to the offline workflow, embed the content into a regular field (e.g., a checklist as structured JSON in a `Long_Text__c` field, rather than a PDF attachment).
- Train users that attachments require connectivity. The "files attached" indicator is informational — actual viewing needs a network round-trip.
- Use Salesforce Files external link patterns only for read-after-reconnect use cases; do not promise offline file viewing.

---

## Gotcha 5: Geolocation, location services, and offline have a timing trap

**What happens:** A "Log Visit" LWC captures the user's GPS coordinates when they tap "Save." When offline, the save succeeds (LDS queues the write), but the geolocation field is blank or stale because `navigator.geolocation.getCurrentPosition` was never resolved before the save fired.

**When it occurs:** `getCurrentPosition` requires user permission and a position fix. On a phone in a basement with no GPS lock and no cellular tower triangulation, the request can hang for 30+ seconds or fail outright. If the LWC fires `getCurrentPosition` *and* the save in parallel without awaiting the position, the queued offline write captures whatever geolocation state existed (often `null`).

**How to avoid:**
- Always `await` the geolocation result before submitting. If the request times out, surface a "couldn't get location — submit anyway?" prompt rather than silently submitting with `null`.
- Cache the last-known good position when online. Use that as a fallback for offline submissions, marked as "approximate location" in the UI.
- Set an explicit `timeout` and `maximumAge` on the `PositionOptions` parameter — defaults are platform-dependent and often surprise.

---

## Gotcha 6: A user assigned to multiple Briefcases gets the union, not the smallest one

**What happens:** Admin defines two Briefcases:

- `EU_Reps`: primes `Account WHERE Region__c = 'EU'`
- `Senior_Reps`: primes `Account WHERE Owner.Profile.Name = 'Senior Sales'`

A senior rep covering EU is assigned to both via permission set assignments. The admin expected they'd get only the intersection (EU + Senior). Instead the device receives every EU account *and* every Senior-rep-owned account globally, blowing past the per-object soft limit and triggering sync slowdowns.

**When it occurs:** Briefcase audience assignment is *additive*. A user belongs to multiple Briefcases via the union of their permission set assignments, and the device receives the union of all primed records. There is no built-in intersection or scoping mechanism.

**How to avoid:**
- Treat Briefcase audiences as mutually exclusive. Use one permission set per Briefcase and ensure users are in exactly one.
- If you genuinely need overlapping coverage, build a single Briefcase rule that expresses the combined logic with `OR` filters, rather than two separate Briefcases.
- Audit user assignments quarterly. A user accumulating Briefcase memberships through role changes is a slow path to the per-user record cap.

---

## Gotcha 7: SmartStore on legacy Mobile SDK is not the same surface as Briefcase

**What happens:** A team inherits an older Salesforce Mobile SDK app that uses SmartStore for offline cache (the encrypted IndexedDB-backed key-value store from the Mobile SDK). They assume Briefcase Builder integrates with that store. Configuring a Briefcase rule has no effect on what their SDK app sees.

**When it occurs:** Briefcase Builder is a feature of the *standard Salesforce Mobile App* (the one in App Store / Play Store). Custom apps built with the Mobile SDK use SmartStore (or the newer Mobile SDK offline managers) which are configured at the SDK level — programmatically through the SDK's `SmartSyncManager`, not through Setup → Briefcase Builder.

**How to avoid:**
- Confirm the deployment target before designing the offline strategy. "Salesforce on iOS" can mean the standard mobile app *or* a customer-built SDK app — they are different surfaces.
- For SDK apps, refer to the Mobile SDK Developer Guide for SmartStore / Mobile Sync; Briefcase Builder is irrelevant.
- For LWC components running in the standard mobile app, Briefcase is the only configurable offline-priming layer.

---

## Gotcha 8: Sync failures don't always surface to the LWC

**What happens:** A queued offline write fails on reconnect because of a validation rule. The Salesforce Mobile App marks the record with a "pending issue" indicator on the record detail page, but the LWC that originally captured the input has been unmounted long ago — there is no way for the user to know which record failed unless they navigate back to it.

**When it occurs:** Any time an offline write violates a server-side rule that didn't fire client-side: validation rules with formulas the LWC can't replicate, required fields added since the user last synced, trigger-based rejects, or duplicate rules.

**How to avoid:**
- Replicate the most-likely-to-fail validation rules in the LWC (`lightning-record-edit-form` with `onsubmit` handler that pre-validates).
- After offline submit, persist a "pending submissions" log somewhere visible (a related list on the user's home page, or a custom "My Pending Syncs" tab) so the user can see what failed.
- Train end users to check the Pending Issues area after every reconnect, not assume "no error = saved."

---

## Gotcha 9: Briefcase priming runs on a schedule the user can't control

**What happens:** A rep adds a new Case in CRM (online), then immediately goes offline. The new Case isn't primed to their device because the next priming run hasn't happened yet. The rep can't see the case they literally just created when they go offline two minutes later.

**When it occurs:** Briefcase priming runs on a server-side schedule (typically hourly, but it has tightened in recent releases). Newly-created or newly-matching records appear on the device after the next priming run, not instantly.

**How to avoid:**
- For workflows where "just-created" records must be immediately offline-available, ensure the user views the record in the mobile app *before* going offline. The LDS recently-viewed cache picks it up.
- For multi-step "create then continue offline" flows, the LWC should keep a local copy of the created record's ID and any captured fields, then re-query (or re-fetch) on reconnect rather than relying on priming.
- Set realistic expectations with end users: Briefcase is for "yesterday's data, available today," not "data created in the last 5 minutes."
