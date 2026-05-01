# Examples — LWC Reactive State Patterns

## Example 1 — "Selected items array does not rerender after toggle"

**Context:** A component renders a list of opportunity rows with a
checkbox on each. Clicking the checkbox toggles `selected: true` on the
matching row in `this.opportunities`. The handler runs but the visual
checkbox state does not update.

**Problem:** The handler mutates the array element in place, and
`opportunities` has no `@track`:

```javascript
// BUG
handleToggle(event) {
  const id = event.target.dataset.id;
  const row = this.opportunities.find(o => o.Id === id);
  row.selected = !row.selected; // in-place mutation, NOT reactive
}
```

**Solution:** Reassign the array with a fresh row object:

```javascript
handleToggle(event) {
  const id = event.target.dataset.id;
  this.opportunities = this.opportunities.map(o =>
    o.Id === id ? { ...o, selected: !o.selected } : o
  );
}
```

**Why it works:** Reassigning `this.opportunities` is reactive in API
v48+. The new object literal for the toggled row is a fresh reference
the diffing layer can detect. No `@track` needed.

---

## Example 2 — "Set-based filter never updates the UI"

**Context:** A filter UI lets users add tags. The component holds
`activeTags = new Set()` and pushes new tags via `this.activeTags.add(tag)`.
Tag count in the header is bound to `activeTags.size`. Clicking "add tag"
runs the handler but the count stays at 0.

**Problem:** `Set` is not observed. Even adding `@track` does not help:

```javascript
// BUG — neither without nor with @track does this rerender
@track activeTags = new Set();

addTag(tag) {
  this.activeTags.add(tag); // no rerender
}
```

**Solution:** Re-create the Set and reassign:

```javascript
activeTags = new Set();

addTag(tag) {
  this.activeTags = new Set([...this.activeTags, tag]);
}

removeTag(tag) {
  const next = new Set(this.activeTags);
  next.delete(tag);
  this.activeTags = next;
}
```

**Why it works:** Reassignment is reactive; the contents of the new Set
do not need to be observed because every change produces a new Set
instance. Same shape works for Map (`new Map([...this.cache, [k, v]])`)
and Date (`new Date(this.lastUpdated.getTime())` then mutate the new
instance, then reassign — or build a fresh Date end-to-end).

---

## Anti-Pattern — "Adding @track to every field as a precaution"

**What practitioners do:** Decorate every reactive field with `@track`
"to be safe", on the theory that it can never hurt:

```javascript
import { LightningElement, track } from 'lwc';
export default class Defensive extends LightningElement {
  @track count = 0;
  @track userName = '';
  @track isLoading = false;
  @track lastUpdated = new Date();
  @track activeTags = new Set();
}
```

**What goes wrong:** Three real harms.

1. The decorator is now noise — readers cannot tell which fields
   actually need deep observation versus which were decorated by habit.
2. The Date and Set fields are still not reactive. `@track` does not
   make them so. The developer who wrote the code typically does not
   know, and the bug surfaces months later.
3. Code review loses a useful signal. A reviewer who sees `@track` on
   a primitive field correctly suspects the author is unfamiliar with
   the post–Spring '20 rules; that signal is gone if every field has
   it.

**Correct approach:** Use `@track` only when the rules in `SKILL.md`
Pattern B specifically apply. Pin the component's `apiVersion` to ≥ 48
in `js-meta.xml`. For primitives and reassignment-style updates, omit
the decorator. For Date/Set/Map, use re-create-and-reassign.
