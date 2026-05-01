# LLM Anti-Patterns — LWC Reactive State Patterns

Mistakes AI coding assistants commonly make about LWC reactivity. Each
entry is **what / why / correct / detection** so the consuming agent
can self-check.

## 1. Adding `@track` to every reactive field "to be safe"

**What the LLM generates:**

```javascript
import { LightningElement, track } from 'lwc';
export default class Defensive extends LightningElement {
  @track count = 0;
  @track userName = '';
  @track isLoading = false;
}
```

**Why:** Pre–Spring '20 docs and StackOverflow answers (the bulk of the
training corpus) all said `@track` was needed for reactivity. The
post-v48 simplification is underrepresented in training data, so LLMs
default to "always decorate" out of caution.

**Correct pattern:** Drop `@track` from primitives and from fields
updated via reassignment. Keep it only when in-place deep mutation is
genuinely needed.

```javascript
import { LightningElement } from 'lwc';
export default class Lean extends LightningElement {
  count = 0;
  userName = '';
  isLoading = false;
}
```

**Detection:** `@track` on a primitive field, or on a field whose only
updates use reassignment / spread, is a smell. Search for
`@track\s+\w+\s*=\s*(0|''|false|true|null)` to catch the obvious cases.

## 2. Recommending `@track` for Date / Set / Map mutations

**What the LLM generates:** "Decorate `lastUpdated` with `@track` so the
template rerenders when you call `setHours()`." Or: "Add `@track` to the
Set so `.add()` is reactive."

**Why:** LLMs treat `@track` as "make this reactive". The corpus does
not strongly distinguish between "field is reactive" and "field's
internal mutations are observed". For Date/Set/Map, neither applies.

**Correct pattern:** Re-create and reassign:

```javascript
// Date
this.lastUpdated = new Date();

// Set
this.tags = new Set([...this.tags, newTag]);

// Map
this.cache = new Map([...this.cache, [key, value]]);
```

**Detection:** `@track` on a field initialized to `new Date()`,
`new Set()`, or `new Map()` — always wrong.

## 3. Writing reactive fields in `renderedCallback` without a guard

**What the LLM generates:**

```javascript
renderedCallback() {
  this.measuredHeight = this.template.querySelector('.box').offsetHeight;
}
```

**Why:** "Read DOM after render" is a classic React lifecycle pattern
(`useLayoutEffect`). The LLM ports the pattern without porting the
guard idiom, because the React equivalent has implicit dependency
tracking (effects only re-run when deps change). LWC has no equivalent
implicit dependency tracking.

**Correct pattern:** Guard with `_hasRenderedOnce` for one-time setup;
use compare-then-set when the work must run on real layout changes.

```javascript
renderedCallback() {
  if (this._hasRenderedOnce) return;
  this._hasRenderedOnce = true;
  this.measuredHeight = this.template.querySelector('.box').offsetHeight;
}
```

**Detection:** `renderedCallback` whose body assigns `this.<field> =`
without an early-return guard or a compare-then-set pattern.

## 4. Reaching for `Object.assign` to "force reactivity"

**What the LLM generates:**

```javascript
this.user.name = 'Ada';
this.user = Object.assign({}, this.user); // "force a rerender"
```

**Why:** Older React/MobX/Vue idioms use `Object.assign({}, x)` as a
"refresh the reference" trick. LLMs port the idiom into LWC without
realizing that the spread `{ ...this.user, name: 'Ada' }` is the
equivalent in one step and avoids the in-place mutation entirely.

**Correct pattern:**

```javascript
this.user = { ...this.user, name: 'Ada' };
```

**Detection:** A line that mutates a property of `this.x` followed by
an `Object.assign({}, this.x)` reassignment. The mutation should be
folded into the spread.

## 5. Recommending Redux / Pinia / MobX as "the LWC state solution"

**What the LLM generates:** A long answer about installing a
third-party state library inside an LWC bundle, with explanations of
provider patterns and selectors.

**Why:** Cross-component state is a real problem and the LLM has rich
training data on Redux / Pinia / MobX. It defaults to those even when
the host platform offers built-ins (Lightning Message Service, custom
events, shared ES modules) that are friction-free.

**Correct pattern:** For component-local state, this skill's patterns
are sufficient. For cross-component state, prefer (in order):
1. Custom events for parent ↔ child.
2. Shared ES module exporting a small reactive store for siblings.
3. Lightning Message Service for cross-DOM-tree state (Aura host,
   different page, etc).

Reach for a third-party library only when none of the above fits, and
weigh the bundle-size cost — LWC bundles are constrained.

**Detection:** Output that mentions Redux, MobX, Pinia, Zustand, or
"global store" without first ruling out custom events + shared
modules + LMS.
