# Examples — Analytics External Data

## Example 1: Programmatic CSV Upload via InsightsExternalData API

**Scenario:** A nightly ETL job (Python script running on an external server) needs to push a 500 MB flat file of e-commerce order data from a proprietary system into CRM Analytics as a materialized dataset.

**Problem:** The source system has no prebuilt Salesforce connector. Using Data Loader or Bulk API targets Salesforce objects — neither can write into CRM Analytics datasets. Uploading the full file as a single API call exceeds the 10 MB per-chunk limit.

**Solution:**

The job follows the three-phase External Data API protocol:

```json
// Step 1: POST to /services/data/v63.0/sobjects/InsightsExternalData
// Create the header record with metadata JSON schema
{
  "Name": "EcommerceOrders",
  "EdgemartAlias": "EcommerceOrders",
  "MetadataJson": "<base64-encoded metadata JSON>",
  "Format": "Csv",
  "Operation": "Overwrite",
  "Action": "None"
}

// Metadata JSON (before base64 encoding) defines the dataset schema:
{
  "fileFormat": {
    "charsetName": "UTF-8",
    "fieldsDelimitedBy": ",",
    "linesTerminatedBy": "\n"
  },
  "objects": [
    {
      "connector": "CSV",
      "fullyQualifiedName": "EcommerceOrders",
      "label": "Ecommerce Orders",
      "name": "EcommerceOrders",
      "fields": [
        {"fullyQualifiedName": "OrderId", "name": "OrderId", "type": "Text", "label": "Order ID"},
        {"fullyQualifiedName": "Revenue", "name": "Revenue", "type": "Numeric", "label": "Revenue",
         "defaultValue": "0", "precision": 18, "scale": 2},
        {"fullyQualifiedName": "OrderDate", "name": "OrderDate", "type": "Date",
         "label": "Order Date", "format": "yyyy-MM-dd"}
      ]
    }
  ]
}
```

```python
# Step 2: Upload data in 10 MB gzip chunks
# Python pseudocode — stdlib only
import gzip, base64, json, urllib.request

def upload_chunk(session_id, instance_url, parent_id, part_number, csv_bytes):
    compressed = gzip.compress(csv_bytes)
    body = {
        "InsightsExternalDataId": parent_id,
        "PartNumber": part_number,
        "DataFile": base64.b64encode(compressed).decode("utf-8")
    }
    req = urllib.request.Request(
        f"{instance_url}/services/data/v63.0/sobjects/InsightsExternalDataPart",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {session_id}", "Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req)

# Step 3: Trigger processing
# PATCH InsightsExternalData record: set Action = "Process"
```

**Why it works:** The three-phase sequence (schema first, chunks second, process action third) matches exactly what the External Data API requires. Chunking into 10 MB compressed pieces stays within the per-part limit. The `Overwrite` operation replaces the dataset cleanly each night.

---

## Example 2: Snowflake Data Connector for Scheduled Materialized Sync

**Scenario:** An analytics team needs a CRM Analytics dashboard showing Snowflake marketing attribution data refreshed every four hours. Query performance must be fast — the marketing team runs the dashboard repeatedly during campaign reviews.

**Problem:** Configuring a Live Dataset would push every dashboard query to Snowflake at runtime, creating unpredictable latency and Snowflake credit consumption during peak usage. The four-hour freshness window makes materialization the better fit.

**Solution:**

1. In CRM Analytics Data Manager, create a Remote Connection of type Snowflake. Provide account URL, warehouse, database, schema, and OAuth or username/password credentials. Test the connection.
2. Create a new Recipe in Analytics Studio. Add an Input node of type "Remote Connection" referencing the Snowflake connection. Select the target table (e.g., `MARKETING.ATTRIBUTION_EVENTS`).
3. Add an Output node targeting a new CRM Analytics dataset named `MarketingAttribution`.
4. Set the Recipe refresh schedule to every four hours.
5. Run the Recipe manually once to validate row counts match Snowflake source.

```text
Recipe node sequence:
[Snowflake Remote Connection Input] → [Filter: only last 90 days by EventDate] → [Output: MarketingAttribution dataset]
```

**Why it works:** Data is materialized inside CRM Analytics after each scheduled Recipe run. Dashboard queries run against the local dataset — fast and consistent regardless of Snowflake availability. The four-hour window is acceptable for marketing attribution use cases where near-real-time is not required.

---

## Example 3: Live Dataset for Real-Time Finance Queries

**Scenario:** The CFO requires a CRM Analytics dashboard that shows current Snowflake general ledger balances — data that changes intraday and cannot tolerate even a one-hour refresh lag.

**Problem:** Scheduling a Data Connector refresh cannot achieve sub-hour freshness at acceptable cost. A materialized dataset would always show stale data during peak finance review periods.

**Solution:**

1. Create a Remote Connection to Snowflake in Data Manager (same setup as above, but used for Live Dataset rather than a Recipe).
2. Navigate to CRM Analytics Setup → Live Datasets and create a new Live Dataset referencing the Remote Connection and the target Snowflake view `FINANCE.CURRENT_GL_BALANCES`.
3. Build a SAQL query against the Live Dataset in the dashboard lens. Every dashboard load executes this query live against Snowflake.
4. Monitor Snowflake query history to validate response times stay under 5 seconds under concurrent dashboard load.

**Why it works:** Every dashboard load reflects current Snowflake data with no refresh lag. The tradeoff is explicit: dashboard performance depends entirely on Snowflake availability and response time. This is acceptable for a CFO dashboard where data accuracy outweighs display speed.

---

## Anti-Pattern: Using Data Loader to Push Data into CRM Analytics

**What practitioners do:** They export a CSV from an external system and attempt to import it using Salesforce Data Loader, targeting CRM Analytics "datasets" as if they were standard Salesforce objects.

**What goes wrong:** Data Loader operates on Salesforce SObjects (standard and custom objects in the core platform). CRM Analytics datasets are not SObjects — they live in a separate analytics store. Data Loader has no mechanism to address them. The import either fails with an object-not-found error or silently does nothing.

**Correct approach:** Use the External Data API (`InsightsExternalData` SObject) for programmatic CSV ingestion. For Salesforce-connected data, use native CRM Analytics Dataflows or Recipes with local connectors. For external warehouse data, use Data Connectors or Live Datasets.
