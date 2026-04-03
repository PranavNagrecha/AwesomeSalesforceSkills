# DataRaptor Patterns — Examples

## Example 1: Turbo Extract For A Flat Card Read

**Context:** A FlexCard needs a few Account fields for a fast summary view.

**Problem:** The team starts with a standard Extract plus extra mapping steps even though the read is simple.

**Solution:**

```text
Use Turbo Extract:
- one object
- flat field set
- no complex formulas or transformation layer
```

**Why it works:** The requirement fits the simplified, performance-oriented case.

---

## Example 2: Extract Plus Transform For Shaped Output

**Context:** An OmniScript needs Salesforce data retrieved first and then reshaped into a cleaner response contract.

**Problem:** One large Extract asset tries to both fetch and remap everything.

**Solution:**

```text
DataRaptor Extract -> DataRaptor Transform
```

**Why it works:** Read concerns and response-shaping concerns stay separate and easier to maintain.

---

## Anti-Pattern: DataRaptor As A Hidden Process Engine

**What practitioners do:** Keep adding mapping complexity and write behavior until the DataRaptor chain is acting like orchestration.

**What goes wrong:** The asset becomes difficult to debug, version, and reason about.

**Correct approach:** Keep DataRaptors focused on data responsibility. Move multi-step coordination into an Integration Procedure or Apex.
