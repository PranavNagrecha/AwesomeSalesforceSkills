# Flow Test Strategy Worksheet

## Flow Under Test

- Flow API name:
- Flow type:
- Custom boundaries involved:

## Path Matrix

- Happy path:
- Branch path:
- Fault path:
- High-risk edge case:

## Test Assets

- Flow Tests to create:
- Debug scenarios to inspect:
- Apex or LWC boundary tests:
- Test data setup notes:

## Sign-Off Checklist

- [ ] Success, branch, and fault paths are covered.
- [ ] Test data is explicit.
- [ ] Boundary dependencies are tested appropriately.
- [ ] Debug findings were converted into repeatable coverage where needed.

## Coverage Worklist (from the deploy result)

`DeployResult.flowCoverage` returns `elementsNotCovered` per flow version — element names,
not a percentage (`api_meta.txt` L7714–7736). One row per uncovered element:

| Element | Real gap or structurally unreachable? | Action / reason accepted |
|---|---|---|
|  |  |  |

## Checker Output

`python3 skills/flow/flow-testing/scripts/check_flow_testing.py --manifest-dir <src>`

| Code | File | Resolved / accepted (why) |
|---|---|---|
|  |  |  |
