# LLM Anti-Patterns — Related List Configuration

Common mistakes AI coding assistants make when generating or advising on Related List Configuration. These patterns help the consuming agent self-check its own output.

UNVERIFIED (2026-10-21), applies to this file: whether "Enhanced Related Lists" is a separate component or a list-type setting (AP2, AP5), the 10-column cap (AP2), silent sort fallback (AP4) and the "> 6 Enhanced components / hundreds of milliseconds" figure (AP5) are Help or field reports, not corpus facts. Grounded truths to use instead: the Layout's `RelatedListItem` holds `fields`, one `sortField` and `sortOrder` Asc/Desc (api_meta 264 L85859-85873); the Layout type has **no description field** (L85051-85153); lookup dialog columns are `SearchLayouts.lookupDialogsAdditionalFields`, not Search Filter Fields (L47528, L47574).

---

## Anti-Pattern 1: Telling the user to edit related lists in Lightning App Builder

**What the LLM generates:** "To change the columns on the Cases related list, open the Lightning record page in Lightning App Builder, click the Related Lists component, and update the columns property."

**Why it happens:** LLMs conflate "where the related list is displayed" (Lightning App Builder) with "where the related list is defined" (Page Layout). The Lightning App Builder UI does expose component-level properties, so LLMs assume column choice is one of them.

**Correct pattern:** Direct the user to edit the **Page Layout** that the affected (Profile × Record Type) resolves to. Setup → Object Manager → <Object> → Page Layouts → <layout> → Related Lists section → wrench icon on the related list. Columns are `RelatedListItem.fields` on the Layout (api_meta 264 L85859), and the guide's FlexiPage sample gives `force:relatedListContainer` only a `relatedListComponentOverride` property (L70339-70342). UNVERIFIED (2026-10-21): that no Lightning related-list component (for example an Enhanced `Related List - Single`) can carry its own column list — Help-only; check the component's properties before telling the user App Builder cannot set columns.

```text
WRONG: "In Lightning App Builder, open the Related List - Single component
        and edit the Columns field."

RIGHT: "Edit the Page Layout in Object Manager → <Object> → Page Layouts.
        Find the related list (Related Lists section), click the wrench
        icon, and configure columns there. The Lightning component will
        pick up the change because it reads from the Page Layout."
```

**Detection hint:** If the response mentions "Columns" as a Lightning App Builder property or instructs the user to change related-list columns through Setup → Lightning App Builder for a layout-driven related list, the LLM is wrong (the Enhanced-list case is UNVERIFIED, above).

---

## Anti-Pattern 2: Promising more than 10 columns on the classic related list (cap per Help, UNVERIFIED)

**What the LLM generates:** "Add the 12 columns you need to the related list: Name, Status, Owner, CreatedDate, LastModifiedDate, Type, Priority, Reason, Source, AccountId, Subject, Description."

**Why it happens:** LLMs treat column lists as unbounded prose and don't know about Salesforce's silent 10-column cap on classic related lists. There is no error in the layout editor when you exceed 10, so the LLM has no documented failure mode to anchor on.

**Correct pattern:** Cap at 10 columns when using the classic `Related Lists` or `Related List - Single` components. Push secondary columns behind View All. If > 10 columns are essential, recommend the **Enhanced Related Lists** component, which raises the practical limit, and explicitly state that columns beyond 10 only render in the Enhanced view.

```text
WRONG: "Configure the related list with all 12 columns the user requested."

RIGHT: "Salesforce silently caps classic related list columns at 10. Pick
        the 10 most important: Name, Status, Owner, Priority, CreatedDate,
        LastModifiedDate, Type, Reason, Source, AccountId. Subject and
        Description show up in View All. If all 12 must be inline, switch
        the component to Enhanced Related Lists."
```

**Detection hint:** Count any column list in the response. If it has > 10 fields for a classic component, flag.

---

## Anti-Pattern 3: Suggesting visibility filters on the Lightning record page as the per-record-type related-list strategy

**What the LLM generates:** "Add the Opportunities related list to the Account Page Layout, then on the Lightning record page set a visibility filter `RecordType.DeveloperName != 'Service_Account'` on the Related List - Single (Opportunities) component."

**Why it happens:** LLMs prefer one-config-fits-all (a single Page Layout) and reach for Lightning App Builder visibility filters as the "modern" path. They don't understand that the Page Layout block remains visible to layout-editing admins regardless of the App Builder filter.

**Correct pattern:** Use one Page Layout per record type when related-list sets diverge. Route via Page Layout Assignment (`ProfileLayoutAssignments`, api_meta 264 L100702-100705). Record the divergence in the change record or config workbook — not "in the Page Layout description", which does not exist in Layout metadata.

```text
WRONG: "Hide the Opportunities related list on the Service record type
        with a Lightning App Builder visibility filter."

RIGHT: "Create Account_Service_Layout (without Opportunities) and assign
        it to the Service_Account record type via Page Layout Assignment.
        Note in the change record: 'INTENTIONAL: Opportunities removed for
        Service record type.' Leave the Lightning record page lean — no
        visibility filters needed."
```

**Detection hint:** If the response uses `RecordType.DeveloperName` inside a Lightning component visibility filter to control related-list display, flag.

---

## Anti-Pattern 4: Choosing an unsortable field as the related-list sort field

**What the LLM generates:** "Sort the Contacts related list by `Account.Owner.Name` descending so the most recent owner's contacts surface first."

**Why it happens:** LLMs treat all dotted relationship fields as queryable in any context. They have not seen the Salesforce platform constraint that related-list sorting requires a directly stored, sortable scalar on the child object.

**Correct pattern:** Pick a directly stored sortable field on the child. If sorting by a related value is essential, expose that value as a denormalized field on the child via a single-hop formula (still risky) or a workflow / process / Flow that copies it.

```text
WRONG: "Set sort field to Account.Owner.Name on the Contacts related list."

RIGHT: "Pick a directly stored sortable field on Contact, like
        LastModifiedDate or CreatedDate. Cross-object formula and long-text
        sort fields silently fall back to default sort. If sorting by
        Account.Owner.Name is essential, expose it as a denormalized
        Contact field via Flow or a formula."
```

**Detection hint:** If the suggested sort field is a cross-object (dotted) reference, a long text area, an encrypted text field, or a base64 field, flag.

---

## Anti-Pattern 5: Treating Enhanced Related Lists as a drop-in replacement with no performance cost

**What the LLM generates:** "Use Enhanced Related Lists for every related list on the record page — they have filtering, mass actions, and a better UX."

**Why it happens:** LLMs default to "newer is always better." Enhanced Related Lists are visibly richer than classic, so the LLM assumes blanket adoption is the right move.

**Correct pattern:** Use Enhanced Related Lists for the related lists that actually benefit (filtering or mass actions are needed). Keep the rest on classic or `Related List - Single`. UNVERIFIED (2026-10-21): the claim that placing > 6 Enhanced components above the fold adds hundreds of milliseconds to First Paint — measure on the org's own page.

```text
WRONG: "Replace all 8 related lists on the Lightning record page with
        Enhanced Related Lists components."

RIGHT: "Use Enhanced Related Lists for the Cases related list (users need
        the filter) and the Opportunities related list (mass close-won
        action). Keep Contacts, Files, Notes, Activity History, and the
        rest on the classic all-in-one Related Lists block to limit
        initial render cost."
```

**Detection hint:** If the response recommends Enhanced Related Lists for every related list on a page without distinguishing which ones need the filter / mass-action features, flag.
