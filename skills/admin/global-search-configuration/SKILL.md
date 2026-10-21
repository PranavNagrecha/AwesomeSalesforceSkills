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
  - "Synonym Group inventory and additions, with a scope-impact check per group"
  - "Search Settings configuration table (Sidebar Search, per-object Lookup Auto-Completion and results per page, blank User lookup source)"
  - "External object searchability validation (Enable Search on the data source, Allow Search on the external object, adapter SEARCH capability)"
  - "audit checklist confirming FLS, sharing, and search index assumptions hold for the configured layouts"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Global Search Configuration

Activate when an admin is configuring how global search behaves in a Salesforce org — what columns appear in search results, which fields users can search and filter by, what synonyms map to each other, and how lookup dialogs render. This skill covers the platform-level admin features that work regardless of whether Einstein Search is enabled. Einstein Search ranking signals, Natural Language Search, and Experience Cloud site search are separately scoped.

---

## Before Starting

Gather this context before changing any search-related setting:

- **Surface matrix.** Lightning Experience only, Classic only, or both? Several Search Settings are Classic-specific: advanced sidebar search is "Available in Salesforce Classic only" and the single-result shortcut "doesn't apply to ... global search" (api_meta 264 L129105-129106, L129213-129217).
- **Edition.** Confirm whether the org relies on the admin layer alone or has Einstein Search active too (`enableEinsteinSearchPersonalization`, Lightning Experience only, api_meta 264 L129134-129136). UNVERIFIED (2026-10-20): edition availability of synonyms, search layouts and Einstein Search is Help-only.
- **Permissions.** Synonym groups need the **Manage Synonyms** permission: "Only users with the 'Manage Synonyms' permission can access this object", and synonyms must be enabled in the org (api_meta 264 L136378). Editing per-object Search Layouts uses **Customize Application** (UNVERIFIED (2026-10-20): no corpus line names the search-layout permission); grant it through scoped Permission Sets.
- **Search index lag.** "After a searchable object's record is created or updated, it could take about 15 minutes or more for the updated text to become searchable" (ldv 264 L160-162). Treat "doesn't appear in search" as an indexing wait, not a configuration bug, for at least 15 minutes after a record change.
- **Pre-existing synonyms.** `enableSalesforceGeneratedSynonyms` "indicates whether search synonyms are enabled" (api_meta 264 L129148-129149). UNVERIFIED (2026-10-20): the size and content of a Salesforce-shipped standard synonym pack, and that standard groups can be deactivated but not deleted, are Help-only.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Do different profiles need different search result columns? | The default layout applies only where no profile layout exists (Gotcha 1) | `profileSearchLayouts` entries instead of one compromise layout |
| Could a proposed synonym mean something else on another object? | Synonym groups carry no object scope (Gotcha 2) | A scope-impact check per term |
| Is any standard synonym group producing unwanted matches? | Standard groups are deactivated, not deleted (Gotcha 3) | A documented deactivation and a custom replacement |
| Are there still Classic users? | Classic sidebar settings and lookup caps differ (Gotcha 5) | Column priority order that works on both |
| Which search-layout fields are FLS-restricted for some users? | Restricted columns render blank (Gotcha 6) | An FLS matrix per added column |
| Which external objects must be searchable, and through which adapter? | Every search gate must be on (Gotcha 7) | Enable Search, Allow Search and `SEARCH` capability confirmed |
| When will testing happen relative to the change or data load? | Record index lag is about 15 minutes or more (Gotcha 8) | A test plan with an index wait |

UNVERIFIED (2026-10-20): row 3 (standard groups deactivated, not deleted), row 4's Classic lookup caps, and row 5 (blank rendering of restricted columns) are Help-only.

A proper configuration adds per-profile layouts, scoped synonyms and an index-aware test plan, where "just doing it" leaves blank columns and false-negative tests.

---

## Core Concepts

### Search Layouts — Per-Object, Per-Profile

`Setup → Object Manager → <Object> → Search Layouts` maps to the `SearchLayouts` type, reachable "only by accessing its encompassing CustomObject" (api_meta 264 L47496-47498). Its column lists (L47518-47595):

| Metadata field | What it controls |
|---|---|
| `searchResultsAdditionalFields` | Search results columns — the default layout "used when no layout is specified for a user profile" (L47265-47266, L47580-47582) |
| `profileSearchLayouts` (on CustomObject) | A different search results layout per profile — the CustomObject field says API 47.0+ (L44503-44506), the ProfileSearchLayouts page says 48.0+ for custom objects (L47270) |
| `lookupDialogsAdditionalFields` | Lookup dialog columns (L47528) |
| `lookupPhoneDialogsAdditionalFields` | Phone-related lookup columns for softphone integration (L47557-47560) |
| `customTabListAdditionalFields` | The Recent records list on the object's tab (L47518-47519) |
| `searchFilterFields` / `lookupFilterFields` | Fields that filter a search / an enhanced lookup (L47574-47575, L47550-47552) |

A text-type Name field "is mandatory; it's always displayed as the first column" and is not returned in the field list (L47509-47510). The lists are independent fields — changing `searchResultsAdditionalFields` does not change `lookupDialogsAdditionalFields`. The corpus documents ONE search-results list per object (plus per-profile overrides); it does not describe separate Lightning and Classic search-results lists. `SearchLayouts` does not support the `*` wildcard (L47621-47622). UNVERIFIED (2026-10-20): per-list column caps (10 columns; 6 in a Classic lookup dialog; 5 search filter fields) are Help-only.

### Setup → Search Settings (Not Einstein Search Settings)

`Setup → Search Settings` is a distinct page from `Setup → Einstein Search → Settings` (UNVERIFIED (2026-10-20): Setup page names). It maps to the `SearchSettings` type, "an org's search settings", stored in `settings/Search.settings` (api_meta 264 L129087-129093). The same type also carries the Einstein toggles — `enableEinsteinSearchNaturalLanguage`, `enableEinsteinSearchPersonalization` (L129127-129136) — so the two-page split is a UI fact only; in metadata both live in one file:

- **Lookup Auto-Completion** — per object: `lookupAutoCompleteEnabled`, "when users edit the lookup field inline by choosing an autosuggestion" (L129243-129245); `enhancedLookupEnabled` sits beside it (L129240).
- **Search results per page** — per object: `resultsPerPageCount`, "the number of search results per page" (L129249).
- **Blank User lookup source** — `recentlyViewedUsersForBlankLookupEnabled` "only applies to User object blank lookup searches" (L129189-129194); it does not narrow lookups on other objects.
- **Sidebar search** (Classic) — `sidebarAutoCompleteEnabled`, `sidebarDropDownListEnabled` (a list to search within tags, one object, or all objects — a toggle, not a size), `sidebarLimitToItemsIOwnCheckboxEnabled`, `singleSearchResultShortcutEnabled` (L129198-129217).

The type is org-level with a per-object list (`searchSettingsByObject`, L129196); it has no profile or permission-set dimension. UNVERIFIED (2026-10-20): a numeric "Drop-Down List size" (default 5, max 10) — no SearchSettings field holds one.

### Synonym Groups

`Setup → User Interface → Synonyms` lets admins define equivalence groups so that a search for one term also matches records containing any other term in the same group.

Mechanics:
- Metadata: `SynonymDictionary` (suffix `.synonymDictionary`, folder `synonymDictionaries`) holding `SynonymGroup` entries (api_meta 264 L136361-136401).
- Each group needs `languages` (Required) and at least two `terms`, each "Maximum of 50 characters" (L136404-136410).
- Groups are symmetric: "a search for oranges will return a match for apples, and vice versa" (L136411-136413).
- UNVERIFIED (2026-10-20): a Salesforce-shipped standard pack that can be deactivated but not deleted, custom groups searched in addition to it, a 2,000-active-group org limit, that synonyms apply to every searchable object with no per-object scope, and any Active/Inactive state on a group (`SynonymGroup` has only `languages` and `terms`, L136400-136410) — none is on a corpus line.

### Searchable Objects vs. Searchable Fields

Two different concepts. A custom object is searchable when `enableSearch` ("Allow Search" in the UI) is true; "by default, search is turned off for new custom objects", and Einstein Search turns searchability off for custom objects not searched for more than 120 days (api_meta 264 L44347-44351). UNVERIFIED (2026-10-20): which field types are searchable (rich text, encrypted, formula) is Help-only.

External Objects are searchable only when:
1. The **External Data Source** has **Enable Search** on — `searchEnabled` in its `customConfiguration`, a parameter of both the Cross-Org and the OData 2.0/4.0 adapters (api_meta 264 L13818-13826, L13830-13850).
2. For a custom Apex adapter, the adapter declares the `SEARCH` capability, which "allows SOSL and Salesforce searches of the external data" (apexref 262 L151747-151751).
3. The external object's **Allow Search** (`enableSearch`) is on — "by default, search is turned off for new external objects", and a sync sets it to match the data source (api_meta 264 L44352-44354).

Only text, text area, and long text area fields on external objects are searched (apexref 262 L151752). UNVERIFIED (2026-10-20): the data source's own default for Enable Search.

### Search Index and FLS Behavior

Salesforce maintains a separate search index from the live data store. A few non-obvious behaviors:

- **Index lag is normal.** Indexing servers "asynchronously process queue entries of newly created or modified data"; a created or updated record "could take about 15 minutes or more" to become searchable (ldv 264 L160-162).
- **Updates re-index too.** Renaming an account from "Acme" to "Acme Inc" leaves the new name un-indexed for that same window — searching "Acme Inc" may miss it while "Acme" still hits.
- **FLS hides field values from result column rendering but not from matching.** A column the user lacks FLS on renders as blank. UNVERIFIED (2026-10-20): this rendering behaviour is Help-only. Grounded: a search layout is not a security control — "to hide a field that's not protected by field-level security, omit it from the layout" (secguide 262 L2384-2385).
- **Access still filters results.** Search narrows the index hits "based on access permissions, search limits, and other filters" (ldv 264 L171-172), so a match on a record the user cannot read simply does not appear.

---

## Common Patterns

### Pattern: Org-Wide Search Layout Audit and Refresh

**When to use:** New org launch, post-migration cleanup, or a Lightning rollout from Classic where the search layouts still carry columns nobody has revisited in years.

**How it works:**

1. List every object in scope (`tooling_query("SELECT QualifiedApiName FROM EntityDefinition WHERE IsCustomizable = true AND IsSearchable = true")` — UNVERIFIED (2026-10-20): these EntityDefinition fields are not in the corpus).
2. For each object, retrieve `CustomObject` metadata and read the `<searchLayouts>` and `<profileSearchLayouts>` blocks — note the columns in each list.
3. Identify objects whose `searchResultsAdditionalFields` is empty. These objects render a Name-only search result and are the most painful for users.
4. Define a target column set per object based on what fields users actually scan in record list views — typically Name, Owner, Phone (Contact/Account), Status (Case/Opportunity), Modified Date.
5. Deploy via Metadata API or Object Manager. Validate per surface (Lightning global search bar, Classic search if applicable, lookup dialogs on related objects).

**Why not the alternative:** Users cannot fix it themselves (UNVERIFIED (2026-10-20): user personalization of search columns is Help-only); the admin lever is the default layout plus per-profile `profileSearchLayouts` (api_meta 264 L44503-44506).

### Pattern: Custom Synonym Group for Domain Vocabulary

**When to use:** Users speak a domain shorthand that doesn't match the data ("VIP" customers stored as "Priority", "BD" stored as "Business Development").

**How it works:**

1. List the vocabulary variants users actually search for (interview reps; check support ticket subjects).
2. Confirm the data representation — what's the canonical word in the Name or text fields?
3. Create a Synonym Group (`SynonymDictionary` metadata, or `Setup → User Interface → Synonyms` — UNVERIFIED (2026-10-20): Setup path, comma entry and whitespace stripping are Help-only). Add the canonical word and every variant: at least two terms, each at most 50 characters, with `languages` set (api_meta 264 L136404-136410).
4. Save the group (UNVERIFIED (2026-10-20): any Active toggle on the Synonyms page — `SynonymGroup` has no active field, api_meta 264 L136400-136410).
5. Validate with representative queries; if a term does not match yet, retest after the index wait (UNVERIFIED (2026-10-20): whether a synonym change waits on the ~15-minute record index lag).

**Why not the alternative:** Renaming records or maintaining "alias" custom fields creates data duplication and reporting drift. Synonyms operate purely at the search layer and leave the data model untouched.

### Pattern: External Object Search Enablement

**When to use:** A Salesforce Connect external object has data, page layouts work, but the records never appear in global search.

**How it works:**

1. `Setup → External Data Sources → <source>` — confirm **Enable Search** (`searchEnabled` in `customConfiguration`) is on. If not, turn it on and save.
2. `Setup → External Objects → <object> → Edit` — confirm **Allow Search** (`enableSearch`) is checked at the object level; a re-sync resets it to the data source's setting (api_meta 264 L44352-44354).
3. For a custom Apex adapter, confirm it declares the `SEARCH` capability (apexref 262 L151747-151751). Cross-Org and OData 2.0/4.0 adapters both carry the Enable Search parameter (api_meta 264 L13818-13850).
4. For OData adapters: if the remote service needs a custom search function, set `searchFunc` — "Custom Query Option for Salesforce Search" (api_meta 264 L13851). UNVERIFIED (2026-10-20): how the OData adapter translates a Salesforce search for a service without one.
5. Validate with a SOSL query in Developer Console: `FIND {<term>} IN ALL FIELDS RETURNING ExternalObject__x` — if this returns rows but global search doesn't, check the per-object Search Layout (UNVERIFIED (2026-10-20): that an empty search layout hides an external object's results).

**Why not the alternative:** Telling users "search doesn't work for external objects" is a workaround, not a fix. The platform supports it; the configuration steps are just usually missed.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Users see only Name in global search results | Add 3–6 useful columns to `searchResultsAdditionalFields` for each high-traffic object | One-column results force users to click into every record to disambiguate |
| Users search shorthand the data doesn't store | Custom Synonym Group at `Setup → User Interface → Synonyms` | Operates at the search layer; no data model change required |
| Lookup picker for an Account field shows only Name | Edit `Account → Search Layouts → Lookup Dialog` to add Industry, Phone, Owner | `lookupDialogsAdditionalFields` is a separate list from `searchResultsAdditionalFields` |
| Different teams need different result columns | Add `profileSearchLayouts` entries per profile | The default layout applies only where no profile layout exists (api_meta 264 L47265-47266) |
| External object missing from global search | Enable Search on the data source AND Allow Search on the external object; custom adapters declare `SEARCH` | All gates must be open; new external objects start with search off |
| Need keyword aliasing for one specific object | `SynonymGroup` has no object field (api_meta 264 L136400-136410), so assume it reaches other objects (UNVERIFIED (2026-10-20): org-wide reach). Decide whether the alias is harmless on other objects | If not, consider a saved search or a custom Search experience instead of a synonym |
| Newly created record not in search | Wait 15 minutes or more; if still missing, confirm the object is searchable and the user has access | "About 15 minutes or more" is the documented index lag (ldv 264 L160-162) |
| Many objects need the same Search Layout refresh | Deploy `CustomObject` entries (named, no wildcard) with updated `<searchLayouts>` | `SearchLayouts` is reachable only through CustomObject and does not support `*` (api_meta 264 L47497-47498, L47621-47622) |

UNVERIFIED (2026-10-20): the 3–6 column guidance in the first row is a usability heuristic, not a platform limit.

---

## Recommended Workflow

1. **Inventory the surface matrix.** Confirm Lightning vs Classic usage. Confirm Einstein Search is on or off. Confirm which user populations rely on global search heavily versus those who navigate via list views or related lists. The configuration priorities follow real usage.

2. **Audit per-object Search Layouts.** For each searchable object, capture `searchResultsAdditionalFields`, `profileSearchLayouts`, `lookupDialogsAdditionalFields`, `lookupPhoneDialogsAdditionalFields`, `customTabListAdditionalFields` and `searchFilterFields`. Note objects whose search results list has fewer than three columns — they are the highest-impact fixes. Run `scripts/check_global_search_configuration.py --manifest-dir <project>`.

3. **Define target columns per object.** For each object, agree with stakeholders on the column set users need to scan a result row: typically Name + owner + status field + a date or quantity field. Keep within the column caps (UNVERIFIED (2026-10-20): 10 columns, 6 in a Classic lookup dialog — Help-only).

4. **Audit and extend Synonym Groups.** Retrieve the `SynonymDictionary` components. Identify domain vocabulary gaps. Author custom groups (UNVERIFIED (2026-10-20): the 2,000-active-group cap). Test with representative search queries.

5. **Configure Search Settings.** Set `lookupAutoCompleteEnabled` per object that needs it (api_meta 264 L129243). Disable Classic sidebar settings if the org is Lightning-only.

6. **Validate external objects.** For each Salesforce Connect external object expected in search, confirm Enable Search on the data source + Allow Search on the external object (+ `SEARCH` capability for a custom adapter). Run a SOSL probe in Developer Console as the final check.

7. **Deploy and document.** Push changes via Metadata API where possible. Update the org's Configuration Workbook with the Search Layouts and Synonym Groups in effect, so future admins inherit the rationale.

---

## Review Checklist

- [ ] Per-object Search Layouts audited (every list in `<searchLayouts>` plus `<profileSearchLayouts>`) on every searchable object
- [ ] `searchResultsAdditionalFields` populated with at least 3 useful columns on every high-traffic object
- [ ] Lookup Dialog Search Layout configured separately from Search Results
- [ ] Search Filter Fields configured for objects where users want faceted filtering
- [ ] Synonym Group inventory captured; custom groups deployed (UNVERIFIED (2026-10-20): any per-group active state)
- [ ] Synonym Group count recorded (UNVERIFIED (2026-10-20): the 2,000-active cap)
- [ ] Search Settings reviewed (per-object Lookup Auto-Completion and results per page, Sidebar Search where Classic applies)
- [ ] External objects' search flags verified at both data source (Enable Search) and object (Allow Search) level
- [ ] FLS confirmed for every column added to a Search Layout (UNVERIFIED (2026-10-20): blank-column rendering)
- [ ] Manage Synonyms and Customize Application scoped to the right admin users only
- [ ] Configuration Workbook updated with current Search Layout and Synonym state
- [ ] Indexing-wait expectation documented for future admins ("record changes take about 15 minutes or more to appear", ldv 264 L160-162)
- [ ] Boundary documented with `agentforce/einstein-search-personalization` if Einstein Search is also configured

---

## Salesforce-Specific Gotchas

1. **The default search results layout is overridden per profile, not per UI.** `searchResultsAdditionalFields` is used "when no layout is specified for a user profile"; a `profileSearchLayouts` entry replaces it for that profile (api_meta 264 L47265-47266). Editing the default does not change what a profile with its own layout sees.
2. **Synonym Groups have no per-object scope in metadata.** `SynonymGroup` carries only `languages` and `terms` (api_meta 264 L136400-136410). A "VIP, Priority" group can produce noisy matches on objects where the terms mean something else. UNVERIFIED (2026-10-20): that a group applies to every searchable object.
3. **Standard Synonym Groups cannot be deleted, only deactivated.** UNVERIFIED (2026-10-20): Help-only; deactivating a standard group risks breaking expected behavior org-wide.
4. **Name is always the first column.** A text-type Name "is mandatory; it's always displayed as the first column"; an auto-number Name can be removed, but a Metadata API import "will always add the Name field back" (api_meta 264 L47509-47511). UNVERIFIED (2026-10-20): the 10-column cap and whether Name counts toward it.
5. **Lookup Dialog limit is 6 columns in Classic, 10 in Lightning.** If the org has any Classic users, validate column priority order. UNVERIFIED (2026-10-20): both caps are Help-only.
6. **Hidden FLS renders as blank columns, not as access-denied errors.** Audit FLS for every field added to a Search Layout. UNVERIFIED (2026-10-20): the blank-cell rendering is Help-only.
7. **External objects need search on at every gate** (data source Enable Search, external object Allow Search, a custom adapter's `SEARCH` capability). New external objects start with search off (api_meta 264 L44352). The error mode is silent — search just returns zero rows for the external object.
8. **Record index lag means change-then-test-immediately produces false negatives.** A created or updated record "could take about 15 minutes or more" to become searchable (ldv 264 L160-162). UNVERIFIED (2026-10-20): whether Search Layout or Synonym changes wait on the same lag.
9. **Lookup autocomplete is per object; the blank-lookup recently-viewed setting is User-only.** `lookupAutoCompleteEnabled` sits in each `ObjectSearchSetting` (api_meta 264 L129243); `recentlyViewedUsersForBlankLookupEnabled` "only applies to User object blank lookup searches" (L129189-129194).
10. **Customize Application is a powerful permission.** Grant it via narrowly scoped Permission Sets, not via profile updates — and not at all to non-admin populations. UNVERIFIED (2026-10-20): that search-layout editing requires it.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Search Layout audit report | Per-object inventory of current columns in each `<searchLayouts>` list and `<profileSearchLayouts>` entry, with gap analysis |
| Search Layout target configuration | Per-object proposed column set per slot, ready for Metadata API deploy |
| Synonym Group inventory | Standard groups in use (UNVERIFIED (2026-10-20): Help-only), custom groups from `SynonymDictionary`, proposed additions, total count |
| Search Settings configuration table | Per-object Lookup Auto-Completion and results per page, Sidebar Search settings — current vs target |
| External object searchability matrix | For each external object: data source Enable Search, object Allow Search, adapter `SEARCH` capability, validation status |
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
