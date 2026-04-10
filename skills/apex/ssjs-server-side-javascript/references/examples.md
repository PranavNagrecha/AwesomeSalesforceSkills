# Examples — SSJS Server-Side JavaScript

## Example 1: WSProxy Retrieve with Paging and Filtered Results

**Context:** An Automation Studio Script Activity needs to retrieve all Active subscribers from the All Subscribers list whose email domain is a specific partner domain, then write their keys to a Data Extension for a targeted send.

**Problem:** A developer uses `prox.retrieve("Subscriber", cols, filter)` but does not check `HasMoreRows`, so only the first page of results (up to 2,500 rows) is processed. The remaining thousands of matching subscribers are silently skipped, causing an under-count that is not caught until the send shows lower-than-expected volume.

**Solution:**

```javascript
<script runat="server">
Platform.Load("Core", "1.1.1");
try {
  var prox = new Script.Util.WSProxy();
  var cols = ["SubscriberKey", "EmailAddress", "Status"];
  var filter = {
    Property: "Status",
    SimpleOperator: "equals",
    Value: "Active"
  };

  var result = prox.retrieve("Subscriber", cols, filter);
  var allRows = [];

  while (result && result.Results && result.Results.length > 0) {
    for (var i = 0; i < result.Results.length; i++) {
      allRows.push(result.Results[i]);
    }
    if (result.HasMoreRows) {
      result = prox.getNextPage();
    } else {
      break;
    }
  }

  Write("Total subscribers retrieved: " + allRows.length);

  // Upsert to target DE
  var upsertRows = [];
  for (var j = 0; j < allRows.length; j++) {
    var sub = allRows[j];
    upsertRows.push({
      keys: { SubscriberKey: sub.SubscriberKey },
      values: { EmailAddress: sub.EmailAddress }
    });
  }

  if (upsertRows.length > 0) {
    var upsertResult = prox.upsertBatch("DataExtensionObject", upsertRows, { Name: "Partner_Targets_DE" });
    Write("Upsert status: " + upsertResult.Status);
  }
} catch(e) {
  Write("ERROR in subscriber retrieve: " + e.message);
}
</script>
```

**Why it works:** The `while` loop checks `result.HasMoreRows` on every iteration and calls `prox.getNextPage()` to advance. WSProxy handles the SOAP continuation token internally. Without this loop, the script silently processes only the first page.

---

## Example 2: Outbound REST API Call with Structured Error Handling

**Context:** A Script Activity needs to pull lead score data from an external REST API after each nightly batch run, then write the scores to a Data Extension used for segmentation.

**Problem:** The developer calls `req.send()` without checking `resp.statusCode`. When the external API returns a 401 or 503, `resp.content` contains an error body, not the expected JSON array. `Platform.Function.ParseJSON()` on the error body throws an exception that crashes the Script Activity step, leaving no log of which API endpoint failed or what status was returned.

**Solution:**

```javascript
<script runat="server">
Platform.Load("Core", "1.1.1");

var API_URL = "https://api.example.com/v2/lead-scores";
var API_TOKEN = Platform.Function.Lookup("Config_DE", "Value", "Key", "API_TOKEN");

try {
  var req = new Script.Util.HttpRequest(API_URL);
  req.emptyContentHandling = 0;
  req.retryCount = 2;
  req.setHeader("Authorization", "Bearer " + API_TOKEN);
  req.setHeader("Accept", "application/json");
  req.method = "GET";

  var resp = req.send();

  if (resp.statusCode != 200) {
    throw new Error("API returned HTTP " + resp.statusCode + ": " + resp.content);
  }

  var leads = Platform.Function.ParseJSON(resp.content);
  Write("Leads received: " + leads.length);

  var rows = [];
  for (var i = 0; i < leads.length; i++) {
    var lead = leads[i];
    rows.push({
      keys: { LeadID: lead.id },
      values: { Score: lead.score.toString(), UpdatedAt: lead.updated_at }
    });
  }

  if (rows.length > 0) {
    var prox = new Script.Util.WSProxy();
    var res = prox.upsertBatch("DataExtensionObject", rows, { Name: "Lead_Scores_DE" });
    Write("DE upsert status: " + res.Status + ", rows: " + rows.length);
  }

} catch(e) {
  Write("CRITICAL ERROR: " + e.message);
  // Optionally insert a row into an Error_Log DE for alerting
  var errProx = new Script.Util.WSProxy();
  errProx.createItem("DataExtensionObject", {
    CustomerKey: "Error_Log_DE",
    Properties: [
      { Name: "ActivityName", Value: "LeadScoreSync" },
      { Name: "ErrorMessage", Value: e.message },
      { Name: "Timestamp", Value: Platform.Function.Now().toString() }
    ]
  });
}
</script>
```

**Why it works:** The `resp.statusCode` check prevents parsing a non-JSON error body. The `catch` block logs the error via `Write()` and inserts a structured error record to a logging Data Extension, enabling Automation Studio monitors to alert on failures without the Activity step crashing the entire Automation.

---

## Anti-Pattern: Using Raw HTTP to Call the Marketing Cloud SOAP API Instead of WSProxy

**What practitioners do:** They construct raw SOAP XML strings, set `Content-Type: text/xml`, and POST to the Marketing Cloud SOAP endpoint using `Script.Util.HttpRequest`, manually embedding a SOAP UsernameToken or OAuth header.

**What goes wrong:** Raw SOAP construction is error-prone — envelope namespaces, action headers, and authentication token refreshes must all be managed manually. WSProxy handles all of this automatically including token lifecycle. Raw HTTP SOAP calls also have higher latency and are more likely to fail silently when the token expires mid-activity.

**Correct approach:** Use WSProxy for all Marketing Cloud object operations. Raw `Script.Util.HttpRequest` should be reserved for external REST APIs or non-Marketing Cloud SOAP endpoints that WSProxy cannot reach.
