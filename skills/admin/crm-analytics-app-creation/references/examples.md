# Examples — CRM Analytics App Creation

## Example 1: Users Assigned Permission Set But See No Data in App

**Context:** A sales operations admin creates a CRM Analytics app with a pipeline dashboard. The admin assigns the CRM Analytics Plus User permission set to the sales team. The sales reps report they can access Analytics Studio and see the app name, but the dashboard shows no data.

**Problem:** The admin stopped at permission set assignment. The sales reps have access to Analytics Studio but have not been granted Viewer access on the specific app. Additionally, the Opportunity dataset has no security predicate, so even if they had app access, all 500,000 Opportunity rows would be visible to every Viewer without any data restriction.

**Solution:**

1. In Analytics Studio, open the app and select Share.
2. Add the "Sales Reps" public group as Viewer.
3. Navigate to the dataset settings and add a security predicate:
```
'OwnerId' == "$User.Id"
```
This restricts each sales rep to seeing only their own Opportunity records.

4. Re-test with a sales rep login — they should now see the dashboard populated with their own pipeline data.

**Why it works:** App sharing grants access to the app container and its assets. The security predicate restricts which dataset rows each user can see. Both must be configured independently.

---

## Example 2: Building a Service Metrics Dashboard from Scratch

**Context:** A service operations manager needs a dashboard showing open case volume by priority, average handle time, and agent utilization. Standard Salesforce reports are insufficient because the analysis requires joining Case, User, and Account data and computing handle time as a derived metric.

**Problem:** The manager needs a CRM Analytics app with a multi-object dataset that does not exist yet.

**Solution:**

1. In Analytics Studio, create a Blank App named "Service Operations."
2. In Data Manager > Connected Objects, enable sync for Case, User, and Account objects.
3. Create a Data Prep Recipe:
   - Load Case connected object
   - Join User on OwnerId (to get agent name and role)
   - Join Account on AccountId (to get account tier)
   - Add a Formula node: `CASE_HANDLE_TIME = (ClosedDate - CreatedDate) / 3600` (hours)
   - Output to a registered dataset named "ServiceCases"
4. Schedule the recipe to run every 6 hours.
5. Create lenses:
   - "Cases by Priority" — group by Priority, count rows
   - "Avg Handle Time by Agent" — group by Owner.Name, measure AVG(CASE_HANDLE_TIME)
6. Build a dashboard assembling both lenses with a date range filter and a Priority filter widget.
7. Share the app with the Service Operations Manager group as Viewer and the admin as Manager.

**Why it works:** Data Prep recipes enable admin-friendly multi-object joins and derived metric calculation without writing SAQL or JSON dataflow nodes. The joined dataset powers multiple lenses and a unified dashboard.

---

## Anti-Pattern: Querying Connected Objects Directly in Dashboard Steps

**What practitioners do:** After enabling Data Sync for the Opportunity object (creating a connected object), attempt to select that connected object as the data source for a new lens or dashboard step.

**What goes wrong:** Connected objects do not appear in the dataset selector for lens creation or dashboard steps. The admin may not find them at all, or may find them but see empty results because connected objects are staging-layer replicas that cannot be directly visualized. Time is wasted troubleshooting data ingestion when the real fix is adding a recipe or dataflow to materialize the connected object into a registered dataset.

**Correct approach:** Always create a recipe or dataflow that consumes connected objects and outputs to a registered dataset. The registered dataset — not the connected object — is the data source for lenses and dashboards.
