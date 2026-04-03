# Apex Mocking Worksheet

## Dependency Under Test

| Item | Value |
|---|---|
| Dependency type | HTTP / SOAP / Internal collaborator |
| Current seam | Interface / Virtual class / Static helper / None |
| Success scenario | |
| Failure scenarios | |

## Chosen Test Double

| Option | Use? | Notes |
|---|---|---|
| `HttpCalloutMock` | | |
| `StaticResourceCalloutMock` | | |
| `StubProvider` | | |
| Refactor seam first | | |

## Guardrails

- [ ] Test doubles cover meaningful failure paths
- [ ] No `Test.isRunningTest()` workaround remains
- [ ] Fixture maintenance owner is known if static resources are used
- [ ] Mock choice matches dependency type
