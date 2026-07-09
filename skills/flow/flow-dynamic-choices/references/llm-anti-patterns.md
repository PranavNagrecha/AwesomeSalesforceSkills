# LLM Anti-Patterns — Flow Dynamic Choices

1. Hard-coded choices that mirror records
2. Unbounded SOQL in Choice Set
3. No empty-state path
4. Ignoring sharing implications
5. Not testing dependent picklists
6. Building a custom LWC for a tile picker when the standard Visual Picker component (Summer '25) already renders icon-tagged Choice resources as tiles
7. Pointing a Visual Picker at Choice resources that have no icon, then wondering why they don't render as tiles
8. Reaching for the standard Lookup component when the requirement is a filtered or restricted record list — that is what a Choice Lookup over a filtered Record or Collection Choice Set is for
9. Assuming Choice Lookup multi-select works in Classic runtime, or wiring its multi-select output to a single-value variable instead of a collection
