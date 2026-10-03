# Learning Brief Examples

## Beginner variant

For an administrator learning record-triggered Flow timing, define before-save and after-save in one table, then use a Case example. Preserve the core constraints—same-record updates, related-record work, transaction behavior, fault handling—without introducing Apex implementation detail unless the outcome requires it.

The knowledge check should change one constraint: "The requirement now creates a related Task. Does the timing choice change, and what evidence would you verify?"

## Developer variant

For an LWC TypeScript migration brief, assume the learner knows JavaScript. Skip a general TypeScript tutorial. Teach project configuration, source-to-compiled output, Lightning base-component types, migration sequencing, test/static-analysis implications, and how to avoid overwriting hand-authored JavaScript.

## Architect variant

For a Salesforce integration pattern brief, teach the contract and decision dimensions before showing code. The practice task asks the learner to classify requirements and identify missing evidence, not to generate an endpoint from an underspecified prompt.

## Partial brief

When edition availability is not supported by the research packet, keep the conceptual lesson but state: "The supplied sources do not establish target-org entitlement. Verify edition/add-on availability before applying the procedure." Place the missing conclusion under `Do Not Teach as Fact`.

## Worked learning artifact fragment

```markdown
### Decision point: before-save or after-save?

Use before-save when the requirement changes fields on the triggering record and does not need related-record DML. Use after-save when the requirement creates the related Task in this exercise.

**Illustrative assumption:** `Case.Priority` and a related `Task` are available in the scratch exercise org.
**Expected result:** one Task is created only when the entry criteria are met.
**Verify:** run the positive and negative Flow tests and confirm no duplicate Task on an unrelated update.
**Does not prove:** production volume, target-org permissions, or compatibility with existing Case automation.
```

The example teaches a branch, identifies assumptions, and includes a proof boundary rather than implying target-org facts.
