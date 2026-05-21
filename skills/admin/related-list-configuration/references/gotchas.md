# Gotchas — Related List Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Classic related lists silently drop the 11th column

**What happens.** An admin adds an 11th or 12th field to a related list on a Page Layout. The layout editor accepts it without warning. End users never see those columns — only the first 10 render. The columns appear in View All (which is the full-page related list grid and supports more), so the admin testing via View All concludes "it works" while end users on the inline view see something different.

**When it occurs.** Any related list rendered through the classic `Related Lists` or `Related List - Single` Lightning component, whose source is the underlying Page Layout. The cap is 10 columns inline.

**How to avoid.** Treat 10 as a hard cap. If users need an 11th column, either drop a less-used column, move the data into a different display surface (compact layout / highlights panel / Dynamic Forms), or migrate that one related list to the Enhanced Related Lists component, which raises the practical column count via wider rows but still bumps against display-width constraints.

---

## Gotcha 2: Cross-object formulas and long text fields silently fall back to default sort

**What happens.** An admin sets a related list's sort field to a cross-object formula (e.g., `Account.Owner.Name` on the Contact related list) or to a long text area. The field picker accepts the choice. At render, the related list uses default sort instead — no error, no warning — because the platform cannot index those field types for related-list sorting.

**When it occurs.** Sort field is a cross-object reference formula, a base64 / blob field, an encrypted text field, a long text area, or any field that the platform cannot sort against the parent → child query.

**How to avoid.** Always pick a directly stored, sortable scalar field on the child object. If users want to sort by a related field, expose it as a denormalized field on the child via a formula that resolves on a single hop (still risky) or via a workflow/process that copies the value at write time.

---

## Gotcha 3: FLS-hidden fields render as blank cells, not access-denied

**What happens.** A field is on the related list's column set, but FLS hides it from the running user's Profile. The cell renders as empty space (an apparently blank column for that record). Users report "the data is missing" or "the field is broken." Admins debug the layout, the data, and the related list before discovering it is an FLS issue.

**When it occurs.** Any related list column where the running user's Profile has Read Field-Level Security set to false on the column's field.

**How to avoid.** When investigating "missing data on the related list," start by impersonating the affected user (Setup → Users → Login) and confirming FLS on each column. Add the field to the user's permission set if access is intended, or remove it from the related list if not.

---

## Gotcha 4: Per-record-type page layouts drift silently after a layout clone

**What happens.** An admin clones Account Page Layout A → Layout B to support a new record type. Months later, a different admin adds a `Cases (Open Only)` related list to Layout A but forgets Layout B. Users on the new record type see no Cases at all where users on the old record type see the new list. There is no automatic drift warning.

**When it occurs.** Any object with > 1 record type backed by > 1 Page Layout, where changes are made unilaterally to one layout.

**How to avoid.** Document the intent in each Page Layout's description field (e.g., "Sales record-type layout — Opportunities related list is mandatory here"). Periodically diff related-list configurations across layouts during an audit. Treat layout B as a peer that needs the same review whenever layout A changes.

---

## Gotcha 5: Lightning App Builder visibility filter hides the component but not the underlying Page Layout block

**What happens.** An admin uses a visibility filter on a Lightning record page component (e.g., `Related List - Single (Opportunities)` shows only when `RecordType = 'Sales'`) and assumes "the related list is removed for Service." The next admin opens the Account Page Layout and sees Opportunities still listed under Related Lists. They cannot tell from the Page Layout that any record types do not see it. They may add fields assuming all record types see them.

**When it occurs.** Any time a related list's visibility is controlled at the Lightning App Builder layer instead of at the Page Layout layer.

**How to avoid.** Prefer per-record-type Page Layouts to express related-list divergence; this puts the intent where layout-editing admins look. When App Builder visibility filters are the only practical option, leave a comment in the Page Layout description naming the visibility-filter source.

---

## Gotcha 6: Enhanced Related Lists per-user column-width preferences are wiped on component swap

**What happens.** Users have been using a related list for months and have set per-user column widths (drag-to-resize). The admin swaps the component from classic `Related List - Single` to `Enhanced Related Lists` (or vice versa) for that relationship. All per-user width preferences are reset to defaults. Users notice and complain.

**When it occurs.** Swapping between `Related Lists`, `Related List - Single`, and `Enhanced Related Lists` components for the same relationship on the same Lightning record page.

**How to avoid.** Communicate the change in advance. Do the swap during a quiet window. Do not flip the component back and forth as a configuration experiment in production — each flip is a UX reset for end users.

---

## Gotcha 7: Mobile App applies the same Page Layout but renders ~4 columns inline

**What happens.** The configured related list has 10 columns on desktop. On the Salesforce Mobile App, only the first 3–4 columns render inline; the rest are accessible by tapping the row to drill into the record. Users on mobile report "the related list has no useful info" while desktop users see it fine. The admin tests on desktop and concludes the configuration works.

**When it occurs.** Any related list viewed in the Salesforce Mobile App. The exact column count varies by device width, but treat ~4 as the working assumption.

**How to avoid.** Order related-list columns with the most customer-facing / decision-critical fields first. Test on the Salesforce Mobile App (or via the Lightning App Builder mobile preview) before declaring done. The columns mobile users see are the first N from the Page Layout's order.

---

## Gotcha 8: `Related Lists - Quick Links` does not honor Enhanced Related Lists filters

**What happens.** An admin sets up `Enhanced Related Lists` with a default user filter on Cases (e.g., Open Cases). They also add the `Related Lists - Quick Links` component at the top of the page so users can jump to each list. The Quick Links count shown next to "Cases (47)" reflects the **unfiltered** count, not the filtered Enhanced view count. Users click through, expecting 47, and see 12.

**When it occurs.** Any page combining Enhanced Related Lists with a user-applied filter and the Quick Links component.

**How to avoid.** Treat Quick Links counts as advisory only. Tell users the count is total related records, not filtered. If accurate filtered counts matter, omit Quick Links or surface a custom Lightning Web Component that queries the filtered count explicitly.
