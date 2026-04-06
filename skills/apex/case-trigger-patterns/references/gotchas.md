# Gotchas — Case Trigger Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex DML Silently Bypasses Case Assignment Rules

**What happens:** When Apex uses the `insert` or `update` DML keyword on Case records, assignment rules are not evaluated. The case is saved with the default owner (typically the running user) and no routing occurs. No exception is thrown and no log entry is created — the failure is completely silent.

**When it occurs:** Any time a trigger, batch job, invocable Apex, or integration service inserts or updates cases using the standard `insert`/`update` DML keywords without providing `Database.DmlOptions`. This is the default behavior for all programmatic DML.

**How to avoid:** Replace `insert caseList;` with `Database.insert(caseList, opts)` where `opts.assignmentRuleHeader.useDefaultRule = true`. To target a specific rule rather than the active default, set `opts.assignmentRuleHeader.assignmentRuleId` to the 18-character rule Id. The `Database.DmlOptions` approach works for both insert and update contexts.

---

## Gotcha 2: Closing a Case Does Not Auto-Complete Open Milestones

**What happens:** Setting `Case.Status` to a closed value (where `IsClosed = true`) does not automatically set open `CaseMilestone` records for that case to `IsCompleted = true`. Open milestones remain in a "violation pending" or "in progress" state even after the case is closed. Milestone violation workflows may fire on closed cases, creating noise and inaccurate SLA metrics.

**When it occurs:** Any time a case with an active entitlement process closes — whether via UI, Apex, Flow, or API — and one or more milestones are still open. The platform evaluates entitlement process milestones asynchronously; the same-transaction view always shows milestones as open at the moment of close.

**How to avoid:** Add an `After Update` trigger handler that detects the `IsClosed` transition, queries `CaseMilestone` for open records on the closing cases, and sets `CaseMilestone.CompletionDate` to `Datetime.now()`. Setting `CompletionDate` is the write-path for completing a milestone from Apex — `IsCompleted` is a read-only computed field.

---

## Gotcha 3: Merge Fires Delete Triggers, Not a Dedicated Merge Event

**What happens:** Merging two Case records fires `before delete` and `after delete` on the losing record(s). There is no merge-specific trigger event. Any cleanup or archival logic in an existing delete trigger will execute for both true deletes and merge deletes, potentially purging data that should be migrated to the master record instead.

**When it occurs:** Any case merge operation, whether performed via the UI (Cases > Merge Cases) or via the Apex `merge` DML statement.

**How to avoid:** Inside `before delete` and `after delete` handlers on Case, check `MasterRecordId` on each record in `Trigger.old`. A non-null `MasterRecordId` indicates the record is being merged into the master; a null value indicates a true permanent delete. Branch the logic accordingly. The Apex Developer Guide confirms this is the canonical detection method for merge operations within delete triggers.

---

## Gotcha 4: `ConvertedContactId` and Related Fields Are Not in `Trigger.new` for Lead Triggers (Relevant for Case-Related Lead Flows)

**What happens:** When a lead is converted and a Case is created as part of the conversion flow, any lead `after update` trigger that tries to read `ConvertedContactId` directly from `Trigger.new` will find it null. The field is populated in the database but not in the in-memory trigger context objects.

**When it occurs:** Any after update trigger on Lead that reads `ConvertedContactId`, `ConvertedAccountId`, or `ConvertedOpportunityId` from `Trigger.new` rather than re-querying the Lead from SOQL after the conversion.

**How to avoid:** Re-query the Lead records from SOQL inside the `after update` trigger handler when conversion is detected (`l.IsConverted && !oldMap.get(l.Id).IsConverted`). The re-queried result will have the converted record Ids populated.

---

## Gotcha 5: `Database.DmlOptions` Cannot Be Passed to the `insert` Keyword

**What happens:** Apex developers accustomed to the `insert` keyword attempt to chain options — for example, `insert(caseList, opts)` — which is not valid Apex syntax. The compiler error can cause confusion about how to supply DML options at all.

**When it occurs:** Any time a developer tries to pass `Database.DmlOptions` to a keyword DML statement rather than to the equivalent `Database.*` method.

**How to avoid:** Use `Database.insert(recordList, opts)` and `Database.update(recordList, opts)`. These are the static methods on the `Database` class that accept a `Database.DmlOptions` second argument. The DML keyword syntax (`insert`, `update`, `upsert`) has no mechanism for DML options.
