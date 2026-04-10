# SSJS Server-Side JavaScript — Work Template

Use this template when authoring, debugging, or reviewing SSJS code in Salesforce Marketing Cloud.

## Scope

**Skill:** `ssjs-server-side-javascript`

**Request summary:** (fill in what the practitioner asked for)

**Execution context:** [ ] Script Activity  [ ] Cloud Page  [ ] Landing Page

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **API target:** (WSProxy for MC SOAP objects / Script.Util.HttpRequest for external REST / both)
- **Data Extension(s) involved:** (name and external key)
- **Estimated row volume:** (needed to assess 30-min timeout risk)
- **Error message or failure mode observed:** (paste Activity log output or browser error)
- **AMPscript in same file?:** [ ] Yes — AMPscript declared before SSJS  [ ] No

---

## Approach

Which pattern from SKILL.md applies?

- [ ] WSProxy retrieve with pagination
- [ ] WSProxy upsertBatch to Data Extension
- [ ] Outbound REST call via Script.Util.HttpRequest
- [ ] Mixed SSJS/AMPscript content block
- [ ] Other: _______________

---

## SSJS Code Block

```javascript
<script runat="server">
Platform.Load("Core", "1.1.1");
try {

  // === YOUR IMPLEMENTATION HERE ===

  // WSProxy pattern (for MC SOAP API calls):
  // var prox = new Script.Util.WSProxy();
  // var cols = ["FieldA", "FieldB"];
  // var filter = { Property: "FieldA", SimpleOperator: "equals", Value: "SomeValue" };
  // var result = prox.retrieve("DataExtensionObject", cols, filter);
  // var rows = [];
  // while (result && result.Results && result.Results.length > 0) {
  //   for (var i = 0; i < result.Results.length; i++) { rows.push(result.Results[i]); }
  //   if (result.HasMoreRows) { result = prox.getNextPage(); } else { break; }
  // }
  // Write("Rows retrieved: " + rows.length);

  // HTTP pattern (for external REST API calls):
  // var req = new Script.Util.HttpRequest("https://api.example.com/endpoint");
  // req.emptyContentHandling = 0;
  // req.retryCount = 1;
  // req.setHeader("Authorization", "Bearer " + token);
  // req.setHeader("Content-Type", "application/json");
  // req.method = "POST";
  // req.postData = Stringify({ key: "value" });
  // var resp = req.send();
  // if (resp.statusCode != 200) { throw new Error("HTTP " + resp.statusCode + ": " + resp.content); }
  // var data = Platform.Function.ParseJSON(resp.content);

} catch(e) {
  Write("ERROR: " + e.message);
}
</script>
```

---

## Pre-Deploy Checklist

Run through these before saving to Automation Studio or Cloud Pages:

- [ ] All code is inside `<script runat="server">` tags
- [ ] `Platform.Load("Core", "1.1.1")` is the first line inside the script tag
- [ ] No `let`, `const`, arrow functions (`=>`), template literals (`` ` ``), or `async`/`await`
- [ ] No `JSON.stringify()` or `JSON.parse()` — using `Stringify()` and `Platform.Function.ParseJSON()` instead
- [ ] All API calls and WSProxy operations are inside `try/catch` with `Write(e.message)` in catch
- [ ] WSProxy `retrieve()` has a `HasMoreRows` pagination loop (or retrieve is bounded to single-record lookups)
- [ ] `resp.statusCode` is checked before consuming `resp.content` in any HttpRequest call
- [ ] No API tokens or passwords hardcoded — retrieved from an encrypted Data Extension field at runtime
- [ ] Estimated execution time is well under 30 minutes for expected data volume

---

## Estimated Row Volume and Timeout Risk

| Operation | Est. Rows | Est. Time/Row | Est. Total Time | Risk |
|---|---|---|---|---|
| (describe operation) | ___ | ___ ms | ___ min | Low / Medium / High |

If any operation is in the Medium or High risk band, document the mitigation:
(e.g., split into multiple Activities, use SQL Query Activity for data reduction first)

---

## Notes

Record any deviations from the standard SSJS patterns and the reason:

- 
