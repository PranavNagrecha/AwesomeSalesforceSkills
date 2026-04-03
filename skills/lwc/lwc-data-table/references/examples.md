# Examples - LWC Data Table

## Example 1: Inline Edit With Stable Save Handling

**Context:** A sales-ops team needs quick editing of Opportunity stage and amount from a compact table on a record page.

**Problem:** The first version updates local row data immediately and clears the edit state before the server confirms the save.

**Solution:**

Keep edits in `draftValues`, save explicitly, then clear drafts only after persistence succeeds.

```javascript
columns = [
    { label: 'Opportunity', fieldName: 'Name' },
    { label: 'Stage', fieldName: 'StageName', editable: true },
    { label: 'Amount', fieldName: 'Amount', type: 'currency', editable: true }
];

async handleSave(event) {
    const updates = event.detail.draftValues.map((draft) => ({
        fields: { ...draft }
    }));

    await Promise.all(updates.map((recordInput) => updateRecord(recordInput)));
    this.draftValues = [];
    await refreshApex(this.wiredOpportunities);
}
```

**Why it works:** The table keeps view state and persistence state separate, so the user sees a predictable edit lifecycle.

---

## Example 2: Infinite Loading With A Clear Stop Condition

**Context:** A service dashboard needs to browse recent cases without loading every historical record at first render.

**Problem:** The original component keeps appending rows forever and never disables loading once the server is exhausted.

**Solution:**

Use a server-side page size and turn off infinite loading when the returned batch is smaller than the requested size.

```javascript
async handleLoadMore(event) {
    event.target.isLoading = true;
    const nextRows = await getRecentCases({ offsetSize: this.rows.length, pageSize: 50 });

    this.rows = [...this.rows, ...nextRows];
    if (nextRows.length < 50) {
        this.enableInfiniteLoading = false;
    }

    event.target.isLoading = false;
}
```

**Why it works:** The browser only holds the rows users are likely to inspect, and the table knows when to stop asking for more.

---

## Anti-Pattern: Using Array Index As Row Identity

**What practitioners do:** They use a generated row index as `key-field` because the source data does not expose a stable ID.

**What goes wrong:** Sorting, filtering, refresh, and pagination all reshuffle row identity. Selection and draft state jump to the wrong records.

**Correct approach:** Choose a real unique identifier, usually `Id` or another stable key from the source model, and make it part of the table contract.
