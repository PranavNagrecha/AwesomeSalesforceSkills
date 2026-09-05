# Flow Cross Object Updates — Work Template

Fill this in before opening Flow Builder. Sections 1 and 2 are the ones people
skip; they are also the two that decide whether any flow gets built at all.

**Skill:** `flow-cross-object-updates`

**Request summary:**
_(one sentence: which object triggers, which object gets written, and what value moves)_

---

## 1. The relationship

| Question | Answer |
|---|---|
| Parent object | |
| Child object | |
| Relationship field API name (on the child) | |
| `type` — `MasterDetail` or `Lookup` | |
| If Lookup: `deleteConstraint` — `SetNull` / `Restrict` / `Cascade` | |
| If MasterDetail: `reparentableMasterDetail`, `writeRequiresMasterRead` | |
| Can the relationship be changed? Who owns that decision? | |

**Stop here if the relationship is MasterDetail and the value is a Count / Sum /
Min / Max.** A `Summary` `CustomField` replaces the whole flow — see
`references/metadata-examples.md` § 5.3. Record the field definition instead and
close this template.

## 2. The write graph

Every record-triggered flow currently Active on **either** object, and the fields
each one writes. Retrieve them; do not rely on memory.

| Flow | Triggering object | Fields it writes | On which object | Entry criteria field(s) |
|---|---|---|---|---|
| | | | | |
| | | | | |

- Does any flow on the child write a field that a flow on the parent watches?
- Does any flow on the parent write a field that a flow on the child watches?
- If yes to either: which entry condition gets narrowed, and to what?

## 3. Direction and volume

| Question | Answer |
|---|---|
| Direction: child→parent stamp, parent→child fan-out, or both | |
| Worst-case children per parent | |
| Worst-case parents changed in one transaction | |
| Product of the two, against 10,000 DML rows (`apexdev.txt` L19556) | |
| `<limit>` value chosen for the child Get, and why | |
| Can a child exist with an empty parent lookup today? (`SELECT COUNT() FROM <Child> WHERE <Lookup> = NULL`) | |

## 4. Approach

Which pattern from `SKILL.md` applies, and why the alternatives were rejected:

- Chosen pattern:
- Roll-up summary rejected because:
- `flow/flow-collection-processing` Transform rejected because:
- Apex rejected because:

Entry criteria for each side, written out:

- Parent-side flow fires when:
- Child-side flow fires when:
- The field each side writes that the *other* side does **not** watch:

## 5. Checklist

- [ ] No Update/Create Records reachable from a Loop's `nextValueConnector`
- [ ] `doesRequireRecordChangedToMeetCriteria` set on both objects' flows
- [ ] Null guard on the parent lookup before any traversal or parent write
- [ ] Child Get filtered by the parent Id **and** bounded by `<limit>`
- [ ] Child Get also excludes rows that already carry the target value
- [ ] `runInMode` set explicitly, with the reason recorded
- [ ] Fault path on every data element, landing per `templates/flow/FaultPath_Template.md`
- [ ] `FlowTest` for each direction, exercising the initial→updated transition
- [ ] `python3 scripts/check_flow_cross_object_updates.py --manifest-dir <tree> --strict` clean
- [ ] Debug log at Workflow FINE shows no `FLOW_CREATE_INTERVIEW_BEGIN` for the other flow
- [ ] Activation staged: one side, exercised, then the other

## 6. Deviations

Anything done differently from `references/metadata-examples.md`, and the reason.
A deviation with no reason recorded here is the one that gets reverted at the next
review.
