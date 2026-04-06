# LLM Anti-Patterns — LWC Imperative Apex

Common mistakes AI coding assistants make when generating or advising on imperative Apex calls from LWC.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Marking a DML method as cacheable

**What the LLM generates:**

```java
@AuraEnabled(cacheable=true)
public static void updateAccount(Id accountId, String name) {
    Account a = new Account(Id = accountId, Name = name);
    update a;
}
```

**Why it happens:** LLMs add `cacheable=true` by default because it appears in most @wire examples. But cacheable methods cannot perform DML — the platform throws a runtime error.

**Correct pattern:**

```java
@AuraEnabled
public static void updateAccount(Id accountId, String name) {
    Account a = new Account(Id = accountId, Name = name);
    update a;
}
```

Only use `cacheable=true` on read-only methods that return data.

**Detection hint:** `cacheable=true` on an Apex method that contains `insert`, `update`, `delete`, `upsert`, or `Database.` DML calls.

---

## Anti-Pattern 2: Not handling errors from the imperative call

**What the LLM generates:**

```javascript
handleClick() {
    doSomething({ recordId: this.recordId })
        .then(result => {
            this.data = result;
        });
    // No .catch() — errors silently swallowed
}
```

**Why it happens:** LLMs generate the happy path and omit error handling because it clutters the example. In production, unhandled Apex exceptions cause confusing failures.

**Correct pattern:**

```javascript
async handleClick() {
    try {
        this.data = await doSomething({ recordId: this.recordId });
    } catch (error) {
        this.dispatchEvent(new ShowToastEvent({
            title: 'Error',
            message: reduceErrors(error).join(', '),
            variant: 'error'
        }));
    }
}
```

**Detection hint:** `.then(` without a matching `.catch(` or `await` without a surrounding `try/catch`.

---

## Anti-Pattern 3: Using the wrong import path for Apex methods

**What the LLM generates:**

```javascript
import doSomething from '@salesforce/apex/MyController/doSomething';
// or
import doSomething from 'c/MyController.doSomething';
```

**Why it happens:** LLMs confuse the Apex import syntax with module imports or Java-style package paths.

**Correct pattern:**

```javascript
import doSomething from '@salesforce/apex/MyController.doSomething';
```

The format is always `@salesforce/apex/ClassName.methodName` with a dot separator.

**Detection hint:** Apex import paths using `/` instead of `.` between class and method, or missing the `@salesforce/apex/` prefix.

---

## Anti-Pattern 4: Calling refreshApex on imperative results instead of wired results

**What the LLM generates:**

```javascript
async handleSave() {
    await saveData({ record: this.record });
    await refreshApex(this.data); // this.data was set imperatively, not by @wire
}
```

**Why it happens:** LLMs see `refreshApex` in many examples and apply it universally. But `refreshApex` only works on the provisioned value from a `@wire` decorator. It does nothing for imperatively fetched data.

**Correct pattern:**

```javascript
// If data was fetched imperatively, just re-call the method
async handleSave() {
    await saveData({ record: this.record });
    this.data = await getData({ recordId: this.recordId });
}

// If using @wire, store the full wired result
@wire(getData, { recordId: '$recordId' })
wiredResult;

async handleSave() {
    await saveData({ record: this.record });
    await refreshApex(this.wiredResult); // Pass the wired property, not .data
}
```

**Detection hint:** `refreshApex` called on a variable that was assigned by an imperative call rather than a `@wire` decorator.

---

## Anti-Pattern 5: Not showing a loading state during the async call

**What the LLM generates:**

```javascript
async handleClick() {
    const result = await fetchRecords({ filter: this.filter });
    this.records = result;
}
```

**Why it happens:** Loading indicators are a UX concern that LLMs skip in favor of functional correctness. Users see nothing happen during the call, leading to double-clicks and confusion.

**Correct pattern:**

```javascript
async handleClick() {
    this.isLoading = true;
    try {
        this.records = await fetchRecords({ filter: this.filter });
    } catch (error) {
        this.error = reduceErrors(error);
    } finally {
        this.isLoading = false;
    }
}
```

```html
<lightning-spinner lwc:if={isLoading} alternative-text="Loading"></lightning-spinner>
```

**Detection hint:** Imperative Apex call without setting a loading flag before and after.

---

## Anti-Pattern 6: Passing complex objects instead of serializable primitives to Apex

**What the LLM generates:**

```javascript
// Passes a Proxy-wrapped LWC reactive object to Apex
saveRecord({ record: this.record });
```

**Why it happens:** LLMs pass LWC tracked/reactive objects directly. These are Proxy-wrapped and may not serialize correctly over the Aura bridge.

**Correct pattern:**

```javascript
saveRecord({ record: JSON.parse(JSON.stringify(this.record)) });
// Or pass individual primitive parameters
saveRecord({ name: this.record.Name, phone: this.record.Phone });
```

**Detection hint:** Imperative Apex call passing `this.<trackedProperty>` that is an object, without `JSON.parse(JSON.stringify(...))` or explicit destructuring.
