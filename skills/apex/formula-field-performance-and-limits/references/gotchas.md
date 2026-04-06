# Gotchas — Formula Field Performance and Limits

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Compile-Size Limit Counts Expanded Internal Paths, Not Source Characters

**What happens:** A formula that appears short in the editor fails to save with a "Formula is too large" error. The formula editor shows a source character count (e.g., 950 characters), but the actual compiled representation is several times larger because every field reference is expanded into its internal API path during compilation. Cross-object references are especially expensive: `Account.Owner.Profile.Name` expands to a multi-component internal reference far longer than the four tokens in the source.

**When it occurs:** When a formula contains many cross-object field references, when the same sub-expression is repeated multiple times (e.g., the same `IF()` condition copy-pasted in several branches), or when `TEXT()` is used on picklist fields that have long internal paths.

**How to avoid:** Use helper formula fields to share sub-expressions across a large formula. Each helper field is referenced as a single token at compile time regardless of its own complexity. Also avoid unnecessary `TEXT()` conversions of long picklist API names if the result is only used in a comparison.

---

## Gotcha 2: Formula Fields in SOQL WHERE Clauses Cause Full Table Scans Even With Other Indexed Fields in the Clause

**What happens:** A SOQL query has a compound WHERE clause combining an indexed standard field with a formula field predicate. Practitioners assume the indexed field will filter the result set first, making the formula evaluation cheap. In practice, the query optimizer may still evaluate the formula predicate across a large portion of the table if the formula predicate is the one that drives selectivity. The Query Plan Tool will show `TableScan: true` or a high relative cost for the formula filter step.

**When it occurs:** Any SOQL query that includes a formula field in the WHERE, ORDER BY, or GROUP BY clause, regardless of what other fields are present. The severity scales with object record count — problems typically become production-critical at 500,000+ records but can surface earlier in orgs with many concurrent users.

**How to avoid:** Remove formula fields from all SOQL filter, sort, and grouping positions. Replace them with stored fields that mirror the formula value and carry an index. Use the Query Plan Tool in Developer Console (Help > Training > Query Plan) to verify index usage before deploying any SOQL change.

---

## Gotcha 3: No Trigger or CDC Event Fires When Formula-Dependent Data Changes

**What happens:** A formula field `Days_Since_Close__c` on Opportunity references the `CloseDate` field and today's date (`TODAY()`). A practitioner writes a trigger or CDC subscription expecting to detect when this field's "value" changes. No trigger fires and no CDC event arrives when the calculated result would be different — because the formula field has no stored value and Salesforce never writes a change to the Opportunity row when only the passage of time or the referenced parent record changes.

**When it occurs:** Whenever a developer tries to react to a formula field result changing as if it were a stored field. Common cases: wanting to send a notification when a formula-computed status changes, trying to capture a formula value in a trigger's `Trigger.new` vs `Trigger.old` comparison, or subscribing to a formula field in a Change Data Capture channel.

**How to avoid:** If the business requirement is to detect or react to a change in a calculated value, the value must be stored. Use a Record-Triggered Flow to write the formula result into a stored field on each record save. For time-based changes (e.g., `TODAY()` makes a formula result flip), use a Scheduled Flow or Scheduled Apex job that periodically evaluates and updates the stored field.

---

## Gotcha 4: Cross-Object Formula Spanning Limit Counts Unique Relationships, Not Hops

**What happens:** The platform enforces a limit of 10 unique spanning relationships per formula field. Practitioners sometimes assume this means 10 lookup traversals in a single reference chain (e.g., A.B.C.D counts as 3). In reality, the limit counts distinct relationship paths across the entire formula expression. A formula that references `Account.Owner.Name`, `Account.Owner.Department`, and `Account.Owner.Profile.Name` spans Account→User (one relationship), User (implicitly, already counted for Owner), and Profile — the count accumulates across all references in the formula, not just in one chain.

**When it occurs:** Complex formula fields on junction objects or fields that aggregate information from several parent objects (e.g., an Opportunity formula that reads from Account, Account.Owner, Contract, Contract.Account, and Pricebook fields simultaneously).

**How to avoid:** Count all unique relationship objects traversed by the formula, not just the depth of any single path. When approaching the limit, split the formula across multiple fields or use a Flow that reads the data and writes it to a stored field, which bypasses formula-field relationship limits entirely.

---

## Gotcha 5: Backfilling the Stored Field After Creation Is Mandatory, Not Optional

**What happens:** A stored field is created to replace a formula field for SOQL filtering. A Flow is deployed to keep it in sync. But the stored field's initial value is blank or null for all existing records — only new saves after the Flow is activated populate it. SOQL queries that filter on the stored field return empty or incorrect result sets for all records created before the backfill, causing silent data quality failures.

**When it occurs:** Any time a stored field is introduced to replace or mirror a formula field on an object with pre-existing records, and the backfill step is skipped or deferred. This is the most common operational failure when implementing the materialization pattern.

**How to avoid:** Always include a backfill step as part of the deployment checklist. Execute a Batch Apex job or use Data Loader with a formula-evaluated export to populate the stored field on existing records before any production SOQL query switches to the new field. Verify backfill completion with a `SELECT COUNT() FROM ObjectName WHERE Stored_Field__c = null` check before releasing.
