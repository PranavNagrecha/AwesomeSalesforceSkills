# Gotchas — CRM Analytics Dashboard JSON

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Dataset Name References Fail Silently After Migration

**What happens:** A SAQL step that references a dataset by display name instead of `datasetId`/`datasetVersionId` works in the authoring org but returns zero results in any other org or sandbox without throwing an error. The dashboard renders as if the step has no data — widgets show empty charts, tables show no rows.

**When it occurs:** Any time the dashboard is deployed via Metadata API, copied to a sandbox, refreshed in a sandbox, or shared to another org. Dataset IDs are org-specific; the same dataset in a sandbox has a different ID than the same dataset in production. Name-based fallback resolution can match the wrong version or find no match at all.

**How to avoid:** Always use `datasetId` and `datasetVersionId` from `GET /services/data/vXX.X/wave/datasets` in both the SAQL `load` statement and the `datasets` array entry of the step. The format in the `load` statement is `"datasetId/datasetVersionId"`. Never use the display name as the primary reference. When deploying across orgs, include a post-deploy step that patches dataset IDs in dashboard JSON to match the target org.

---

## Gotcha 2: Empty Bindings Return Empty String, Not Null or Error

**What happens:** When a binding expression such as `{{cell(stepName.selection, 0, "fieldName")}}` has no source value — because the user has not made a selection in the source step — the expression evaluates to an empty string `""`. This is not an error condition and produces no console or UI warning. The behavior of the downstream SAQL query or widget parameter that consumes this empty string depends on how it is written.

**When it occurs:** Any time a filter-driven binding is present and the dashboard first loads (no default selection set in `state`), or after a user clears a selection in a filter widget. Also occurs when the source step returns zero rows.

**How to avoid:** Explicitly handle the empty-binding case in the SAQL query. For example, use a conditional pattern that produces an unfiltered query when the binding resolves to empty:

```saql
q = filter q by ('Industry' == "{{cell(industryStep.selection, 0, "Industry")}}" || "" == "{{cell(industryStep.selection, 0, "Industry")}}");
```

The second clause short-circuits the filter when the binding is empty, returning the full population instead of zero rows. Alternatively, pre-seed the `state` object with a default selection value so the binding always has a non-empty source.

---

## Gotcha 3: SAQL Step Row Limit Defaults to 2,000 with No UI Indication of Truncation

**What happens:** Every SAQL step has a default `limit` of 2,000 rows. If the SAQL query returns more rows than this limit, results are silently truncated. Widgets render the partial dataset without any warning, error badge, or row count indicator showing truncation occurred.

**When it occurs:** Any step that does not have an explicit `limit` property on the step object. This includes newly created steps and steps copied from older dashboards. Steps that happen to return fewer than 2,000 rows are unaffected, making the issue latent until data volume grows.

**How to avoid:** Set `"limit": 10000` on the step object in the dashboard JSON for any step where full-population accuracy matters. Also add `limit 10000` to the SAQL query string itself. The platform-enforced maximum is 10,000 rows per step; values higher than 10,000 are silently capped. Note that increasing the limit increases render time — do not raise limits on steps where truncation is acceptable for performance reasons.

---

## Gotcha 4: REST API PUT Replaces the Entire Dashboard Body

**What happens:** `PUT /services/data/vXX.X/wave/dashboards/{dashboardId}` replaces the entire dashboard JSON body atomically. There is no partial-update or patch mechanism. If the PUT body omits any existing step, widget, or state key that was present before, those elements are permanently removed from the dashboard (though accessible via history).

**When it occurs:** Any time a developer edits only a portion of the JSON (e.g., extracts one step to modify it, then PUTs just that step object) without wrapping it in the full dashboard body structure.

**How to avoid:** Always retrieve the complete dashboard body with `GET /wave/dashboards/{dashboardId}` immediately before making edits. Modify the full body in memory, then PUT the entire body. Never construct a PUT payload from partial extracts or from a locally cached copy that may be stale.

---

## Gotcha 5: History API Versions Are Not Automatically Cleaned Up

**What happens:** Every PUT to a dashboard creates a new history snapshot. Over time, dashboards with frequent programmatic updates accumulate large numbers of history entries. While old versions are accessible, there is no built-in history pruning mechanism and the Salesforce UI does not surface a history count or storage warning.

**When it occurs:** Automated processes that PUT dashboard JSON on a schedule (e.g., CI/CD pipelines refreshing dashboards programmatically) can generate hundreds of history snapshots per day. This is generally not a blocking problem but can complicate debugging if practitioners need to identify which version introduced a change.

**How to avoid:** When running automated PUT operations, record the `id` and `lastModifiedDate` from each PUT response in a change log external to Salesforce. This provides a human-readable audit trail without relying on the History API to enumerate all versions. For manual edits, use the History API (`GET /wave/dashboards/{id}/histories`) to list and verify versions before and after major changes.
