---
name: omnistudio-performance
description: "Use when diagnosing or improving runtime performance in OmniStudio assets: slow OmniScripts, Integration Procedures with high latency, DataRaptor caching, excessive API call counts, FlexCard rendering delays, or async IP fire-and-forget patterns. Triggers: 'OmniScript slow', 'Integration Procedure timeout', 'DataRaptor cache', 'FlexCard loading too long', 'reduce API calls OmniStudio'. NOT for LWC performance outside of OmniScript runtime (use lwc-performance skill). NOT for OmniScript step design or journey UX (use omniscript-design-patterns skill)."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
  - Reliability
triggers:
  - "OmniScript is loading slowly and users are waiting a long time on step transitions"
  - "Integration Procedure is timing out or taking more than a few seconds to respond"
  - "how do I cache DataRaptor results to avoid repeated Salesforce queries"
  - "FlexCard is slow to render when there are many cards or complex data sources"
  - "we are hitting API limits because OmniStudio makes too many calls per transaction"
  - "can I run an Integration Procedure asynchronously without blocking the user"
tags:
  - omnistudio-performance
  - integration-procedures
  - dataraptor-caching
  - flexcard
  - lazy-loading
  - async-ip
inputs:
  - "OmniScript step count and which steps load remotely"
  - "Integration Procedure structure: number of elements, external callout usage, nested IPs"
  - "DataRaptor type and whether caching is configured"
  - "FlexCard data source type and number of rendered cards"
  - "current observed latency or timeout symptoms"
outputs:
  - "lazy loading configuration guidance for OmniScript steps"
  - "DataRaptor caching key recommendations"
  - "async Integration Procedure fire-and-forget design"
  - "DataRaptor consolidation or batching recommendations"
  - "FlexCard data source optimization guidance"
  - "LWC runtime versus Managed Package runtime performance comparison"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# OmniStudio Performance

Use this skill when OmniStudio assets are slow, hitting limits, or creating poor user experiences due to latency. Performance problems in OmniStudio fall into a small set of root causes: too many synchronous remote calls, DataRaptors that re-query on every load, FlexCards rendering against unoptimized data sources, and Integration Procedures that block the UI when they could run asynchronously. This skill identifies which root cause applies and maps it to the right fix.

---

## Before Starting

Gather this context before working on anything in this domain:

- Which asset type is slow: OmniScript, FlexCard, Integration Procedure, or DataRaptor?
- Is the latency per-step (step transitions) or on initial load?
- How many remote actions or DataRaptor calls fire during a single user flow?
- Is the OmniScript running in LWC Runtime (preferred) or the legacy Managed Package runtime?
- Is the Integration Procedure doing external callouts, or only Salesforce data operations?
- Is DataRaptor caching currently configured, and if so, what is the cache key?

---

## Core Concepts

### Synchronous Remote Calls Are The Most Common Root Cause

OmniScript steps that rely on Integration Procedures or remote DataRaptors fire synchronously by default. When a step has multiple elements each fetching data independently, those calls serialize. A step with five DataRaptor calls can take five times as long as one with a single consolidated call. Consolidating DataRaptors into a single Integration Procedure call that returns all needed data for a step is the primary fix.

### DataRaptor Caching Reduces Repeated Salesforce Queries

OmniStudio supports response caching for DataRaptor Extract and Turbo Extract assets. When caching is enabled, the result is stored for the duration of the OmniScript session and reused when the same cache key is matched again. Cache keys should be specific enough to avoid returning stale data but broad enough to get reuse. A cache key based on a stable record ID with no user-editable fields in it is the typical correct shape. Caching is not appropriate for DataRaptors that read data expected to change mid-session, such as a record the OmniScript is actively editing.

### LWC Runtime vs Managed Package Runtime

OmniStudio has two runtimes for OmniScripts: the LWC OmniScript runtime (the current supported path) and the legacy Managed Package runtime. The LWC runtime has a faster initial load profile because it defers non-critical rendering and integrates with Lightning's native caching. New implementations should use LWC runtime. Orgs still on the Managed Package runtime should plan migration because the performance gap widens as components are added.

### Async Integration Procedures Eliminate UI Blocking

Integration Procedures that perform write operations or external callouts do not always need to complete before the user continues. When the operation is fire-and-forget (audit logging, async enrichment, downstream notifications), the IP can be invoked asynchronously. The OmniScript continues and the IP runs in the background. This pattern requires the consuming OmniScript to not depend on the IP response to proceed.

### FlexCard Rendering Performance

FlexCards call data sources for every rendered card instance unless conditional rendering is used to suppress cards that are not visible. Nested FlexCards that each trigger independent data source calls multiply quickly. The fix is to move data aggregation into a single Integration Procedure or DataRaptor that returns all the data the card set needs, then pass it down from a parent card using state rather than separate fetches.

---

## Common Patterns

### Consolidate Per-Step DataRaptor Calls Into One Integration Procedure Call

**When to use:** An OmniScript step has multiple DataRaptor or remote elements that each fire independently.

**How it works:** Replace the individual DataRaptor elements with a single Integration Procedure Action element. The IP runs all the DataRaptor calls internally and returns a single combined response. The OmniScript waits on one network round trip instead of several.

**Why not the alternative:** Leaving individual DataRaptor calls in the step is simpler to configure but serializes all the latency. Each call adds its own round trip. At three or more calls per step the user wait time becomes noticeable on typical enterprise networks.

### DataRaptor Response Caching With Stable Cache Key

**When to use:** The same DataRaptor read fires on multiple steps, or the user is likely to revisit a step within the same session without the underlying data having changed.

**How it works:** Enable caching on the DataRaptor Extract or Turbo Extract asset. Set the cache key to a value that uniquely identifies the record being read (e.g., the record Id field from the OmniScript context). Set the cache duration appropriate for the session lifetime.

**Why not the alternative:** Without caching, every step transition that reaches a DataRaptor element re-queries Salesforce. In a long OmniScript with many back-forward navigation events, this adds up to many unnecessary SOQL queries and user-visible latency.

### Async Fire-And-Forget Integration Procedure

**When to use:** An Integration Procedure performs a side-effect operation (enrichment, logging, notification) that does not need to return a result to the OmniScript.

**How it works:** Set the Integration Procedure Action element's execution type to asynchronous. The OmniScript posts the request and immediately continues to the next step. The IP runs in a background Apex invocation. The OmniScript must not read from the IP response.

**Why not the alternative:** Synchronous IP execution for non-blocking operations forces the user to wait for server-side work they cannot observe and that does not change the UI state.

### Lazy Loading For Non-Critical OmniScript Steps

**When to use:** An OmniScript has many steps and the later steps are rarely reached by most users. Loading all step data upfront increases initial load time unnecessarily.

**How it works:** Configure lazy loading on OmniScript steps beyond the first few. Steps load their data only when the user navigates to them. This reduces the initial payload and spreads remote calls across navigation events.

**Why not the alternative:** Eager loading all steps upfront is simpler to reason about but front-loads all the latency onto the initial page load, which penalizes every user even those who abandon early.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Step takes too long due to multiple DataRaptor calls | Consolidate into one Integration Procedure call | Eliminates serial round trips |
| Same data queried repeatedly in one session | Enable DataRaptor response caching with stable key | Avoids redundant SOQL and network round trips |
| IP writes or notifies but result is not needed in UI | Use async fire-and-forget IP invocation | Removes blocking latency from the user path |
| OmniScript initial load is slow with many steps | Enable lazy loading on non-critical steps | Defers load cost to navigation events |
| FlexCard batch is slow with independent data calls | Move aggregation into parent IP, pass down state | Collapses N card fetches into one call |
| On legacy Managed Package runtime | Plan migration to LWC OmniScript runtime | LWC runtime has better caching and smaller load profile |
| External callout in IP blocks user navigation | Evaluate async execution or offline enrichment pattern | External call latency is non-deterministic |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Each OmniScript step fires at most one network round trip (all per-step data in one IP call).
- [ ] DataRaptor caching is enabled where the data does not change mid-session.
- [ ] Cache keys are specific enough to avoid cross-user or cross-record data reuse.
- [ ] Fire-and-forget Integration Procedures are invoked asynchronously and not read back.
- [ ] Lazy loading is enabled on OmniScript steps unlikely to be reached by most users.
- [ ] FlexCard data aggregation happens in the parent IP, not per-card source calls.
- [ ] The OmniScript is running in LWC runtime, not the legacy Managed Package runtime.
- [ ] External callout latency is accounted for; timeout handling is configured in the IP.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **DataRaptor caching does not survive OmniScript context reloads** — Cache is session-scoped to the OmniScript instance. A full page reload or a new OmniScript instance starts with a cold cache. Do not rely on caching to reduce load across sessions.
2. **Async IP execution requires the caller not to read the IP response** — If the OmniScript has a data mapping that reads from the IP output, the async call will produce empty or stale data in that mapping. The OmniScript must be structured to ignore the response entirely for the async pattern to be correct.
3. **Lazy loading can cause visible step-load delay if the deferred step has a heavy DataRaptor call** — Lazy loading spreads the latency but does not eliminate it. A step that fires a slow uncached DataRaptor will be slow whenever it loads. Caching and consolidation are still needed on those deferred steps.
4. **FlexCard conditional visibility does not suppress the data source call** — Hiding a card with a condition prevents rendering, but if the data source call fires before the condition is evaluated, the call still runs. Condition logic must be placed at the data source level or in the parent IP to actually suppress the fetch.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Step consolidation recommendation | Which DataRaptor calls to move into a single Integration Procedure per step |
| Caching configuration guidance | Cache key structure, duration, and which DataRaptors are safe to cache |
| Async IP design | Which IPs can be made asynchronous and what response handling must be removed |
| FlexCard data source plan | Aggregation pattern for replacing per-card calls with parent IP state |

---

## Related Skills

- `omnistudio/dataraptor-patterns` — use when the DataRaptor type choice (Extract vs Turbo vs Transform) is itself the problem, not just the caching configuration.
- `omnistudio/integration-procedures` — use when IP design complexity (element count, branching, nesting) is the root cause of latency beyond what async and consolidation can fix.
- `omnistudio/omniscript-design-patterns` — use when the journey structure itself (step count, navigation model) is driving performance issues, not the data fetching layer.
- `lwc/lwc-performance` — use when the performance issue is in custom LWC components embedded in OmniScript, not in OmniStudio runtime behavior itself.
