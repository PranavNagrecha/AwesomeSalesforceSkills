# Gotchas - List Views And Compact Layouts

## Broad Public List Views Become The Default By Accident

**What happens:** Users gravitate to the broadest shared view because it seems safest, even if it is noisy and not tied to an actual workflow.

**When it occurs:** Governance is weak and many public views are allowed to accumulate.

**How to avoid:** Curate a small set of authoritative list views per persona and review public sharing periodically.

---

## Compact Layouts Are Mistaken For Security Or Layout Enforcement

**What happens:** Teams assume removing a field from the compact layout hides it in a meaningful security sense.

**When it occurs:** UX configuration is used as a substitute for profile, permission-set, or page design work.

**How to avoid:** Treat compact layouts as recognition aids only. Handle actual visibility with security and full record design separately.

---

## Search Result Tuning And Browse Tuning Drift Apart

**What happens:** Search results show one set of identifying fields while list views show another, and users stop trusting both because they cannot scan consistently.

**When it occurs:** Search layouts and list views are maintained by different teams or changed reactively without a shared persona model.

**How to avoid:** Review browse and search surfaces together for the same object and user role, even though they are configured separately.

---

## Mobile Reveals Weak Compact Layout Decisions Quickly

**What happens:** A highlights panel that felt acceptable on desktop becomes unreadable or low-signal on smaller screens.

**When it occurs:** Compact layout design is reviewed only in Lightning desktop by admins with large monitors.

**How to avoid:** Validate the top compact-layout fields in the actual mobile container or with a true mobile-first workflow in mind.

---

## "Visible Only To Me" List Views Are Invisible To Metadata API

**What happens:** A migration or org comparison reports zero drift on list views, but users in the target org are missing views they had in the source. Nothing appears in the retrieve, nothing appears in the deploy log, and no error is raised.

**When it occurs:** The missing views were created with the **Visible only to me** restrict-visibility option. The Metadata API Developer Guide states it directly for `ListView`: those views "aren't accessible in Metadata API" because each one is associated with a particular user.

**How to avoid:** Treat private views as user data, not configuration. Before a sandbox refresh or an org merge, query the `ListView` object (`SELECT DeveloperName, Name, SobjectType FROM ListView`) against both orgs and reconcile against source — the object exposes views the retrieve cannot. Anything a team depends on must be re-created as a shared view before it can be deployed at all.

---

## The Absence Of `sharedTo` Is What Makes A View Public

**What happens:** A reviewer scans the list-view XML for a sharing element, finds none, and concludes the view is unshared and harmless. It is in fact visible to the whole org.

**When it occurs:** Any public list view. The guide's `SharedTo` topic says the element "is included in the metadata for shared and private list views" and "isn't in the metadata for public list views" — so the broadest possible audience is encoded as nothing at all, while a narrowly shared view is the one that carries visible markup.

**How to avoid:** Invert the review: flag list-view files that have **no** `sharedTo` element, especially when combined with `filterScope` = `Everything` and no `filters`. The skill's checker script does exactly this. A public view is a deliberate decision that should be justified in the pull request, not the default that slips through because it looks empty.

---

## List View Columns Are Legacy Tokens, Not API Names

**What happens:** A hand-written list view deploys with a column that renders blank, or the deploy fails on an unknown field, even though the field's API name is correct everywhere else in the project.

**When it occurs:** Standard fields in `columns` use legacy column tokens rather than API names. The guide states that "Field names in the ListView columns don't always match their API name counterparts", and its own sample uses `NAME` and `CREATED_DATE`. Person accounts make the mismatch systematic: a standard contact field merged into an account starts with the `PC_` prefix in the column list while the API name starts with `Person` — the column token is `PC_Email` for the API field `PersonEmail`.

**How to avoid:** Never hand-author `columns` for standard fields. Retrieve one existing list view on the object, harvest the tokens, and edit from there. Custom fields are the safe case — they use the API name (`MyCustomField__c`) directly.

---

## Creating A Queue Silently Creates A List View You Did Not Author

**What happens:** After deploying queues, the object's list-view selector has more entries than the repository does, and a later `retrieve` produces list-view files nobody wrote.

**When it occurs:** The guide notes under the `ListView` `queue` field that "When you create a queue, a corresponding list view is automatically created." Deploy five queues and you have five extra views. If somebody then also hand-authors a `filterScope` = `Queue` view for the same queue, the object carries two near-identical queues in the picker.

**How to avoid:** Decide per queue whether the auto-created view is the working view or whether a curated one replaces it, and record that decision in the object worksheet. Check the queue inventory in `admin/queues-and-public-groups` (`references/queue-behaviour-matrix.md`) before adding a `Queue`-scoped list view by hand.

---

## The Search Layout Re-Adds The Name Field On Every Deploy

**What happens:** A `searchLayouts` block is deployed, retrieved back, and the file differs from what was sent. The diff never converges, and every release ships a one-line change nobody made.

**When it occurs:** The `SearchLayouts` topic states that a text-type Name field is mandatory and always the first search-results column, that it is not returned when you query the field list, and that an autonumber Name field removed from the list "will always add the Name field back" on Metadata API import. The rule covers `customTabListAdditionalFields`, `lookupDialogsAdditionalFields`, `lookupPhoneDialogsAdditionalFields`, and `searchResultsAdditionalFields`.

**How to avoid:** Author the additional-field lists **without** the Name field and accept the platform's round-trip. If the diff still churns, retrieve immediately after a clean deploy and commit that retrieved form as the baseline rather than the hand-written one.

---

## Compact Layouts Reject Four Field Types At Deploy Time

**What happens:** A compact layout designed around a description, a set of tags, or a formatted note fails to deploy, or the field cannot be picked in Setup at all.

**When it occurs:** The `CompactLayout` topic lists the exclusions: compact layouts support all field types **except** text area, long text area, rich text area, and multi-select picklist. These are precisely the fields an admin reaches for when asked to "show what the case is about" in the highlights panel — `Case.Description` is a long text area.

**How to avoid:** Design the compact layout from identifier and state fields (number, picklist, lookup, date, currency, checkbox). When the summary text genuinely has to be visible at a glance, back it with a short formula or text field populated from the long field, and keep the long field on the record page.

---

## `ListView` And `SearchLayouts` Reject The Package.xml Wildcard, `CompactLayout` Accepts It

**What happens:** A manifest that retrieves compact layouts with `*` works, the same pattern for list views returns nothing, and a partial deploy ships compact layouts without the views and search layouts they were designed alongside.

**When it occurs:** The three types have different wildcard rules in the same manifest file. The guide records that `ListView` "doesn't support the wildcard character *", that `SearchLayouts` doesn't either, and that `CompactLayout` does. `ListView` members also need the `objectName.listViewUniqueName` form, so the unique names must be known before the manifest can be written.

**How to avoid:** Retrieve the encompassing object (`<name>CustomObject</name>` with the object as the member) when you want all three together — the guide names this as the easiest way to get a standard object's list views — and reserve the enumerated `ListView` entries for surgical, single-view changes.
