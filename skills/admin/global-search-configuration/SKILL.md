---
name: global-search-configuration
description: "Configure platform-level global search in a Salesforce org — per-object Search Layouts (Search Results, Lookup Dialogs, Lookup Phone Dialogs, Tab columns), the Setup → Search Settings page (Sidebar Search, Lookup Auto-Completion, Drop-Down List size), and Synonym Groups (Setup → User Interface → Synonyms). NOT for Einstein Search personalization signals or Natural Language Search (use agentforce/einstein-search-personalization), NOT for Experience Cloud site Search Manager (use lwc/experience-cloud-search-customization), NOT for SOSL query authoring (use data/sosl-search-patterns), NOT for Commerce storefront search tuning."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
  - Performance
triggers:
  - "users complain the columns shown in global search results are not the fields they need"
  - "how do I add a custom synonym group so searching 'VIP' also finds 'Priority' accounts"
  - "lookup dialog on Account field is missing Industry column — how do I add it"
  - "Setup → Search Settings page is confusing — what controls global search vs lookup vs sidebar"
  - "external object records are not appearing in global search even though the data source is active"
  - "how do I configure search layouts at scale across many custom objects"
  - "newly created record is not appearing in global search results yet"
tags:
  - global-search
  - search-layouts
  - synonym-groups
  - lookup-dialog
  - search-settings
  - admin-configuration
  - tab-columns
inputs:
  - "object scope (which sObjects' search layouts need configuration)"
  - "user populations affected (so the right Search Layout assignment context is known)"
  - "any pre-existing synonym groups the org wants to keep or override"
  - "whether the org has Lightning Experience only, Classic only, or both (some settings are surface-specific)"
  - "whether the org uses Einstein Search (changes the layering between admin-controlled and AI-controlled ranking)"
outputs:
  - "per-object Search Layout configuration plan (Search Results, Lookup Dialogs, Lookup Phone Dialogs, Tab columns, Search Filter Fields)"
  - "Synonym Group inventory and additions, with active/inactive choices justified"
  - "Search Settings configuration table (Sidebar Search, Lookup Auto-Completion, Drop-Down List size, Limit to Recently Viewed)"
  - "External object searchability validation (Allow Search on data source, SOSL-capable adapter)"
  - "audit checklist confirming FLS, sharing, and search index assumptions hold for the configured layouts"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-19
---

# Global Search Configuration

Activate when an admin is configuring how global search behaves in a Salesforce org — what columns appear in search results, which fields users can search and filter by, what synonyms map to each other, and how lookup dialogs render. This skill covers the platform-level admin features that work regardless of whether Einstein Search is enabled. Einstein Search ranking signals, Natural Language Search, and Experience Cloud site search are separately scoped.

---

## Before Starting

Gather this context before changing any search-related setting:

- **Surface matrix.** Lightning Experience only, Classic only, or both? Several Search Settings are Classic-specific (Sidebar Search, Single Search Result for Single Match) and have no effect in Lightning.
- **Edition.** Synonyms and per-object Search Layouts are available on every edition that ships Lightning. Einstein Search features layer on top in Enterprise+ — confirm whether the org is relying on the admin layer alone or has Einstein Search active too.
- **Permissions.** Editing per-object Search Layouts and Synonym Groups requires the **Customize Application** system permission. Granting it broadly is a common mistake — most admins only need scoped object access via Permission Sets.
- **Search index lag.** Records added or updated do not appear in search results instantly. Index lag is typically a few minutes for record-level changes and longer for bulk loads. Treat "doesn't appear in search" as a possible indexing wait, not a configuration bug, for the first 15 minutes after a change.
- **Pre-existing synonym pack.** Salesforce ships hundreds of standard synonym groups (geographic abbreviations, common business terms). Disabling a standard group is rare and reversible; never delete one without checking who else in the org relies on it.

---

## Core Concepts

### Search Layouts — Per-Object, Per-Surface

`Setup → Object Manager → <Object> → Search Layouts` exposes five layout slots per object:

| Layout slot | Where it renders | Hard limits |
|---|---|---|
| **Default Layout (Lightning)** | Columns shown in Lightning global search results for this object | Up to 10 columns; first column is always the record name |
| **Search Results (Classic)** | Columns shown in Classic global search results | Up to 10 columns |
| **Lookup Dialog** | Columns when a user opens a lookup picker from a record field referencing this object | Up to 10 columns (Lightning) / 6 (Classic) |
| **Lookup Phone Dialog** | Lookup picker variant invoked from telephony / CTI surfaces | Up to 10 columns |
| **Tab** | Columns when a user lands on the object's tab and has not selected a list view | Up to 10 columns |
| **Search Filter Fields** | Fields available as filterable facets in Lightning global search results | Up to 5 fields |

The five slots are independent — changing the Search Results layout does **not** change the Lookup Dialog layout, and Lightning Experience does not auto-mirror Classic Search Results. Layouts are stored as the `SearchLayout` block inside each `CustomObject` metadata file and deploy via standard package XML.

### Setup → Search Settings (Not Einstein Search Settings)

`Setup → Search Settings` is a distinct page from `Setup → Einstein Search → Settings`. The classic admin page controls platform-level behaviors:

- **Lookup Auto-Completion** — per-object toggle. When on, lookup fields show a type-ahead drop-down of recently viewed records of the target object before the user finishes typing.
- **Drop-Down List size** — number of items in the type-ahead drop-down (default 5; max 10).
- **Limit to Recently Viewed Records** — when on, the lookup auto-complete only returns records the current user has viewed recently (faster, narrower).
- **Sidebar Search Settings** (Classic only) — Single Search Result for Single Match (auto-navigate when a single match), Search Auto-Complete in the global sidebar input.
- **Number of Search Results displayed per Object** (Classic only) — caps results per object on a search page.

These settings are org-wide. They cannot be overridden per profile or permission set.

### Synonym Groups

`Setup → User Interface → Synonyms` lets admins define equivalence groups so that a search for one term also matches records containing any other term in the same group.

Mechanics:
- Each Synonym Group is a comma-separated list (e.g., `VIP, Priority, Important, Strategic`).
- Salesforce ships a managed pack of standard synonym groups (e.g., `Inc, Inc.`, `St, Saint`). Standard groups can be deactivated but not deleted.
- Custom groups are searched **in addition to** active standard groups. There is no "replace" mode — adding a custom group adds matches; it does not remove them.
- Limit: **2,000 active synonym groups per org**.
- Synonyms apply to all searchable text fields on all standard and custom objects. They cannot be scoped per object.

### Searchable Objects vs. Searchable Fields

Two different concepts. An object is "searchable" if it's in the search scope (controlled in Lightning by Search Results object configuration and Setup-level toggles). A field is "searchable" if it's a text-like field type marked indexable — most standard and custom text/long-text/email/phone fields are searchable; rich text, encrypted, and many formula fields are not.

External Objects are searchable only when:
1. The **External Data Source** has **Allow Search** enabled (Setup → External Data Sources → <source> → checkbox).
2. The adapter type supports SOSL — OData 2.0 and OData 4.0 adapters support it; Cross-Org and custom adapters may not.
3. The external object's individual **Allow Search** flag is on (`External Object → Edit → Allow Search`).

All three must be true. The default for both flags is off, which is why external objects are commonly "missing from search" right after creation.

### Search Index and FLS Behavior

Salesforce maintains a separate search index from the live data store. A few non-obvious behaviors:

- **Index lag is normal.** A record created via DML or Bulk API is not in the search index until indexing completes (typically minutes; up to ~15 minutes after very high-volume loads).
- **Updates re-index too.** Renaming an account from "Acme" to "Acme Inc" can leave the new name un-indexed for a brief window — searching "Acme Inc" may miss it briefly while "Acme" still hits.
- **FLS hides field values from result column rendering but not from matching.** A search results row will appear if the indexed field matches the query, but a column the user lacks FLS on renders as blank. This can confuse users into thinking results are wrong when they're actually right but visually empty.
- **Sharing rules still filter results.** Even if a field matches, the user only sees records they have read access to. A query that matches private records owned by another user simply returns nothing rather than an "access denied" error.

---

## Common Patterns

### Pattern: Org-Wide Search Layout Audit and Refresh

**When to use:** New org launch, post-migration cleanup, or a Lightning rollout from Classic where Search Layout defaults are still Classic-era columns (Name, Owner, Modified Date and not much else).

**How it works:**

1. List every object in scope (`tooling_query("SELECT QualifiedApiName FROM EntityDefinition WHERE IsCustomizable = true AND IsSearchable = true")`).
2. For each object, retrieve metadata and read the `<searchLayouts>` block — note which columns are configured for each slot.
3. Identify objects where the Default Layout (Lightning) is empty or contains only Name. These objects render a one-column search result and are the most painful for users.
4. Define a target column set per object based on what fields users actually scan in record list views — typically Name, Owner, Phone (Contact/Account), Status (Case/Opportunity), Modified Date.
5. Deploy via Metadata API or Object Manager. Validate per surface (Lightning global search bar, Classic search if applicable, lookup dialogs on related objects).

**Why not the alternative:** Letting users fix it via their own personalization is impossible — Search Layouts are admin-only and not user-personalizable. Every user sees the admin-configured columns until the admin changes them.

### Pattern: Custom Synonym Group for Domain Vocabulary

**When to use:** Users speak a domain shorthand that doesn't match the data ("VIP" customers stored as "Priority", "BD" stored as "Business Development").

**How it works:**

1. List the vocabulary variants users actually search for (interview reps; check support ticket subjects).
2. Confirm the data representation — what's the canonical word in the Name or text fields?
3. Create a Synonym Group: `Setup → User Interface → Synonyms → New Synonym Group`. Add the canonical word and every variant. Use commas, no spaces required (Salesforce strips whitespace).
4. Mark the group Active.
5. Allow ~15 minutes for the search index to incorporate the new group, then validate with representative queries.

**Why not the alternative:** Renaming records or maintaining "alias" custom fields creates data duplication and reporting drift. Synonyms operate purely at the search layer and leave the data model untouched.

### Pattern: External Object Search Enablement

**When to use:** A Salesforce Connect external object has data, page layouts work, but the records never appear in global search.

**How it works:**

1. `Setup → External Data Sources → <source>` — confirm **Allow Search** is checked. If not, check it and save.
2. `Setup → External Objects → <object> → Edit` — confirm **Allow Search** is checked at the object level.
3. Confirm the data source adapter is one that supports SOSL on external data (OData 2.0 / OData 4.0). Cross-Org adapters and most custom Apex adapters do not.
4. For OData adapters: confirm the remote service exposes a SOSL-equivalent endpoint or returns a usable schema for Salesforce's search query translation.
5. Validate with a SOSL query in Developer Console: `FIND {<term>} IN ALL FIELDS RETURNING ExternalObject__x` — if this returns rows but global search doesn't, the issue is in the per-object Search Layout (Default Layout has no columns, so results are invisible).

**Why not the alternative:** Telling users "search doesn't work for external objects" is a workaround, not a fix. The platform supports it; the configuration steps are just usually missed.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Users see only Name in global search results | Add 3–6 useful columns to the Default Layout (Lightning) Search Layout for each high-traffic object | One-column results force users to click into every record to disambiguate |
| Users search shorthand the data doesn't store | Custom Synonym Group at `Setup → User Interface → Synonyms` | Operates at the search layer; no data model change required |
| Lookup picker for an Account field shows only Name | Edit `Account → Search Layouts → Lookup Dialog` to add Industry, Phone, Owner | Lookup Dialog is a separate slot from Search Results; both must be configured |
| Org migrated to Lightning but search columns are stuck on Classic-era fields | Audit and refresh the **Default Layout** slot on every searchable object | Default Layout (Lightning) is independent of Search Results (Classic) |
| External object missing from global search | Enable Allow Search on both data source AND external object; confirm adapter supports SOSL | All three gates must be open; default for each is off |
| Need keyword aliasing for one specific object | Synonym Groups are org-wide — there is no per-object scope. Decide whether the alias is harmless on other objects | If not, consider a saved search or a custom Search experience instead of a synonym |
| Newly created record not in search | Wait 15 minutes; if still missing, confirm the field is searchable and the user has FLS + sharing access | Index lag is the default explanation; configuration is rarely the cause for new records |
| Many objects need the same Search Layout refresh | Deploy via Metadata API as a `package.xml` containing `CustomObject` entries with updated `<searchLayouts>` | Object Manager click-ops at scale is error-prone; metadata deploys are diff-able and repeatable |

---

## Recommended Workflow

1. **Inventory the surface matrix.** Confirm Lightning vs Classic usage. Confirm Einstein Search is on or off. Confirm which user populations rely on global search heavily versus those who navigate via list views or related lists. The configuration priorities follow real usage.

2. **Audit per-object Search Layouts.** For each searchable object, capture the current state of all five slots (Default Layout, Search Results, Lookup Dialog, Lookup Phone Dialog, Tab) and Search Filter Fields. Note objects whose Default Layout has fewer than three columns — they are the highest-impact fixes.

3. **Define target columns per object.** For each object, agree with stakeholders on the column set users need to scan a result row: typically Name + owner + status field + a date or quantity field. Honor the 10-column limit (Lightning) / 6-column limit (Classic Lookup Dialog).

4. **Audit and extend Synonym Groups.** Pull the list of active groups (`Setup → User Interface → Synonyms`). Identify domain vocabulary gaps. Author custom groups, keeping under the 2,000-active-group cap. Test with representative search queries after a ~15-minute indexing wait.

5. **Configure Setup → Search Settings.** Validate Lookup Auto-Completion is enabled for objects that need it. Set Drop-Down List size to 10 if users frequently search picklist-style lookups. Disable Sidebar Search settings that are Classic-only if the org is Lightning-only.

6. **Validate external objects.** For each Salesforce Connect external object expected in search, confirm Allow Search on data source + Allow Search on external object + SOSL-capable adapter. Run a SOSL probe in Developer Console as the final check.

7. **Deploy and document.** Push changes via Metadata API where possible. Update the org's Configuration Workbook with the Search Layouts and Synonym Groups in effect, so future admins inherit the rationale.

---

## Review Checklist

- [ ] Per-object Search Layouts audited for all five slots on every searchable object
- [ ] Default Layout (Lightning) populated with at least 3 useful columns on every high-traffic object
- [ ] Lookup Dialog Search Layout configured separately from Search Results
- [ ] Search Filter Fields configured for objects where users want faceted filtering
- [ ] Synonym Group inventory captured; custom groups deployed and active
- [ ] Synonym Group count remains under 2,000 active
- [ ] Setup → Search Settings reviewed (Lookup Auto-Completion, Drop-Down List size, Sidebar Search where Classic applies)
- [ ] External objects' Allow Search flags verified at both data source and object level
- [ ] FLS confirmed for every column added to a Search Layout (hidden FLS will render blank columns)
- [ ] Customize Application permission scoped to the right admin users only
- [ ] Configuration Workbook updated with current Search Layout and Synonym state
- [ ] Indexing-wait expectation documented for future admins ("changes take ~15 min to appear")
- [ ] Boundary documented with `agentforce/einstein-search-personalization` if Einstein Search is also configured

---

## Salesforce-Specific Gotchas

1. **Default Layout (Lightning) and Search Results (Classic) are independent slots.** Editing one does not change the other. Lightning-only orgs frequently leave Search Results un-configured because they assume Default Layout covers it — but Default Layout only renders in Lightning global search, not in Classic if a Classic user logs in.
2. **Synonym Groups are org-wide and cannot be scoped by object or profile.** A "VIP, Priority" group affects Account search, Contact search, Case search, custom object search — everywhere. Adding a domain shorthand that happens to also be a common dictionary word can produce noisy matches.
3. **Standard Synonym Groups cannot be deleted, only deactivated.** Some standard groups (geographic abbreviations, business-entity suffixes) are baseline assumptions users rely on. Deactivating a standard group risks breaking expected behavior org-wide.
4. **Search Layout column count limit is 10 — record Name counts.** The first column slot is always Name and cannot be replaced. Configuring 10 columns including Name effectively gives you 9 user-chosen columns.
5. **Lookup Dialog limit is 6 columns in Classic, 10 in Lightning.** Configuring 10 columns deploys cleanly but the Classic Lookup Dialog will render only the first 6. If the org has any Classic users, validate column priority order.
6. **Hidden FLS renders as blank columns, not as access-denied errors.** Users searching with FLS-restricted fields in their Search Layout will see blank cells and assume the data is missing or the result is wrong. Audit FLS for every field added to a Search Layout.
7. **External objects need three independent Allow Search toggles** (data source, external object, adapter-supports-SOSL). All default off. The error mode is silent — search just returns zero rows for the external object.
8. **Search index lag means change-then-test-immediately produces false-negative test results.** Wait ~15 minutes after a Search Layout, Synonym, or external object change before validating, especially in sandbox.
9. **Drop-Down List size is org-wide, not per-object.** A change for one painful lookup affects every lookup in the org.
10. **Customize Application is a powerful permission.** Grant it via narrowly scoped Permission Sets, not via profile updates — and not at all to non-admin populations.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Search Layout audit report | Per-object inventory of current columns in each of the 5 layout slots, with gap analysis |
| Search Layout target configuration | Per-object proposed column set per slot, ready for Metadata API deploy |
| Synonym Group inventory | Active standard groups, active custom groups, proposed additions, total count vs 2000 cap |
| Search Settings configuration table | Lookup Auto-Completion, Drop-Down List size, Sidebar Search settings — current vs target |
| External object searchability matrix | For each external object: data source Allow Search, object Allow Search, adapter SOSL support, validation status |
| FLS validation report | For every column in every Search Layout, the profiles/permission sets that have FLS and the populations that do not |
| Configuration Workbook section update | Search Layouts and Synonyms section refresh for the org's master config doc |

---

## Related Skills

- `agentforce/einstein-search-personalization` — Einstein Search ranking signals, Natural Language Search, promoted results; layers on top of admin-controlled Search Layouts.
- `lwc/experience-cloud-search-customization` — Search Manager in Experience Builder sites, federated search, guest user search rules.
- `data/sosl-search-patterns` — SOSL query authoring for Apex; SOSL is the underlying mechanism global search uses.
- `admin/list-views-and-compact-layouts` — Adjacent UX layer: list views and compact layouts on records.
- `data/data-virtualization-patterns` — Salesforce Connect external object basics; pair when external-object search misses are diagnosed.
- `security/api-security-and-rate-limiting` — Search API limits if global search is consumed via API rather than UI.
