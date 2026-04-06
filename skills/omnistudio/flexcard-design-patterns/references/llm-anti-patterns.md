# LLM Anti-Patterns — FlexCard Design Patterns

Common mistakes AI coding assistants make when generating or advising on OmniStudio FlexCard design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Multiple Data Sources When One Would Suffice

**What the LLM generates:** A FlexCard with three separate data sources (one for Account fields, one for Contact count, one for Opportunity total) when a single Integration Procedure could return all data in one call.

**Why it happens:** LLMs decompose data retrieval by object. FlexCards support multiple data sources, but each one fires independently on card load, increasing page load time and API consumption.

**Correct pattern:**

```text
FlexCard data source strategy:

Prefer fewer data sources:
1. Single Integration Procedure that returns all needed data
2. FlexCard maps fields from the single response JSON
3. One callout instead of three = faster rendering

Use multiple data sources only when:
- Data sources are independent and can load in parallel
- One data source is cached and another must be real-time
- Different data sources refresh on different user actions

Performance rule: each data source = one server round-trip.
Minimize round-trips for faster FlexCard rendering.
```

**Detection hint:** Flag FlexCards with 3+ data sources querying related data from the same record context. Check whether a single Integration Procedure could consolidate the calls.

---

## Anti-Pattern 2: Not Using Card States for Conditional Display

**What the LLM generates:** Complex conditional visibility expressions on individual elements to show/hide content based on record status, when card states provide a cleaner pattern for displaying entirely different layouts based on a field value.

**Why it happens:** Element-level conditional visibility is the more granular approach and appears in more training examples. Card states (which switch the entire card layout based on a condition) are a FlexCard-specific feature with less documentation.

**Correct pattern:**

```text
Card states vs conditional visibility:

Card States (preferred for layout-level changes):
- Define multiple card layouts (states) within one FlexCard
- Switch state based on a field value (e.g., Status = 'Active' vs 'Closed')
- Each state can have completely different elements and layout
- Cleaner than hiding/showing 20 individual elements

Conditional Visibility (for element-level control):
- Show/hide individual elements based on conditions
- Best for small variations within the same layout
- Can become unwieldy with many conditions

Use Card States when: the layout changes significantly based on a value
Use Conditional Visibility when: only 1-3 elements change
```

**Detection hint:** Flag FlexCards with more than 5 conditional visibility expressions that could be simplified with card states. Look for patterns where most elements are conditionally visible based on the same field.

---

## Anti-Pattern 3: Embedding Heavy Logic in FlexCard Actions Instead of OmniScript or IP

**What the LLM generates:** FlexCard action configurations that chain multiple DataRaptor calls, conditional logic, and field updates directly from the card action, creating a complex execution chain that is hard to debug.

**Why it happens:** FlexCard actions can invoke DataRaptors and Integration Procedures directly. LLMs chain multiple actions together without recognizing that complex orchestration belongs in an Integration Procedure or OmniScript.

**Correct pattern:**

```text
FlexCard action complexity guidelines:

Simple actions (appropriate for FlexCard):
- Navigate to a record page
- Launch an OmniScript
- Call a single Integration Procedure
- Refresh the card data

Complex actions (move to Integration Procedure or OmniScript):
- Multi-step data operations (read, transform, write)
- Error handling with conditional paths
- External API calls with response processing
- Operations that require user confirmation before proceeding

Pattern: FlexCard action -> single Integration Procedure -> all logic inside IP
This keeps the FlexCard simple and the logic testable/debuggable in the IP.
```

**Detection hint:** Flag FlexCard actions that chain 3+ operations. Check whether the logic should be encapsulated in a single Integration Procedure call.

---

## Anti-Pattern 4: Not Considering Mobile Rendering for FlexCards

**What the LLM generates:** FlexCard designs with fixed-width layouts, multiple columns, and desktop-optimized elements without considering that FlexCards may render on mobile devices via the Salesforce mobile app.

**Why it happens:** LLMs design for desktop UI by default. Mobile rendering constraints (narrow viewport, touch targets, limited screen real estate) are not applied unless explicitly requested.

**Correct pattern:**

```text
FlexCard mobile considerations:

1. Use responsive layout elements that stack on narrow viewports
2. Avoid fixed-width columns that exceed mobile screen width
3. Ensure touch targets are at least 44x44 pixels
4. Minimize data density: show key fields only on mobile
5. Test FlexCard in mobile preview mode before deployment
6. Consider separate FlexCard variants for mobile if the
   desktop layout does not adapt well

FlexCard mobile testing:
- Use the OmniStudio Preview with mobile viewport simulation
- Test in the Salesforce mobile app on actual devices
- Verify that child card iteration does not create excessive scrolling
```

**Detection hint:** Flag FlexCard designs with fixed-width columns or complex multi-column layouts without mobile viewport considerations.

---

## Anti-Pattern 5: Ignoring FlexCard Caching for Repeated Data Sources

**What the LLM generates:** FlexCard configurations where the same data source is called repeatedly (on every card render or in child card iterations) without using cached data from a parent card or shared data source.

**Why it happens:** LLMs configure each FlexCard independently without considering the parent-child card relationship or data inheritance from the page context.

**Correct pattern:**

```text
FlexCard data reuse strategies:

1. Parent-to-child data passing:
   - Parent card fetches data once
   - Child cards receive data via the parent's data context
   - No additional data source call needed in child card

2. Record context inheritance:
   - FlexCards on a record page inherit the record context
   - Use {recordId} in data source parameters
   - Avoid re-querying data already available on the page

3. Integration Procedure caching:
   - Configure IP with caching enabled (cache duration)
   - Subsequent FlexCard renders use cached IP response
   - Best for: reference data that does not change frequently

Avoid: each child card making its own DataRaptor Extract call
for the same parent record data.
```

**Detection hint:** Flag child FlexCards with their own data sources that duplicate data already available from the parent card. Check for missing data context inheritance.
