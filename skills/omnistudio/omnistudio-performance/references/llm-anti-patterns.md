# LLM Anti-Patterns — OmniStudio Performance

Common mistakes AI coding assistants make when generating or advising on OmniStudio performance optimization.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Loading All Data on OmniScript Initialization

**What the LLM generates:** OmniScript designs that call multiple Integration Procedures on the first step load to prefill all data upfront, causing long initial load times even for data the user may never see.

**Why it happens:** LLMs frontload data retrieval to ensure all steps have data available. The lazy-loading pattern (load data only when the user navigates to the step that needs it) is less commonly documented.

**Correct pattern:**

```text
OmniScript data loading strategies:

Eager (current anti-pattern):
- Step 1 loads ALL data for all steps
- User waits 5-10 seconds before seeing anything
- Data may be wasted if user does not reach all steps

Lazy (recommended):
- Step 1: load only Step 1's data (fast render)
- Step 2: load Step 2's data when user clicks "Next"
- Step 3: load Step 3's data when user clicks "Next"
- Each step loads in 1-2 seconds

Implementation:
- Use per-step Integration Procedure actions (not a single monolithic IP)
- Configure prefill actions on each step, not on the OmniScript level
- Use "Run on Entry" for step-level data actions
```

**Detection hint:** Flag OmniScripts with multiple Integration Procedure calls on initialization. Check for monolithic prefill IPs that retrieve data for all steps.

---

## Anti-Pattern 2: Not Caching Integration Procedure Responses

**What the LLM generates:** Integration Procedures called from FlexCards or OmniScripts without caching enabled, causing redundant API calls every time the component re-renders or the user navigates back to a step.

**Why it happens:** Caching is an opt-in configuration that LLMs do not apply by default. The performance impact of uncached IPs (repeated callouts to external APIs or Salesforce queries) is not highlighted in feature documentation.

**Correct pattern:**

```text
Integration Procedure caching options:

1. IP-level caching:
   - Enable "Use Data Cache" in IP properties
   - Set cache duration (minutes)
   - Cache key: based on input parameters
   - Best for: reference data, picklist values, rate tables

2. Platform Cache:
   - Store IP results in Salesforce Platform Cache
   - Org-level or session-level partition
   - Requires Platform Cache allocation

3. Client-side caching:
   - OmniScript data JSON persists between steps
   - Data loaded on Step 1 is available on Step 3 without re-fetching
   - Use the OmniScript data structure as in-memory cache

When NOT to cache:
- Data that changes frequently (real-time inventory, pricing)
- User-specific data that must reflect the current state
- Data from external APIs with their own caching headers
```

**Detection hint:** Flag Integration Procedures called from FlexCards without caching enabled. Check for repeated IP calls with the same input parameters.

---

## Anti-Pattern 3: Using DataRaptor Extract Instead of Turbo Extract for Simple Queries

**What the LLM generates:** DataRaptor Extract configurations for simple single-object queries (e.g., "get Account by Id") when Turbo Extract would be significantly faster with no mapping configuration.

**Why it happens:** DataRaptor Extract is the default data retrieval component in training data. Turbo Extract is a newer, faster alternative for simple use cases that LLMs do not consistently recommend.

**Correct pattern:**

```text
Turbo Extract vs DataRaptor Extract performance:

Turbo Extract:
- No field mapping configuration required
- Faster execution (bypasses the mapping engine)
- Single object queries only
- Supports basic WHERE filters
- Best for: record prefill, simple lookups

DataRaptor Extract:
- Full field mapping with transformation
- Multi-object relationship queries
- Formula fields in mappings
- Slower due to mapping engine overhead
- Best for: complex data shapes, multi-object joins

Performance impact:
- Turbo Extract: ~50-100ms typical execution
- DataRaptor Extract: ~200-500ms typical execution
- The difference multiplies when called multiple times per page
```

**Detection hint:** Flag DataRaptor Extract configurations for single-object queries with no transformation. Recommend Turbo Extract as a faster alternative.

---

## Anti-Pattern 4: Not Using Async Integration Procedures for Long-Running Operations

**What the LLM generates:** Synchronous Integration Procedure calls from OmniScripts for operations that take 5+ seconds (external API calls, complex calculations, bulk data operations), blocking the user interface.

**Why it happens:** Synchronous execution is the default. LLMs do not evaluate expected execution time and apply async patterns proactively.

**Correct pattern:**

```text
Async IP patterns for performance:

Fire-and-forget:
- OmniScript calls IP asynchronously
- IP runs in the background
- OmniScript continues without waiting
- Best for: logging, notifications, non-blocking operations

Polling:
- OmniScript launches async IP
- Step shows a spinner
- Periodic check for completion (IP writes result to a record)
- OmniScript reads the result when available
- Best for: operations that take 5-30 seconds

Thresholds:
- < 3 seconds: synchronous IP is acceptable
- 3-10 seconds: consider async with loading indicator
- > 10 seconds: async is required, consider background processing
```

**Detection hint:** Flag synchronous IP calls with HTTP Actions configured for >5 second timeouts. Check for OmniScript steps that block on long-running external calls.

---

## Anti-Pattern 5: Rendering Too Many Child Cards in FlexCard Iterations

**What the LLM generates:** FlexCard designs that iterate over 100+ child records, rendering a child FlexCard for each one, causing severe rendering performance degradation.

**Why it happens:** FlexCard iteration is a convenient feature. LLMs do not apply pagination or virtualization patterns because the iteration configuration is simple and works for small datasets.

**Correct pattern:**

```text
FlexCard iteration performance guidelines:

Recommended: render 10-25 child cards per page
Maximum practical: 50 child cards before performance degrades

For large datasets (>25 items):
1. Implement pagination in the Integration Procedure
   - Return only N records per page
   - Add "Load More" or pagination controls
2. Use a data table component instead of FlexCard iteration
   - Tables render faster than individual cards for lists
3. Add filtering to reduce the dataset before rendering
4. Use virtual scrolling for very long lists

Performance impact:
- Each child card = separate DOM rendering
- Each child card's data source = separate server call (if not inherited)
- 100 child cards with data sources = 100 callouts + 100 DOM renders
```

**Detection hint:** Flag FlexCard iterations over datasets larger than 50 records without pagination. Check for child cards with independent data sources in iteration context.
