# LLM Anti-Patterns — Global Search Configuration

Common mistakes AI coding assistants make when generating or advising on global search configuration in Salesforce. These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Conflating Setup → Search Settings with Setup → Einstein Search → Settings

**What the LLM generates:** "Go to Setup → Einstein Search → Settings to disable Lookup Auto-Completion" or "Configure Promoted Search Terms in Setup → Search Settings."

**Why it happens:** Both pages have the word "Search" and live in Setup. Training data freely mixes their content because Salesforce documentation has cross-references between them. LLMs do not consistently distinguish the AI-layer settings from the platform-level admin settings.

**Correct pattern:**

```
Setup → Search Settings        = Lookup Auto-Completion, Drop-Down List size,
                                 Sidebar Search, Single Search Result for Single Match.
Setup → Einstein Search → Settings = Personalization signals (Activity, Location, Ownership,
                                     Specialization), Natural Language Search toggle,
                                     Promoted Search Terms.
```

**Detection hint:** If output references "Einstein Search Settings" for Lookup Auto-Completion or Drop-Down List size, the page is wrong. If output references "Search Settings" for Promoted Search Terms or NLS, the page is wrong.

---

## Anti-Pattern 2: Assuming Search Layout Slots Are Linked

**What the LLM generates:** "Edit the Search Results layout for Account to add Industry. This will also update the Lookup Dialog when users search for an Account from a Case." Or: "After updating the Default Layout, the columns will appear in both Lightning and Classic search."

**Why it happens:** LLMs apply DRY-like assumptions to repeated UI nodes. The five Search Layout slots have similar names and similar configuration UIs, so the LLM presumes a single source-of-truth model.

**Correct pattern:**

```
Search Layout slots are independent:
  - Default Layout (Lightning global search)
  - Search Results (Classic global search)
  - Lookup Dialog (lookup pickers)
  - Lookup Phone Dialog (telephony lookup)
  - Tab (object Tab default columns)

Each slot is stored as a separate <SearchLayout> entry in CustomObject metadata.
Each must be configured independently.
```

**Detection hint:** Any statement like "updating Search Results will also update Lookup Dialog" or "Lightning will inherit from Classic Search Results" is wrong. Slots are independent.

---

## Anti-Pattern 3: Recommending Synonym Groups Without Acknowledging Org-Wide Scope

**What the LLM generates:** "Create a Synonym Group: `VIP, Priority` to help sales reps find tier-1 accounts in global search."

**Why it happens:** LLMs frame solutions in the context of the user's stated problem (Accounts) and assume scope can be limited to that context. The model does not surface that Synonym Groups apply org-wide — across every searchable object.

**Correct pattern:**

```
Synonym Group "VIP, Priority" will affect search on EVERY object:
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
Three gates, all default off:
  1. Setup → External Data Sources → <source> → Allow Search
  2. Setup → External Objects → <object>      → Allow Search
  3. Adapter supports SOSL on external data:
       - OData 2.0     → supported
       - OData 4.0     → supported
       - Cross-Org     → NOT supported
       - Custom Apex   → only if the developer implemented SOSL
                          in the apex adapter — rare

Validation (Developer Console):
  FIND 'term' IN ALL FIELDS RETURNING Inventory_Item__x(Id, Name)
```

**Detection hint:** Any external-object search advice that mentions fewer than two of the three gates is incomplete. Cross-Org adapter advice that claims search works without qualification is incorrect.

---

## Anti-Pattern 5: Ignoring Search Index Lag When Validating Configuration Changes

**What the LLM generates:** "Add the synonym group, then immediately search for one of its terms to validate that the change worked." Or: "After updating the Search Layout, refresh the page and confirm the new columns appear in results within 30 seconds."

**Why it happens:** LLMs default to "immediate validation" because that is the pattern for most Salesforce configuration changes (validation rules, page layouts, profile changes — all immediate). Search index lag is a less-trained-on edge case.

**Correct pattern:**

```
After any change to:
  - Search Layouts
  - Synonym Groups
  - External Object / Data Source Allow Search flags

Wait ~15 minutes before validation. Index lag is typically 2–5 minutes
for small orgs and small changes; up to ~15 minutes for large orgs
or post-bulk-load. Do NOT conclude the change is broken before the wait.

If the change still has not taken effect after 30 minutes:
  - Confirm the configuration was actually saved (Setup audit trail).
  - Confirm the user testing has the FLS and sharing access required.
  - Confirm the field being searched is indexable
    (rich text and encrypted fields are not).
```

**Detection hint:** Any test plan that "validates the change immediately after saving" without a wait window is at risk of false-negative results.
