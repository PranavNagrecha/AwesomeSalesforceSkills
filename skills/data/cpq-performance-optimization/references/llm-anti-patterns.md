# LLM Anti-Patterns — CPQ Performance Optimization

Common mistakes AI coding assistants make when generating or advising on CPQ performance optimization. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Enabling Large Quote Mode Without Mentioning the UX Change

**What the LLM generates:** Instructions to enable Large Quote Mode in CPQ Package Settings with no mention of the async calculation UX change for sales reps, as if it is a transparent background improvement.

**Why it happens:** LLMs treat performance settings as infrastructure concerns and omit end-user impact. Training data on Large Quote Mode skews toward technical configuration steps; change management content is underrepresented.

**Correct pattern:**

```text
Before enabling Large Quote Mode in production:
1. Notify sales reps and sales ops that quotes above [threshold] lines will now
   show an async "calculating" indicator. Reps must wait for calculation to complete
   before saving — do NOT refresh the page.
2. Schedule a walkthrough with affected teams on a sandbox quote.
3. Enable in production during a low-activity window.
4. Monitor the Apex job queue for failed calculation jobs for 48 hours post-enablement.
```

**Detection hint:** Any response that says "enable Large Quote Mode" without the words "UX", "async indicator", "communication", or "change management" is missing critical context.

---

## Anti-Pattern 2: Declaring All Fields in QCP "for Completeness"

**What the LLM generates:** A `fieldsToCalculate` or `lineFieldsToCalculate` array that includes every standard CPQ field plus every custom field "just in case they're needed later." The LLM may describe this as "comprehensive" or "future-proof."

**Why it happens:** LLMs default to permissive field lists when unsure of the exact requirement. They model this as "more is safer" — a reasonable heuristic outside CPQ that inverts in this context.

**Correct pattern:**

```javascript
// WRONG — over-declared, inflates payload
export function lineFieldsToCalculate() {
  return [
    'SBQQ__ListPrice__c', 'SBQQ__NetPrice__c', 'SBQQ__Discount__c',
    'SBQQ__Quantity__c', 'SBQQ__StartDate__c', 'SBQQ__EndDate__c',
    'SBQQ__Description__c', 'SBQQ__ProductCode__c', // not used in this plugin
    'Custom_Field_1__c', 'Custom_Field_2__c'         // not used in this plugin
  ];
}

// CORRECT — declare only what this plugin reads or writes
export function lineFieldsToCalculate() {
  return [
    'SBQQ__ListPrice__c', 'SBQQ__NetPrice__c', 'SBQQ__Discount__c',
    'Custom_Field_1__c'  // only field actually referenced in plugin logic
  ];
}
```

**Detection hint:** Field declaration arrays longer than 10–15 entries without an explicit comment explaining each entry are a candidate for over-declaration audit. Any array that includes description or product code fields without a clear plugin reference is suspect.

---

## Anti-Pattern 3: Treating Calculate Quote API as a High-Performance Batch Path

**What the LLM generates:** Code that routes all quote repricing through `SBQQ.ServiceRouter.load('SBQQ.QuoteAPI.Calculate', ...)` in an Apex batch job, described as "bypassing the QLE calculation limits" or "using the server-side calculation path for better performance."

**Why it happens:** The term "async" is used in CPQ documentation to describe the API's non-blocking invocation pattern relative to the UI. LLMs interpret "async" as implying higher or separate governor limits — a reasonable inference that is wrong in this context.

**Correct pattern:**

```text
The Calculate Quote API invokes the same CPQ pricing engine as the UI path.
It is subject to the same governor limits. Large Quote Mode must be enabled
in CPQ Package Settings for large quotes to calculate reliably whether triggered
from the UI or the API. The API is the correct programmatic trigger; Large Quote
Mode is the correct performance lever. Both are required together.
```

**Detection hint:** Any response that describes the Calculate Quote API as a "performance bypass," "server-side alternative," or "batch-safe path" without mentioning that Large Quote Mode is still required is incorrect.

---

## Anti-Pattern 4: Suggesting Per-Quote Large Quote Mode Toggle in Code

**What the LLM generates:** Apex or Flow code that sets a field or calls a method to "enable Large Quote Mode for this specific quote" when line count exceeds a threshold — implying that the mode can be dynamically toggled per quote at calculation time.

**Why it happens:** LLMs generalize from patterns in other Salesforce contexts where behavior can be controlled per-record (e.g., Apex triggers checking record type, flows using decision elements). They apply this mental model to CPQ without knowing that Large Quote Mode is a package-level setting, not a per-quote flag.

**Correct pattern:**

```text
Large Quote Mode is controlled by:
1. CPQ Package Settings > Large Quote Mode threshold (org-wide)
2. SBQQ__LargeQuote__c checkbox on the Account record (account-wide)

There is no per-quote or per-transaction toggle. If dynamic control is needed,
use the Account-level field to target specific high-volume accounts. There is no
Apex API to switch calculation mode per quote.
```

**Detection hint:** Any code that attempts to set a Large Quote Mode field on a Quote record, or calls a CPQ method with a "largeQuote" parameter at quote-create or quote-save time, is based on a false premise.

---

## Anti-Pattern 5: Recommending JavaScript Minification as a Solution to the SBQQ__Code__c Size Limit

**What the LLM generates:** Instructions to minify the QCP JavaScript using a tool like UglifyJS or Terser to stay under the 131,072-character limit in `SBQQ__Code__c`, presented as a complete solution.

**Why it happens:** Minification is a standard web performance technique and LLMs reach for it as the obvious solution to a "code is too large" problem. It is technically feasible short-term but is the wrong architectural answer for this constraint.

**Correct pattern:**

```text
Minification buys temporary relief and produces unmaintainable code. The correct
solution for QCP plugins approaching or exceeding 131,072 characters is the Static
Resource + eval() bootstrap architecture:

1. Extract full plugin JavaScript to a Static Resource.
2. Replace SBQQ__Code__c with only the bootstrap loader (~10 lines).
3. Deploy the Static Resource in every change set that updates the plugin.

This removes the practical size ceiling (Static Resources support up to 5 MB),
preserves readable source code, and enables standard JavaScript tooling.
```

**Detection hint:** Any response to a "QCP too large" problem that mentions minification, compression, or "splitting into multiple scripts" without recommending the Static Resource architecture is providing an incomplete or incorrect solution.

---

## Anti-Pattern 6: Missing the SBQQ__LargeQuote__c Account Field When Documenting Large Quote Mode

**What the LLM generates:** Documentation or configuration steps for Large Quote Mode that only describe the CPQ Package Settings threshold, omitting the `SBQQ__LargeQuote__c` checkbox on the Account record that provides account-level override control.

**Why it happens:** The Package Settings threshold is prominently documented; the Account-level field is described in a separate help article and is less frequently cited in training data. LLMs produce incomplete Large Quote Mode documentation as a result.

**Correct pattern:**

```text
Large Quote Mode has two control points:
1. CPQ Package Settings > Large Quote Mode threshold: applies to all quotes in the org
   that exceed the specified line count.
2. Account.SBQQ__LargeQuote__c: when checked on an Account, forces async calculation
   for ALL quotes on that account regardless of line count.

Both should be documented in any Large Quote Mode implementation guide.
```

**Detection hint:** Large Quote Mode documentation that does not mention `SBQQ__LargeQuote__c` on Account is incomplete.
