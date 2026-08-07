# LLM Anti-Patterns — LWC Testing

Common mistakes AI coding assistants make when generating or advising on LWC Jest tests.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Not awaiting DOM updates after state changes

**What the LLM generates:**

```javascript
it('shows the name after load', () => {
    const element = createElement('c-my-component', { is: MyComponent });
    document.body.appendChild(element);
    element.recordName = 'Test Account';

    const nameEl = element.shadowRoot.querySelector('.name');
    expect(nameEl.textContent).toBe('Test Account'); // Fails — DOM not yet updated
});
```

**Why it happens:** LLMs write synchronous assertions because that is simpler. LWC rerenders are microtask-based and require a Promise flush before the DOM reflects new state.

**Correct pattern:**

```javascript
it('shows the name after load', async () => {
    const element = createElement('c-my-component', { is: MyComponent });
    document.body.appendChild(element);
    element.recordName = 'Test Account';

    await Promise.resolve(); // or await flushPromises();
    const nameEl = element.shadowRoot.querySelector('.name');
    expect(nameEl.textContent).toBe('Test Account');
});
```

**Detection hint:** Test assertions on `shadowRoot.querySelector` results without a preceding `await Promise.resolve()` or `await flushPromises()`.

---

## Anti-Pattern 2: Not mocking @wire adapters correctly

**What the LLM generates:**

```javascript
import { getRecord } from 'lightning/uiRecordApi';

jest.mock('lightning/uiRecordApi', () => ({
    getRecord: jest.fn()
}));
```

**Why it happens:** LLMs mock wire adapters like regular `jest.fn()` functions. A wire adapter is a class the framework instantiates, not a function it calls, so a plain mock never provisions anything — the component renders its loading state forever and the assertion fails with no useful message. The `create*TestWireAdapter` factories from `@salesforce/sfdx-lwc-jest` produce a real adapter shape with `emit()`, `error()`/`emitError()`, and `getLastConfig()`.

**Correct pattern:**

```javascript
import { getRecord } from 'lightning/uiRecordApi';

jest.mock(
    'lightning/uiRecordApi',
    () => {
        const { createLdsTestWireAdapter } = require('@salesforce/sfdx-lwc-jest');
        return { getRecord: createLdsTestWireAdapter(jest.fn()) };
    },
    { virtual: true }
);

// In the test — the mocked export IS the adapter:
getRecord.emit(mockData);
await flushPromises();

// Error path:
getRecord.error({ message: 'Not found' }, 404);
```

For Apex, the same shape with `createApexTestWireAdapter` and the `@salesforce/apex/Class.method` module path.

**Detection hint:** a `jest.mock('lightning/uiRecordApi')` factory that returns bare `jest.fn()`s rather than `createLdsTestWireAdapter(...)` — i.e. `jest.mock` is correct and required, what matters is what the factory returns. Note that `jest.mock` plus `create*TestWireAdapter` is exactly what Salesforce now prescribes, so do **not** flag `jest.mock` itself.

---

## Anti-Pattern 3: Testing implementation details instead of observable behavior

**What the LLM generates:**

```javascript
it('calls the handler method', () => {
    const spy = jest.spyOn(element, 'handleClick');
    const button = element.shadowRoot.querySelector('lightning-button');
    button.click();
    expect(spy).toHaveBeenCalled();
});
```

**Why it happens:** LLMs spy on internal methods because it is easy to assert. This creates brittle tests that break when the method is renamed but behavior is unchanged.

**Correct pattern:**

```javascript
it('dispatches select event on button click', async () => {
    const handler = jest.fn();
    element.addEventListener('select', handler);

    const button = element.shadowRoot.querySelector('lightning-button');
    button.click();
    await flushPromises();

    expect(handler).toHaveBeenCalled();
    expect(handler.mock.calls[0][0].detail).toEqual({ id: '001xx000003ABCD' });
});
```

Test what the user or parent component observes: dispatched events, rendered output, navigation calls.

**Detection hint:** `jest.spyOn(element, '<privateMethodName>')` in test files.

---

## Anti-Pattern 4: Not cleaning up the DOM between tests

**What the LLM generates:**

```javascript
describe('c-my-component', () => {
    it('test one', () => {
        const element = createElement('c-my-component', { is: MyComponent });
        document.body.appendChild(element);
        // No cleanup
    });

    it('test two', () => {
        // Previous component still in DOM — tests bleed into each other
    });
});
```

**Why it happens:** LLMs omit `afterEach` cleanup because it is boilerplate. Without it, components from previous tests remain attached and can interfere.

**Correct pattern:**

```javascript
afterEach(() => {
    while (document.body.firstChild) {
        document.body.removeChild(document.body.firstChild);
    }
    jest.clearAllMocks();
});
```

**Detection hint:** Test file with `document.body.appendChild` but no `afterEach` block that removes children.

---

## Anti-Pattern 5: Mocking imperative Apex with the wrong pattern

**What the LLM generates:**

```javascript
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

jest.mock('@salesforce/apex/AccountController.getAccounts', () => jest.fn(), {
    virtual: true
});

it('loads accounts', async () => {
    getAccounts.mockResolvedValue(mockData);
    // Component never calls the mock because it was imported before mock was set up
});
```

**Why it happens:** LLMs mix up the mock timing and the `virtual: true` requirement for `@salesforce/apex` modules, which do not exist on disk.

**Correct pattern:**

```javascript
import getAccounts from '@salesforce/apex/AccountController.getAccounts';

// Jest automatically handles @salesforce/apex/* mocks with sfdx-lwc-jest
// Just set the resolved value before triggering the component behavior:
jest.mock(
    '@salesforce/apex/AccountController.getAccounts',
    () => ({ default: jest.fn() }),
    { virtual: true }
);

it('loads accounts', async () => {
    getAccounts.mockResolvedValue(mockData);
    const element = createElement('c-account-list', { is: AccountList });
    document.body.appendChild(element);
    await flushPromises();

    const items = element.shadowRoot.querySelectorAll('.account-item');
    expect(items.length).toBe(mockData.length);
});
```

**Detection hint:** `jest.mock('@salesforce/apex/...')` without `{ virtual: true }` or with incorrect default export structure.

---

## Anti-Pattern 6: Hardcoding mock data inline instead of using separate fixture files

**What the LLM generates:**

```javascript
it('renders contacts', async () => {
    getContacts.mockResolvedValue([
        { Id: '003xx1', FirstName: 'John', LastName: 'Doe', Email: 'john@test.com' },
        { Id: '003xx2', FirstName: 'Jane', LastName: 'Doe', Email: 'jane@test.com' },
        // 20 more inline records...
    ]);
});
```

**Why it happens:** LLMs inline mock data for self-contained examples. Large inline data blocks make tests hard to read and the mock data hard to reuse across tests.

**Correct pattern:**

```javascript
// __tests__/data/getContacts.json
// Store mock data in a separate file

import mockContacts from './data/getContacts.json';

it('renders contacts', async () => {
    getContacts.mockResolvedValue(mockContacts);
});
```

**Detection hint:** More than 10 lines of literal mock data inside a test function body.


---

## Anti-Pattern: `register*TestWireAdapter` — the removed wire-service-jest-util 2.x API

**What the LLM generates:**

```javascript
import { registerApexTestWireAdapter } from '@salesforce/sfdx-lwc-jest';
import getCases from '@salesforce/apex/CaseController.getCases';

const getCasesAdapter = registerApexTestWireAdapter(getCases);
getCasesAdapter.emit([]);
```

…and, in its inverted form, an anti-pattern rule that flags the *correct* modern shape: "using `jest.mock('lightning/uiRecordApi')` instead of `registerLdsTestWireAdapter` is wrong."

**Why it happens:** `register*TestWireAdapter` was the real API for years and dominates the blog/StackExchange corpus. It was superseded in wire-service-jest-util **3.x** — the version current `sfdx-lwc-jest` bundles — and the official migration doc states: *"With your wire adapters mocked using `create*TestWireAdapter`, you can use them directly in your test, making `register*TestWireAdapter` unnecessary."* The import simply does not resolve now, so the whole test file fails to load and the error (an unresolved named export) points at the import line rather than at the pattern.

The inverted variant is the more damaging half: it tells a reviewer to reject `jest.mock`, which is precisely what Salesforce now prescribes.

**Correct version:**

```javascript
jest.mock(
    '@salesforce/apex/CaseController.getCases',
    () => {
        const { createApexTestWireAdapter } = require('@salesforce/sfdx-lwc-jest');
        return { default: createApexTestWireAdapter(jest.fn()) };
    },
    { virtual: true }
);

// the mocked export IS the adapter
getCases.emit([{ Id: '500...' }]);
getCases.error({ message: 'boom' }, 500);
getCases.getLastConfig();
```

Three factories exist: `createTestWireAdapter` (generic), `createLdsTestWireAdapter` (LDS shape), `createApexTestWireAdapter` (Apex, also callable imperatively). All are re-exported from `@salesforce/sfdx-lwc-jest`, so no extra dependency is needed. The key mental shift: **there is no separate handle.** The mocked module export is the adapter you call `.emit()` on.

**Detection hint:** grep test files and LWC testing guidance for `registerApexTestWireAdapter`, `registerLdsTestWireAdapter`, `registerTestWireAdapter` — all three are removed. Structural hint: `const someAdapter = register…(someImport)` assigns a *handle* separate from the import; in the 3.x API no such variable exists, so any two-name pattern (`getCases` and `getCasesAdapter` both in scope) is a 2.x tell. Inverted-rule hint: any guidance that lists `jest.mock` as the anti-pattern and `register*` as the fix has the polarity backwards.
