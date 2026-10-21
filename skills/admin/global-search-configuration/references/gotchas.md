# Gotchas — Global Search Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: A Profile Search Layout Overrides the Default Search Results Layout

**What happens:** An admin updates the default search results columns. Users on one profile still see the old columns.

**When it occurs:** Orgs that created profile-specific search layouts. `searchResultsAdditionalFields` is "the default search results layout used when no layout is specified for a user profile" (api_meta 264 L47265-47266); a `profileSearchLayouts` entry replaces it for its profiles (API 47.0+ on the CustomObject field, L44503-44506; 48.0+ for custom objects on the ProfileSearchLayouts page, L47270). The corpus documents one search-results list per object — not separate Lightning and Classic lists.

**How to avoid:** Audit `<searchLayouts>` and every `<profileSearchLayouts>` entry together, and configure each list you need (`searchResultsAdditionalFields`, `lookupDialogsAdditionalFields`, `lookupPhoneDialogsAdditionalFields`, `customTabListAdditionalFields`). Deploy them as named `CustomObject` members — `SearchLayouts` has no wildcard support (L47621-47622). A profile layout deploys only if the profile exists in the target org and, for a custom object, search is enabled and the object's tab exists or ships with it (L47292-47294).

---

## Gotcha 2: Synonym Groups Carry No Object or Profile Field (Org-Wide Reach UNVERIFIED)

**What happens:** Adding a "VIP, Priority, Important" synonym group to help reps find tier-1 accounts also affects Cases (where "Important" is now an equivalent of "Priority" in case subjects), custom objects, Knowledge articles — every searchable object.

**When it occurs:** Whenever a custom Synonym Group is created. `SynonymGroup` has only `languages` and `terms` — no object field (api_meta 264 L136400-136410). UNVERIFIED (2026-10-20): that a group applies to every searchable object, including Knowledge and custom objects.

**How to avoid:** Before adding a synonym group, list every object whose searchable text fields might contain any of the proposed terms. Confirm with stakeholders that the equivalence makes sense in all those contexts. If not, the synonym approach is wrong — consider a saved search, a custom Lightning component with a constrained SOSL query, or a normalization on a specific field instead.

---

## Gotcha 3: External Objects Need Search On at Every Gate

**What happens:** A Salesforce Connect external object is visible on related lists, queryable via SOQL, but does not appear in global search.

**When it occurs:** Default state for a new external object — "by default, search is turned off for new external objects" (api_meta 264 L44352). UNVERIFIED (2026-10-20): the data source's own default.

**How to avoid:** Check every gate in order:
1. `Setup → External Data Sources → <source> → Enable Search` (`searchEnabled` in `customConfiguration` — a parameter of both the Cross-Org and the OData 2.0/4.0 adapters, api_meta 264 L13818-13850)
2. `Setup → External Objects → <object> → Allow Search` (`enableSearch`; a sync resets it to the data source's setting, L44352-44354)
3. For a custom Apex adapter, confirm it declares the `SEARCH` capability (apexref 262 L151747-151751).

The platform error mode is silent — there is no banner (UNVERIFIED (2026-10-20): UI behaviour). Run a SOSL probe in Developer Console to confirm reachability before declaring the configuration broken.

---

## Gotcha 4: Search Index Lag — About 15 Minutes or More Is Normal

**What happens:** Admin adds a new Synonym Group, immediately searches for one of its terms, sees no new matches, concludes the synonym doesn't work.

**When it occurs:** After any record create or update — "it could take about 15 minutes or more for the updated text to become searchable" (ldv 264 L160-162). UNVERIFIED (2026-10-20): that Search Layout, Synonym or Allow Search changes wait on the same lag.

**How to avoid:** Wait at least 15 minutes before validation. For bulk record loads, expect a longer wait (UNVERIFIED (2026-10-20): that lag scales with load size). Build the wait into runbooks so future admins don't false-negative their own changes.

---

## Gotcha 5: Lookup Dialog Column Cap Differs Between Classic and Lightning (UNVERIFIED (2026-10-20): Help-only caps)

**What happens:** Admin configures 10 columns in a Lookup Dialog Search Layout. Lightning users see all 10. A Classic user logging in for a maintenance task sees only the first 6, missing the columns the admin assumed were primary.

**When it occurs:** Hybrid orgs with both Lightning and Classic users. The column-count limit is 10 in Lightning but 6 in Classic (UNVERIFIED (2026-10-20): both caps are Help-only).

**How to avoid:** Order columns by priority. The first 6 must be the most important; columns 7–10 are Lightning-only enhancements. If the org is genuinely Lightning-only and Classic access has been removed, 10 columns is safe.

---

## Gotcha 6: FLS-Restricted Fields Render as Blank Columns, Not as Access-Denied (UNVERIFIED (2026-10-20): Help-only rendering)

**What happens:** A user runs a global search; the result row has the column for Industry, but Industry is blank for some users despite the data being present.

**When it occurs:** When a column in a Search Layout references a field the user lacks FLS read access to. The user sees the column header but the cell is empty. UNVERIFIED (2026-10-20): this rendering is Help-only.

**How to avoid:** For every field added to a Search Layout, audit FLS across all profiles and permission sets that use search. Either grant read FLS or remove the field from the Search Layout. Users assuming the data is "missing" rather than "FLS-hidden" file support tickets that look like data bugs.

---

## Gotcha 7: The Name Column Cannot Be Removed from Search Layouts

**What happens:** Admin tries to remove the Name column from a Search Layout, intending to feature a different identifier (e.g., Account_Number__c). The save fails or the Name column reappears.

**When it occurs:** A text-type Name "is mandatory; it's always displayed as the first column"; an auto-number Name can be removed, but a Metadata API import "will always add the Name field back" (api_meta 264 L47509-47511).

**How to avoid:** Treat the first column as fixed and leave Name out of the field list ("the name field isn't returned", L47510). Configure the remaining columns intentionally (UNVERIFIED (2026-10-20): the 10-column cap). If a custom identifier is more important than Name, consider using it as the Name field directly (auto-numbered Name fields are a common pattern for this).

---

## Gotcha 8: Customize Application Permission Is Org-Wide

**What happens:** Granting an admin the ability to edit Search Layouts means they can also edit profiles, page layouts, custom fields, validation rules, deployment metadata — Customize Application is a broad system permission.

**When it occurs:** Mid-size and large orgs where a delegated admin needs to manage search but should not have access to the rest of Setup.

**How to avoid:** Salesforce does not provide a granular "manage search layouts only" permission (UNVERIFIED (2026-10-20): the permission model for search layouts is Help-only; synonyms alone need "Manage Synonyms", api_meta 264 L136378). Scope the permission via a tightly-controlled Permission Set; assign to as few users as possible. For partial delegation, train delegated admins on the boundary of what they should and shouldn't change.

---

## Gotcha 9: Setup → Search Settings Is a Different Page from Einstein Search Settings

**What happens:** Admin looking to disable Lookup Auto-Completion navigates to `Setup → Einstein Search → Settings` and finds no such toggle. Concludes the feature is unavailable.

**When it occurs:** Org has Einstein Search enabled. The Einstein Search settings page exists for AI-layer toggles; the classic Search Settings page (`Setup → Search Settings`) is a separate node and is where Lookup Auto-Completion lives (`lookupAutoCompleteEnabled`, api_meta 264 L129243). UNVERIFIED (2026-10-20): Setup page names and layout.

**How to avoid:** Distinguish the two pages in admin training. `Setup → Search Settings` = platform-level admin (Lookup Auto-Completion, results per page, Sidebar Search). `Setup → Einstein Search → Settings` = AI-layer (signals, NLS, Promoted Search Terms). Both can be present in the same org; neither replaces the other.

---

## Gotcha 10: Standard Synonym Groups Cannot Be Deleted (UNVERIFIED (2026-10-20): Help-only)

**What happens:** An admin discovers a standard synonym group that is producing unwanted matches (e.g., "St." being treated as a synonym for "Saint" causes hits in an org that has many street-address records). They try to delete it, find only a Deactivate toggle.

**When it occurs:** Standard Salesforce ships a managed pack of synonym groups (geographic abbreviations, business-entity suffixes, common business terms). The pack is read-only — entries can be Activated or Deactivated, not edited or removed. UNVERIFIED (2026-10-20): the standard pack and its read-only behaviour are Help-only; the corpus has only the `enableSalesforceGeneratedSynonyms` switch (api_meta 264 L129148-129149).

**How to avoid:** Use the Deactivate toggle. Document why a standard group was deactivated. Note that a standard group reactivation may bring back its original equivalences exactly — if the org needs a modified version, deactivate the standard and create a custom group with the desired subset.
