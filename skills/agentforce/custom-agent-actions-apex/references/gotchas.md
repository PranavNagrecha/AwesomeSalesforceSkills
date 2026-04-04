# Gotchas — Custom Agent Actions Apex

## 1. Empty Description = Random or Never Invocation

**What happens:** A developer builds a custom action with a descriptive label ("Get Account Details") but leaves the `description` field blank. In testing, the agent sometimes invokes the action when relevant but misses it 70% of the time. In production, the action is rarely called correctly.

**Why:** The Atlas Reasoning Engine uses the `description` field — not the `label` — to decide when to invoke the action. The label is a display name; the description is the semantic signal the LLM reads. A blank description gives the engine no information.

**How to avoid:** Write the description as a one-sentence directive that starts with "Use when" or "Invoke when": "Invoke when the user asks for account details, account information, or wants to look up a customer record by name or ID."

---

## 2. callout=true Omission Causes Silent Failure

**What happens:** An action that makes an HTTP callout compiles and deploys without `callout=true`. In a test run, the action is invoked, and it fails with `System.CalloutException: Callout from triggers are currently not supported`. Or it fails with `You have uncommitted work pending. Please commit or rollback before calling out`.

**Why:** Salesforce requires the `callout=true` annotation modifier to allow HTTP callouts from `@InvocableMethod` methods. Without it, the platform blocks the callout at runtime, not at compile time. The error message varies depending on whether there was prior DML in the same transaction.

**How to avoid:** Any `@InvocableMethod` that calls `new Http().send(req)` must include `callout=true` in the annotation: `@InvocableMethod(label='...' description='...' callout=true)`.

---

## 3. Service Agent User Context Differs From Developer Console Context

**What happens:** An action works perfectly when tested in Developer Console (anonymous Apex execution or Apex test). When deployed and invoked by the Service Agent in production, it returns no records or throws an exception because the service agent user has different profile permissions.

**Why:** Developer Console tests run as the current logged-in user (often an admin or developer). Service Agents run as a designated service agent user — typically a restricted user with a custom profile. If the action uses `with sharing`, the service agent user's sharing model and FLS apply, which may differ drastically from the developer's.

**How to avoid:** Create a test user that matches the service agent user's profile and run `System.runAs(serviceAgentUser)` in unit tests to simulate the actual execution context. Verify SOQL returns expected records under that user's permissions.

---

## 4. Returning Raw SObjects Instead of DTOs Exposes Unexpected Fields

**What happens:** An action returns `List<Account>` directly via an `@InvocableVariable`. The agent serializes the entire Account SObject including every populated field, including sensitive fields like `BillingStreet`, `Phone`, and `AnnualRevenue`. These values appear in the agent's response to the user.

**Why:** When you return raw SObjects from an @InvocableVariable, the platform serializes all fields that were populated in the query result. If the SOQL selected all fields with `SELECT *` (via Schema describe) or if the field was populated by a formula, it is included in the response.

**How to avoid:** Always return DTO (data transfer object) classes from action methods. Define exactly which fields are included in the DTO and annotate each with `@InvocableVariable`. This provides explicit control over what the agent can surface to the user.
