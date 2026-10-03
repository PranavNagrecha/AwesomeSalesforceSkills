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
   - Add a Formula node: `CASE_HANDLE_TIME = (ClosedDate - CreatedDate) / 3600` (hours). UNVERIFIED (2026-10-03): recipe formula syntax for date differences was not confirmed in a fetched source; build the formula in the recipe editor's function list and check the unit on a few known cases.
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

---

## Example 3: The App As Deployable Metadata, With Its Sharing And A Recipe Predicate

**Context:** The Service Operations app from Example 2 is ready in a full sandbox and must be promoted to production with the same sharing and row-level security.

**Step 1: confirm row-level security in the source org before retrieving.** Check what sharing inheritance covers for the current dataset version (REST Guide, Security Coverage Dataset Version Resource, API 41.0):

```bash
curl "https://MyDomainName.my.salesforce.com/services/data/v67.0/wave/security/coverage/datasets/ServiceCases/versions/$VERSION_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H "X-PrettyPrint:1"
```

Get `$VERSION_ID` from `GET /services/data/v67.0/wave/datasets/ServiceCases/versions` (Dataset Versions List Resource).

**Step 2: the app container.** `force-app/main/default/wave/Service_Operations.wapp-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <assetIcon>/analytics/wave/web/proto/images/app/icons/11.png</assetIcon>
    <description>Case volume, handle time, and agent utilization for Service Operations</description>
    <folder>Service_Operations</folder>
    <masterLabel>Service Operations</masterLabel>
    <shares>
        <accessLevel>View</accessLevel>
        <sharedTo>Service_Operations_Managers</sharedTo>
        <sharedToType>Group</sharedToType>
    </shares>
    <shares>
        <accessLevel>Manage</accessLevel>
        <sharedTo>CRM_Analytics_Admins</sharedTo>
        <sharedToType>Group</sharedToType>
    </shares>
</WaveApplication>
```

Field names and the sample icon path come from the Metadata API WaveApplication reference; `accessLevel` values `View`, `EditAllContents`, and `Manage` and `sharedToType` `Group` come from FolderShare, the type of `shares`. UNVERIFIED (2026-10-03): whether `sharedTo` takes the group's developer name in source format (the reference sample shows a username for a `User` share); retrieve the app after sharing it in Analytics Studio and match the values.

**Step 3: the recipe with its predicate.** Retrieve, do not hand-author, the recipe: `WaveRecipe.dataflow` is the org's dataflow Id. The retrieved `force-app/main/default/wave/ServiceCases_Recipe.wdpr-meta.xml` should look like:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WaveRecipe xmlns="http://soap.sforce.com/2006/04/metadata">
    <dataflow>02KXXXXXXXXXXXXXXX</dataflow>
    <format>R3</format>
    <masterLabel>ServiceCases Recipe</masterLabel>
    <securityPredicate>'OwnerId' == "$User.Id"</securityPredicate>
    <targetDatasetAlias>ServiceCases</targetDatasetAlias>
</WaveRecipe>
```

The element names and the `'UserId' == "$User.Id"` predicate style are from the Metadata API WaveRecipe sample. The recipe predicate applies when the dataset is first created; later security changes must be made on the dataset itself (Security Guide).

**Step 4: the manifest.** `manifest/package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Service_Operations</members>
        <name>WaveApplication</name>
    </types>
    <types>
        <members>ServiceCases</members>
        <name>WaveDataset</name>
    </types>
    <types>
        <members>ServiceCases_Recipe</members>
        <name>WaveRecipe</name>
    </types>
    <types>
        <members>ServiceCases_Recipe</members>
        <name>WaveDataflow</name>
    </types>
    <types>
        <members>Service_Operations_Overview</members>
        <name>WaveDashboard</name>
    </types>
    <types>
        <members>Cases_by_Priority</members>
        <name>WaveLens</name>
    </types>
    <version>67.0</version>
</Package>
```

The recipe's dataflow is listed by name because "Use of the wildcard character doesn't return the recipe's associated dataflows." UNVERIFIED (2026-10-03): that the dataflow member shares the recipe's API name; list the org's dataflows (`sf org list metadata --metadata-type WaveDataflow`) and use the name shown.

**Step 5: after deployment.** Run the recipe in production so `ServiceCases` has rows, open the dashboard as a member of `Service_Operations_Managers`, and confirm each manager sees only their own cases.

**Why it works:** the app share, the predicate, and the manifest are all files, the recipe and its dataflow travel together, and the post-deployment run fills the dataset before anyone opens the app.

