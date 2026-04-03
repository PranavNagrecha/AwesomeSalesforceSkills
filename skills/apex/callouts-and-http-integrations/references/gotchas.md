# Gotchas — Callouts And HTTP Integrations

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## DML And Callouts In The Same Transaction Need Careful Boundaries

**What happens:** Code performs DML, then immediately attempts an outbound callout and fails with transaction-state issues.

**When it occurs:** Trigger, controller, or service logic tries to mix save work and remote HTTP in one synchronous path.

**How to avoid:** Persist Salesforce work first, then hand the outbound callout to Queueable Apex when the interaction does not have to complete inline.

---

## Queueable Callouts Require `Database.AllowsCallouts`

**What happens:** The Queueable compiles and enqueues correctly, but the callout fails at runtime.

**When it occurs:** The class implements `Queueable` but forgets `Database.AllowsCallouts`.

**How to avoid:** Treat `Queueable` callout work as a two-part contract: `implements Queueable, Database.AllowsCallouts`.

---

## Named Credential Design Affects User Context

**What happens:** The integration works for admins but fails for some users because identity or principal mapping was modeled incorrectly.

**When it occurs:** Teams do not think through org-wide versus per-user identity, External Credential principals, or the target system’s auth expectations.

**How to avoid:** Decide the identity model explicitly before coding. Use per-user identity only when the remote system truly needs end-user delegation.

---

## Tests Must Simulate Both Success And Failure

**What happens:** The happy-path mock returns `200`, the test passes, and production later fails on `401`, `429`, or malformed JSON.

**When it occurs:** Test suites use one mock response and never assert on failure behavior.

**How to avoid:** Build multiple `HttpCalloutMock` responses and assert what the code does for retryable, non-retryable, and malformed responses.
