# LLM Anti-Patterns — Approval Processes

Common mistakes AI coding assistants make when generating or advising on Salesforce Approval Processes.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Forgetting that records lock on submission by default

**What the LLM generates:** "Submit the record for approval. The owner can continue editing it while it is pending."

**Why it happens:** LLMs focus on approval routing and forget that Salesforce locks the record when it enters an approval process by default. Unless the admin explicitly changes the Record Editability setting, no one except admins can edit the record while pending.

**Correct pattern:**

```
When configuring the approval process, under "Record Editability Properties":
- "Administrator ONLY can edit..." (strictest, default)
- "Administrator OR Current Approver can edit..."
If fields must remain editable during approval, use a pre-submission
screen flow or a child object for in-flight updates.
```

**Detection hint:** If the output says users can "continue editing" during approval without mentioning the lock setting, the lock behavior is being ignored. Search for `Lock the record` or `Record Editability`.

---

## Anti-Pattern 2: Chaining approval processes across objects with field updates

**What the LLM generates:** "When the Opportunity is approved, use a field update to submit the related Quote for approval."

**Why it happens:** LLMs try to orchestrate multi-object approvals using field updates. Standard Approval Processes operate on one object. Field updates cannot invoke approval submission on a related object.

**Correct pattern:**

```
For multi-object approval orchestration:
- Use a Record-Triggered Flow on Object A's status field to submit
  Object B via the "Submit for Approval" action element.
- Or use Apex Approval.ProcessSubmitRequest in an invocable method.
- Field updates CANNOT trigger approval submissions on related records.
```

**Detection hint:** If the output describes chaining approvals across objects using field updates, the approach is invalid. Search for `field update` combined with `submit for approval`.

---

## Anti-Pattern 3: Ignoring the blank approver field scenario

**What the LLM generates:** "Set the approver to the Manager field on the submitter's user record."

**Why it happens:** LLMs assume the Manager field is always populated. When the Manager field is blank, the approval submission fails and the record may be stuck with no approver.

**Correct pattern:**

```
Always handle the blank approver scenario:
1. Add entry criteria blocking submission when the approver is blank:
   NOT(ISBLANK(Owner.ManagerId))
2. Or use a Queue as the fallback approver.
3. In multi-step processes, configure "If no approver found" on each step.
```

**Detection hint:** If the output sets `Manager` or a lookup field as the approver without mentioning what happens when blank, the scenario is unhandled. Search for `ISBLANK` or `fallback`.

---

## Anti-Pattern 4: Confusing entry criteria with step criteria

**What the LLM generates:** "Set the approval criteria to Amount > 10000 for manager approval and Amount > 50000 for VP approval."

**Why it happens:** LLMs conflate entry criteria (which records enter the process) with step criteria (which steps execute within the process). Multiple thresholds at different approval levels should be separate approval steps, not multiple entry criteria.

**Correct pattern:**

```
Entry Criteria (process level): Amount > 10000
  → Records ≤ 10000 are never submitted.

Step 1: Manager Approval — no additional step criteria.
Step 2: VP Approval — step criteria: Amount > 50000.
  If NOT met → skip step → approved after Step 1.
  If met → route to VP for additional approval.
```

**Detection hint:** If the output puts multiple threshold conditions on entry criteria instead of using separate approval steps, the step structure is wrong.

---

## Anti-Pattern 5: Recommending Process Builder for auto-submission

**What the LLM generates:** "Use Process Builder to automatically submit the record for approval when Status changes."

**Why it happens:** Pre-2025 training data references Process Builder, which supported a Submit for Approval action. Process Builder is now retired.

**Correct pattern:**

```
Use a Record-Triggered Flow (After Save) to auto-submit:
1. Object: target object.
2. Entry criteria: Status = 'Ready for Review'.
3. Add a "Submit for Approval" core action element.
4. Add a fault path to handle submission failures gracefully.
```

**Detection hint:** If the output references `Process Builder` for new approval automation, it is recommending a retired tool. Search for `Process Builder`.

---

## Anti-Pattern 6: Omitting recall actions and delegation configuration

**What the LLM generates:** "Configure the approval and rejection actions. The process is complete."

**Why it happens:** LLMs focus on approve/reject and forget that submitters may need to recall pending requests and approvers may need to delegate while out of office.

**Correct pattern:**

```
Complete the full action set:
1. Initial Submission Actions: field updates, email alerts, lock record.
2. Final Approval Actions: field updates, unlock record.
3. Final Rejection Actions: field updates, unlock record.
4. Recall Actions: revert status, unlock record, notify submitter.
   Check "Allow submitters to recall approval requests."
5. Delegation: Setup → Approval Processes → Settings →
   enable "Allow Approver to Delegate Approval Requests."
```

**Detection hint:** If the output only covers approve and reject actions without mentioning `recall` or `delegate`, the design is incomplete.
