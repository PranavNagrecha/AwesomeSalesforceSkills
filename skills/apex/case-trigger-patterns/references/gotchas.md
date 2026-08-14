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

**How to avoid:** Inside the **`after delete`** handler on Case, check `MasterRecordId` on each record in `Trigger.old`. A non-null `MasterRecordId` indicates the record was merged into the master; a null value indicates a true permanent delete. Branch the logic accordingly.

The check must be in `after delete`, not `before delete`: "The MasterRecordId field is only set in after delete trigger events." The platform's documented sequence is `before delete` fires → records are deleted, children reparented, and `MasterRecordId` set → `after delete` fires. A merge guard written in `before delete` compiles, runs, and always reads null, so every merged case takes the true-delete branch — reproducing the exact data loss the guard was added to prevent, while looking correct in review.

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

---

## Gotcha 6: Case Is Mergeable from Apex but Not from the SOAP `merge()` Call

**What happens:** The two merge surfaces support different object sets, and the narrower one is the API surface most integrations use. The Apex Developer Guide states "Only leads, contacts, cases, and accounts can be merged" — so `merge masterCase duplicateCase;` is valid Apex. The SOAP API `merge()` call documents a different list: "The supported object types are Lead, Contact, Account, Person Account, and Individual." Case is absent from it. A middleware job that merges cases over the SOAP API fails on the object type, not on the data.

**When it occurs:** Porting a case-dedupe routine from Apex to an API-driven integration, or assuming that because `Case.MasterRecordId` exists and the Lightning UI has a case merge action, every merge surface accepts Case.

**How to avoid:** Merge cases from Apex, from the Lightning case merge UI, or from a service the integration calls into — not from a SOAP `merge()` envelope typed to Case. Both surfaces cap one merge at three records — Apex: "You can pass a main record and up to two additional sObject records to a single merge method"; SOAP: "Up to three records can be merged in a single request, including the main record." The SOAP call adds "Up to 200 merge requests can be made in a single SOAP call" and "External ID fields can't be used with merge()." Merging is irreversible — the losing records are deleted and their children reparented.
