---
name: ssjs-server-side-javascript
description: "Use this skill when writing, debugging, or reviewing Server-Side JavaScript (SSJS) in Salesforce Marketing Cloud — Script Activities, Cloud Pages, and Landing Pages. Covers WSProxy for SOAP API access, Script.Util.HttpRequest for outbound REST calls, error handling patterns, execution limits, and SSJS/AMPscript interoperability. NOT for AMPscript-only personalization logic inside Email Studio sends, not for standard Apex (Salesforce Platform), and not for client-side JavaScript in Experience Cloud or LWC."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "I need to call a SOAP API from a Marketing Cloud Script Activity without writing raw XML"
  - "My Script Activity is failing silently and I don't know where the error is"
  - "How do I make an outbound HTTP REST call from a Cloud Page using SSJS"
  - "WSProxy is returning null and I don't understand why my retrieve filter is wrong"
  - "My SSJS uses let and const but it throws a syntax error in Marketing Cloud"
  - "Script Activity timed out after 30 minutes — how do I handle long-running data operations"
  - "I want to mix AMPscript and SSJS in the same Cloud Page content block"
  - "How do I log debug output from inside a Script Activity to diagnose failures"
tags:
  - ssjs
  - marketing-cloud
  - script-activity
  - wsproxy
  - cloud-pages
  - automation-studio
  - http-functions
  - ampscript-interop
inputs:
  - "The SSJS file or Script Activity content block to review or write"
  - "The target API endpoint (SOAP or REST) the script needs to call"
  - "The data extension name and field list if doing WSProxy retrieve/upsert"
  - "Any known error messages or Activity failure codes"
  - "Execution context: Script Activity, Cloud Page, or Landing Page"
outputs:
  - "Corrected or authored SSJS wrapped in <script runat='server'> tags"
  - "WSProxy retrieve/upsert/create/delete code with proper filter syntax"
  - "Script.Util.HttpRequest code for outbound REST calls"
  - "try/catch error logging pattern for Script Activity resilience"
  - "Decision guidance on SSJS vs AMPscript split for the given use case"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# SSJS — Server-Side JavaScript

This skill activates when a practitioner needs to author, debug, or architect Server-Side JavaScript (SSJS) code running inside Salesforce Marketing Cloud. It provides grounded guidance on execution environments, WSProxy for SOAP access, HTTP functions for REST calls, error handling, variable scoping rules, and the SSJS/AMPscript interoperability model.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Execution context:** is this running in a Script Activity (Automation Studio), a Cloud Page, or a Landing Page? The timeout, available functions, and subscriber context differ across contexts.
- **API target:** if calling SOAP APIs (retrieve/upsert Data Extensions, send Email, etc.), WSProxy is preferred over raw HTTP+XML. If calling external REST endpoints, use Script.Util.HttpRequest.
- **Most common wrong assumption:** SSJS is modern JavaScript. It is not. Marketing Cloud runs an ES3-compatible engine — `let`, `const`, arrow functions, template literals, destructuring, and Promises are unavailable.
- **Limits:** Script Activities time out at 30 minutes and have a 6 GB memory limit per execution. Cloud Pages have no documented long-execution window and should be treated as synchronous request/response.

---

## Core Concepts

### Execution Environments and the `<script runat="server">` Tag

SSJS code must be wrapped in `<script runat="server">` tags. Without the `runat="server"` attribute the block is treated as client-side JavaScript and does not execute on the Marketing Cloud server. SSJS can coexist with AMPscript in the same file — the Marketing Cloud rendering engine processes AMPscript substitutions first, then evaluates SSJS blocks. This allows AMPscript variables to be referenced inside SSJS if the AMPscript block is declared before the SSJS block.

### WSProxy — Preferred SOAP API Client

WSProxy (`Script.Util.WSProxy`) is the built-in Marketing Cloud SOAP API client for SSJS. It is the correct and preferred way to interact with Marketing Cloud objects (Data Extensions, Subscribers, Sends, etc.) from SSJS because:

- It handles SOAP envelope construction, authentication token injection, and paging automatically.
- It has significantly lower overhead than constructing raw SOAP XML via `Script.Util.HttpRequest`.
- Common operations: `retrieve`, `createItem`, `updateItem`, `upsertBatch`, `deleteItem`.

The core pattern:
```javascript
var prox = new Script.Util.WSProxy();
var cols = ["SubscriberKey", "EmailAddress", "Status"];
var filter = {
  Property: "Status",
  SimpleOperator: "equals",
  Value: "Active"
};
var result = prox.retrieve("Subscriber", cols, filter);
```

Retrieve results are paged. If `result.HasMoreRows` is true, use `prox.getNextPage()` to iterate.

### Script.Util.HttpRequest — Outbound REST/HTTP

For calls to external REST APIs or non-Marketing Cloud SOAP endpoints, use `Script.Util.HttpRequest`. This is a synchronous HTTP client that supports GET, POST, PUT, PATCH, and DELETE. Set headers and body before calling `request.send()`.

```javascript
var req = new Script.Util.HttpRequest("https://api.example.com/data");
req.emptyContentHandling = 0;
req.retryCount = 2;
req.setHeader("Content-Type", "application/json");
req.setHeader("Authorization", "Bearer " + token);
req.method = "POST";
req.postData = Stringify(payload);
var resp = req.send();
var body = Platform.Function.ParseJSON(resp.content);
```

### Error Handling and the Write() Logging Pattern

SSJS does not surface uncaught exceptions to the user in a useful way in Script Activities — an uncaught exception causes the entire Activity step to fail with a generic error, which makes diagnosis difficult. The mandatory pattern is `try/catch` around all significant operations with `Write()` logging inside the catch block.

`Write()` outputs text to the Script Activity log tab in Automation Studio, making it the primary debugging mechanism. Log the error message, stack if available, and any relevant variable state before re-throwing or gracefully continuing.

### ES3 Dialect Constraints

The SSJS engine is ES3-compatible. This means:
- Use `var` for variable declarations — `let` and `const` cause syntax errors.
- No arrow functions (`=>`); use `function` keyword.
- No template literals (backtick strings); use `+` concatenation.
- No destructuring, spread, or `Promise`.
- `JSON.stringify` / `JSON.parse` are not available — use `Stringify()` and `Platform.Function.ParseJSON()` instead.
- `typeof`, `instanceof`, standard `for` loops, and `try/catch/finally` work normally.

---

## Common Patterns

### WSProxy Upsert to a Data Extension

**When to use:** Bulk insert or update records in a Data Extension from a Script Activity, typically after retrieving data from an external API or another system.

**How it works:**
```javascript
<script runat="server">
Platform.Load("Core", "1.1.1");
try {
  var prox = new Script.Util.WSProxy();
  var rows = [
    { keys: { SubscriberKey: "abc123" }, values: { FirstName: "Ana", Score: "95" } },
    { keys: { SubscriberKey: "def456" }, values: { FirstName: "Ben", Score: "80" } }
  ];
  var result = prox.upsertBatch("DataExtensionObject", rows, { Name: "My_DE_ExternalKey" });
  Write("Upserted: " + result.Status);
} catch(e) {
  Write("ERROR: " + e.message);
}
</script>
```

**Why not the alternative:** Using AMPscript `UpsertDE()` works for small single-record updates inside sends, but it cannot handle batch operations, does not provide programmatic status checking, and is not appropriate for Automation Studio Script Activities.

### Outbound REST Call with Error Logging

**When to use:** Pulling data from an external REST API (CRM, ERP, custom backend) inside a Script Activity and writing results to a Data Extension.

**How it works:**
```javascript
<script runat="server">
Platform.Load("Core", "1.1.1");
try {
  var req = new Script.Util.HttpRequest("https://api.example.com/leads");
  req.emptyContentHandling = 0;
  req.retryCount = 1;
  req.setHeader("Authorization", "Bearer MyToken");
  req.method = "GET";
  var resp = req.send();
  if (resp.statusCode != 200) {
    throw new Error("HTTP error: " + resp.statusCode);
  }
  var data = Platform.Function.ParseJSON(resp.content);
  // process data...
  Write("Retrieved " + data.length + " leads.");
} catch(e) {
  Write("FAILED: " + e.message);
  // log to error DE if needed
}
</script>
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Retrieve/upsert Marketing Cloud objects (Subscribers, DEs, Sends) | WSProxy | Handles auth, paging, SOAP envelope automatically; lower overhead than raw HTTP |
| Call external REST API from Script Activity | Script.Util.HttpRequest | Designed for outbound HTTP; handles headers, methods, retries |
| Per-subscriber email personalization at send time | AMPscript | AMPscript has subscriber context; SSJS does not run per-subscriber during sends |
| Complex data transformation, looping, conditional logic in Automation | SSJS Script Activity | SSJS supports full procedural logic; AMPscript is template-oriented |
| Debugging a failing Script Activity | Write() + try/catch | Write() outputs to Activity log; uncaught exceptions give no diagnostic info |
| Need to call a SOAP API without WSProxy | Script.Util.HttpRequest + raw XML | Last resort only — WSProxy is always preferred for SOAP |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm execution context** — identify whether this is a Script Activity, Cloud Page, or Landing Page. Script Activity: check timeout risk (30-min limit). Cloud Page: check whether code needs to be synchronous and handle subscriber context.
2. **Identify the API target** — if interacting with Marketing Cloud objects (Data Extensions, Subscribers, Sends), plan to use WSProxy. If calling external endpoints, plan to use Script.Util.HttpRequest.
3. **Author the SSJS block** — wrap all code in `<script runat="server">` tags. Load the Core library with `Platform.Load("Core", "1.1.1")`. Use only `var` for declarations. Use `Stringify()` and `Platform.Function.ParseJSON()` instead of `JSON.stringify`/`JSON.parse`.
4. **Wrap in try/catch** — every meaningful operation (API call, WSProxy call, data write) must be inside a try/catch block with `Write()` logging in the catch. Never allow uncaught exceptions in Script Activities.
5. **Implement paging if using WSProxy retrieve** — check `result.HasMoreRows` after every `prox.retrieve()` call and loop with `prox.getNextPage()` until false to avoid silently missing records.
6. **Test incrementally** — run the Script Activity manually in Automation Studio, check the Activity log tab for Write() output, verify DE row counts before and after.
7. **Review for ES3 compatibility** — scan for `let`, `const`, arrow functions, template literals, `JSON.stringify`, `JSON.parse`, `Promise`, and `async/await` — all are unsupported and will cause syntax or runtime errors.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All code is inside `<script runat="server">` tags
- [ ] `Platform.Load("Core", "1.1.1")` is present at the top of the block
- [ ] No `let`, `const`, arrow functions, template literals, or modern JS syntax
- [ ] All API calls and data writes are wrapped in try/catch with Write() in the catch block
- [ ] WSProxy retrieve loops check `HasMoreRows` and call `getNextPage()` if paging is possible
- [ ] Script.Util.HttpRequest calls check `resp.statusCode` before consuming `resp.content`
- [ ] Sensitive values (tokens, passwords) are stored in Data Extensions or Content Builder, not hardcoded

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Script Activity 30-minute timeout is absolute** — If a Script Activity exceeds 30 minutes of execution time, it terminates without completing and the step is marked as an error. There is no graceful shutdown callback. For large-volume operations, split work across multiple Activities or use Query Activities for set-based data operations instead.

2. **WSProxy retrieve does not return all rows by default** — `prox.retrieve()` returns a paged result set. If you do not check `result.HasMoreRows` and call `prox.getNextPage()`, you silently process only the first page of results (typically 2,500 rows). This causes data processing gaps that are very hard to detect.

3. **AMPscript is evaluated before SSJS** — In a mixed file, AMPscript variable substitution happens before the SSJS engine runs. This means AMPscript `@variables` can inject values into SSJS string literals, but SSJS variables cannot be read by AMPscript in the same file. Relying on SSJS output being available to AMPscript in the same render pass will not work.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| SSJS Script Activity file | Complete `<script runat="server">` block ready to paste into an Automation Studio Script Activity |
| WSProxy retrieve/upsert snippet | Parameterized code block for reading from or writing to a Data Extension via WSProxy |
| HTTP request snippet | Script.Util.HttpRequest pattern for outbound REST calls with header, method, and error handling |
| Error logging pattern | try/catch + Write() template for any Script Activity block |

---

## Related Skills

- `data/marketing-cloud-sql-queries` — Use for set-based data transformation inside Automation Studio; SQL Query Activity is more efficient than SSJS loops for bulk DE-to-DE operations
- `data/marketing-cloud-data-sync` — Use when the goal is syncing data between Marketing Cloud and external systems at the platform configuration level rather than via SSJS scripting
- `admin/consent-management-marketing` — Use when SSJS is being used to read or write subscription/preference data; consent rules affect which DE fields are writable
