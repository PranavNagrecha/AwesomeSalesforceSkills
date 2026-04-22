# LLM Anti-Patterns — LWC NavigationMixin

Common mistakes AI coding assistants make with LWC navigation.

## Anti-Pattern 1: Using window.location for navigation

**What the LLM generates:** `window.location.href = '/r/Account/001.../view';`

**Why it happens:** Model applies general web practice.

**Correct pattern:**

```
this[NavigationMixin.Navigate]({
    type: 'standard__recordPage',
    attributes: { recordId, objectApiName: 'Account', actionName: 'view' }
});

window.location bypasses Salesforce's router — breaks in Mobile,
Experience Cloud, and tab-aware apps.
```

**Detection hint:** LWC JS assigning to `window.location.href` or calling `window.open`.

---

## Anti-Pattern 2: Not extending NavigationMixin

**What the LLM generates:**

```
import { NavigationMixin } from 'lightning/navigation';
export default class Foo extends LightningElement {
    goToRecord() { this[NavigationMixin.Navigate]({...}); }  // undefined
}
```

**Why it happens:** Model imports but forgets the class extension.

**Correct pattern:**

```
export default class Foo extends NavigationMixin(LightningElement) {
    goToRecord() { this[NavigationMixin.Navigate]({...}); }
}

NavigationMixin must be applied as a class extension to inject
the Navigate / GenerateUrl symbols on `this`.
```

**Detection hint:** LWC importing NavigationMixin but extending plain LightningElement.

---

## Anti-Pattern 3: Mixing standard__ and comm__ page refs

**What the LLM generates:** In an Experience Cloud component, uses `standard__namedPage`.

**Why it happens:** Model doesn't know the surface distinction.

**Correct pattern:**

```
Experience Cloud requires comm__namedPage (and related comm__* types).
standard__* types work in internal Lightning app only.

Detect context via @api isInCommunity or branch at build time; use
the correct type per surface.
```

**Detection hint:** LWC intended for Experience Cloud (in `force-app/main/default/experiences/...` or with `isExposed` + `targets` including community pages) using `standard__namedPage`.

---

## Anti-Pattern 4: Not awaiting GenerateUrl promise

**What the LLM generates:**

```
const url = this[NavigationMixin.GenerateUrl](ref);
window.open(url);  // url is a Promise, not a string
```

**Why it happens:** Model treats it as synchronous.

**Correct pattern:**

```
const url = await this[NavigationMixin.GenerateUrl](ref);
window.open(url);

Or:
this[NavigationMixin.GenerateUrl](ref).then(url => ...);
```

**Detection hint:** LWC using `GenerateUrl` result without `await` or `.then`.

---

## Anti-Pattern 5: Omitting c__ prefix on custom state params

**What the LLM generates:** `{ state: { selectedTab: 'history' } }`

**Why it happens:** Model picks a reasonable name without knowing the framework rule.

**Correct pattern:**

```
{ state: { c__selectedTab: 'history' } }

Custom state params must start with c__ (or ns__ for namespaced
packages). Without the prefix, the framework may drop them or
collide with reserved keys.
```

**Detection hint:** PageReference state object with keys that don't start with `c__` or a namespace prefix.
