# Gotchas — LWC Imperative Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: refreshApex() Is a No-Op on Imperative Results

**What happens:** Calling `refreshApex(this.someProperty)` after a write operation returns a resolved Promise but does not re-fetch data. The component displays stale values with no error or warning.

**When it occurs:** Practitioners who know `refreshApex` from wire patterns apply it to imperative calls when they want fresh data after a save. Because it returns a Promise (not throwing), the code appears correct during review. The bug only shows up at runtime when the UI fails to reflect the newly saved data.

**How to avoid:** Always re-call the Apex method imperatively and assign the result back to the reactive property. `refreshApex` is exclusively a wire-service utility and has no effect on values obtained via direct function calls.

```js
// Correct: re-call after write
this.contacts = await getContacts({ accountId: this.recordId });

// Wrong: does nothing for imperative variables
await refreshApex(this.contacts);
```

---

## Gotcha 2: cacheable=true Throws at Runtime if Any DML Occurs in the Call Stack

**What happens:** Salesforce enforces the `cacheable=true` constraint at runtime, not at compile time. If a `@AuraEnabled(cacheable=true)` method calls a utility method, trigger logic fires, or a flow is invoked that performs DML, Salesforce throws `System.QueryException: Callout not allowed after DML` and the Apex call fails for all users.

**When it occurs:** The original developer marks the method cacheable because the primary logic is a SOQL query, not realizing that a `before insert` trigger on a queried object runs a DML operation, or that a utility helper internally inserts an audit log record. It is also common in orgs that add new trigger logic after the component was already deployed.

**How to avoid:** Mark methods `@AuraEnabled(cacheable=true)` only when you can guarantee that the entire execution path — including triggers, flows, and helpers invoked by the method — never performs DML. When in doubt, use `@AuraEnabled` without `cacheable=true`. The caching benefit is real but the runtime error is catastrophic.

---

## Gotcha 3: Apex Parameter Names Are Case-Sensitive — Null Is Silently Passed

**What happens:** When the JavaScript call passes a parameter key that does not exactly match the Apex parameter name (including casing), Apex receives `null` for that parameter. No error is thrown by the platform. The Apex method runs with null input, which may silently return empty results or throw a null pointer exception inside the Apex body.

**When it occurs:** The Apex method uses camelCase (`accountId`) but the LWC call uses PascalCase (`AccountId`) or a different spelling. This is especially common when copying parameter names from Salesforce's standard field API names (which are `PascalCase`) into imperative call arguments.

**How to avoid:** Match parameter names exactly. Add a null check at the top of the Apex method to surface mismatches quickly:

```apex
@AuraEnabled(cacheable=true)
public static List<Contact> getContacts(Id accountId) {
    if (accountId == null) {
        throw new AuraHandledException('accountId is required');
    }
    return [SELECT Id, Name FROM Contact WHERE AccountId = :accountId];
}
```

The JS call must then pass `{ accountId: this.recordId }` — lowercase `a`.

---

## Gotcha 4: Double-Submission When isLoading Is Not Set Synchronously

**What happens:** If `isLoading` is set inside the `try` block (after the first `await`) rather than as the first line of the handler, a fast user can click the button a second time before `isLoading` becomes `true`. This fires two concurrent Apex calls, causing duplicate DML operations.

**When it occurs:** Developers write `this.isLoading = true` after an intermediate step that uses `await`, such as validating fields asynchronously before saving.

**How to avoid:** Set `isLoading = true` as the very first synchronous statement in the handler, before any `await` expression. Setting it synchronously ensures the button is disabled before the browser can process another click event.

```js
async handleSave() {
    this.isLoading = true;  // <-- must be first, before any await
    try {
        await someValidation();
        await saveRecord({ ... });
    } finally {
        this.isLoading = false;
    }
}
```

---

## Gotcha 5: Error Object Shape Differs Between AuraHandledException and Unhandled Exceptions

**What happens:** When Apex throws `AuraHandledException`, the error object in the LWC catch block has `error.body.message` as a string. When Apex throws an unhandled exception (like a null pointer or a SOQL exception), `error.body` may be an array of objects each with a `message` property, or the shape may differ entirely depending on the exception type.

**When it occurs:** Developers write `this.error = error.body.message` expecting it to always be a string. When an unhandled exception occurs in production, `error.body.message` is `undefined` and the error display shows nothing.

**How to avoid:** Use a defensive `getErrorMessage` utility that handles both shapes:

```js
function getErrorMessage(error) {
    if (Array.isArray(error.body)) {
        return error.body.map(e => e.message).join(', ');
    }
    if (typeof error.body?.message === 'string') {
        return error.body.message;
    }
    return error.message ?? 'Unknown error';
}
```

Always throw `AuraHandledException` in Apex for user-facing error messages — it provides the cleanest `body.message` shape and lets you control the message text.
