# Gotchas — Custom Index Requests

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: External ID Indexes the Field but Does Not Make It Unique

**What happens:** Two opposite mistakes. Teams avoid External ID on a filter field because they believe it will reject duplicate values; or they rely on External ID to keep integration keys unique and later find duplicates, and upserts by that key fail.

**When it occurs:** The LDV guide says External IDs cause an index to be created, and the Apex guide lists custom fields marked External ID *or* Unique among the fields indexed by default; in `CustomField` metadata, `externalId` and `unique` are separate booleans. The upsert documentation shows duplicates are possible: "If the external ID is matched multiple times, then a 300 error is reported, and the record isn't created or updated."

**How to avoid:** Set `unique` to true when values must be unique. Use External ID alone when you need the index (and upsert matching) without a uniqueness constraint, and expect upserts on a duplicated value to fail.

---

## Gotcha 2: Some Field Types Can Never Take a Custom Index

**What happens:** A Support case asks for an index on a long text field or a formula and is turned down, after weeks of waiting.

**When it occurs:** The LDV guide excludes long and rich text areas, non-deterministic formula fields, and encrypted text. The Apex guide adds multi-select picklists, currency fields in a multicurrency org, some formula fields, binary fields, and formulas that call TEXT() on a picklist. Formulas that reference other objects or use TODAY or NOW are non-deterministic.

**How to avoid:** Check the type first. For a non-deterministic formula, store the value in a regular field kept current by automation and index that, or filter through cross-object notation on an indexed parent field.

---

## Gotcha 3: An Index That Misses Its Threshold Is Simply Not Used

**What happens:** Support creates the index, and the plan still shows a table scan.

**When it occurs:** The optimizer pre-queries its statistics and uses a custom index only when the filter matches less than 10% of the first million rows and 5% of rows beyond that (the LDV guide's examples: 50,000 on a 500,000-row object, 300,000 on 5 million). As the object grows or the value distribution shifts, a value that used to qualify can stop qualifying.

**How to avoid:** Attach the counts and arithmetic to the request, and re-check plans when the object grows. If the value can never be selective, change the query rather than asking for an index.

---

## Gotcha 4: Null Rows Are Not in the Index Unless Support Rebuilds It

**What happens:** `WHERE Region__c = null` scans the table even though `Region__c` is indexed.

**When it occurs:** The LDV guide: index tables don't include null records by default; Customer Support can create indexes that include null rows, and existing custom indexes must be explicitly enabled and rebuilt to index empty values. The `CustomIndex` metadata type exposes this as `allowNullValues`, default false.

**How to avoid:** Ask for a null-inclusive index explicitly, or store a placeholder value such as `NA` (the LDV guide's suggestion for picklist and foreign-key nulls) and filter on that.

---

## Gotcha 5: Two-Column Indexes Have a Selecting Column and a Sorting Column

**What happens:** A two-column index is requested without stating the order, or in an order that does not match how the list view selects and sorts.

**When it occurs:** The LDV guide's example is an Account list view that selects by State and sorts by City, served by a two-column index "with State in the first column and City in the second." It also shows a two-column index on two fields always filtered together. Two-column indexes have the same restrictions as single-column ones, except that the second column may hold nulls.

**How to avoid:** Put the selecting field first and the sorting field second in the case, quote the exact query or list view, and confirm with a plan after creation.

---

## Gotcha 6: Skinny Tables Help Only the Queries They Cover, and Can Hurt

**What happens:** A skinny table is created and a report stays slow, or other operations slow down.

**When it occurs:** Read-only operations that reference only fields in the skinny table avoid an extra join between the standard and custom field tables. A query that also needs one field outside the skinny table gets no benefit. The LDV guide warns that skinny tables "aren't a magic wand" and that using them in the wrong context can degrade performance; they hold at most 200 columns and no fields from other objects, and a change to the report's fields needs another Support request.

**How to avoid:** Request a skinny table only for a stable set of read-only queries on objects with millions of rows, list every field those queries need, and repeat the request when the field list changes.

---

## Gotcha 7: Custom Indexes Reach Every New Sandbox; Skinny Tables Reach Only Full Sandboxes

**What happens:** A developer tests in a Developer sandbox and concludes "the skinny table isn't working," or files a second index request because they assume a Support-built index never reaches sandboxes.

**When it occurs:** The LDV guide: custom indexes that Customer Support creates in production are copied to all sandboxes created from that production org. Skinny tables are copied to Full sandboxes only; other sandbox types need a Support request. Query statistics are gathered nightly, so plans right after a large data change can mislead.

**How to avoid:** Test skinny tables in a Full sandbox. Test custom indexes in any sandbox created after the index exists, and capture plans after the first nightly statistics run.
