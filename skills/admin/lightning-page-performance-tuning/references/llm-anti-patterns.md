# LLM Anti-Patterns — Lightning Page Performance Tuning

Common mistakes AI coding assistants make when generating or advising on Lightning Page Performance Tuning.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming a Hard Component Count Limit Exists

**What the LLM generates:** Statements like "Salesforce limits Lightning pages to 25 components" or "you cannot add more than 20 components to a record page."

**Why it happens:** LLMs conflate best-practice guidance (keep component counts low) with platform-enforced limits. No hard component count limit exists in Lightning App Builder. Salesforce flags slow pages via EPT measurement in Lightning Experience Insights, not by counting components.

**Correct pattern:**

```
There is no hard component count limit on Lightning pages. However, every
additional component adds DOM rendering cost and may trigger server
round-trips. Salesforce flags pages as slow in Lightning Experience Insights
based on measured EPT (Experienced Page Time), not component count.

Best practice: keep initial-viewport components to 8-10 and defer the rest
to tabs.
```

**Detection hint:** Any response citing a specific numeric component limit (e.g., "max 25 components") without linking to an official Salesforce documentation source should be flagged.

---

## Anti-Pattern 2: Recommending Tab Deferral as a Universal Solution Without Considering User Workflow

**What the LLM generates:** Blanket advice to "move all non-essential components to tabs" without asking whether users need all information on every record view.

**Why it happens:** Tab deferral is the most commonly documented optimization, so LLMs default to it without considering that some workflows require accessing all tabs on every record. In those workflows, tab deferral shifts load time from initial render to sequential tab clicks, potentially making the total experience worse.

**Correct pattern:**

```
Tab deferral works best when non-default tabs are accessed on fewer than
30% of page views. Before recommending tabs:
1. Ask whether users access all information on every record
2. If yes, consider component removal or page variants instead
3. If no, identify which components are accessed infrequently and defer those
```

**Detection hint:** Recommendations to "put everything in tabs" without first asking about the user's workflow or access frequency.

---

## Anti-Pattern 3: Confusing EPT with Server Response Time or TTFB

**What the LLM generates:** Advice to "reduce server response time to improve EPT" or "EPT measures how long the server takes to respond."

**Why it happens:** LLMs conflate different web performance metrics. EPT (Experienced Page Time) is a client-side metric that measures from navigation start to full page interactivity. It includes server response time but also includes client-side rendering, JavaScript execution, and component initialization. Server response time (TTFB) is only one component of EPT.

**Correct pattern:**

```
EPT includes:
- Server response time (TTFB)
- Client-side JavaScript execution (Aura/LWC framework)
- DOM rendering and layout calculations
- Component-level data fetching (XHR calls after initial page load)

To reduce EPT, address all four areas — not just server performance.
Client-side optimizations (fewer components, tab deferral, conditional
rendering) often have more impact than server-side changes for Lightning
page performance.
```

**Detection hint:** Responses that treat EPT as purely a server-side metric or recommend only server-side optimizations for EPT improvement.

---

## Anti-Pattern 4: Suggesting Visualforce-Era Techniques for Lightning Pages

**What the LLM generates:** Recommendations like "use action:support to lazy-load sections" or "add rendered='false' to defer component loading" — techniques from Visualforce that do not apply to Lightning.

**Why it happens:** LLMs trained on older Salesforce content mix Visualforce rendering attributes with Lightning component architecture. Visualforce `rendered` attributes, `action:support`, and `rerender` have no equivalent in Lightning App Builder or LWC.

**Correct pattern:**

```
In Lightning pages:
- Use the Tabs component in Lightning App Builder for progressive disclosure
- Use lwc:if (or if:true in older API versions) in LWC for conditional rendering
- Use component visibility filters in Lightning App Builder for role-based display
- Do NOT use Visualforce-era attributes (rendered, rerender, action:support)
```

**Detection hint:** Any response referencing `rendered`, `rerender`, `action:support`, `actionRegion`, or other Visualforce-specific attributes in the context of Lightning page optimization.

---

## Anti-Pattern 5: Recommending Lightning Experience Insights Features That Do Not Exist

**What the LLM generates:** Claims that Lightning Experience Insights shows "per-component load time breakdown" or "component-level rendering metrics."

**Why it happens:** LLMs infer capabilities that would be logical for a performance monitoring tool but do not actually exist in Lightning Experience Insights. The tool shows page-level EPT and identifies slow pages, but it does not provide per-component timing breakdown.

**Correct pattern:**

```
Lightning Experience Insights provides:
- P75 EPT for first and subsequent page loads
- High-Impact Slow-Performing Pages view (ranked by user impact)
- Page-level performance trends over time

It does NOT provide:
- Per-component load time breakdown
- Component-level rendering metrics
- Network waterfall charts

For component-level performance profiling, use browser DevTools (Network tab,
Performance tab) or Chrome's Lighthouse audit.
```

**Detection hint:** Responses that describe Lightning Experience Insights providing component-level or granular rendering metrics beyond page-level EPT.

---

## Anti-Pattern 6: Ignoring the Distinction Between First Load and Subsequent Load EPT

**What the LLM generates:** A single EPT target or recommendation without distinguishing between first load and subsequent load performance.

**Why it happens:** LLMs simplify EPT into a single number. In practice, first-load EPT (cold cache, framework initialization) is 2-4x slower than subsequent-load EPT (warm cache). Optimizations that improve subsequent load may not affect first load, and vice versa.

**Correct pattern:**

```
Always measure and report both:
- First page load EPT: includes framework initialization, cold cache
- Subsequent page load EPT: warm cache, faster rendering

Common scenario: tab deferral significantly improves subsequent-load EPT
but has less impact on first-load EPT because the framework initialization
cost dominates.

Set separate targets for each and optimize accordingly.
```

**Detection hint:** EPT recommendations that cite a single target number or discuss "EPT" without specifying which load type.
