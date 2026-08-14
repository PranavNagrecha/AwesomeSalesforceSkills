# Gotchas — OmniStudio Performance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: DataRaptor Cache Is Not Shared Across OmniScript Instances

**What happens:** When a user opens the same OmniScript a second time (a new browser tab, a new LWC component mount, or after a full page reload), the DataRaptor cache starts cold. There is no cross-instance or cross-session cache warming. Each new OmniScript instance pays the full first-call cost regardless of how many times a prior instance has fetched the same data.

**When it occurs:** Any time a user or test harness opens a fresh OmniScript instance. This is especially visible in high-traffic call center flows where agents open the same OmniScript repeatedly throughout the day and teams incorrectly assume the cache reduces load across sessions.

**How to avoid:** Design for first-call latency being the baseline. Use caching to improve revisit behavior within a single session. Do not model expected performance on the cache-warm case unless you have a specific warm-up strategy. If first-call latency is the primary problem, the fix is Integration Procedure consolidation, not caching.

---

## Gotcha 2: Async IP Responses Are Silently Ignored, Not Surfaced As Errors

**What happens:** When an Integration Procedure is invoked asynchronously, any errors that occur inside the IP (Apex exception, callout failure, DML error) do not surface to the OmniScript or the user. The OmniScript continues normally. The IP failure is visible only in debug logs or a custom error-handling mechanism built into the IP itself.

**When it occurs:** Any time an async IP encounters a failure condition — external API downtime, SOQL errors inside the IP, or Apex limits being hit by the background job. Teams often discover this in production when compliance logs or activity records go missing with no user-facing symptoms.

**How to avoid:** Async IPs must include explicit error handling. Use a Platform Event element inside the IP to emit a failure event that a monitoring subscriber picks up, or write a custom error log record inside a dedicated error-handling branch. Never use async execution for operations where silent failure is unacceptable (financial writes, compliance requirements). Test async IPs with intentional failure injection before going live.

---

## Gotcha 3: FlexCard Conditional Visibility Does Not Suppress The Data Source Call

**What happens:** A FlexCard has a visibility condition that hides the card when a certain field is empty or a flag is false. The data source (DataRaptor or Integration Procedure) that feeds the card still fires before the condition is evaluated, consuming a network round trip and server resources even when the card will never render.

**When it occurs:** Any time FlexCard conditional visibility is used as a performance optimization to skip unnecessary data fetches. Teams design a card, realize it should only appear in certain cases, add a visibility condition, and assume the data source is now conditionally skipped. It is not — visibility controls rendering, not data fetch.

**How to avoid:** Move the condition logic upstream. Either pass a flag to the parent Integration Procedure and return an empty data set when the card should not render, or structure the parent card using a Repeat element over an empty array when the condition is false, which prevents child card instantiation entirely. For FlexCards that appear in lists, the most reliable approach is to filter at the data source level rather than relying on card-level visibility.

---

## Gotcha 4: Integration Procedure Timeout Limit Is Fixed And Cannot Be Extended Per-Call

**What happens:** Integration Procedures run inside Salesforce Apex and are subject to the platform's standard governor limits. External callouts from an IP have a maximum timeout of 120 seconds per callout, but the overall Apex CPU time limit still applies to the entire IP execution. A complex IP with many elements hitting the CPU limit fails with a governor exception, not a graceful timeout.

**When it occurs:** Large IPs with many DataRaptor calls, complex looping elements, or sequential external callouts that individually stay under the callout timeout but collectively push CPU or heap limits. This surfaces in high-data-volume orgs where DataRaptor queries return large result sets.

**How to avoid:** Profile IPs in a scratch org or sandbox with production-representative data volumes before going live. Use the OmniStudio debug mode to measure element execution times. For IPs approaching limit pressure, split them into smaller IPs called in sequence, or move heavy data processing into a dedicated Apex action that is more efficient than the DataRaptor element chain for bulk data operations.

---

## Gotcha 5: Lazy Loading Does Not Pre-Fetch; Step Data Loads On Navigation

**What happens:** Enabling lazy loading on a step defers the step's data fetch until the user actually navigates to that step. The latency is not eliminated — it is moved from initial load time to the moment the user arrives at the step. If the deferred step has a slow uncached DataRaptor or Integration Procedure, the user experiences the full latency as a delay when they click Next into that step.

**When it occurs:** OmniScripts that use lazy loading as a blanket optimization without addressing the per-step data performance. Users see a fast initial load but then encounter step-level waits that feel arbitrary and inconsistent.

**How to avoid:** Apply lazy loading and per-step data consolidation together. Lazy loading is most effective when the deferred steps themselves are fast (cached DataRaptors, bundled IP calls). Profile each lazy-loaded step individually to confirm the step-entry latency is acceptable before releasing. The goal is to spread fast calls across navigation events, not to defer slow calls until the user notices them.

---

## Gotcha 6: Preview Bypasses The Cache By Default, So Designer Testing Never Proves Caching Works

**What happens:** Top-level Integration Procedure caching — a different mechanism from the DataRaptor session cache in Gotcha 1 — is configured in Procedure Configuration with "Salesforce Platform Cache Type" and "Time To Live In Minutes". But in the Preview tab, the Options JSON setting `ignoreCache` defaults to `true` — it "Doesn't clear or save data to the cache" — and `resetCache` defaults to `false`. A default preview run therefore never saves to the cache, and the runtime returns `vlcCacheEnabled` set to false because `ignoreCache` disabled caching for that run. Timing two preview runs proves nothing about the cache.

**When it occurs:** Any time caching is validated in the designer rather than in the consuming OmniScript or FlexCard. It also hides a second behavior: "If an Integration Procedure that has top-level caching enabled fails, its data isn't cached." An IP that intermittently fails looks like a permanent cache miss with no error surfaced in the timing.

**How to avoid:** Set `ignoreCache` to false in the Preview Options JSON (and `resetCache` to true when you want to force a save), then assert on the JSON nodes the runtime adds to the response root rather than on elapsed time: `vlcCacheKey` (the key data was stored under), `vlcCacheResult` (true when the response came from cache), `vlcCacheEnabled`, and `vlcCacheException` (caching errors). Between test runs, clear state with `ConnectApi.OmniDesignerConnect.ClearIntegrationProcedureCache(input)` (Summer '25 and later) instead of waiting out the TTL. `input` is a `ConnectApi.IntegrationProcedureCacheInputRepresentation` whose `cacheStorageType` is `ConnectApi.CacheStorageType.Session`, `.Org`, or `.All` — the method takes that input representation, not a bare enum.

---

## Gotcha 7: "Calculation Matrix: Not Found" On Export Is Expected And Safe To Ignore

**What happens:** Exporting an Integration Procedure that calls a Decision Matrix Action emits a `Calculation Matrix: Not Found` error. The export is not broken and the matrix is not missing. Salesforce documents the message explicitly: "You can ignore a Calculation Matrix: Not Found error when exporting an Integration Procedure that calls a Decision Matrix."

**When it occurs:** DataPack export or migration of any IP containing a Decision Matrix Action — the action configured with "Input Parameters: Data Source" (the IP data JSON node holding the value), "Input Parameters: Filter Value" (the matching Decision Matrix input parameter), and "Decision Matrix Name" (shown as "Matrix Name" in the managed package designer).

**How to avoid:** Do not spend a deployment cycle re-importing or reactivating the matrix in response to this message. Treat the export as successful and verify resolution at runtime instead: set a Default Matrix Result on the action so a null return surfaces as a known value, and use the `executionDateTime` Remote Option to pin the matrix Effective Date when testing dated rate tables. If the action returns the default at runtime, the matrix genuinely is not resolving — that, not the export message, is the real signal.
