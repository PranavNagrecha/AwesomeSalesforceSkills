# Examples — Workflow Field Update Patterns

## Example 1 — Same-record stamp implemented as after-save (wrong) → before-save (right)

**Context.** Stamp `Opportunity.Last_Reviewed_Date__c = TODAY()` when
`StageName` changes to "Negotiation". Admin built it as an after-save
flow that does an Update Records on the same Opportunity.

**What happens.** The flow fires; the Update Records counts as a
second DML; the Opportunity update fires the flow AGAIN; recursion
detected by the platform; transaction errors.

**Right answer.** Before-save flow with entry condition
`ISCHANGED(StageName) AND ISPICKVAL(StageName, 'Negotiation')`.
Single Update Records modifying `Last_Reviewed_Date__c` on the
in-flight record. Free, no DML, no recursion.

---

## Example 2 — Cross-object: Case Closed decrement parent Account counter

**Context.** Each Account has `Open_Cases__c` rolled up via custom
counter (not a Roll-Up Summary because the Case-Account
relationship is master-detail-shaped but stored via lookup). When a
Case closes, decrement.

**Approach.** After-save record-triggered flow on Case with entry
condition `ISCHANGED(Status) AND ISPICKVAL(Status, 'Closed')`.
Update Records on `{!$Record.AccountId}` setting
`Open_Cases__c = Open_Cases__c - 1`.

**Watchout.** The Account update can fire Account's own automation.
That's the standard cross-object cascade — document it.

---

## Example 3 — Workflow Rule with Field Update being migrated

**Context.** Existing Workflow Rule "Set Priority on High-Value
Opportunities" with Field Update action "Priority = High" when
Amount > $100K. Modernizing to flow.

**Migration sequence.**

1. Setup → Workflow Rules → find the rule → click "Migrate to Flow".
2. Tool produces a draft record-triggered flow. Review it.
3. Save the draft. Activate it in the **same sandbox** the WFR is
   active in.
4. Test: edit an Opportunity to satisfy the criteria. Both the WFR
   and the new flow fire (both stamp Priority = High). The save
   succeeds; same outcome.
5. Now deactivate the original Workflow Rule.
6. Test again: only the flow fires. Same outcome.
7. Deploy the flow + WFR-deactivation to production as a single
   change set. The flow fires; WFR is off; behavior preserved.

**Don't deactivate the WFR before activating the flow** — the gap
leaves the field unstamped on records saved during the gap.

---

## Example 4 — Formula field where a flow was reflexively used

**Context.** Admin built a before-save flow on Account that stamps
`Display_Name__c = Name + " — " + Type` on every save.

**Critique.** This is a formula. The value is purely derived from
two same-record fields. A formula field with that expression
computes at read time, no stamping needed, no automation, no
recursion potential.

**Right answer.** Delete the flow. Create a formula field
`Display_Name__c = Name & " — " & TEXT(Type)`. Same outcome,
zero automation cost.

The bias to "build a flow" when a formula fits is one of the most
common over-engineering patterns in Salesforce admin work.

---

## Example 5 — Apex trigger for logic that flow can't express

**Context.** When an Opportunity reaches `StageName = 'Closed Won'`,
generate a unique invoice number from a hash of the Opportunity Id +
the closing user's tenant code, and call a JWT-signed callout to a
billing system. The result of the callout determines whether the
invoice number is committed or rolled back.

**Why flow doesn't fit.** Hashing requires a deterministic algorithm
that flow doesn't expose. JWT signing requires Apex
`Crypto.signWithCertificate`. The transactional rollback-on-callout-
failure is too complex for flow's error handling.

**Right answer.** Apex trigger using the framework at
`templates/apex/TriggerHandler.cls` with a recursion guard
(`Set<Id> processedIds`) and the callout wrapped in
`templates/apex/HttpClient.cls` for retry / circuit-breaker.

---

## Anti-Pattern: Multiple admins, each adding their own flow on the same object

**What it looks like.** Account has 5 record-triggered flows: one
per BU, each set up by a different admin team. All fire on every
Account save event. Ordering is not guaranteed; some fire after
others; debugging cross-flow effects is painful.

**Correct.** One flow per object per save context (one before-save,
one after-save), with internal decision branches per BU's logic. A
flat list of flows scales worse than one branching flow.
