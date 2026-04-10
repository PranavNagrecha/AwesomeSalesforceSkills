---
name: cpq-performance-optimization
description: "Use when diagnosing or resolving slow CPQ quote calculation, QLEx timeouts, or governor limit errors on large quotes. Trigger keywords: Large Quote Mode, QCP field declaration, quote calculation performance, SBQQ calculation timeout, async pricing. NOT for generic Apex performance tuning, CPQ pricing rule logic design, or billing engine performance."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "quote calculation is timing out or hitting governor limits when there are more than 150 lines"
  - "the Quote Line Editor is hanging or freezing when sales reps add products to large deals"
  - "QCP JavaScript plugin is running slowly or causing null field errors on quote save"
  - "how do I enable Large Quote Mode and what changes when I turn it on"
  - "my CPQ quote calculator plugin exceeds the 131072 character limit in SBQQ_Code__c"
tags:
  - cpq
  - cpq-performance
  - large-quote-mode
  - qcp
  - quote-calculation
  - sbqq
  - governor-limits
inputs:
  - "Approximate quote line count (or range) for typical deals"
  - "Whether a Quote Calculator Plugin (QCP) is in use, and its current field declaration list"
  - "Current CPQ package settings (Large Quote Mode threshold, calculation timeout)"
  - "Whether Calculate Quote API is being used in batch or async flows"
  - "Static resource usage status for the QCP code"
outputs:
  - "Recommendation on whether and how to enable Large Quote Mode"
  - "Corrected QCP field declaration list (declared fields pruned to exactly what is read/written)"
  - "Architecture decision on static resource vs inline SBQQ__Code__c for large plugins"
  - "Checklist for validating performance after changes"
  - "UX communication plan for reps when async calculation mode is activated"
dependencies:
  - data/cpq-data-model
  - apex/cpq-api-and-automation
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# CPQ Performance Optimization

This skill activates when a Salesforce CPQ implementation is experiencing slow or failing quote calculations, QLEx timeouts, or governor limit errors at scale. It covers the primary platform levers — Large Quote Mode, QCP field declaration discipline, and static resource architecture for large plugins — and explains the exact trade-offs each choice forces.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Line count:** What is the typical and maximum quote line count for deals in this org? The synchronous CPQ calculation engine starts to produce governor pressure around 200–300 lines. Large Quote Mode is the primary lever past that threshold.
- **QCP field declarations:** Does the org use a Quote Calculator Plugin? If yes, pull the current `fieldsToCalculate` and `lineFieldsToCalculate` arrays. Undeclared fields cause silent null reads; overdeclared fields inflate the JSON payload sent to the calculation engine.
- **SBQQ__Code__c size:** Is the QCP code currently stored inline in `SBQQ__Code__c`? That field is hard-capped at 131,072 characters. Large plugins must use a Static Resource loaded via `eval()`.
- **Large Quote Mode status:** Check CPQ Package Settings > Large Quote Mode and the threshold value (default 100 lines). Confirm whether `SBQQ__LargeQuote__c` on the Account record is also in use — the mode can be toggled at the account level independently of the package setting.
- **Calculate Quote API usage:** If the org uses the `SBQQ.ServiceRouter` calculate API in Apex batch jobs, understand that it runs at async speed — it does not bypass governor limits and is not a substitute for Large Quote Mode on large quotes.

---

## Core Concepts

### Large Quote Mode

Large Quote Mode shifts quote calculation from a synchronous in-browser model to an asynchronous server-side model. When enabled and the quote line count exceeds the configured threshold, the CPQ engine queues a server-side calculation job and returns control to the user immediately. The QLE displays a "calculating" status indicator; reps cannot save or submit the quote until calculation completes.

This is a UX-breaking change. Reps accustomed to immediate recalculation will see a delay and a status indicator they have not seen before. Enablement without user communication causes support tickets. The threshold must be tuned: too low and reps are interrupted on medium quotes; too high and large quotes still hit governor limits.

Large Quote Mode is controlled at two levels: (1) the CPQ Package Settings field "Large Quote Mode" with a line count threshold, and (2) the `SBQQ__LargeQuote__c` checkbox on the Account record, which forces async mode for all quotes on that account regardless of line count. Both controls must be considered.

### QCP Field Declaration

A Quote Calculator Plugin must declare every field it intends to read or write in two arrays: `fieldsToCalculate` (quote header fields) and `lineFieldsToCalculate` (quote line fields). CPQ uses these declarations to build the JSON payload sent to the plugin; fields not declared are excluded from the payload entirely.

Two failure modes exist:
- **Underdeclaring:** The plugin reads a field that is not declared. The field value is `null` in the payload. The plugin operates on null silently — no error is thrown, pricing logic produces wrong results, and the bug is hard to diagnose.
- **Overdeclaring:** Fields are declared "just in case." Each additional field increases JSON payload size, calculation API call size, and round-trip time. On 200+ line quotes the overhead compounds.

The correct discipline is to declare exactly the fields the plugin reads or writes — no more, no less. This requires auditing the plugin code against the declaration arrays.

### SBQQ__Code__c Size Limit and Static Resource Architecture

The `SBQQ__Code__c` field on the `SBQQ__CustomScript__c` object stores QCP JavaScript inline. The field is a Long Text Area capped at 131,072 characters. Modern QCPs that include helper functions, pricing tables, or complex bundle logic routinely exceed this limit.

The correct architecture for large plugins is to store the JavaScript in a Static Resource and load it at runtime using `eval()`. The inline `SBQQ__Code__c` field holds only the bootstrap code that fetches and evaluates the static resource. This approach has no practical code-size limit (Static Resources support up to 5 MB per file) but requires the static resource to be deployed as part of every plugin release — a build and deployment discipline change that must be documented.

### Calculate Quote API Is Not a Performance Bypass

The `SBQQ.ServiceRouter` Calculate Quote API (`SBQQ.ServiceRouter.load('SBQQ.QuoteAPI.Calculate', ...)`) runs quote calculation programmatically. It is commonly mistaken for a high-performance batch path. It is not — it runs at the same async speed as the UI path and is subject to the same governor limits on large quotes. Enabling Large Quote Mode affects both the UI and the API paths. The API is useful for automation and integration, not for circumventing calculation limits.

---

## Common Patterns

### Pattern 1: Enabling Large Quote Mode With UX Coordination

**When to use:** Quote line counts frequently exceed 150–200 lines, causing QLEx timeouts or governor limit errors during calculation.

**How it works:**
1. Navigate to CPQ Package Settings > Large Quote Options.
2. Set "Large Quote Mode" to Enabled.
3. Set the threshold to the line count above which async mode should activate (start with 150 if unsure; tune based on governor error frequency).
4. Optionally enable `SBQQ__LargeQuote__c` on specific accounts where all quotes should be async regardless of line count.
5. Update the QLE save button label or add a custom notification to inform reps that calculation is running asynchronously.
6. Add a process to monitor Apex jobs for failed calculation queue entries.

**Why not the alternative:** Leaving synchronous mode in place and trying to optimize Apex limits on the calculation path (adding custom indexes, trimming price rules) provides incremental gains but cannot overcome the fundamental CPU and SOQL limits that fire at scale.

### Pattern 2: Auditing and Correcting QCP Field Declarations

**When to use:** QCP is returning unexpected null values for fields, or calculation is slower than expected on mid-size quotes (50–150 lines).

**How it works:**
1. Extract the current `fieldsToCalculate` and `lineFieldsToCalculate` arrays from the QCP source.
2. Search the plugin code for every field API name referenced in `record.*` or `quoteModel.*` expressions.
3. Build a new declaration list containing exactly those fields.
4. Compare old list vs new list: remove any field not referenced; add any field referenced but missing.
5. Deploy the updated plugin to a sandbox and validate with a representative large quote that all pricing logic produces correct results.
6. Monitor calculation time on a set of test quotes before and after to confirm payload reduction.

**Why not the alternative:** Declaring all fields "to be safe" is a common shortcut that degrades performance at scale and masks logic bugs where the plugin accidentally depends on fields that should not be in scope.

### Pattern 3: Migrating QCP Code to Static Resource

**When to use:** `SBQQ__Code__c` is approaching or has exceeded 131,072 characters, or deployment of plugin updates is failing due to field size limits.

**How it works:**
1. Extract the full plugin JavaScript into a new Static Resource (e.g., `QuoteCalculatorPlugin.js`).
2. In `SBQQ__Code__c`, retain only the bootstrap loader:
   ```javascript
   // Bootstrap: load QCP from Static Resource
   var resourceUrl = '/resource/QuoteCalculatorPlugin';
   var xhr = new XMLHttpRequest();
   xhr.open('GET', resourceUrl, false);
   xhr.send(null);
   eval(xhr.responseText);
   ```
3. Include the Static Resource in every Salesforce DX package version and change set that includes a plugin update.
4. Document the deployment order: Static Resource must be deployed before or alongside the `SBQQ__CustomScript__c` record.
5. Validate in sandbox: open the QLE on a test quote and confirm the plugin loads correctly via browser console.

**Why not the alternative:** Splitting logic across multiple inline scripts or compressing code to stay under the character limit produces unmaintainable code and does not scale.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Quotes regularly exceed 200 lines with timeout errors | Enable Large Quote Mode at 150-line threshold | The synchronous engine cannot handle this scale; async is the only reliable path |
| QCP returns wrong prices silently on some fields | Audit and correct field declarations | Undeclared fields return null silently; no error surface |
| QCP code exceeds or approaches 131,072 chars | Migrate to Static Resource + eval() bootstrap | Hard field cap; static resource scales to 5 MB |
| Batch job re-prices all quotes nightly | Use Calculate Quote API with Large Quote Mode enabled | API is the correct programmatic path; Large Quote Mode still applies |
| Medium quotes (50-150 lines) calculate slowly | Audit field declarations and price rule count | Over-declared fields and excessive lookup price rules are the primary cause |
| Account always has large quotes regardless of line count | Set SBQQ__LargeQuote__c on Account | Account-level flag forces async for all quotes on that account |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Establish baseline:** Record current quote line counts, average calculation time, and frequency of governor errors. Identify the threshold at which errors begin. Pull CPQ Package Settings to confirm current Large Quote Mode status and threshold value.
2. **Audit QCP field declarations:** If a QCP is in use, compare declared fields against all field references in plugin code. Produce a corrected declaration list. Fix underdeclared fields immediately — they produce silent wrong prices.
3. **Assess SBQQ__Code__c size:** Check the current character count of `SBQQ__Code__c`. If it exceeds 100,000 characters, plan a migration to Static Resource architecture before the next plugin update.
4. **Enable Large Quote Mode if needed:** If quotes exceed 150 lines and governor errors are occurring, enable Large Quote Mode. Set the threshold conservatively and document the async UX change for end users and sales operations.
5. **Communicate UX change to reps:** Prepare user guidance describing the async calculation indicator, expected wait time, and that quotes cannot be saved during active calculation. Coordinate with the sales ops team before production enablement.
6. **Validate in sandbox:** Run a set of representative large quotes through the full calculation cycle. Confirm correct prices, no null field errors, and successful save. Check the Apex job queue for any failed calculation jobs.
7. **Monitor in production:** After enablement, monitor Apex job queue for calculation failures, track average calculation time, and confirm governor error frequency drops. Tune the Large Quote Mode threshold if necessary.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Large Quote Mode threshold is set and tuned to the actual quote volume distribution (not left at the default 100 without review)
- [ ] QCP field declarations match exactly the fields the plugin reads and writes — no over-declaration, no under-declaration
- [ ] SBQQ__Code__c character count is below 131,072; if approaching the limit, Static Resource migration is planned
- [ ] Sales reps and sales operations have been informed of async calculation UX change before production enablement
- [ ] Apex job queue monitoring is in place for failed calculation jobs
- [ ] Calculate Quote API usage in batch jobs is accounted for — Large Quote Mode affects the API path as well

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Large Quote Mode Is Not Quote-Level** — It is controlled by the CPQ Package Settings threshold and the `SBQQ__LargeQuote__c` Account field. There is no per-quote toggle. Turning it on affects all quotes above the threshold across the org.
2. **Undeclared QCP Fields Return Null, Not an Error** — If a field is missing from `fieldsToCalculate` or `lineFieldsToCalculate`, the plugin receives `null` for that field. No exception is thrown. Pricing logic silently computes wrong values. This is the most common source of subtle QCP bugs.
3. **Calculate Quote API Shares Governor Limits** — Using the `SBQQ.ServiceRouter` calculate API in an Apex batch job does not bypass CPQ calculation limits. It runs at the same speed and under the same governor constraints as the UI path.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Corrected QCP field declaration list | Pruned `fieldsToCalculate` and `lineFieldsToCalculate` arrays ready to deploy |
| Large Quote Mode configuration record | Recommended threshold value and Account-level flag decisions |
| Static Resource bootstrap loader | Minimal `SBQQ__Code__c` content for large plugin architecture |
| UX communication plan | End-user guidance for async calculation mode |

---

## Related Skills

- `data/cpq-data-model` — CPQ object model and field relationships; foundational for understanding which fields to declare in QCP
- `apex/cpq-api-and-automation` — ServiceRouter calculate API, async quote calculation patterns, and batch re-pricing
- `architect/cpq-architecture-patterns` — System-level CPQ architecture decisions including Large Quote Mode placement in the overall solution design
- `admin/cpq-pricing-rules` — Price rule volume and lookup query counts are a secondary performance factor after line count

---

## Official Sources Used

- Large Quote Performance Settings — https://help.salesforce.com/s/articleView?id=sf.cpq_large_quote.htm&type=5
- CPQ Quote Calculation Stages — https://help.salesforce.com/s/articleView?id=sf.cpq_calculation_stages.htm&type=5
- JavaScript Quote Calculator Plugin (QCP) — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_jsqcp_parent.htm
- Salesforce CPQ Developer Guide: Calculate Quote API — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_quote_calculator.htm
