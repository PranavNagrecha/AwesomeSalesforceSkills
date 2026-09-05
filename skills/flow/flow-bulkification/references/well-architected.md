# Well-Architected Notes — Flow Bulkification

## Relevant Pillars

### Performance

Bulkification is directly tied to Flow performance because query count, DML fan-out, and unnecessary after-save work all increase transaction cost.

### Scalability

A flow that only works for one record is not production-ready. Scalable Flow design means handling mass updates, imports, and API-driven operations without per-record amplification.

### Reliability

Poorly bulkified flows are a reliability risk because they fail unpredictably during the highest-volume business events.

## Architectural Tradeoffs

- **Declarative simplicity vs transaction efficiency:** Flow is faster to change, but high-volume logic sometimes belongs in Apex or async patterns.
- **After-save flexibility vs before-save efficiency:** After-save can update related records, but before-save is the better fit for same-record enrichment.
- **Subflow reuse vs hidden complexity:** Reuse improves maintainability, but it can hide expensive loop behavior if nobody reviews the full call chain.

## Anti-Patterns

1. **Query or DML inside a Flow loop** — the classic scale failure that turns record volume into limit usage.
2. **After-save for same-record field updates** — unnecessary DML and extra automation firing for a requirement that belongs in before-save.
3. **Leaving high-volume orchestration in Flow when Apex is the safer boundary** — maintainability suffers when declarative tooling is pushed past its fit.
4. **Staging a collection and never committing it** — a Loop with no `noMoreValuesConnector` is the only bulkification defect that produces no error at all.
5. **Quoting a batch size the platform does not offer** — `maxBatchSize` belongs to scheduled paths on record-triggered flows, not to schedule-triggered flows, which have no batch-size field.

The full set with detection hints is in `references/llm-anti-patterns.md`.

## Official Sources Used

Every source below was read for this skill; the parenthesis names the claim it carries.

- **Metadata API Developer Guide**, Flow section — `Flow` L68065+, `FlowLoop` L70698–70717
  (`nextValueConnector` / `noMoreValuesConnector`), `FlowRecordLookup` L71091–71249
  (`getFirstRecordOnly`, `storeOutputAutomatically`, `limit` 2–20,000),
  `FlowRecordUpdate` L71279–71296 (`inputReference` vs `filters`; no all-or-none field),
  `FlowRecordCreate` L70953–70963 (`doesUpsert`, `doesUpsertAllOrNone` default `true`),
  `FlowCollectionProcessor` L69926–69984 (Filter / Sort / recommendation-Map; sort-then-limit),
  `FlowAssignmentOperator` L69786–69790 (`Add` on a collection variable is Metadata-API-only),
  `FlowStart` L72279–72553 (`<object>` starts one interview per matching record;
  `triggerType` enum), `FlowSchedule` L71335–71386 (no batch-size field),
  `FlowScheduledPath` L71397–71398 (`maxBatchSize` 1–200, default 200), `FlowTest`
  L73960–74050 and its samples L74344–74450. Every XML element name, enum value and
  version floor in `references/metadata-examples.md`.
  PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Apex Developer Guide — Per-Transaction Apex Limits** (L19541–19580): 100 SOQL queries
  synchronous / 200 asynchronous, 150 DML statements, 10,000 DML rows, 6 MB / 12 MB heap,
  10,000 ms / 60,000 ms CPU. Every number in the limits table in `SKILL.md` and in the
  scale arithmetic in `references/examples.md`.
  PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide — Running Apex within Governor Execution Limits** (L20161–20290):
  "The governor execution limits are per transaction" (L20172–20173), the bulkified-DML
  worked example (L20177–20205), and the SOQL-in-a-for-loop worked example
  (L20211–20250). The framing that a per-transaction limit cannot be fixed by a per-record
  filter (`references/llm-anti-patterns.md` § 8).
- **Apex Developer Guide — Triggers and Order of Execution** (L15402–15490): record-triggered
  flows run at step 3 (before save) and step 14 (after save), the record is written at step
  7, and asynchronous paths run post-commit at step 20. Why before-save costs no DML
  (`SKILL.md` § Before-Save And After-Save Have Different Scale Costs).
- **Apex Developer Guide — Trigger context variables and bulk considerations** (L15029–15034,
  L14904–14907): "DML operations that include over 200 records are processed in batches, and
  the trigger is invoked for each batch"; "governor limits are reset between these trigger
  invocations for the same HTTP request". Why 200 is the default cardinality in the scale
  math, and why a 10,000-row load test proves only that 200 works
  (`references/gotchas.md` § batches of 200).
- **Apex Developer Guide — `InvocableMethod` considerations** (L5432–5460): "For a correct
  bulkification implementation, the Inputs and Outputs must match on both the size and the
  order … such as when an apex action is used in a record trigger flow". The invocable-Apex
  gotcha, and the fact that the failure mode is data correctness rather than an exception.
- **Apex Developer Guide — Debug log event types** (L38712–38900): `FLOW_START_INTERVIEWS_BEGIN`,
  `FLOW_BULK_ELEMENT_BEGIN` / `_DETAIL` / `_END` / `_LIMIT_USAGE` / `_NOT_SUPPORTED`,
  `FLOW_INTERVIEW_FINISHED_LIMIT_USAGE`, `FLOW_LOOP_DETAIL`. The only grounded evidence in
  this package for what the platform bulkifies and what it does not; the verification
  procedure in `references/metadata-examples.md` § 8.
- **Salesforce App Limits Cheat Sheet** — read and reported as a **negative**: it contains no
  Flow or flow-interview limits. Four occurrences of "flow", all the word "workflow" in
  unrelated rows (L172, L648, L655, L731), and no numeric platform-event allocation figures.
  Nothing in this skill is sourced from it, and the widely repeated "2,000 elements per
  interview" figure is not there — `flow/flow-loop-element-patterns`
  `references/gotchas.md` § 3 covers that limit and its removal in API 57.0.
  PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf
- Flow Bulkification in Transactions — https://help.salesforce.com/s/articleView?id=platform.flow_concepts_bulkification.htm&type=5
  (pre-existing citation; help.salesforce.com cannot be fetched from this environment, so
  nothing new was taken from it in the 2026-09-05 pass)
- Schedule-Triggered Flow Considerations, "if a schedule-triggered flow has a Create Records,
  Delete Records, Get Records, or Update Records element that processes multiple records and
  some records fail, all records are rolled back" — https://help.salesforce.com/s/articleView?id=sf.flow_considerations_trigger_schedule.htm&type=5
  (pre-existing citation, carried forward; it is corroborated from the metadata side by
  `FlowRecordUpdate` having no all-or-none field, `api_meta.txt` L71279–71296)
- Salesforce Developer Documentation — "Platform Event Allocations" (per-edition
  publish/delivery figures; verified 2026-08-01): https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
  (supports the platform-event allocation gotcha in `SKILL.md`; not re-verifiable from the
  offline corpus, and the App Limits cheat sheet carries no numeric figures for it)
