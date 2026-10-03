# Gotchas — Large Data Volume Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
"LDV guide" means *Best Practices for Deployments with Large Data Volumes* (Summer '26, `salesforce_large_data_volumes_bp.pdf`). Each gotcha names its section. Claims no fetched source confirms carry an inline `UNVERIFIED (date):` marker.

## Gotcha 1: LIKE and custom index sampling

**What happens:** For LIKE, the query optimizer does not use its statistics table. The LDV guide ("Standard and Custom Indexed Fields") says it samples up to 100,000 records of actual data to decide whether to use the custom index. A leading-`%` pattern rarely qualifies.

**When it occurs:** Text search-style filters on large custom objects in integrations or Apex loops.

**How to avoid:** Prefer selective equality or prefix filters on indexed fields. Move free-text search to SOSL with targeted search groups, which the same guide recommends, and redesign integrations that depend on non-sargable LIKE patterns at LDV scale.

---

## Gotcha 2: OR defeats indexes unless every field is indexed

**What happens:** The LDV guide says that for OR, the optimizer uses the indexes unless they all return more than 10% of the object's records, and all fields in the OR clause must be indexed for any index to be used. For AND, it uses the indexes unless one of them returns more than 20%.

**When it occurs:** Dynamic SOQL builders that concatenate OR across optional search fields, where one optional field is unindexed.

**How to avoid:** Index every field that can appear in an OR, or decompose the query: the guide's SOQL table says to break an OR of two indexed fields into two queries and join the results. Use `IN` instead of a long list of OR conditions on one field.

---

## Gotcha 3: Divisions require scale and a Support request

**What happens:** The LDV guide ("Divisions") says an org must have over one million records in a single object and more than 35 licenses to use divisions, and Salesforce enables the partitioning support through Customer Support.

**When it occurs:** Teams plan divisions as a quick fix on moderately sized objects.

**How to avoid:** Confirm both thresholds before putting divisions in the architecture. Otherwise invest in selectivity and skew fixes first.

---

## Gotcha 4: The custom index threshold is no longer a flat 333,333 rows

**What happens:** Selectivity math done with the old rule (10% of total rows, capped at 333,333) misjudges large objects. Correction (2026-10-03): the current LDV guide says a custom index is used when the filter matches less than 10% of the first million records and less than 5% of additional records. Its own examples: 500,000 rows allows 50,000 matches; 5 million rows allows 300,000. For standard indexes the rule is less than 30% of the first million and less than 15% of additional records (2 million rows allows 450,000; 5 million allows 900,000). UNVERIFIED (2026-10-03): the one-million-row cap on standard index matches that earlier text stated is not in the current guide's threshold section.

**When it occurs:** Index requests and query reviews that quote thresholds from older blog posts or training material.

**How to avoid:** Recompute thresholds with the current formula for the object's actual row count, and confirm the chosen plan with the REST API `explain` parameter (REST API Developer Guide, "Get Feedback on Query Performance (Beta)").

---

## Gotcha 5: Custom index tables leave out nulls by default

**What happens:** A filter like `Region__c = null` or a lookup `= null` scans the table even though the field has a custom index. The LDV guide ("Index Tables") says index tables do not include null rows by default; Customer Support can create indexes that include them, and existing indexes must be explicitly enabled and rebuilt. The Metadata API `CustomIndex` type exposes this as `allowNullValues` (default `false`, API 50.0 and later, Support involvement required).

**When it occurs:** "Unassigned" queues, orphan-record cleanup jobs, and integrations that pick up rows where a status or lookup is still blank.

**How to avoid:** Replace nulls with a real value (the LDV guide suggests a value such as `NA` for picklists and foreign keys) or request a null-inclusive index. Avoid negative filters such as `!= null`, which the guide lists separately as non-selective.

---

## Gotcha 6: Formula, cross-object, and special standard fields cannot be indexed

**What happens:** A dashboard filters on a formula that references a lookup or uses `TODAY()`, and no index request can fix it. The LDV guide says custom indexes work only on deterministic formulas. Non-deterministic ones include formulas that reference other objects, use dynamic date functions, or reference owner, autonumber, division, or audit fields, multi-select picklists, currency fields in a multicurrency org, long text, and binary fields. It also lists standard fields with special behavior, such as Opportunity `Amount`, `IsClosed` and `IsWon`, and Case `ClosedDate` and `IsClosed`.

**When it occurs:** Reports built on convenience formulas, and Opportunity or Case reporting at LDV scale.

**How to avoid:** Materialize the needed value into a plain field (via a before-save flow or batch job) and index that field. Check the field type against the guide's list before opening a Support case.

---

## Gotcha 7: Skinny tables have sandbox, scope, and change-management limits

**What happens:** Performance tests pass in production and fail in a Partial Copy sandbox, or a report gets slower after someone adds a column. The LDV guide ("Skinny Tables") says skinny tables are copied to Full sandboxes only (Support can activate them elsewhere), cannot include fields from other objects, are limited to 200 columns, omit soft-deleted records, and must be redefined by Salesforce whenever the report, list view, or query they serve changes.

**When it occurs:** Any skinny table program without a change-control step, and testing done outside Full sandboxes.

**How to avoid:** Record each skinny table's column list next to the reports it serves. Add a change-control check that routes new columns on those reports to a Support request. Test skinny-table-dependent performance only in a Full sandbox.

---

## Gotcha 8: Skew thresholds apply to owners and to parents

**What happens:** The LDV guide's best-practice tables say to avoid any user owning more than 10,000 records and to distribute child records so that no parent has more than 10,000 children (for example, spreading contacts across several placeholder accounts). Exceeding either concentrates sharing computation or lock contention.

**When it occurs:** Integration users that own every record they load, and "unassigned" or catch-all parent accounts.

**How to avoid:** Partition ownership across queues or role-aligned owners and split mega-parents. During loads, group child records by `ParentId` in the same batch to minimize parent locking conflicts, as the guide recommends.

---

## Gotcha 9: Mass deletes need the hard delete path, children first

**What happens:** A cleanup deletes several million rows with a normal delete and runs for days. The LDV guide ("Deleting Data" table) says that for one million or more records you should use the hard delete option of Bulk API or Bulk API 2.0, and that records with many children should have the children deleted first.

**When it occurs:** Archival cut-overs and data retention purges.

**How to avoid:** Plan deletes as Bulk API hard deletes in child-to-parent order, after the archive copy is verified. Grant the hard-delete permission only to the integration user running the purge, for the purge window.

---

## Gotcha 10: Very large queries belong in Bulk API 2.0, and long-running SOQL is cancelled

**What happens:** An integration pulls 8 million rows through REST queries and times out. The LDV guide says that when a query can return more than one million results, the Bulk API 2.0 query capability may be more suitable, and to tune scope and filters, then add a `LIMIT` (starting at 100,000) if timeouts persist. The Apex Developer Guide ("Execution Governors and Limits") cancels a transaction whose SOQL query runs longer than 120 seconds.

**When it occurs:** Nightly extracts and reconciliation jobs written against small sandboxes.

**How to avoid:** Route extracts above a million rows through Bulk API 2.0 query jobs, keep filters selective, and design incremental extracts (by `SystemModstamp`, which carries a standard index) instead of full pulls.
