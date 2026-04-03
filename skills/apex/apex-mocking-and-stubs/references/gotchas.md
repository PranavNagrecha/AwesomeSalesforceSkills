# Gotchas — Apex Mocking And Stubs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `StubProvider` Depends On A Real Seam

**What happens:** The team reaches for `Test.createStub`, but the production dependency is a static helper with no injectable boundary.

**When it occurs:** Mocking is treated as a framework problem rather than a design problem.

**How to avoid:** Add an interface or stub-friendly collaborator seam first.

---

## One Success Mock Does Not Test Reliability

**What happens:** Tests pass while retry, timeout, and malformed payload handling remain broken.

**When it occurs:** Only the happy path is mocked.

**How to avoid:** Create focused mocks for the failure paths that actually matter.

---

## Static Resource Fixtures Can Drift Quietly

**What happens:** Large JSON fixtures stay in static resources for months while the real API contract changes.

**When it occurs:** Fixtures are convenient but never reviewed.

**How to avoid:** Keep fixture ownership explicit and update them when the contract changes.

---

## Transport Mocks And Service Stubs Are Not Interchangeable

**What happens:** A team uses a callout mock to compensate for a missing internal abstraction, or vice versa.

**When it occurs:** The dependency type is not identified clearly.

**How to avoid:** Choose `Test.setMock` for transport boundaries and `StubProvider` for Apex collaborator seams.
