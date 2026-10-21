# LLM Anti-Patterns — Global Search Configuration

Common mistakes AI coding assistants make when generating or advising on global search configuration in Salesforce. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Conflating Setup → Search Settings with Setup → Einstein Search → Settings

**What the LLM generates:** "Go to Setup → Einstein Search → Settings to disable Lookup Auto-Completion" or "Configure Promoted Search Terms in Setup → Search Settings."

**Why it happens:** Both pages have the word "Search" and live in Setup. Training data freely mixes their content because Salesforce documentation has cross-references between them. LLMs do not consistently distinguish the AI-layer settings from the platform-level admin settings.

**Correct pattern:**

```
Setup → Search Settings        = per-object Lookup Auto-Completion and results
                                 per page, Sidebar Search, Single Search Result
                                 shortcut (SearchSettings, api_meta 264 L129086-129249).
Setup → Einstein Search → Settings = Personalization signals (Activity, Location, Ownership,
                                     Specialization), Natural Language Search toggle,
                                     Promoted Search Terms.
```

**Detection hint:** If output references "Einstein Search Settings" for Lookup Auto-Completion, the page is wrong. UNVERIFIED (2026-10-20): the Einstein Search page contents listed above are Help-only. In metadata the split does not exist: `enableEinsteinSearchNaturalLanguage` and `enableEinsteinSearchPersonalization` are fields of the same `SearchSettings` type as the lookup settings (api_meta 264 L129127-129136), so an answer that deploys the NLS toggle in `Search.settings` is right.

---

## Anti-Pattern 2: Assuming Search Layout Slots Are Linked

**What the LLM generates:** "Edit the Search Results layout for Account to add Industry. This will also update the Lookup Dialog when users search for an Account from a Case." Or: "Edit the default layout and every profile will see the new columns."

**Why it happens:** LLMs apply DRY-like assumptions to repeated UI nodes. The SearchLayouts lists have similar names and similar configuration UIs, so the LLM presumes a single source-of-truth model.

**Correct pattern:**

```
SearchLayouts lists are separate fields (api_meta 264 L47518-47595):
  - searchResultsAdditionalFields       (default search results)
  - lookupDialogsAdditionalFields       (lookup dialog)
  - lookupPhoneDialogsAdditionalFields  (softphone lookup)
  - customTabListAdditionalFields       (recent records on the tab)
  - searchFilterFields                  (search filters)
profileSearchLayouts (on CustomObject) overrides the default
search results per profile (L47265-47266, L44503-44506).
```

**Detection hint:** Any statement like "updating Search Results will also update Lookup Dialog", or a `<customSearchLayout>` element (not a SearchLayouts field), is wrong.

---

## Anti-Pattern 3: Recommending Synonym Groups Without Acknowledging Org-Wide Scope

**What the LLM generates:** "Create a Synonym Group: `VIP, Priority` to help sales reps find tier-1 accounts in global search."

**Why it happens:** LLMs frame solutions in the context of the user's stated problem (Accounts) and assume scope can be limited to that context. `SynonymGroup` has no object field (api_meta 264 L136400-136410). UNVERIFIED (2026-10-20): that a group applies to every searchable object, as listed below.

**Correct pattern:**

```
Synonym Group "VIP, Priority" can affect search on every object
(UNVERIFIED (2026-10-20): org-wide reach; SynonymGroup has no object field):
  - Accounts (intended)
  - Cases (where "Priority" is a different concept)
  - Knowledge articles
  - Custom objects
  - Chatter posts (if Chatter search is enabled)

Before creating the group:
1. List every object whose searchable text fields might contain any of these terms.
2. Confirm with stakeholders that the equivalence is correct in ALL those contexts.
3. If equivalence is correct only on Accounts, do NOT use a Synonym Group —
   consider a saved search, a custom LWC with a constrained SOSL query,
   or a normalized custom field instead.
```

**Detection hint:** A recommendation to add a Synonym Group without a scope-impact analysis on other objects is incomplete and should be revised.

---

## Anti-Pattern 4: Forgetting External Object Search Requires Three Independent Gates

**What the LLM generates:** "To make the Salesforce Connect external object searchable, enable Allow Search on the external data source. Done."

**Why it happens:** LLMs latch onto the first relevant configuration step (the data source flag) and skip the second (the external object flag) and third (adapter capability). The Salesforce documentation describes each gate in a separate section, so LLMs that summarize the docs from a single section produce incomplete instructions.

**Correct pattern:**

```
Gates (new external objects start with search off, api_meta 264 L44352):
  1. Setup → External Data Sources → <source> → Enable Search
     (searchEnabled in customConfiguration - Cross-Org AND OData
     2.0/4.0 both have it, api_meta 264 L13818-13850)
  2. Setup → External Objects → <object>      → Allow Search
     (enableSearch; a sync resets it to the data source's setting)
  3. Custom Apex adapter → declares the SEARCH capability
     (apexref 262 L151747-151751)

Validation (Developer Console):
  FIND 'term' IN ALL FIELDS RETURNING Inventory_Item__x(Id, Name)
```

**Detection hint:** Any external-object search advice that mentions only one gate is incomplete. Advice that the Cross-Org adapter cannot be searched is incorrect — it has an Enable Search parameter (api_meta 264 L13826).

---

## Anti-Pattern 5: Ignoring Search Index Lag When Validating Configuration Changes

**What the LLM generates:** "Add the synonym group, then immediately search for one of its terms to validate that the change worked." Or: "After updating the Search Layout, refresh the page and confirm the new columns appear in results within 30 seconds."

**Why it happens:** LLMs default to "immediate validation" because that is the pattern for most Salesforce configuration changes (validation rules, page layouts, profile changes — all immediate). Search index lag is a less-trained-on edge case.

**Correct pattern:**

```
After any change to:
  - Search Layouts
  - Synonym Groups
  - External object Allow Search / data source Enable Search flags

Wait at least 15 minutes before validating record changes: a created or
updated record "could take about 15 minutes or more" to become
searchable (ldv 264 L160-162). Do NOT conclude the change is broken
before the wait. UNVERIFIED (2026-10-20): that layout and synonym
changes wait on the same lag.

If the change still has not taken effect after 30 minutes:
  - Confirm the configuration was actually saved (Setup audit trail).
  - Confirm the user testing has the FLS and sharing access required.
  - Confirm the field being searched is indexable
    (UNVERIFIED (2026-10-20): which field types are not).
```

**Detection hint:** Any test plan that "validates the change immediately after saving" without a wait window is at risk of false-negative results.
