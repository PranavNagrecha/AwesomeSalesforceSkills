# LLM Anti-Patterns — List Views and Compact Layouts

Common mistakes AI coding assistants make when generating or advising on Salesforce list views, compact layouts, and search layouts.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing compact layouts with page layouts

**What the LLM generates:** "Edit the page layout to change the fields shown in the record highlights panel."

**Why it happens:** LLMs conflate compact layouts with page layouts. The highlights panel at the top of a Lightning record page is controlled by the compact layout, not the page layout. Page layouts control the field detail section and related lists below the highlights panel.

**Correct pattern:**

```
What controls what:
- Highlights Panel (top of record page): Compact Layout.
  Setup → Object Manager → [Object] → Compact Layouts.
  Shows the first 4-7 fields (depending on space).
  Also controls what appears on mobile record cards.

- Record Detail Section: Page Layout (or Dynamic Forms).
  Setup → Object Manager → [Object] → Page Layouts.
  Controls full field display, sections, related lists.

- Search Result Columns: Search Layouts.
  Setup → Object Manager → [Object] → Search Layouts.
  Controls fields shown in lookup dialogs and global search results.

To change the highlights panel → edit the Compact Layout, not the page layout.
```

**Detection hint:** If the output edits the page layout to change the highlights panel, it is targeting the wrong configuration. Search for `compact layout` when the highlights panel is mentioned.

---

## Anti-Pattern 2: Creating too many public list views without governance

**What the LLM generates:** "Create a public list view for each sales rep: 'John's Accounts', 'Jane's Accounts', 'Bob's Accounts'..."

**Why it happens:** LLMs create per-user list views as public views. Public list views are visible to everyone and create clutter in the list view selector. Per-user views should be created as private ("Only I can see this list view") by the individual user, not as public views by an admin.

**Correct pattern:**

```
List view visibility governance:
- Public list views: shared business views that serve a team or role.
  Examples: "All Open Cases", "This Quarter's Opportunities", "Unassigned Leads".
  Create sparingly — each public view adds to everyone's list.

- Private list views: personal views created by individual users.
  Examples: "My High Priority Cases", "My Territory Accounts".
  Users create these themselves via the list view editor.

- Pinned list views: users can pin their preferred view per object.

Best practice: create 3-5 public list views per object maximum.
Let users create personal views for their individual needs.
```

**Detection hint:** If the output creates more than 5 public list views for a single object, or creates person-specific public views, the governance is missing. Count the number of public list views created.

---

## Anti-Pattern 3: Adding too many fields to a compact layout

**What the LLM generates:** "Add all 15 key fields to the compact layout so users can see everything in the highlights panel."

**Why it happens:** LLMs try to maximize information density. Compact layouts display a maximum of 7 fields on desktop (fewer on mobile). Adding more than 7 fields means the extra fields are silently dropped. The first field becomes the record title. Fields beyond the visible limit are wasted configuration.

**Correct pattern:**

```
Compact layout field limits:
- Maximum: 10 fields can be added to a compact layout.
- Visible in highlights panel: first 7 fields on desktop, fewer on mobile.
- The FIRST field in the compact layout becomes the record's primary
  display name in related lists, lookups, and mobile cards.
- Choose high-scan-value fields:
  1. Record Name or primary identifier (always first).
  2. Status or stage field.
  3. Owner.
  4. Key metric (Amount, Priority, Date).
  5-7. Context fields needed for quick triage.
```

**Detection hint:** If the output adds more than 7-10 fields to a compact layout, the excess fields will not display. Count the number of fields in the compact layout configuration.

---

## Anti-Pattern 4: Ignoring that list view filters have AND-only logic by default

**What the LLM generates:** "Create a list view filter: Status = 'New' OR Priority = 'High'."

**Why it happens:** LLMs describe OR logic for list view filters. Standard list view filters use AND logic only -- all filter conditions must be true for a record to appear. OR logic is not natively supported in list view filter configuration. For OR conditions, the admin must use filter logic with the Filter Logic feature (available on some editions).

**Correct pattern:**

```
List view filter logic:
- Default: all conditions are ANDed together.
  Status = 'New' AND Priority = 'High' → only records matching BOTH.

- Filter Logic (available on some editions):
  Add a filter logic row: "1 OR 2"
  Where 1 = Status = 'New', 2 = Priority = 'High'.

- If Filter Logic is not available:
  Create separate list views for each OR condition:
  "New Cases" (Status = New) and "High Priority Cases" (Priority = High).
  Or use a Report with cross-filter for complex logic.
```

**Detection hint:** If the output describes OR conditions in a list view filter without using Filter Logic, the filter will not work as expected. Search for `OR` in list view filter descriptions without a corresponding `Filter Logic` configuration.

---

## Anti-Pattern 5: Not configuring search layouts for lookup and global search results

**What the LLM generates:** "Users can find records using the global search bar. The search results show the record name."

**Why it happens:** LLMs assume search results show useful context automatically. By default, search results show the record name and a few standard fields. Admins can configure search layouts to add additional fields (Account Industry, Case Status, Opportunity Stage) that help users identify the correct record without opening each one.

**Correct pattern:**

```
Configure search layouts for discoverability:
1. Setup → Object Manager → [Object] → Search Layouts for Salesforce Classic.
   (In Lightning, search layouts are configured via the same path.)
2. Edit "Search Results" layout:
   - Add fields that help users distinguish similar records:
     Account: Industry, Type, Billing State.
     Contact: Title, Account Name, Email.
     Case: Status, Priority, Subject.
3. Edit "Lookup Dialogs" layout:
   - Add the same distinguishing fields.
4. Edit "Lookup Phone Dialogs" (for CTI).
5. Lightning search result layout may also be configured via
   Object Manager → [Object] → Search Layouts → Edit next to
   "Search Results."
```

**Detection hint:** If the output does not mention search layouts when discussing record discoverability, the search experience is left at defaults. Search for `search layout` or `Search Results` in the configuration instructions.
