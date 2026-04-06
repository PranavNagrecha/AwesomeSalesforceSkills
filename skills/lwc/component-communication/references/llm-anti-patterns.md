# LLM Anti-Patterns — Component Communication

Common mistakes AI coding assistants make when generating or advising on LWC component communication patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Lightning Message Service for parent-child communication

**What the LLM generates:**

```javascript
// Parent publishes on a message channel to talk to its own child
import { publish, MessageContext } from 'lightning/messageService';
import MY_CHANNEL from '@salesforce/messageChannel/ParentChildChannel__c';

publish(this.messageContext, MY_CHANNEL, { recordId: this.recordId });
```

**Why it happens:** LMS appears frequently in training data as the "universal" LWC communication mechanism, so models default to it even when the relationship is direct parent-child.

**Correct pattern:**

```html
<!-- Parent passes data down via @api property -->
<c-child-component record-id={recordId}></c-child-component>
```

**Detection hint:** Look for `messageChannel` imports in components that also contain the target component in their HTML template.

---

## Anti-Pattern 2: Dispatching custom events with `bubbles: true, composed: true` by default

**What the LLM generates:**

```javascript
this.dispatchEvent(new CustomEvent('select', {
    detail: { id: this.recordId },
    bubbles: true,
    composed: true
}));
```

**Why it happens:** Training data often includes Aura-era patterns or Stack Overflow snippets where `composed: true` was needed to escape Aura wrapper boundaries. LLMs apply this indiscriminately.

**Correct pattern:**

```javascript
// Default: bubbles: false, composed: false — event reaches direct parent only
this.dispatchEvent(new CustomEvent('select', {
    detail: { id: this.recordId }
}));
```

Only set `bubbles: true, composed: true` when the event genuinely must cross shadow DOM boundaries to reach an ancestor that is not the direct parent.

**Detection hint:** Regex `composed:\s*true` in custom event constructors — flag for review unless cross-shadow traversal is explicitly justified.

---

## Anti-Pattern 3: Passing mutable objects down via @api and mutating them in the child

**What the LLM generates:**

```javascript
// Child component
@api record;

handleUpdate() {
    this.record.Name = 'Updated'; // Mutates parent's object reference
}
```

**Why it happens:** In plain JavaScript, object references are shared, and many generic JS tutorials mutate props directly. LLMs carry this habit into LWC where it violates the one-way data flow contract.

**Correct pattern:**

```javascript
// Child: dispatch an event with the intended change
handleUpdate() {
    this.dispatchEvent(new CustomEvent('namechange', {
        detail: { name: 'Updated' }
    }));
}

// Parent: handles event and updates its own state
handleNameChange(event) {
    this.record = { ...this.record, Name: event.detail.name };
}
```

**Detection hint:** Look for direct property assignment on `this.<@api property>.<field>` inside child component methods.

---

## Anti-Pattern 4: Calling child public methods instead of using reactive @api properties

**What the LLM generates:**

```javascript
// Parent calls child method imperatively
this.template.querySelector('c-child').refreshData(this.newFilter);
```

**Why it happens:** Imperative method calls feel familiar to developers coming from OOP or Aura backgrounds. LLMs mirror this preference because imperative examples are heavily represented in training data.

**Correct pattern:**

```html
<!-- Let the reactive system handle it — child reacts to property change -->
<c-child filter-value={currentFilter}></c-child>
```

```javascript
// Child: use a setter or wire to react
@api
get filterValue() { return this._filter; }
set filterValue(val) {
    this._filter = val;
    this.loadData();
}
```

Public methods are appropriate only for imperative actions with no natural reactive trigger (e.g., `focus()`, `reset()`).

**Detection hint:** `querySelector.*\.\w+\(` calls on child component tags outside of focus/reset use cases.

---

## Anti-Pattern 5: Forgetting to unsubscribe from Lightning Message Service in disconnectedCallback

**What the LLM generates:**

```javascript
connectedCallback() {
    this.subscription = subscribe(this.messageContext, MY_CHANNEL, (msg) => {
        this.handleMessage(msg);
    }, { scope: APPLICATION_SCOPE });
}
// No disconnectedCallback — subscription leaks
```

**Why it happens:** Many LMS examples in training data show only the subscribe side. The cleanup step is in a different section or omitted entirely.

**Correct pattern:**

```javascript
connectedCallback() {
    this.subscription = subscribe(this.messageContext, MY_CHANNEL, (msg) => {
        this.handleMessage(msg);
    }, { scope: APPLICATION_SCOPE });
}

disconnectedCallback() {
    unsubscribe(this.subscription);
    this.subscription = null;
}
```

**Detection hint:** File contains `subscribe(` from `lightning/messageService` but no `unsubscribe(` call.

---

## Anti-Pattern 6: Using APPLICATION_SCOPE when default scope is sufficient

**What the LLM generates:**

```javascript
subscribe(this.messageContext, MY_CHANNEL, handler, { scope: APPLICATION_SCOPE });
```

**Why it happens:** LLMs treat `APPLICATION_SCOPE` as the "safe default" because it makes messages work across utility bars and workspace tabs. But in most cases, components are on the same page and default scope is correct and more efficient.

**Correct pattern:**

```javascript
// Default scope — only receives messages from the active page area
subscribe(this.messageContext, MY_CHANNEL, handler);
```

Use `APPLICATION_SCOPE` only when components genuinely live in different workspace tabs or utility bars.

**Detection hint:** `APPLICATION_SCOPE` with no comment explaining why cross-tab delivery is needed.
