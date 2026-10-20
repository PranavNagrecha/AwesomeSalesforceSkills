# Flow Invocable From Apex — Work Template

Use this template when authoring an `@InvocableMethod` for Flow, or when Apex starts a flow.

## Scope

**Skill:** `flow-invocable-from-apex`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Questions to Ask Before Configuring table in SKILL.md.

- Batch size and calling flow type:
- Calls an external system (`callout=true`)?:
- Wrapper field types and visibility:
- Failure strategy (output field, fault path, rollback):
- Class `apiVersion` and sharing keyword:
- Statics or caches in the class:
- Flow started from Apex: API name, flow type, variables read:

## Approach

Which pattern from SKILL.md applies (bulk-safe action, action with a callout, calling a flow from Apex), and why.

## Checklist

- [ ] One `List` input parameter; return type `void` or a `List`
- [ ] Output list has the same size and order as the input list
- [ ] No SOQL or DML inside a loop over the input list
- [ ] `@InvocableVariable` members are `public` or `global` fields, no properties
- [ ] `callout=true` set when the method calls an external system
- [ ] Sharing keyword declared; `apiVersion` checked against 67.0
- [ ] Tests: single record, N=200, null, empty, partial failure, non-admin user
- [ ] `check_flow_invocable_from_apex.py --manifest-dir` run with no ERROR

## Notes

Record any deviation from the standard pattern and why.
