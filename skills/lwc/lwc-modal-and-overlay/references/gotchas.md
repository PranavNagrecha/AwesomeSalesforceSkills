# Gotchas - LWC Modal And Overlay

## `LightningModal` Has A Different Mental Model Than Template Toggles

**What happens:** Developers expect to open the modal by conditionally rendering it in the parent template.

**When it occurs:** Teams approach the modal as normal component markup instead of an overlay API.

**How to avoid:** Treat the modal as an interaction surface opened through `LightningModal.open()` and closed through `close(result)`.

---

## Focus Return Is Easy To Forget

**What happens:** The modal closes, but keyboard users land at the top of the page or lose context.

**When it occurs:** The launching control is not remembered and focus restoration is left implicit.

**How to avoid:** Store the launcher when appropriate and define where focus should return after cancel or success.

---

## Overlays Multiply Quickly

**What happens:** A modal opens another dialog or quick action, and the user can no longer reason about the stack.

**When it occurs:** Teams keep escalating interruption instead of simplifying the workflow.

**How to avoid:** Avoid nested overlays and move larger workflows to a dedicated page or flow experience.

---

## Blocking Close During Save Must Be Temporary

**What happens:** Users are trapped in an overlay with no escape path after an error or long-running action.

**When it occurs:** `disableClose` or an equivalent pattern is left active longer than the bounded save window.

**How to avoid:** Pair any temporary close lock with visible progress, timeout awareness, and immediate restoration once the action settles.
