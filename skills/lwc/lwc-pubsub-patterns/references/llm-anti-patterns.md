# LLM Anti-Patterns — LWC Pub/Sub Patterns

Mistakes AI assistants commonly make when generating LWC sibling-
communication code.

---

## Anti-Pattern 1: Subscribe without matching unsubscribe

**What the LLM generates.**

```javascript
connectedCallback() {
    subscribe(this.messageContext, MY_CHANNEL, this.handle);
}
// (no disconnectedCallback)
```

**Why it happens.** The LLM emits the simplest version that "works"
on first render.

**Correct pattern.**

```javascript
connectedCallback() {
    if (this.subscription) return;
    this.subscription = subscribe(this.messageContext, MY_CHANNEL, this.handle);
}
disconnectedCallback() {
    unsubscribe(this.subscription);
    this.subscription = null;
}
```

Always pair subscribe with unsubscribe; guard against re-subscribe.

**Detection hint.** Any LWC with `subscribe(` but no `unsubscribe(`
in the same file.

---

## Anti-Pattern 2: Using LMS for parent-child communication

**What the LLM generates.**

> Parent and child should communicate via LMS.

**Why it happens.** Treating LMS as the universal answer.

**Correct pattern.** Parent-child uses `@api` props (down) and
`CustomEvent` (up). LMS is for siblings without a shared parent.

**Detection hint.** Any LMS recommendation between components in a
direct parent-child template relationship.

---

## Anti-Pattern 3: Recommending the legacy `c/pubsub` for new code

**What the LLM generates.**

```javascript
import { fireEvent, registerListener } from 'c/pubsub';
```

**Why it happens.** `c/pubsub` is older training data and the
samples are abundant.

**Correct pattern.** New code uses Lightning Message Service.
`c/pubsub` is a community utility, not platform-supported, and
cannot be consumed by Aura / Visualforce.

**Detection hint.** Any new-development recommendation importing
`c/pubsub`.

---

## Anti-Pattern 4: LMS for cross-tab communication

**What the LLM generates.**

> Use LMS to coordinate state across browser tabs.

**Why it happens.** "Pub/sub" is conflated with cross-process
messaging.

**Correct pattern.** LMS is per-tab. Cross-tab needs Platform
Events (or a shared backend / `BroadcastChannel` if tabs are in the
same origin).

**Detection hint.** Any LMS recommendation that mentions multiple
tabs or windows.

---

## Anti-Pattern 5: Default scope when publisher and subscriber are in different navigation contexts

**What the LLM generates.**

```javascript
subscribe(this.messageContext, MY_CHANNEL, handler);
// (no scope option)
```

**Why it happens.** Defaults are simpler.

**Correct pattern.** When publisher and subscriber may be in
different navigation contexts (e.g. utility bar vs page-level), use
`{ scope: APPLICATION_SCOPE }`.

**Detection hint.** Any LMS subscribe involving a utility bar or
cross-app component without `APPLICATION_SCOPE`.

---

## Anti-Pattern 6: Sending non-serializable payloads

**What the LLM generates.**

```javascript
publish(this.messageContext, MY_CHANNEL, {
    handler: () => doStuff(),  // function
    instance: this              // component reference
});
```

**Why it happens.** JS lets you pass anything as an object.

**Correct pattern.** LMS messages must be JSON-serializable.
Functions are stripped. References are flattened. Use plain data;
if you need richer interaction, the components are likely
parent-child and should use direct method calls.

**Detection hint.** Any `publish` call payload containing functions
or class instances.

---

## Anti-Pattern 7: Subscribing in `renderedCallback` without guard

**What the LLM generates.**

```javascript
renderedCallback() {
    subscribe(this.messageContext, MY_CHANNEL, this.handle);
}
```

**Why it happens.** `renderedCallback` is a common place to put
post-render setup.

**Correct pattern.** `renderedCallback` fires on every render.
Subscribing there without guarding produces duplicate subscriptions.
Guard with `if (!this.subscription)` and remember to unsubscribe in
`disconnectedCallback`.

**Detection hint.** Any subscribe in `renderedCallback` without a
subscription-existence guard.
