# Well-Architected — Save Order

## Relevant Pillars

- **Reliability** — predictable ordering eliminates a large class of
  "why is this field stale" bugs.
- **Operational Excellence** — one document per object mapping which
  automation owns which step is cheaper than debugging recursion.

## Architectural Tradeoffs

- **Before-save vs after-save Flow:** before is ~10× cheaper for
  same-record field writes; after is the only option for related-DML.
- **Flow vs Trigger on same step:** a single trigger handler wins on
  complex control; flow wins on declarative readability for simple
  field-update rules.
- **Consolidate vs isolate:** "one flow per concern" helps discovery but
  can blow up CPU if each flow re-queries the same record. A dispatcher
  flow pattern trades modularity for performance.

## Hygiene

- Per-object save-order map kept in `docs/`.
- One before-save flow per object maximum.
- After-save flows guard against no-op DML.
- No workflow rules + record-triggered flows overlapping on the same
  field.

## Official Sources Used

- Triggers and Order of Execution —
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm
- Before-Save Flows —
  https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_before_save.htm
