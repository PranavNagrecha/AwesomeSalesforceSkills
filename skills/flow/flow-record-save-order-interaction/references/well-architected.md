# Well-Architected — Save Order

## Relevant Pillars

- **Reliability** — a documented step number per automation eliminates a large
  class of "why is this field stale" bugs, and makes the failure modes that
  produce no error (a duplicate block at step 6, a skipped step 14 on a
  recursive save) visible before they ship.
- **Operational Excellence** — one map per object naming which automation owns
  which step is cheaper than debugging recursion, and it is the only artifact
  that survives the person who built the flow.

## Architectural Tradeoffs

- **Before-save vs after-save Flow:** before-save writes cost no extra save
  procedure; after-save is the only option for related-record DML, for the
  assignment-rule owner, and for anything produced at steps 7–13.
- **Flow vs Trigger at before-save timing:** they occupy adjacent steps
  (Flow 3, trigger 4), so a shared field always resolves to the trigger's
  value. Choose one owner per field. A single trigger handler wins on complex
  control; flow wins on declarative readability for simple field-update rules.
- **Guard vs relocate:** `doesRequireRecordChangedToMeetCriteria` and marker
  fields make a badly placed automation fire less often. Moving the logic to
  the right step makes the problem go away. Prefer relocation; use guards for
  the cases relocation cannot reach (a record that legitimately crosses the
  same boundary twice).
- **In-transaction vs post-commit:** an `AsyncAfterCommit` path buys a fast
  user-facing save and a smaller limits footprint, and costs the ability to
  roll back. That is a trade about who owns the failure, not about
  performance.
- **Consolidate vs isolate:** "one flow per concern" helps discovery but can
  blow up CPU if each flow re-queries the same record, and it multiplies the
  number of `triggerOrder` values someone has to keep true. A dispatcher flow
  trades modularity for a single ordered entry point.

## Hygiene

- Per-object save-order map kept in `docs/`, regenerated from the checker's
  `--map-only` output rather than hand-maintained.
- One before-save flow per object maximum.
- Every co-resident active flow declares `triggerOrder`.
- After-save flows that write their own object carry a transition test and a
  marker.
- No workflow rules and record-triggered flows overlapping on the same field.
- Platform events published from record-triggered flows use
  `publishBehavior` `PublishAfterCommit` unless the signal is deliberately
  independent of the save.

## Official Sources Used

- Apex Developer Guide — *Triggers and Order of Execution*, `apexdev.txt`
  L15402–L15489 (the 20-step list and every step number in SKILL.md, the
  observe/mutate table, and Gotchas 1–5, 8–10, 12).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide — *Triggers and Order of Execution*, "Additional
  Considerations", `apexdev.txt` L15493–L15510 (the `Trigger.old` behaviour
  after a workflow field update in Gotcha 7, the no-guaranteed-order rule for
  multiple triggers in Gotcha 14, and the API 53.0 entitlement ordering in
  Gotcha 13).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide — Execution Governors and Limits, `apexdev.txt` L19559
  (recursive trigger stack depth 16, quoted in Gotcha 5).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide — Debug Log Event Types, `apexdev.txt` L38533,
  L38658–L38662, L38768, L38850–L38862, L38896, L39201–L39210, L39325
  (every event name, category and level in the verification table of
  `references/metadata-examples.md` § 8b).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Metadata API Developer Guide — `Flow`, `api_meta.txt` L68020–L68051 and
  L68438–L68441 (the deploy-active preference, the `.flow` suffix and
  directory, and `triggerOrder` as an int 1–2,000 from API 54.0 — Gotcha 14
  and checker rule R3).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `FlowStart`, `api_meta.txt` L72279–L72545
  (`triggerType` values `RecordBeforeSave` / `RecordAfterSave` /
  `RecordBeforeDelete`, `recordTriggerType`,
  `doesRequireRecordChangedToMeetCriteria`, `filterFormula`, `scheduledPaths`
  — Gotcha 6, checker rules R1/R2, and every `<start>` block in
  `references/metadata-examples.md`).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `FlowScheduledPath`, `api_meta.txt`
  L71389–L71424 (`pathType` `AsyncAfterCommit`, `maxBatchSize` 1–200 default
  200, `timeSource`, `offsetUnit` — Gotcha 10 and § 4 of
  `references/metadata-examples.md`).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `FlowRecordUpdate` and `FlowTest`,
  `api_meta.txt` L71264–L71290 and L73960–L74460 (`inputReference` as the
  `$Record` write that checker rule R1 detects; the `FlowTest` element names,
  `Start`/`Finish` test points and sample XML reproduced in § 5).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `CustomObject`, `publishBehavior`,
  `api_meta.txt` L42206–L42229 (`PublishImmediately` as the default and what
  it means for a save that later fails — Gotcha 11).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Object Reference — `AssignmentRule`, `object_reference.txt` L7044
  ("Represents an assignment rule associated with a Case or Lead" — the
  Case/Lead scope of step 9 in Gotcha 9).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- REST API Developer Guide — Assignment Rule Header, `api_rest.txt`
  L691–L706 (the header applies to Accounts, Cases and Leads, which is why
  "assignment rules are Case/Lead only" needs the territory caveat in
  Gotcha 9).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
