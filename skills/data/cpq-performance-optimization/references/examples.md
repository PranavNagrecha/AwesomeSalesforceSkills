# Examples — CPQ Performance Optimization

## Example 1: Enabling Large Quote Mode for a High-Volume Deals Org

**Context:** A manufacturing company uses CPQ for complex equipment bundles. Top deals have 250–400 quote lines. Sales reps report that the Quote Line Editor hangs for 30–60 seconds on large opportunities and occasionally displays a "Calculation timed out" error requiring a page refresh.

**Problem:** The CPQ synchronous calculation engine hits CPU and SOQL governor limits at this line count. The QLE waits for calculation to complete before allowing the rep to save, and the timeout fires before results return. Reps lose unsaved work and re-enter changes, compounding the problem.

**Solution:**

1. Navigate to Setup > Installed Packages > Salesforce CPQ > Configure > Pricing and Calculation tab.
2. Set "Large Quote Mode" to Enabled.
3. Set the threshold to 150 lines (start conservative — tune down if 150-line quotes still error).
4. For named accounts with consistently large quotes, check `SBQQ__LargeQuote__c` on those Account records to force async mode regardless of line count.
5. Communicate the change to sales reps: quotes above 150 lines will show an async calculation indicator; reps should wait for "Calculation complete" before saving.

```text
CPQ Package Settings > Pricing and Calculation:
  Large Quote Mode: Enabled
  Large Quote Line Count: 150

Account record:
  SBQQ__LargeQuote__c: true  (for accounts where all quotes are large)
```

**Why it matters:** The synchronous engine cannot be tuned past governor ceilings — there is no Apex optimization that adds CPU time. Large Quote Mode moves calculation server-side, removing the browser timeout and releasing the rep immediately. The trade-off is an async UX that reps must be prepared for. Enabling without communication is the most common deployment failure mode.

---

## Example 2: Fixing Silent Null Errors from Undeclared QCP Fields

**Context:** A QCP applies a custom discount tier based on `SBQQ__Quote__c.Custom_Tier__c` (a custom field on the Quote header). The field has values in data, but the plugin is always pricing at the default tier — as if the field is blank.

**Problem:** `Custom_Tier__c` is not in the plugin's `fieldsToCalculate` array. CPQ excludes undeclared fields from the JSON payload. The plugin receives `null` for `Custom_Tier__c` and falls through to the default tier silently.

**Solution:**

Before (broken — field not declared):
```javascript
// QCP fieldsToCalculate — missing Custom_Tier__c
export function fieldsToCalculate() {
  return ['SBQQ__StartDate__c', 'SBQQ__EndDate__c'];
}

export function onBeforeCalculate(quoteModel, quoteLineModels, conn) {
  var tier = quoteModel.record['Custom_Tier__c']; // null — not in payload
  applyTierDiscount(quoteLineModels, tier || 'Standard'); // always 'Standard'
  return Promise.resolve();
}
```

After (correct — field declared):
```javascript
export function fieldsToCalculate() {
  return ['SBQQ__StartDate__c', 'SBQQ__EndDate__c', 'Custom_Tier__c'];
}

export function onBeforeCalculate(quoteModel, quoteLineModels, conn) {
  var tier = quoteModel.record['Custom_Tier__c']; // now populated correctly
  applyTierDiscount(quoteLineModels, tier || 'Standard');
  return Promise.resolve();
}
```

**Why it matters:** There is no runtime error when a field is missing from the declaration. The plugin runs to completion with wrong data. This class of bug is uniquely hard to diagnose because the field has valid data in Salesforce — it simply never reaches the plugin. The fix requires auditing every `record.*` and `quoteLineModel.record.*` reference in the plugin and ensuring each appears in the appropriate declaration array.

---

## Example 3: Migrating a Large QCP to Static Resource Architecture

**Context:** A QCP has grown over two years to include pricing helpers, product eligibility rules, and regional discount tables. The inline JavaScript in `SBQQ__Code__c` is 128,000 characters. Developers adding new pricing logic are receiving field-length validation errors on save. The next feature will push the file over the 131,072-character hard limit.

**Problem:** `SBQQ__Code__c` is a Long Text Area field capped at 131,072 characters. There is no setting to increase this limit. New logic cannot be added inline.

**Solution:**

Step 1 — Extract the full plugin JavaScript into a Static Resource named `QuoteCalculatorPlugin` (Content Type: `application/javascript`).

Step 2 — Replace `SBQQ__Code__c` content with the bootstrap loader only:

```javascript
// Bootstrap loader — fetches QCP logic from Static Resource
(function () {
  var resourceUrl = '/resource/QuoteCalculatorPlugin';
  var xhr = new XMLHttpRequest();
  xhr.open('GET', resourceUrl, false); // synchronous is required here
  xhr.send(null);
  if (xhr.status === 200) {
    eval(xhr.responseText); // eslint-disable-line no-eval
  } else {
    throw new Error('QCP static resource failed to load: ' + xhr.status);
  }
})();
```

Step 3 — Add the Static Resource to the Salesforce DX package or change set alongside any plugin update. Deployment order: Static Resource must be present before `SBQQ__CustomScript__c` changes are applied.

Step 4 — Validate in sandbox: open a quote in the QLE and check the browser console for any resource load errors.

**Why it matters:** Static Resources support up to 5 MB per file — effectively unlimited for plugin code. This architecture also enables standard JavaScript tooling (linters, minifiers, unit test frameworks) on the plugin source, improving maintainability significantly.

---

## Anti-Pattern: Using Calculate Quote API as a Performance Bypass

**What practitioners do:** To avoid QLEx timeouts on large quotes, a developer routes all calculation through a nightly Apex batch job using `SBQQ.ServiceRouter.load('SBQQ.QuoteAPI.Calculate', ...)`, reasoning that background jobs have higher limits than the UI path.

**What goes wrong:** The Calculate Quote API runs at async speed — it uses the same CPQ pricing engine and is subject to the same governor constraints. It does not provide a larger CPU or SOQL governor budget than the synchronous UI path. Large quotes that timeout in the UI will also fail in the batch API. Additionally, Large Quote Mode must still be enabled for the API path to handle large quotes correctly.

**Correct approach:** Enable Large Quote Mode in CPQ Package Settings. The API path respects this setting. For batch re-pricing, use the API in conjunction with Large Quote Mode and design the batch to process one quote per transaction to avoid compounding governor usage across lines.
