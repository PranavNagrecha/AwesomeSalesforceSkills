# Gotchas — Flow Reactive Screen Components

## Gotcha 1: Heavy action in reactive

**What happens:** UI freezes.

**When it occurs:** Apex action fires on every keystroke.

**How to avoid:** Use onchange sparingly; debounce with explicit Next.


---

## Gotcha 2: Custom LWC not reactive

**What happens:** Doesn't update others.

**When it occurs:** Missing FlowAttributeChangeEvent.

**How to avoid:** Implement the dispatch.


---

## Gotcha 3: Mobile lag

**What happens:** Updates delayed.

**When it occurs:** Large screen payload.

**How to avoid:** Slim screens; test mobile explicitly.

