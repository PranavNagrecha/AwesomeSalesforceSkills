# Gotchas — Einstein Next Best Action

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Strategy Builder Deprecated Since Spring '24

**What happens:** Practitioners attempt to create or edit NBA strategies using Strategy Builder, but the interface is either missing from Setup or throws errors in newer orgs. Existing Strategy Builder strategies may stop working without warning in future releases.

**When it occurs:** Any org provisioned after Spring '24, or existing orgs where Strategy Builder has been decommissioned by Salesforce. Also triggers when following outdated Trailhead modules or community blog posts that reference Strategy Builder.

**How to avoid:** Always use Autolaunched Flows for NBA strategies. Audit existing orgs for any remaining Strategy Builder strategies and migrate them to Flow Builder. Treat any documentation referencing Strategy Builder as outdated.

---

## Gotcha 2: ActionReference Silent Failure on Inactive or Misnamed Flows

**What happens:** A user clicks the acceptance button on a recommendation and nothing visible occurs — no error message, no action executed. The recommendation appears to have been accepted, but the linked Flow or quick action never fires.

**When it occurs:** When the ActionReference field on the Recommendation record contains an API name that does not match any active Flow or quick action. Common causes include typos in the API name, the referenced Flow being deactivated during deployment, or the Flow being in a managed package with a namespace prefix that was omitted from ActionReference.

**How to avoid:** Maintain a validation routine (manual or automated) that cross-references every Recommendation record's ActionReference value against the org's active Flows and quick actions. Include namespace prefixes when referencing packaged Flows. Test acceptance actions in a sandbox before promoting Recommendation records to production.

---

## Gotcha 3: 25-Recommendation Display Limit with Silent Truncation

**What happens:** The Actions & Recommendations component displays only the first 25 recommendations, silently discarding any beyond that threshold. There is no warning to the user or admin that recommendations were dropped.

**When it occurs:** When the strategy Flow returns more than 25 Recommendation records in its output collection. This is common in orgs with many active recommendations and broad filtering logic.

**How to avoid:** Implement explicit sorting and limiting in your strategy Flow. Use a Loop element with a counter to cap the output list at 25 or fewer. Sort by priority or relevance score before truncating so the most important recommendations survive the cut.

---

## Gotcha 4: Recommendation Records Are Org-Wide, Not Object-Specific

**What happens:** Practitioners expect Recommendation records to be scoped to a specific object (like Case or Opportunity), but the Recommendation sObject is a flat, org-wide table with no built-in object relationship. Every strategy Flow sees the same pool of Recommendation records unless filtering is applied.

**When it occurs:** When multiple strategy Flows are deployed across different objects (Cases, Opportunities, Accounts) and each Flow's Get Records element retrieves all Recommendation records without filters. This leads to irrelevant recommendations appearing on the wrong record pages.

**How to avoid:** Use a custom field (e.g., `Target_Object__c` picklist) on the Recommendation object to tag which object context each recommendation belongs to. Filter by this field in each strategy Flow's Get Records element to ensure only relevant recommendations are retrieved.

---

## Gotcha 5: Flow Output Variable Must Be Specifically Typed as Recommendation Collection

**What happens:** The strategy Flow runs without errors, but the Actions & Recommendations component shows no recommendations. Debug logs show the Flow completed successfully.

**When it occurs:** When the Flow's output variable is defined as a generic `List<SObject>` or as a single Recommendation record instead of a collection variable with sObject type set to Recommendation. The Actions & Recommendations component expects a specifically typed `List<Recommendation>` output variable and silently ignores output that does not match.

**How to avoid:** When creating the output variable in Flow Builder, ensure: (1) it is marked as a collection, (2) the data type is set to Record, (3) the object type is specifically set to Recommendation, and (4) the variable is marked as "Available for Output." Verify all four settings if the component renders blank.
