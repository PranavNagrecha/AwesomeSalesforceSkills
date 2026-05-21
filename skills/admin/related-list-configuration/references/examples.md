# Examples — Related List Configuration

---

## Example 1: Reducing a Bloated Account → Contacts Related List

**Context.** An Account record page shows the Contacts related list with 12 columns, several of which are internal-only (`Internal_Notes__c`, `Renewal_Owner__c`, `Last_Internal_Touch__c`). Reps complain the list is unreadable on the inline view and the columns they actually need (`Title`, `Email`, `Phone`, `LastModifiedDate`) get truncated. Mobile users see a near-blank row.

**Problem.** Two real bugs hide here:
1. The classic Related Lists component silently drops the 11th and 12th columns. The admin who added them sees them in the layout editor but they never render to end users — those fields are effectively dead config.
2. The first 4 columns on the Page Layout (`Name`, `Internal_Notes__c`, `Renewal_Owner__c`, `Last_Internal_Touch__c`) are what mobile users see — and three of the four are internal-only.

**Solution.** Edit the Account → Contacts related list on the affected Page Layout (Setup → Object Manager → Account → Page Layouts → <layout> → Related Lists section → wrench icon on Contacts):

```text
Columns (in order, max 10):
  1. Name
  2. Title
  3. Email
  4. Phone
  5. Account.Owner
  6. LastModifiedDate
  7. CreatedDate
  8. MailingCity
  9. MailingCountry
 10. Reports_To.Name

Sort field: LastModifiedDate
Sort direction: Descending
```

Move `Internal_Notes__c`, `Renewal_Owner__c`, and `Last_Internal_Touch__c` off the related list entirely (or to a second related-list-style component for an internal-ops record page variation). Verify mobile by impersonating a mobile-user profile in the Lightning App Builder mobile preview — the top 4 columns should now be the rep-facing ones.

**Why this works.** Sort on `LastModifiedDate` matches the "most recently touched" mental model reps actually use. The 10-column cap is respected so nothing silently drops. Mobile shows real customer-facing data.

---

## Example 2: Splitting Open vs. Closed Cases on the Account Page

**Context.** An Account record page has a single Cases related list with 200+ rows under busy accounts. Service reps need to triage open Cases quickly; CSMs occasionally need the full closed-case history for renewal calls. Today they scroll endlessly or open View All.

**Problem.** A classic Related Lists block can't filter inline. Adding a second Cases related list to the Page Layout isn't possible — Page Layouts allow only one entry per relationship.

**Solution.** Use the **Enhanced Related Lists** component for Cases, with the inline filter set as the default for service reps:

1. On the Lightning record page in App Builder, remove `Cases` from the all-in-one `Related Lists` block (or replace the all-in-one block with per-list components).
2. Add an **Enhanced Related Lists** component for the `Cases` relationship near the top of the page.
3. In the component's properties, set the default sort field to `LastModifiedDate` descending; configure the columns the Page Layout already defines. The filter UX is per-user (filters persist in the user's session, not as a default), so reps must apply `Status NOT IN ('Closed', 'Closed - Resolved')` once and it will stick for their next visit.
4. (Optional, for CSMs) Create a second Lightning record page variation assigned to the CSM Profile that places a second Enhanced Related Lists component below for closed cases, pre-titled "Closed Cases — last 12 months."

```yaml
component: Enhanced Related Lists
relationship: Cases
columns_from: <Page Layout assigned to this Profile+RecordType>
default_sort_field: LastModifiedDate
default_sort_direction: Descending
allow_filter: true
allow_mass_actions: true
rows_displayed: 10
```

**Why this works.** Reps get instant filter without leaving the record page. The all-in-one block stays for other related lists where filtering isn't needed, keeping initial render cost down. CSMs and reps get different page variations without forking the Page Layout.

---

## Example 3: Per-Record-Type Divergence for Account Service vs. Sales

**Context.** Account has two record types: `Sales_Account` and `Service_Account`. Service reps should not see the Opportunities related list (it is irrelevant to their work and the OpportunityName field leaks deal data). Sales reps need it.

**Problem.** A single Account Page Layout shared across both record types means either both see Opportunities (data leak) or neither sees it (sales loses functionality). Hiding the Opportunities component on the Lightning record page using a visibility filter `RecordType.DeveloperName != 'Service_Account'` works at runtime, but the underlying Page Layout still shows Opportunities to anyone editing the layout later — and any admin who clones the layout inherits the assumption.

**Solution.** Maintain one Page Layout per record type and make the divergence explicit:

```text
Page Layouts:
  - Account_Sales_Layout       → assigned to Sales_Account record type
    Related lists: Contacts, Opportunities, Cases, Activity History
  - Account_Service_Layout     → assigned to Service_Account record type
    Related lists: Contacts, Cases, Activity History, Service Contracts
    Description (editable on the layout): "INTENTIONAL: Opportunities related
      list removed for Service record type. Do not add back without re-confirming
      data-visibility with the service ops lead."

Page Layout Assignment matrix (Setup → Account → Page Layouts → Page Layout Assignment):
  - All Profiles × Sales_Account   → Account_Sales_Layout
  - All Profiles × Service_Account → Account_Service_Layout
```

The Lightning record page can be **one** record page for both record types — no visibility-filter contortions are needed. The Related Lists component just renders whatever the resolved Page Layout dictates.

**Why this works.** The intent is encoded where the next admin will see it: in the Page Layout description and in the explicit per-record-type layout. The Lightning App Builder stays simple. There is no hidden visibility-filter logic to discover.

---

## Anti-Pattern: Putting All Related-List Logic in App Builder Visibility Filters

A common mistake is to keep one big Page Layout with every related list, then use component-level visibility filters on the Lightning record page to show/hide related-list components per (Profile × Record Type).

```text
WRONG:
  Page Layout: Account_All_Layout (related lists: Contacts, Opportunities, Cases,
               Service_Contracts, Marketing_Campaigns, Internal_Notes, Audit_Log)
  Lightning Record Page: Account_Record_Page
    - Related List - Single (Contacts)             visibility: always
    - Related List - Single (Opportunities)        visibility: RecordType = 'Sales_Account'
    - Related List - Single (Cases)                visibility: always
    - Related List - Single (Service_Contracts)    visibility: RecordType = 'Service_Account'
    - Related List - Single (Marketing_Campaigns)  visibility: Profile = 'Marketing User'
    ... etc.
```

**Why this is wrong:**

- Every related list is still in the Page Layout. Any admin editing the layout sees Opportunities under a Service Account and assumes it is intentional.
- Adding a related list later requires editing both the Page Layout (to expose the relationship) AND the Lightning record page (to add another Related List - Single with the right visibility filter). It is easy to do one and forget the other.
- Visibility filters do not compose with Page Layout assignment — a user with the right Profile but the wrong Record Type gets unpredictable results when filters depend on both.
- The Lightning page becomes a tangle of N component instances with overlapping filter expressions, instead of one Related Lists block driven by Page Layout choice.

**Correct pattern.** One Page Layout per intended related-list shape; route via Page Layout Assignment; keep the Lightning record page lean.
