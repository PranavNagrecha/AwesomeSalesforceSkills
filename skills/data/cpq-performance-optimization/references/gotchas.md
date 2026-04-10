# Gotchas — CPQ Performance Optimization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Undeclared QCP Fields Return Null Silently — No Error Is Thrown

**What happens:** A Quote Calculator Plugin reads a quote or quote line field that is not listed in `fieldsToCalculate` or `lineFieldsToCalculate`. The field value in the plugin is `null`. The plugin continues executing with null data — pricing logic silently falls through to defaults or produces wrong calculations. No exception is thrown, no warning is logged, and the quote saves successfully with incorrect prices.

**When it occurs:** Any time a developer adds a new field reference to plugin logic without updating the declaration arrays. Also occurs during initial plugin authorship when developers assume all fields are available by default. Especially common after field renames or API name changes — the old API name is removed from records but may still appear in the declaration array (now a no-op), while the new field is referenced in code but not declared.

**How to avoid:** Treat the declaration arrays as a contract: for every `record['Field_API_Name__c']` expression in the plugin code, verify the field appears in the appropriate declaration array. Perform this audit as part of every plugin code review. A simple grep for `record\['[A-Za-z_]+'\]` against the declaration array list will surface gaps. After any change, test with a quote that has known values in all referenced fields and confirm the plugin produces expected output.

---

## Gotcha 2: Large Quote Mode Changes UX Without Warning — Reps See an Async Indicator They Have Never Seen Before

**What happens:** When Large Quote Mode is enabled and a quote exceeds the threshold, the QLE no longer immediately reflects price recalculation. Instead, a "calculating" spinner or status indicator appears and the Save button is disabled until the async job completes. Reps who expect immediate feedback interpret this as the page having frozen and refresh — losing unsaved line edits.

**When it occurs:** Immediately after Large Quote Mode is enabled in production, on the next large quote any rep opens. There is no grace period or warning in the UI. The first time a rep sees the async indicator is typically mid-deal.

**How to avoid:** Communicate the change to all sales reps and sales operations before enabling in production. Provide a one-page reference showing what the async indicator looks like and what to do (wait, do not refresh). Enable in a sandbox first and walk a representative group of reps through a test quote. Consider a phased rollout: enable on one team or account segment first.

---

## Gotcha 3: SBQQ__Code__c Is Hard-Capped at 131,072 Characters — There Is No Setting to Increase This

**What happens:** When a QCP developer tries to save `SBQQ__Code__c` content that exceeds 131,072 characters, Salesforce throws a field validation error and rejects the save. No partial save occurs. The update fails entirely.

**When it occurs:** Incrementally as the plugin grows over time. Common in orgs where QCP started small and accreted logic over 18–24 months. The limit hits suddenly — one new function or pricing table pushes the file over the edge.

**How to avoid:** Monitor `SBQQ__Code__c` character count during development. At 100,000 characters, plan the Static Resource migration before the next feature addition. Do not attempt to work around the limit by minifying JavaScript inline — minification buys temporary relief but does not scale and produces unmaintainable code. Migrate to the Static Resource + `eval()` bootstrap pattern as described in SKILL.md.

---

## Gotcha 4: Calculate Quote API Is Subject to the Same Governor Limits as the UI — It Is Not a High-Performance Batch Path

**What happens:** A developer routes large-quote repricing through `SBQQ.ServiceRouter.load('SBQQ.QuoteAPI.Calculate', ...)` in an Apex batch job, expecting that background processing provides more headroom. Large quotes still fail with limit errors because the Calculate Quote API invokes the same CPQ pricing engine under the same governor context.

**When it occurs:** When teams try to build nightly repricing jobs or integration-triggered recalculation without enabling Large Quote Mode. The API is described in documentation as "async" relative to the UI trigger point, but it does not grant additional governor budget per transaction.

**How to avoid:** Enable Large Quote Mode in CPQ Package Settings. This affects both the UI and the API calculation paths. For batch jobs, process one quote per Apex batch execute method to avoid compounding governor usage. Do not assume the API is a performance bypass — it is a programmatic trigger for the same calculation engine.

---

## Gotcha 5: Large Quote Mode Is Org-Wide Past the Threshold — It Cannot Be Scoped to Specific Users or Quote Record Types

**What happens:** Large Quote Mode activates for every quote in the org that exceeds the configured line count threshold, regardless of who owns it, which record type it uses, or which sales process created it. There is no per-user or per-record-type opt-out.

**When it occurs:** When an org has mixed quote sizes — some business units regularly use 200+ line quotes while others use 10-line quotes — and the threshold is set to accommodate the large-quote teams. Reps on the small-quote side may still experience the async indicator on quotes that coincidentally grow past the threshold (e.g., during bundle expansion).

**How to avoid:** Set the threshold conservatively above the point where governor errors actually occur, not at the lowest convenient number. Use the `SBQQ__LargeQuote__c` Account field to force async mode on specific high-volume accounts rather than setting a very low global threshold. Communicate to all users regardless of team — the UX change can surprise anyone whose quote grows unexpectedly.
