# LLM Anti-Patterns — Data Seeding For Testing

Common mistakes AI coding assistants make when generating or advising on Data Seeding For Testing.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending SeeAllData=true for Integration Tests

**What the LLM generates:** `@isTest(SeeAllData=true)` on test classes that need access to shared records, often citing it as "the way to access org data in tests."

**Why it happens:** Training data bias — many older Salesforce code examples and Trailhead content used `SeeAllData=true` before test data factory patterns became standard. LLMs over-represent this older pattern.

**Correct pattern:**
```apex
@isTest
private class MyServiceTest {
    @testSetup
    static void setup() {
        Account a = new Account(Name = 'Test Account');
        insert a;
    }
    @isTest
    static void testSomething() {
        Account a = [SELECT Id FROM Account WHERE Name = 'Test Account' LIMIT 1];
        // use a
    }
}
```

**Detection hint:** Look for `SeeAllData=true` in generated test class annotations. If present alongside `@testSetup`, it is always wrong.

---

## Anti-Pattern 2: Generating sf data import tree JSON Without sf_reference_id

**What the LLM generates:** `sf data import tree` plan JSON where child records include the parent's Salesforce ID directly (e.g., `"AccountId": "0014x000001234ABC"`) instead of using the `@sf_reference_id` client-side reference system.

**Why it happens:** LLMs confuse the `sf data import tree` JSON format with generic REST API payloads where real IDs are used. The `@sf_reference_id` mechanism is specific to this CLI command and not widely documented in general Salesforce content.

**Correct pattern:**
```json
// Parent
{"attributes": {"type": "Account", "referenceId": "AccountRef1"}, "Name": "ACME"}

// Child - uses @AccountRef1, NOT a hardcoded ID
{"attributes": {"type": "Contact", "referenceId": "ContactRef1"}, "AccountId": "@AccountRef1", "LastName": "Doe"}
```

**Detection hint:** Look for hardcoded 18-character IDs (pattern `[0-9A-Za-z]{15,18}`) in `sf data import tree` JSON children. These will fail in any target org because IDs differ per org.

---

## Anti-Pattern 3: Placing Child Objects Before Parents in Plan JSON

**What the LLM generates:** A `plan.json` with `Contact` or `Opportunity` steps appearing before the `Account` step when accounts are referenced by contacts.

**Why it happens:** LLMs generating plan files may alphabetize or list objects without considering dependency order, treating the plan as an unordered collection.

**Correct pattern:**
```json
[
  {"sobject": "Account", "saveRefs": true, "resolveRefs": false, "files": ["Account.json"]},
  {"sobject": "Contact", "saveRefs": false, "resolveRefs": true, "files": ["Contact.json"]}
]
```
Parent objects with `saveRefs: true` must appear before child objects with `resolveRefs: true`.

**Detection hint:** Any plan where a step with `resolveRefs: true` appears before the step that `saveRefs: true` for the referenced object.

---

## Anti-Pattern 4: Recommending Thread.sleep() for Async Data Setup

**What the LLM generates:** `Thread.sleep(2000)` or similar delays in test setup to "wait for async processes to complete" after inserting records, particularly for Platform Events or Process Builder automation.

**Why it happens:** Java/C# bleed — in those languages, sleeping to wait for async processing is a common (if bad) pattern. Apex does not support `Thread.sleep()` (throws a compiler error), but LLMs sometimes suggest it anyway, or suggest it in setup scripts outside Apex.

**Correct pattern:** For async test completion, use `Test.startTest()` and `Test.stopTest()` to flush async operations within the test transaction. For external scripts, poll with a SOQL query using exponential backoff rather than a fixed sleep.

**Detection hint:** Any mention of `Thread.sleep`, `wait()`, or fixed delays in Apex test setup code.

---

## Anti-Pattern 5: Suggesting Direct Production Data Export Without Masking

**What the LLM generates:** Instructions to run `sf data export` from production and import the resulting CSV/JSON directly into a sandbox or scratch org for test data.

**Why it happens:** LLMs optimize for "realistic data" without considering PII compliance. Production data export without masking violates GDPR, CCPA, and Salesforce's own data handling guidelines for lower environments.

**Correct pattern:** Use CumulusCI `capture_dataset` with field masking configured for all PII fields (Email, Phone, Name, SSN, etc.) before committing dataset files. Alternatively, use Snowfakery to generate fully synthetic data that is realistic in shape but contains no real personal information.

**Detection hint:** Any instruction involving `sf data export` from a production org followed by import into a non-production org, without mention of masking or anonymization.
