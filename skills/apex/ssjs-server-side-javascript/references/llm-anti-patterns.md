# LLM Anti-Patterns — SSJS Server-Side JavaScript

Common mistakes AI coding assistants make when generating or advising on SSJS in Salesforce Marketing Cloud. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Modern JavaScript Syntax (`let`, `const`, Arrow Functions, Template Literals)

**What the LLM generates:**

```javascript
<script runat="server">
const apiUrl = `https://api.example.com/data`;
let results = [];
const process = (row) => {
  results.push({ key: row.SubscriberKey, email: row.EmailAddress });
};
</script>
```

**Why it happens:** LLMs are trained predominantly on modern JavaScript (ES6+). `let`, `const`, arrow functions, and template literals are the overwhelming norm in training data. The SSJS ES3 engine constraint is rare and counterintuitive — most documentation examples online also use modern syntax incorrectly.

**Correct pattern:**

```javascript
<script runat="server">
var apiUrl = "https://api.example.com/data";
var results = [];
function process(row) {
  results.push({ key: row.SubscriberKey, email: row.EmailAddress });
}
</script>
```

**Detection hint:** Scan generated SSJS for `let `, `const `, `=>`, backtick characters (`` ` ``), `...` spread, `async`, `await`, or `Promise`. Any match is a syntax error in the SSJS engine.

---

## Anti-Pattern 2: Using `JSON.stringify()` and `JSON.parse()` Instead of Marketing Cloud Equivalents

**What the LLM generates:**

```javascript
var payload = JSON.stringify({ key: "value" });
var data = JSON.parse(resp.content);
```

**Why it happens:** `JSON.stringify` and `JSON.parse` are universal JavaScript built-ins. LLMs have no reason to know that the Marketing Cloud SSJS engine does not expose them. The failure at runtime is an "object not found" or "undefined" error with no clear indication that a Marketing Cloud-specific alternative is needed.

**Correct pattern:**

```javascript
var payload = Stringify({ key: "value" });
var data = Platform.Function.ParseJSON(resp.content);
```

**Detection hint:** Any occurrence of `JSON.stringify(` or `JSON.parse(` in SSJS code is wrong and will fail at runtime on the Marketing Cloud engine.

---

## Anti-Pattern 3: Using Raw HTTP SOAP Calls Instead of WSProxy

**What the LLM generates:**

```javascript
var req = new Script.Util.HttpRequest("https://webservice.s7.exacttarget.com/Service.asmx");
req.method = "POST";
req.setHeader("Content-Type", "text/xml");
req.setHeader("SOAPAction", "Retrieve");
req.postData = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">...' +
  '<fueloauth>' + token + '</fueloauth>...' +
  '</s:Envelope>';
var resp = req.send();
```

**Why it happens:** LLMs default to generic HTTP patterns when a specialized client exists. SOAP API documentation examples sometimes show raw HTTP patterns. The LLM treats WSProxy as just one option rather than the strongly preferred mechanism.

**Correct pattern:**

```javascript
var prox = new Script.Util.WSProxy();
var cols = ["SubscriberKey", "EmailAddress"];
var filter = { Property: "Status", SimpleOperator: "equals", Value: "Active" };
var result = prox.retrieve("Subscriber", cols, filter);
```

**Detection hint:** If generated code makes HTTP requests to `webservice.s7.exacttarget.com` or `mc.s*.exacttarget.com` with SOAP action headers, it should be replaced with the equivalent WSProxy call.

---

## Anti-Pattern 4: Missing `try/catch` in Script Activity Code

**What the LLM generates:**

```javascript
<script runat="server">
Platform.Load("Core", "1.1.1");
var prox = new Script.Util.WSProxy();
var result = prox.retrieve("DataExtension", ["Name", "CustomerKey"], null);
Write("Done: " + result.Results.length);
</script>
```

**Why it happens:** LLMs optimize for concise, readable examples. Error handling adds boilerplate. In most programming contexts, uncaught exceptions produce visible stack traces — the LLM has no intuition that in Marketing Cloud Script Activities, uncaught exceptions produce only a generic failure with no diagnostic information.

**Correct pattern:**

```javascript
<script runat="server">
Platform.Load("Core", "1.1.1");
try {
  var prox = new Script.Util.WSProxy();
  var result = prox.retrieve("DataExtension", ["Name", "CustomerKey"], null);
  Write("Done: " + result.Results.length);
} catch(e) {
  Write("ERROR: " + e.message);
}
</script>
```

**Detection hint:** Any Script Activity SSJS block that lacks a `try { ... } catch(e) { Write(...) }` wrapper around its main logic is missing critical error handling.

---

## Anti-Pattern 5: Not Checking `HasMoreRows` After WSProxy Retrieve

**What the LLM generates:**

```javascript
var prox = new Script.Util.WSProxy();
var result = prox.retrieve("Subscriber", ["SubscriberKey", "EmailAddress"], filter);
var rows = result.Results; // silently truncated at ~2500 rows
for (var i = 0; i < rows.length; i++) {
  // process rows
}
```

**Why it happens:** LLMs model WSProxy retrieve as a standard query-all operation. The paging behavior is a Marketing Cloud-specific implementation detail not present in most query APIs. LLMs do not know the result set is implicitly limited to a page size, so they do not generate the pagination loop.

**Correct pattern:**

```javascript
var prox = new Script.Util.WSProxy();
var result = prox.retrieve("Subscriber", ["SubscriberKey", "EmailAddress"], filter);
var rows = [];
while (result && result.Results && result.Results.length > 0) {
  for (var i = 0; i < result.Results.length; i++) {
    rows.push(result.Results[i]);
  }
  if (result.HasMoreRows) {
    result = prox.getNextPage();
  } else {
    break;
  }
}
```

**Detection hint:** Any `prox.retrieve()` call not followed by a `while (result.HasMoreRows)` loop should be reviewed. Acceptable exceptions: when the retrieve is known to return at most one record (e.g., a lookup by primary key with an equality filter).

---

## Anti-Pattern 6: Expecting Real-Time or On-Demand Execution of Script Activities

**What the LLM generates:** Recommends putting a Script Activity in an Automation as the response mechanism for a real-time event (e.g., "when a record is updated in Salesforce CRM, trigger this Script Activity to send a transactional email").

**Why it happens:** LLMs understand Script Activities as "code that runs" without understanding the Automation Studio scheduler model. They conflate Script Activities with REST API-triggerable serverless functions.

**Correct pattern:** Script Activities run on Automation Studio schedules or are triggered by other Automation steps. For real-time event-driven responses, use Transactional Messaging API (REST), Triggered Sends, or Journey Builder Entry Sources. Script Activities are appropriate for scheduled batch operations, not event-driven real-time responses.

**Detection hint:** If a recommendation involves "triggering" a Script Activity from a CRM event, webhook, or real-time user action, the architecture is wrong. Script Activities cannot be invoked on-demand via an external event (only the Run Once / API-triggered Automation Start supports external triggering, which is a different concern).
