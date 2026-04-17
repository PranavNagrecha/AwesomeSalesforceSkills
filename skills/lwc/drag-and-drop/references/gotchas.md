# Gotchas — LWC Drag and Drop

## Gotcha 1: Missing preventDefault

**What happens:** Drop never fires; silent bug.

**When it occurs:** Forgot on `dragover`.

**How to avoid:** Template modifier `@dragover.prevent` or preventDefault in handler.


---

## Gotcha 2: Touch devices

**What happens:** Mobile users can't reorder.

**When it occurs:** Drag events only.

**How to avoid:** Feature-detect + render reorder buttons.


---

## Gotcha 3: No keyboard path

**What happens:** A11y audit fails.

**When it occurs:** Drag-only.

**How to avoid:** Always ship keyboard alternative.

