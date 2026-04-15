# Examples — Analytics Data Governance

## Example 1: GDPR Right-to-Erasure Affecting a CRM Analytics Dataset

**Context:** A financial services org stores customer transaction data in a CRM Analytics dataset called `Customer_Transactions`, produced by a nightly recipe that pulls from `Transaction__c`. A data subject submits a GDPR erasure request. The privacy team asks the analytics team to confirm deletion.

**Problem:** The data steward deletes the current dataset version via the Data Manager UI and marks the request closed. Three weeks later, a compliance audit discovers that six earlier dataset versions — retained automatically by CRM Analytics version history — still contain the subject's rows. The erasure was incomplete.

**Solution:**

```python
# Enumerate and delete all dataset versions via REST API (stdlib only)
import urllib.request, json, sys

def delete_all_dataset_versions(instance_url, access_token, dataset_id, api_version="v63.0"):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # 1. List all versions
    versions_url = (
        f"{instance_url}/services/data/{api_version}/wave/datasets/{dataset_id}/versions"
    )
    req = urllib.request.Request(versions_url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        versions = json.load(resp).get("versions", [])

    print(f"Found {len(versions)} version(s) for dataset {dataset_id}")

    # 2. Delete each version
    for v in versions:
        v_id = v["id"]
        del_url = (
            f"{instance_url}/services/data/{api_version}"
            f"/wave/datasets/{dataset_id}/versions/{v_id}"
        )
        del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
        try:
            with urllib.request.urlopen(del_req) as resp:
                print(f"Deleted version {v_id} (status {resp.status})")
        except urllib.error.HTTPError as e:
            print(f"Failed to delete version {v_id}: {e}", file=sys.stderr)

    # 3. Delete the dataset itself
    ds_url = f"{instance_url}/services/data/{api_version}/wave/datasets/{dataset_id}"
    ds_req = urllib.request.Request(ds_url, headers=headers, method="DELETE")
    with urllib.request.urlopen(ds_req) as resp:
        print(f"Deleted dataset {dataset_id} (status {resp.status})")
```

**Why it works:** CRM Analytics version history is a separate resource from the current dataset. A UI delete removes the dataset reference but does not cascade to stored versions. The REST API `/wave/datasets/{id}/versions` endpoint exposes all versions and must be iterated explicitly.

---

## Example 2: Access Audit Log for a Quarterly SOC 2 Review

**Context:** A SaaS company undergoes a SOC 2 Type II audit. The auditor asks for evidence that access to the `Revenue_Forecast` CRM Analytics dataset was restricted to the Finance team during Q1 2026.

**Problem:** The admin attempts to pull an access log from Setup > Login History and the Salesforce Setup Audit Trail. Neither surface captures dataset-level access in CRM Analytics. The admin has the Event Monitoring add-on but is unsure how to query it for analytics events.

**Solution:**

Step 1 — Confirm Event Monitoring is active and `WaveInteraction` event type is enabled.

Step 2 — If org is Summer '24+ with Event Log Objects enabled, query directly:

```soql
SELECT
    UserId,
    SessionKey,
    QueriedEntities,
    RequestSize,
    Timestamp
FROM WaveInteractionLog
WHERE Timestamp >= 2026-01-01T00:00:00Z
  AND Timestamp <  2026-04-01T00:00:00Z
ORDER BY Timestamp ASC
```

Filter results client-side for rows where `QueriedEntities` contains `Revenue_Forecast`.

Step 3 — For older orgs using hourly CSV delivery:

```soql
SELECT Id, EventType, LogDate, LogFile
FROM EventLogFile
WHERE EventType = 'WaveInteraction'
  AND LogDate >= 2026-01-01T00:00:00Z
  AND LogDate <  2026-04-01T00:00:00Z
ORDER BY LogDate ASC
```

Download each `LogFile` content blob, parse the CSV, filter on the `DATASET_ID` or `DATASET_NAME` column, and extract `USER_ID` and `TIMESTAMP`.

Step 4 — Cross-reference `UserId` values against the Finance team's permission set group membership to verify that no unauthorized users accessed the dataset.

**Why it works:** `WaveInteraction` is the correct event type for CRM Analytics dashboard and dataset read access. Setup Audit Trail captures configuration changes (metadata), not runtime data access. Login History captures login events, not which analytics resources were queried.

---

## Example 3: Building a Dataset Lineage Map Before a Schema Change

**Context:** An architect needs to refactor the `Opportunity_Pipeline` recipe, which feeds three downstream datasets used by different dashboards. Before making changes, they need to confirm exactly which datasets are downstream dependencies.

**Problem:** The Data Manager UI shows immediate inputs and outputs for a single recipe run, but does not show cross-recipe or cascading lineage. The architect does not know whether any other recipes use the `Opportunity_Pipeline` output datasets as inputs.

**Solution:**

```python
# Produce a lineage map: dataset_name -> list of producers
import urllib.request, json

def build_lineage_map(instance_url, access_token, api_version="v63.0"):
    headers = {"Authorization": f"Bearer {access_token}"}
    lineage = {}  # dataset_name -> [{"type": ..., "id": ..., "label": ...}]

    # Recipes
    url = f"{instance_url}/services/data/{api_version}/wave/recipes"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        for recipe in json.load(r).get("recipes", []):
            for ds in recipe.get("outputDatasets", []):
                lineage.setdefault(ds["name"], []).append(
                    {"type": "recipe", "id": recipe["id"], "label": recipe.get("label", "")}
                )

    # Dataflows: fetch detail to parse node definitions
    url = f"{instance_url}/services/data/{api_version}/wave/dataflows"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        for df in json.load(r).get("dataflows", []):
            df_url = f"{instance_url}/services/data/{api_version}/wave/dataflows/{df['id']}"
            with urllib.request.urlopen(
                urllib.request.Request(df_url, headers=headers)
            ) as r2:
                df_detail = json.load(r2)
            for node in df_detail.get("definition", {}).get("nodes", {}).values():
                ds_params = node.get("parameters", {}).get("dataset", {})
                ds_name = ds_params.get("name") if isinstance(ds_params, dict) else None
                if ds_name and node.get("action") not in ("sfdcDigest", "edgemart"):
                    lineage.setdefault(ds_name, []).append(
                        {"type": "dataflow", "id": df["id"], "label": df.get("label", "")}
                    )
    return lineage
```

Run the script, then inspect the output for `Opportunity_Pipeline`'s downstream dataset names. Also search the map to see if any other recipes list those downstream datasets as inputs (making them indirect dependencies).

**Why it works:** The CRM Analytics REST API exposes the full recipe and dataflow graph in machine-readable form. Building the lineage map programmatically is the only way to capture cross-recipe dependencies at scale; the Data Manager UI is single-recipe scoped.

---

## Anti-Pattern: Relying on Salesforce Data Classification to Identify Sensitive Data in CRM Analytics

**What practitioners do:** A practitioner sets up Salesforce Data Classification on sensitive fields (`SSN__c` tagged as Restricted, `Salary__c` tagged as Confidential) and assumes that CRM Analytics datasets ingesting from those objects will reflect those tags. They skip manual governance documentation because "the classification is already in the system."

**What goes wrong:** There is no mechanism by which CRM Analytics reads or stores Salesforce field Data Classification metadata. The dataset column `SSN__c` in CRM Analytics carries no tag, no flag, and no restriction derived from the source object classification. When a new analyst is granted access to the dataset, nothing in CRM Analytics signals that the column contains restricted data. The data is effectively unprotected at the analytics layer.

**Correct approach:** Treat CRM Analytics datasets as a fresh governance surface. After ingestion, manually document which dataset columns map to classified source fields. Enforce access controls at the dataset layer (column exclusion in the recipe, row-level security predicates, or dataset-level sharing restrictions). Maintain a governance register that maps source classification → dataset column → applied control.
