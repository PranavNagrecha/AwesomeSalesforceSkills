# Gotchas — Global Search Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Default Layout (Lightning) and Search Results (Classic) Are Independent

**What happens:** An admin updates the Search Results layout in Object Manager. Lightning global search still shows only Name.

**When it occurs:** Lightning-only or hybrid orgs whose Search Results slot was historically populated for Classic but whose Default Layout (Lightning) slot was never touched. The two slots are stored as separate `SearchLayout` entries in metadata and are read by different surfaces.

**How to avoid:** Configure all five Search Layout slots per object, not just Search Results. The slots: Default Layout (Lightning), Search Results (Classic), Lookup Dialog, Lookup Phone Dialog, Tab. Use the Metadata API `<searchLayouts>` block to audit and deploy all five in a single change.

---

## Gotcha 2: Synonym Groups Are Org-Wide; No Per-Object or Per-Profile Scope

**What happens:** Adding a "VIP, Priority, Important" synonym group to help reps find tier-1 accounts also affects Cases (where "Important" is now an equivalent of "Priority" in case subjects), custom objects, Knowledge articles — every searchable object.

**When it occurs:** Whenever a custom Synonym Group is created. Salesforce does not expose object-level scoping for synonyms.

**How to avoid:** Before adding a synonym group, list every object whose searchable text fields might contain any of the proposed terms. Confirm with stakeholders that the equivalence makes sense in all those contexts. If not, the synonym approach is wrong — consider a saved search, a custom Lightning component with a constrained SOSL query, or a normalization on a specific field instead.

---

## Gotcha 3: External Objects Need Three Independent "Allow Search" Toggles

**What happens:** A Salesforce Connect external object is visible on related lists, queryable via SOQL, but does not appear in global search.

**When it occurs:** Default state for a new external object — the data source's `Allow Search` flag is off, the external object's `Allow Search` flag is off, and (for some adapters) SOSL support is not available at all.

**How to avoid:** Check all three gates in order:
1. `Setup → External Data Sources → <source> → Allow Search`
2. `Setup → External Objects → <object> → Allow Search`
3. Confirm the adapter (OData 2.0, OData 4.0, Cross-Org, custom Apex) supports SOSL. OData 2.0 / 4.0 do; Cross-Org and most custom Apex adapters do not.

The platform error mode is silent — there is no banner. Run a SOSL probe in Developer Console to confirm reachability before declaring the configuration broken.

---

## Gotcha 4: Search Index Lag — 15 Minutes Is Normal

**What happens:** Admin adds a new Synonym Group, immediately searches for one of its terms, sees no new matches, concludes the synonym doesn't work.

**When it occurs:** Any change to Search Layouts, Synonyms, or external object Allow Search flags. Also after bulk record loads — the records themselves are searchable only after the index processes them.

**How to avoid:** After any search configuration change, wait ~15 minutes before validation. For bulk record loads, expect proportional lag (the larger the load, the longer the indexing wait). Build the wait into runbooks so future admins don't false-negative their own changes.

---

## Gotcha 5: Lookup Dialog Column Cap Differs Between Classic and Lightning

**What happens:** Admin configures 10 columns in a Lookup Dialog Search Layout. Lightning users see all 10. A Classic user logging in for a maintenance task sees only the first 6, missing the columns the admin assumed were primary.

**When it occurs:** Hybrid orgs with both Lightning and Classic users. The column-count limit is 10 in Lightning but 6 in Classic.

**How to avoid:** Order columns by priority. The first 6 must be the most important; columns 7–10 are Lightning-only enhancements. If the org is genuinely Lightning-only and Classic access has been removed, 10 columns is safe.

---

## Gotcha 6: FLS-Restricted Fields Render as Blank Columns, Not as Access-Denied

**What happens:** A user runs a global search; the result row has the column for Industry, but Industry is blank for some users despite the data being present.

**When it occurs:** When a column in a Search Layout references a field the user lacks FLS read access to. The user sees the column header but the cell is empty.

**How to avoid:** For every field added to a Search Layout, audit FLS across all profiles and permission sets that use search. Either grant read FLS or remove the field from the Search Layout. Users assuming the data is "missing" rather than "FLS-hidden" file support tickets that look like data bugs.

---

## Gotcha 7: The Name Column Cannot Be Removed from Search Layouts

**What happens:** Admin tries to remove the Name column from a Search Layout, intending to feature a different identifier (e.g., Account_Number__c). The save fails or the Name column reappears.

**When it occurs:** Any Search Layout. The first column is hard-coded to the object's Name field (or polymorphic Name proxy).

**How to avoid:** Treat the first column as fixed. Configure the next 9 columns intentionally. If a custom identifier is more important than Name, consider using it as the Name field directly (auto-numbered Name fields are a common pattern for this).

---

## Gotcha 8: Customize Application Permission Is Org-Wide

**What happens:** Granting an admin the ability to edit Search Layouts means they can also edit profiles, page layouts, custom fields, validation rules, deployment metadata — Customize Application is a broad system permission.

**When it occurs:** Mid-size and large orgs where a delegated admin needs to manage search but should not have access to the rest of Setup.

**How to avoid:** Salesforce does not provide a granular "manage search layouts only" permission. Scope the permission via a tightly-controlled Permission Set; assign to as few users as possible. For partial delegation, train delegated admins on the boundary of what they should and shouldn't change.

---

## Gotcha 9: Setup → Search Settings Is a Different Page from Einstein Search Settings

**What happens:** Admin looking to disable Lookup Auto-Completion navigates to `Setup → Einstein Search → Settings` and finds no such toggle. Concludes the feature is unavailable.

**When it occurs:** Org has Einstein Search enabled. The Einstein Search settings page exists for AI-layer toggles; the classic Search Settings page (`Setup → Search Settings`) is a separate node and is where Lookup Auto-Completion lives.

**How to avoid:** Distinguish the two pages in admin training. `Setup → Search Settings` = platform-level admin (Lookup Auto-Completion, Drop-Down List size, Sidebar Search). `Setup → Einstein Search → Settings` = AI-layer (signals, NLS, Promoted Search Terms). Both can be present in the same org; neither replaces the other.

---

## Gotcha 10: Standard Synonym Groups Cannot Be Deleted

**What happens:** An admin discovers a standard synonym group that is producing unwanted matches (e.g., "St." being treated as a synonym for "Saint" causes hits in an org that has many street-address records). They try to delete it, find only a Deactivate toggle.

**When it occurs:** Standard Salesforce ships a managed pack of synonym groups (geographic abbreviations, business-entity suffixes, common business terms). The pack is read-only — entries can be Activated or Deactivated, not edited or removed.

**How to avoid:** Use the Deactivate toggle. Document why a standard group was deactivated. Note that a standard group reactivation may bring back its original equivalences exactly — if the org needs a modified version, deactivate the standard and create a custom group with the desired subset.
